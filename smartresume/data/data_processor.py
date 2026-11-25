import re
from copy import deepcopy
import os
import string
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import tiktoken
import unicodedata
from smartresume.utils.config import config
from smartresume.utils.extraction_schema import RECORD_ROOTS


class DataProcessor:

    def __init__(self):

        self.encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
        self.pattern = r"[a-zA-Z0-9\-~_]{40,}"
        self.word_chars = set()
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            word_path = os.path.join(current_dir, "word.txt")
            if os.path.exists(word_path):
                with open(word_path, "r", encoding="utf-8") as f:
                    self.word_chars = set(f.read().strip().split("\n"))
        except Exception:
            pass

    def should_remove(self, match: re.Match) -> bool:

        encoded = self.encoding.encode(match.group(0))
        return len(encoded) > len(match.group(0)) * 0.5

    def _remove_spaces_around_chars(self, text: str) -> str:

        if not self.word_chars:
            return text
        has_word_chars = any(c in self.word_chars for c in text)
        if not has_word_chars:
            return text
        result = []
        for char in text:
            if char in self.word_chars or not char.isspace():
                result.append(char)
        return "".join(result)

    def build_text_content(
        self,
        processed_data: List[Dict[str, Any]],
        resume_id: str = "",
        use_hybrid_text: bool = False,
    ) -> Tuple[List[str], str, str]:

        text_lines = []
        text_key = "text_hybrid" if use_hybrid_text else "text"

        for page_data in processed_data:
            page_text = page_data.get(text_key) or page_data.get("text")
            if not page_text:
                continue
            if isinstance(page_text, list):
                for text_item in page_text:
                    if isinstance(text_item, dict) and "text" in text_item:
                        text = self._clean_text_content(text_item["text"])
                        text = self._remove_spaces_around_chars(text)
                        if text:
                            text_lines.extend(self._split_text_lines(text))
                    elif isinstance(text_item, str) and text_item.strip():
                        text_lines.extend(self._split_text_lines(text_item))
            elif isinstance(page_text, str) and page_text.strip():
                text_lines.extend(self._split_text_lines(page_text))

        text_content = "\n".join(text_lines)

        indexed_text_content = self._build_indexed_content(text_lines)

        return text_lines, text_content, indexed_text_content

    def _clean_text_content(self, text: str) -> str:

        if not text:
            return ""

        text = unicodedata.normalize("NFKC", text)

        text = re.sub(
            r"[\u0020\u00A0\u1680\u2000-\u200A"
            r"\u2028\u2029\u202F\u205F\u3000\u00A7]",
            " ",
            text,
        )

        text = re.sub(r" {2,}", " ", text)

        text = re.sub(
            self.pattern,
            lambda m: "" if self.should_remove(m) else m.group(0),
            text,
        )

        return text.strip()

    def _split_text_lines(self, text: str) -> List[str]:

        if "\n" in text:
            return [line.strip() for line in text.split("\n") if line.strip()]
        else:
            return [text.strip()] if text.strip() else []

    def _build_indexed_content(self, text_lines: List[str]) -> str:

        trans_table = str.maketrans("", "", '""\'\\')
        indexed_text_lines = []
        for i, line in enumerate(text_lines):
            content = (
                line.translate(trans_table) if isinstance(line, str) else ""
            )
            indexed_text_lines.append(f"[{i}]:{content}")
        return "\n".join(indexed_text_lines)

    def post_process(
        self,
        text_lines: List[str],
        structure_output: Dict[str, Any],
        processed_data: List[Dict[str, Any]],
    ) -> Dict[str, Any]:

        try:
            processed_result = self.process_resume_data(
                structure_output, text_lines
            )

            pages_info = self._extract_pages_info(processed_data)
            if pages_info:
                processed_result["pages"] = pages_info

            processed_result["metadata"] = {
                "text_lines_count": len(text_lines),
                "pages_count": len(processed_data),
            }

            return processed_result

        except Exception:
            return structure_output

    @staticmethod
    def _records(value):

        if not isinstance(value, list):
            return []
        return [deepcopy(item) for item in value if isinstance(item, dict)]

    def process_resume_data(
        self, raw_data: Dict[str, Any], text_lines: List[str]
    ) -> Dict[str, Any]:

        if not isinstance(raw_data, dict):
            raise TypeError("Resume extraction must be a JSON object")
        data = deepcopy(raw_data)
        for key in RECORD_ROOTS:
            if key in data:
                data[key] = self._records(data[key])
        if "basicInfo" in data:
            info = (
                data["basicInfo"]
                if isinstance(data["basicInfo"], dict)
                else {}
            )
            data["basicInfo"] = self._process_basic_info(info)
            data["basicInfo"]["workYears"] = self._calculate_work_years(
                data, text_lines
            )
            data["basicInfo"]["highestEducation"] = (
                self._extract_highest_education(data)
            )
            data["basicInfo"]["idCard"] = self._extract_id_card_from_text(
                text_lines
            )
        if "workExperience" in data:
            data["workExperience"] = self._process_work_experience(
                data["workExperience"], text_lines
            )
        if "education" in data:
            data["education"] = self._process_education(
                data["education"], text_lines
            )
        if "projectExperience" in data:
            data["projectExperience"] = self._process_project_experience(
                data["projectExperience"], text_lines
            )
        for key in ("professionalSkills", "personalStrengths"):
            if key in data:
                value = data[key]
                if isinstance(value, list):
                    data[key + "_refer_index_range"] = deepcopy(value)
                    data[key] = self._text_from_range(value, text_lines) or ""
                elif isinstance(value, str):
                    data[key] = self._clean_description(value)
                else:
                    data[key] = ""
        self._validate_fields_in_text(data, text_lines)
        return data

    def _text_from_range(self, index_range, text_lines):

        if not isinstance(index_range, (list, tuple)) or len(index_range) != 2:
            return ""
        start, end = index_range
        if type(start) is not int or type(end) is not int:
            return ""
        if not 0 <= start <= end < len(text_lines):
            return ""
        stop = end + 1
        return self._clean_description("\n".join(text_lines[start:stop]))

    def _process_project_experience(self, projects, text_lines):
        result = []
        for project in projects:
            item = deepcopy(project)
            for key in ("projectName", "position"):
                if key in item:
                    item[key] = self._clean_text(item[key])
            if "projectPeriod" in item:
                item["projectPeriod"] = self._process_time_period(
                    item["projectPeriod"]
                )
            if "projectDescription_refer_index_range" in item:
                item["projectDescription"] = self._text_from_range(
                    item["projectDescription_refer_index_range"], text_lines
                )
            elif "projectDescription" in item:
                item["projectDescription"] = self._clean_description(
                    item["projectDescription"]
                )
            result.append(item)
        return result

    def _process_basic_info(
        self, basic_info: Dict[str, Any]
    ) -> Dict[str, Any]:

        processed = {}

        if "name" in basic_info:
            processed["name"] = self._clean_text(basic_info["name"])

        if "phoneNumber" in basic_info:
            processed["phoneNumber"] = self._clean_text(
                basic_info["phoneNumber"]
            )

        if "personalEmail" in basic_info:
            processed["personalEmail"] = self._clean_email(
                basic_info["personalEmail"]
            )

        if "age" in basic_info:
            processed["age"] = self._clean_text(basic_info["age"])
            processed["ageNum"] = self._extract_age_number(basic_info["age"])

        if "idCard" in basic_info:
            processed["idCard"] = self._clean_id_card(basic_info["idCard"])

        for key, value in basic_info.items():
            if key not in processed:
                processed[key] = (
                    self._clean_text(value)
                    if isinstance(value, str)
                    else value
                )

        return processed

    def _process_work_experience(
        self,
        work_exp: List[Dict[str, Any]],
        text_lines: List[str],
    ) -> List[Dict[str, Any]]:

        processed_list = []

        for exp in work_exp:
            processed_exp = {}

            if "companyName" in exp:
                processed_exp["companyName"] = self._clean_company_name(
                    exp["companyName"]
                )

            if "position" in exp:
                processed_exp["position"] = self._clean_text(exp["position"])

            if "employmentPeriod" in exp:
                processed_exp["employmentPeriod"] = self._process_time_period(
                    exp["employmentPeriod"]
                )

            if "jobDescription_refer_index_range" in exp:
                processed_exp["jobDescription_refer_index_range"] = exp[
                    "jobDescription_refer_index_range"
                ]
                processed_exp["jobDescription"] = (
                    self._extract_description_from_range(
                        exp["jobDescription_refer_index_range"],
                        text_lines,
                        processed_exp.get("companyName", ""),
                        processed_exp.get("position", ""),
                    )
                )
            elif "jobDescription" in exp:
                processed_exp["jobDescription"] = self._clean_description(
                    exp["jobDescription"]
                )

            for key, value in exp.items():
                if key not in processed_exp:
                    processed_exp[key] = (
                        self._clean_text(value)
                        if isinstance(value, str)
                        else value
                    )

            processed_list.append(processed_exp)

        return processed_list

    def _process_education(
        self,
        education: List[Dict[str, Any]],
        text_lines: List[str],
    ) -> List[Dict[str, Any]]:

        processed_list = []

        for edu in education:
            processed_edu = {}

            if "school" in edu:
                processed_edu["school"] = self._clean_school_name(
                    edu["school"]
                )

            if "major" in edu:
                processed_edu["major"] = self._clean_text(edu["major"])

            if "degreeLevel" in edu:
                raw_degree = self._clean_text(edu["degreeLevel"])
                processed_edu["degreeLevel"] = self._map_internal_degree(
                    raw_degree
                )

            if "period" in edu:
                processed_edu["period"] = self._process_time_period(
                    edu["period"]
                )

            if "gpa" in edu:
                processed_edu["gpa"] = self._clean_text(edu["gpa"])
                processed_edu["gpaNum"] = self._extract_gpa_number(edu["gpa"])

            if isinstance(edu.get("educationDescription"), str):
                processed_edu["educationDescription"] = (
                    self._clean_description(edu["educationDescription"])
                )

            for key, value in edu.items():
                if key not in processed_edu:
                    processed_edu[key] = (
                        self._clean_text(value)
                        if isinstance(value, str)
                        else value
                    )

            processed_list.append(processed_edu)

        return processed_list

    def _clean_email(self, email: str) -> str:

        if not email:
            return ""
        email = str(email).strip().lower()
        email = email.replace(".c0m", ".com").replace(".c0.cn", ".co.cn")
        email = email.replace("gmai1.com", "gmail.com").replace(
            "gmai1.cn", "gmail.cn"
        )
        email = email.replace("hotmai1.com", "hotmail.com")
        email = (
            email.replace("163.c0m", "163.com")
            .replace("126.c0m", "126.com")
            .replace("qq.c0m", "qq.com")
        )
        email = email.replace("gq.com", "qq.com")
        email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if re.match(email_pattern, email):
            return email
        return email

    def _clean_company_name(self, company: str) -> str:

        if not company:
            return ""

        company = str(company).strip()

        suffixes = ["有限公司", "股份有限公司", "科技有限公司", "网络科技有限公司"]
        for suffix in suffixes:
            if company.count(suffix) > 1:
                company = company.replace(
                    suffix, "", company.count(suffix) - 1
                )

        return company

    def _clean_school_name(self, school: str) -> str:

        if not school:
            return ""

        school = str(school).strip()

        school = re.sub(r"\([^)]*\)", "", school)
        school = re.sub(r"（[^）]*）", "", school)

        return school.strip()

    def _clean_text(self, text: str) -> str:

        if not text:
            return ""

        text = str(text).strip()

        text = re.sub(r"\s+", " ", text)

        return text

    def _extract_age_number(self, age_text: str) -> int:

        if not age_text:
            return -1

        age_text = str(age_text).strip()

        age_pattern = r"(\d+)"
        match = re.search(age_pattern, age_text)

        if match:
            try:
                age = int(match.group(1))

                if 16 <= age <= 99:
                    return age
            except ValueError:
                pass

        return -1

    def _extract_gpa_number(self, gpa_text: str) -> float:

        if not gpa_text:
            return -1.0

        gpa_text = str(gpa_text).strip()

        gpa_pattern = r"(\d+\.?\d*)"
        matches = re.findall(gpa_pattern, gpa_text)

        if matches:
            try:

                numbers = [float(match) for match in matches]
                min_gpa = min(numbers)

                if 0.0 <= min_gpa <= 5.0:
                    return min_gpa
            except ValueError:
                pass

        return -1.0

    def _clean_id_card(self, id_card: str) -> str:

        if not id_card:
            return ""
        id_card = str(id_card).strip()
        pattern = (
            r"^[1-9]\d{5}(18|19|20)\d{2}(0[1-9]|1[0-2])"
            r"(0[1-9]|[12]\d|3[01])\d{3}[\dXx]$"
        )
        if re.match(pattern, id_card):
            return id_card.upper()
        return ""

    def _extract_id_card_from_text(self, text_lines: List[str]) -> str:

        pattern = (
            r"[1-9]\d{5}(18|19|20)\d{2}(0[1-9]|1[0-2])"
            r"(0[1-9]|[12]\d|3[01])\d{3}[\dXx]"
        )
        full_text = " ".join(text_lines)
        match = re.search(pattern, full_text)
        if match:
            return self._clean_id_card(match.group(0))
        return ""

    def _extract_description_from_range(
        self,
        index_range: List[int],
        text_lines: List[str],
        name: str,
        position: str,
    ) -> str:

        if not isinstance(index_range, (list, tuple)) or len(index_range) != 2:
            return ""

        start_idx, end_idx = index_range
        if type(start_idx) is not int or type(end_idx) is not int:
            return ""

        if start_idx < 0 or end_idx >= len(text_lines) or start_idx > end_idx:
            return ""

        try:
            stop = end_idx + 1
            extracted_lines = text_lines[start_idx:stop]

            if (
                config.processing.remove_position_and_company_line
                and name
                and position
            ):
                normalized_name = self._normalize_unicode(name)
                normalized_position = self._normalize_unicode(position)
                extracted_lines = [
                    line
                    for line in extracted_lines
                    if self._keep_line_name_or_position(
                        normalized_name, normalized_position, line
                    )
                ]
                extracted_lines = [
                    line
                    for line in extracted_lines
                    if not self._line_contains_name_and_position(
                        normalized_name, normalized_position, line
                    )
                ]

            if len(extracted_lines) == 0:
                return ""
            else:
                description = self._clean_description(
                    "\n".join(extracted_lines)
                )

                return description

        except Exception:
            return ""

    def _keep_line_name_or_position(
        self,
        normalized_name: str,
        normalized_position: str,
        line: str,
    ) -> bool:

        norm_line = self._normalize_unicode(line)
        name_differs = normalized_name != norm_line
        position_differs = normalized_position != norm_line
        return name_differs or position_differs

    def _line_contains_name_and_position(
        self,
        normalized_name: str,
        normalized_position: str,
        line: str,
    ) -> bool:

        norm_line = self._normalize_unicode(line)
        return (
            normalized_name in norm_line and normalized_position in norm_line
        )

    @staticmethod
    def _normalize_description_text(description: str) -> str:

        if not description:
            return ""
        text = str(description).replace("\r\n", "\n").replace("\r", "\n")
        bullet = re.compile(
            r"^(?:[•●○■□▪◦▶▷✓✔\uf02e\uf0b7\uf0a7]"
            r"|[-*](?=\s|$|[\u3400-\u9fff])"
            r"|\d{1,3}[.．、)）](?=\s|$|[\u3400-\u9fff])"
            r"|[（(]\d{1,3}[)）]"
            r"|[一二三四五六七八九十]+[、.．)）]"
            r"|[A-Za-z][.)](?=\s|$))"
        )
        label = re.compile(r"^([^:：]{1,16})[:：](?!/)")

        def is_cjk(char):
            return (
                "\u3400" <= char <= "\u9fff"
                or "\u3040" <= char <= "\u30ff"
                or "\uf900" <= char <= "\ufaff"
                or "\U00020000" <= char <= "\U0003134f"
            )

        def join_wrap(left, right):
            if not left:
                return right

            no_space = (
                right[0] in "，。！？；：、,.!?;:%％…）)]】》」』"
                or left[-1] in "（([【《「『"
                or (is_cjk(left[-1]) and is_cjk(right[0]))
                or (
                    left[-1] in "，。！？；：、,.!?;:"
                    and is_cjk(right[0])
                    and not bullet.fullmatch(left)
                )
            )
            return left + ("" if no_space else " ") + right

        paragraphs = []
        current = ""
        for source_line in text.split("\n"):
            line = re.sub(r"[^\S\n]+", " ", source_line).strip()
            if not line:
                if current:
                    paragraphs.append(current)
                    current = ""
                if paragraphs and paragraphs[-1] != "":
                    paragraphs.append("")
                continue
            match = label.match(line)
            is_label = bool(match and any(c.isalpha() for c in match.group(1)))
            starts_item = bool(bullet.match(line))

            marker_only = bool(current and bullet.fullmatch(current))
            if current and (starts_item or is_label) and not marker_only:
                paragraphs.append(current)
                current = ""
            current = join_wrap(current, line)
        if current:
            paragraphs.append(current)
        return "\n".join(paragraphs).strip()

    def _clean_description(
        self, description: str, text_lines: List[str] = None
    ) -> str:

        return self._normalize_description_text(description)

    def _process_time_period(self, period: Dict[str, Any]) -> Dict[str, Any]:

        if not isinstance(period, dict):
            return {}

        processed_period = {}

        if "startDate" in period:
            processed_period["startDate"] = self._normalize_date(
                period["startDate"]
            )

        if "endDate" in period:
            processed_period["endDate"] = self._normalize_date(
                period["endDate"]
            )

        return processed_period

    def _normalize_date(self, date_str: str) -> str:

        if not date_str:
            return ""

        date_str = str(date_str).strip()

        if date_str in ["至今", "现在", "目前", "present", "now"]:
            return "present"

        date_patterns = [
            r"(\d{4})[年.-](\d{1,2})[月.-]?(\d{1,2})?",
            r"(\d{4})[年.-](\d{1,2})",
            r"(\d{4})",
        ]

        for pattern in date_patterns:
            match = re.search(pattern, date_str)
            if match:
                year = match.group(1)
                month = match.group(2) if len(match.groups()) > 1 else None
                day = match.group(3) if len(match.groups()) > 2 else None

                if month:
                    month = month.zfill(2)
                    if day:
                        return f"{year}.{month}.{day.zfill(2)}"
                    else:
                        return f"{year}.{month}"
                else:
                    return year

        return date_str

    def _extract_pages_info(
        self, processed_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:

        pages_info = []
        for page_num, page_data in enumerate(processed_data):
            page_info = {
                "page_number": page_num + 1,
                "has_text": "text" in page_data and bool(page_data["text"]),
                "has_image": "image" in page_data,
            }
            pages_info.append(page_info)
        return pages_info

    def _normalize_for_comparison(self, text: str) -> str:

        if not text:
            return ""

        normalized = str(text).lower()
        normalized = re.sub(r"[^\w]", "", normalized)
        return normalized

    def _normalize_unicode(self, text: str) -> str:

        return unicodedata.normalize("NFKC", text).strip()

    def _normalize_for_basic_info(self, text: str) -> str:

        if not text:
            return ""
        normalized = str(text).replace("\n", "").replace("\r", "")
        normalized = re.sub(r"\s+", "", normalized)
        chinese_punctuation = (
            "！？｡。＂＃＄％＆＇（）＊＋，－／：；＜＝＞＠［＼］＾＿｀｛｜｝～｟｠｢｣"
            "､、〃》「」『』【】〔〕〖〗〘〙〚〛〜〝〞〟〰〾〿–—"
            '‛""„‟…‧﹏·'
        )
        for punct in string.punctuation + chinese_punctuation:
            normalized = normalized.replace(punct, "")
        return "".join(
            c for c in normalized if c.isalnum() or "\u4e00" <= c <= "\u9fff"
        )

    def _validate_fields_in_text(
        self,
        processed_data: Dict[str, Any],
        text_lines: List[str],
    ) -> None:

        full_text = "".join(text_lines)
        normalized_full_text = self._normalize_for_comparison(full_text)
        normalized_full_text_basic = self._normalize_for_basic_info(full_text)

        if "basicInfo" in processed_data:
            basic_info = processed_data["basicInfo"]
            if basic_info.get("name"):
                norm_name = self._normalize_for_basic_info(basic_info["name"])
                if norm_name and norm_name not in normalized_full_text_basic:
                    basic_info["name"] = ""
            if basic_info.get("phoneNumber"):
                norm_phone = self._normalize_for_basic_info(
                    basic_info["phoneNumber"]
                )
                if norm_phone and norm_phone not in normalized_full_text_basic:
                    basic_info["phoneNumber"] = ""

        if "workExperience" in processed_data:
            valid_works = []
            for work in processed_data["workExperience"]:
                company_name = self._clean_text(work.get("companyName"))
                position = self._clean_text(work.get("position"))

                normalized_company_name = self._normalize_for_comparison(
                    company_name
                )
                normalized_position = self._normalize_for_comparison(position)

                nft = normalized_full_text
                company_found = (
                    normalized_company_name and normalized_company_name in nft
                )
                position_found = (
                    normalized_position and normalized_position in nft
                )
                if company_found or position_found:
                    valid_works.append(work)

            processed_data["workExperience"] = valid_works

        if "education" in processed_data:
            valid_educations = []
            for edu in processed_data["education"]:
                school = self._clean_text(edu.get("school"))
                major = self._clean_text(edu.get("major"))

                normalized_school = self._normalize_for_comparison(school)
                normalized_major = self._normalize_for_comparison(major)

                school_found = (
                    normalized_school
                    and normalized_school in normalized_full_text
                )
                major_found = (
                    normalized_major
                    and normalized_major in normalized_full_text
                )
                if school_found or major_found:
                    valid_educations.append(edu)

            processed_data["education"] = valid_educations

    def _extract_year_from_date(self, date_str: str) -> Optional[int]:

        if not date_str or not str(date_str).strip():
            return None
        match = re.search(r"(\d{4})", str(date_str).strip())
        if match:
            try:
                y = int(match.group(1))
                if 1950 <= y <= 2030:
                    return y
            except ValueError:
                pass
        return None

    def _calculate_work_years(
        self, raw_data: Dict[str, Any], text_lines: List[str]
    ) -> int:

        current_year = datetime.now().year
        earliest_work_year = None
        if "workExperience" in raw_data:
            for work in raw_data["workExperience"]:
                if work.get("internship", 0) == 1:
                    continue
                per = work.get("employmentPeriod", {})
                start = per.get("startDate") if isinstance(per, dict) else None
                if start and str(start).strip():
                    y = self._extract_year_from_date(start)
                    if y is not None and (
                        earliest_work_year is None or y < earliest_work_year
                    ):
                        earliest_work_year = y
        if earliest_work_year is not None:
            return current_year - earliest_work_year
        latest_graduation_year = None
        if "education" in raw_data:
            for edu in raw_data["education"]:
                per = edu.get("period", {})
                if not isinstance(per, dict):
                    continue
                end = per.get("endDate")
                if (
                    end
                    and str(end).strip()
                    and str(end) not in ("至今", "present", "现在", "目前")
                ):
                    y = self._extract_year_from_date(end)
                    is_newer = (
                        latest_graduation_year is None
                        or y > latest_graduation_year
                    )
                    if y is not None and is_newer:
                        latest_graduation_year = y
        if latest_graduation_year is not None:
            return current_year - latest_graduation_year
        return -1

    def _map_internal_degree(self, degree_text: str) -> str:

        if not degree_text:
            return ""
        d = degree_text.lower()
        if "专科" in d:
            if "大专" in d:
                return "大专"
            if "中专" in d:
                return "中专"
            return "大专"
        return degree_text

    def _standardize_education_level(
        self,
        degree_level: str,
        education_keywords: Dict[str, List[str]],
    ) -> str:

        if not degree_level:
            return ""
        dl = degree_level.lower().strip()
        for standard_level, keywords in education_keywords.items():
            for kw in keywords:
                if kw.lower() in dl:
                    return standard_level
        return ""

    def _extract_highest_education(self, raw_data: Dict[str, Any]) -> str:

        if "education" not in raw_data or not raw_data["education"]:
            return ""
        educations = raw_data["education"]
        education_priority = {
            "DOCTOR": 1,
            "MASTER": 2,
            "BACHELOR": 3,
            "ASSOCIATE": 4,
            "VOCATIONAL_SECONDARY": 5,
            "HIGH_SCHOOL": 6,
            "JUNIOR_HIGH_SCHOOL": 7,
            "PRIMARY_SCHOOL": 8,
        }
        education_keywords = {
            "DOCTOR": ["博士", "phd", "doctor", "博士研究生"],
            "MASTER": ["硕士", "研究生", "master", "硕士研究生"],
            "BACHELOR": ["本科", "bachelor", "学士", "本科生"],
            "ASSOCIATE": ["专科", "大专", "associate", "专科生"],
            "VOCATIONAL_SECONDARY": [
                "中专",
                "中等专业学校",
                "vocational high school",
                "secondary vocational school",
            ],
            "HIGH_SCHOOL": ["高中", "high", "高级中学", "中学"],
            "JUNIOR_HIGH_SCHOOL": ["初中", "初级中学"],
            "PRIMARY_SCHOOL": ["小学", "初等教育"],
        }
        latest_education = None
        latest_year = None
        for edu in educations:
            per = edu.get("period", {})
            if isinstance(per, dict) and per.get("startDate"):
                y = self._extract_year_from_date(per["startDate"])
                if y is not None and (latest_year is None or y > latest_year):
                    latest_year = y
                    latest_education = edu
        if latest_education:
            std = self._standardize_education_level(
                latest_education.get("degreeLevel", ""),
                education_keywords,
            )
            if std:
                return std
        highest_priority = 999
        result = ""
        for edu in educations:
            std = self._standardize_education_level(
                edu.get("degreeLevel", ""), education_keywords
            )
            if std:
                p = education_priority.get(std, 999)
                if p < highest_priority:
                    highest_priority = p
                    result = std
        return result

#!/usr/bin/env python3
"""
Data processor
Responsible for processing and cleaning extracted resume data
"""
import re
import os
import string
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import tiktoken
import unicodedata
from smartresume.utils.config import config


class DataProcessor:
    """Data processor class"""

    def __init__(self):
        """Initialize data processor"""
        self.encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
        self.pattern = r'[a-zA-Z0-9\-~_]{40,}'
        self.word_chars = set()
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            word_path = os.path.join(current_dir, 'word.txt')
            if os.path.exists(word_path):
                with open(word_path, 'r', encoding='utf-8') as f:
                    self.word_chars = set(f.read().strip().split('\n'))
        except Exception:
            pass

    def should_remove(self, match: re.Match) -> bool:
        """
        Decide whether a matched text should be removed.

        Args:
            match: Regex match object

        Returns:
            bool: Whether it should be removed
        """
        encoded = self.encoding.encode(match.group(0))
        return len(encoded) > len(match.group(0)) * 0.5

    def _remove_spaces_around_chars(self, text: str) -> str:
        """Remove spaces around characters listed in word.txt (if loaded)."""
        if not self.word_chars:
            return text
        has_word_chars = any(c in self.word_chars for c in text)
        if not has_word_chars:
            return text
        result = []
        for char in text:
            if char in self.word_chars or not char.isspace():
                result.append(char)
        return ''.join(result)

    def build_text_content(
        self,
        processed_data: List[Dict[str, Any]],
        resume_id: str = "",
        use_hybrid_text: bool = False,
    ) -> Tuple[List[str], str, str]:
        """
        Build text content from processed data.

        Args:
            processed_data: Processed data
            resume_id: Resume ID (optional, for compatibility)
            use_hybrid_text: If True, use text_hybrid when present (e.g. for abnormal PDF basicInfo)

        Returns:
            Tuple[List[str], str, str]: (lines, plain text, indexed text)
        """
        text_lines = []
        text_key = 'text_hybrid' if use_hybrid_text else 'text'

        for page_data in processed_data:
            page_text = page_data.get(text_key) or page_data.get('text')
            if not page_text:
                continue
            if isinstance(page_text, list):
                for text_item in page_text:
                    if isinstance(text_item, dict) and 'text' in text_item:
                        text = self._clean_text_content(text_item['text'])
                        text = self._remove_spaces_around_chars(text)
                        if text:
                            text_lines.extend(self._split_text_lines(text))
                    elif isinstance(text_item, str) and text_item.strip():
                        text_lines.append(text_item.strip())
            elif isinstance(page_text, str) and page_text.strip():
                text_lines.append(page_text.strip())

        text_content = '\n'.join(text_lines)

        indexed_text_content = self._build_indexed_content(text_lines)

        return text_lines, text_content, indexed_text_content

    def _clean_text_content(self, text: str) -> str:
        """
        Clean text content.

        Args:
            text: Raw text

        Returns:
            str: Cleaned text
        """
        if not text:
            return ""

        text = unicodedata.normalize('NFKC', text)

        text = re.sub(
            r'[\u0020\u00A0\u1680\u2000-\u200A\u2028\u2029\u202F\u205F\u3000\u00A7]',
            ' ', text
        )

        text = re.sub(r' {2,}', ' ', text)

        text = re.sub(self.pattern, lambda m: '' if self.should_remove(m) else m.group(0), text)

        return text.strip()

    def _split_text_lines(self, text: str) -> List[str]:
        """
        Split text into lines.

        Args:
            text: Text content

        Returns:
            List[str]: List of lines
        """
        if "\n" in text:
            return [line.strip() for line in text.split("\n") if line.strip()]
        else:
            return [text.strip()] if text.strip() else []

    def _build_indexed_content(self, text_lines: List[str]) -> str:
        """
        Build indexed text content for LLM input.

        Args:
            text_lines: List of text lines

        Returns:
            str: Indexed text content
        """
        trans_table = str.maketrans('', '', '""\'\\')
        indexed_text_lines = [
            f"[{i}]:{line.translate(trans_table) if isinstance(line, str) else ''}"
            for i, line in enumerate(text_lines)
        ]
        return '\n'.join(indexed_text_lines)

    def post_process(
        self,
        text_lines: List[str],
        structure_output: Dict[str, Any],
        processed_data: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Post-process structured output.

        Args:
            text_lines: Text line list
            structure_output: Structured output
            processed_data: Processed data

        Returns:
            Dict: Final processed result
        """
        try:
            processed_result = self.process_resume_data(structure_output, text_lines)

            pages_info = self._extract_pages_info(processed_data)
            if pages_info:
                processed_result['pages'] = pages_info

            processed_result['metadata'] = {
                'text_lines_count': len(text_lines),
                'pages_count': len(processed_data)
            }

            return processed_result

        except Exception:
            return structure_output

    def process_resume_data(
        self, raw_data: Dict[str, Any],
        text_lines: List[str],
    ) -> Dict[str, Any]:
        """
        Process raw resume data.

        Args:
            raw_data: Raw data
            text_lines: Text lines

        Returns:
            Dict: Processed data
        """
        try:
            processed_data = {}

            if 'basicInfo' in raw_data:
                processed_data['basicInfo'] = self._process_basic_info(raw_data['basicInfo'])
                processed_data['basicInfo']['workYears'] = (
                    self._calculate_work_years(raw_data, text_lines)
                )
                processed_data['basicInfo']['highestEducation'] = (
                    self._extract_highest_education(raw_data)
                )
                extracted_id = self._extract_id_card_from_text(text_lines)
                processed_data['basicInfo']['idCard'] = extracted_id

            if 'workExperience' in raw_data:
                processed_data['workExperience'] = (
                    self._process_work_experience(
                        raw_data['workExperience'], text_lines
                    )
                )

            if 'education' in raw_data:
                processed_data['education'] = (
                    self._process_education(
                        raw_data['education'], text_lines
                    )
                )

            self._validate_fields_in_text(processed_data, text_lines)

            return processed_data

        except Exception:
            return raw_data

    def _process_basic_info(self, basic_info: Dict[str, Any]) -> Dict[str, Any]:
        """Process basic info"""
        processed = {}

        if 'name' in basic_info:
            processed['name'] = self._clean_text(basic_info['name'])

        if 'phoneNumber' in basic_info:
            processed['phoneNumber'] = self._clean_text(basic_info['phoneNumber'])

        if 'personalEmail' in basic_info:
            processed['personalEmail'] = self._clean_email(basic_info['personalEmail'])

        if 'age' in basic_info:
            processed['age'] = self._clean_text(basic_info['age'])
            processed['ageNum'] = self._extract_age_number(basic_info['age'])

        if 'idCard' in basic_info:
            processed['idCard'] = self._clean_id_card(basic_info['idCard'])

        for key, value in basic_info.items():
            if key not in processed:
                processed[key] = self._clean_text(value) if isinstance(value, str) else value

        return processed

    def _process_work_experience(
        self, work_exp: List[Dict[str, Any]],
        text_lines: List[str],
    ) -> List[Dict[str, Any]]:
        """Process work experience"""
        processed_list = []

        for exp in work_exp:
            processed_exp = {}

            if 'companyName' in exp:
                processed_exp['companyName'] = self._clean_company_name(exp['companyName'])

            if 'position' in exp:
                processed_exp['position'] = self._clean_text(exp['position'])

            if 'employmentPeriod' in exp:
                processed_exp['employmentPeriod'] = (
                    self._process_time_period(exp['employmentPeriod'])
                )

            if 'jobDescription_refer_index_range' in exp:
                processed_exp['jobDescription_refer_index_range'] = (
                    exp['jobDescription_refer_index_range']
                )
                processed_exp['jobDescription'] = (
                    self._extract_description_from_range(
                        exp['jobDescription_refer_index_range'],
                        text_lines,
                        processed_exp['companyName'],
                        processed_exp["position"],
                    )
                )
            elif 'jobDescription' in exp:
                processed_exp['jobDescription'] = self._clean_description(exp['jobDescription'])

            for key, value in exp.items():
                if key not in processed_exp:
                    processed_exp[key] = (
                        self._clean_text(value)
                        if isinstance(value, str) else value
                    )

            processed_list.append(processed_exp)

        return processed_list

    def _process_education(
        self, education: List[Dict[str, Any]],
        text_lines: List[str],
    ) -> List[Dict[str, Any]]:
        """Process education"""
        processed_list = []

        for edu in education:
            processed_edu = {}

            if 'school' in edu:
                processed_edu['school'] = self._clean_school_name(edu['school'])

            if 'major' in edu:
                processed_edu['major'] = self._clean_text(edu['major'])

            if 'degreeLevel' in edu:
                raw_degree = self._clean_text(edu['degreeLevel'])
                processed_edu['degreeLevel'] = self._map_internal_degree(raw_degree)

            if 'period' in edu:
                processed_edu['period'] = self._process_time_period(edu['period'])

            if 'gpa' in edu:
                processed_edu['gpa'] = self._clean_text(edu['gpa'])
                processed_edu['gpaNum'] = self._extract_gpa_number(edu['gpa'])

            for key, value in edu.items():
                if key not in processed_edu:
                    processed_edu[key] = (
                        self._clean_text(value)
                        if isinstance(value, str) else value
                    )

            processed_list.append(processed_edu)

        return processed_list

    def _clean_email(self, email: str) -> str:
        """Clean email address"""
        if not email:
            return ""
        email = str(email).strip().lower()
        email = email.replace(".c0m", ".com").replace(".c0.cn", ".co.cn")
        email = email.replace("gmai1.com", "gmail.com").replace("gmai1.cn", "gmail.cn")
        email = email.replace("hotmai1.com", "hotmail.com")
        email = (
            email.replace("163.c0m", "163.com")
            .replace("126.c0m", "126.com")
            .replace("qq.c0m", "qq.com")
        )
        email = email.replace("gq.com", "qq.com")
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if re.match(email_pattern, email):
            return email
        return email

    def _clean_company_name(self, company: str) -> str:
        """Clean company name"""
        if not company:
            return ""

        company = str(company).strip()

        suffixes = ['有限公司', '股份有限公司', '科技有限公司', '网络科技有限公司']
        for suffix in suffixes:
            if company.count(suffix) > 1:
                company = company.replace(suffix, '', company.count(suffix) - 1)

        return company

    def _clean_school_name(self, school: str) -> str:
        """Clean school name"""
        if not school:
            return ""

        school = str(school).strip()

        school = re.sub(r'\([^)]*\)', '', school)
        school = re.sub(r'（[^）]*）', '', school)

        return school.strip()

    def _clean_text(self, text: str) -> str:
        """Clean general text"""
        if not text:
            return ""

        text = str(text).strip()

        text = re.sub(r'\s+', ' ', text)

        return text

    def _extract_age_number(self, age_text: str) -> int:
        """Extract age number from string"""
        if not age_text:
            return -1

        age_text = str(age_text).strip()

        age_pattern = r'(\d+)'
        match = re.search(age_pattern, age_text)

        if match:
            try:
                age = int(match.group(1))
                # Validate reasonable age range (16-99)
                if 16 <= age <= 99:
                    return age
            except ValueError:
                pass

        return -1

    def _extract_gpa_number(self, gpa_text: str) -> float:
        """Extract the smallest number from GPA text as GPA value"""
        if not gpa_text:
            return -1.0

        gpa_text = str(gpa_text).strip()

        gpa_pattern = r'(\d+\.?\d*)'
        matches = re.findall(gpa_pattern, gpa_text)

        if matches:
            try:
                # Convert to float and pick the minimum
                numbers = [float(match) for match in matches]
                min_gpa = min(numbers)
                # Validate reasonable GPA range (0.0-5.0)
                if 0.0 <= min_gpa <= 5.0:
                    return min_gpa
            except ValueError:
                pass

        return -1.0

    def _clean_id_card(self, id_card: str) -> str:
        """Clean and validate ID card number (18 digits or 17+X)."""
        if not id_card:
            return ""
        id_card = str(id_card).strip()
        pattern = r'^[1-9]\d{5}(18|19|20)\d{2}(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])\d{3}[\dXx]$'
        if re.match(pattern, id_card):
            return id_card.upper()
        return ""

    def _extract_id_card_from_text(self, text_lines: List[str]) -> str:
        """Extract ID card number from text lines."""
        pattern = r'[1-9]\d{5}(18|19|20)\d{2}(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])\d{3}[\dXx]'
        full_text = ' '.join(text_lines)
        match = re.search(pattern, full_text)
        if match:
            return self._clean_id_card(match.group(0))
        return ""

    def _extract_description_from_range(
        self, index_range: List[int],
        text_lines: List[str],
        name: str, position: str,
    ) -> str:
        """
        Extract description from original text based on index range.

        Args:
            index_range: Index range [start, end]
            text_lines: List of text lines
            name: Name
            position: Position

        Returns:
            Extracted description text
        """
        if not index_range or len(index_range) != 2:
            return ""

        start_idx, end_idx = index_range

        if start_idx < 0 or end_idx >= len(text_lines) or start_idx > end_idx:
            return ""

        try:
            extracted_lines = text_lines[start_idx:end_idx + 1]

            if config.processing.remove_position_and_company_line:
                normalized_name = self._normalize_unicode(name)
                normalized_position = self._normalize_unicode(position)
                extracted_lines = [
                    line for line in extracted_lines
                    if self._keep_line_name_or_position(
                        normalized_name, normalized_position, line
                    )
                ]
                extracted_lines = [
                    line for line in extracted_lines
                    if not self._line_contains_name_and_position(
                        normalized_name, normalized_position, line
                    )
                ]

            if len(extracted_lines) == 0:
                return ""
            else:
                description = '\n'.join(line.strip() for line in extracted_lines if line.strip())

                return description

        except Exception:
            return ""

    def _keep_line_name_or_position(
        self, normalized_name: str, normalized_position: str, line: str,
    ) -> bool:
        """Return True unless the line exactly matches both name and position."""
        norm_line = self._normalize_unicode(line)
        name_differs = (normalized_name != norm_line)
        position_differs = (normalized_position != norm_line)
        return name_differs or position_differs

    def _line_contains_name_and_position(
        self, normalized_name: str, normalized_position: str, line: str,
    ) -> bool:
        """Return True if the line contains both name and position."""
        norm_line = self._normalize_unicode(line)
        return normalized_name in norm_line and normalized_position in norm_line

    def _clean_description(self, description: str, text_lines: List[str] = None) -> str:
        """Clean description text"""
        if not description:
            return ""

        description = str(description).strip()

        lines = description.split('\n')
        cleaned_lines = []

        for line in lines:
            line = line.strip()
            if line:
                line = re.sub(r'\s+', ' ', line)
                cleaned_lines.append(line)

        return '\n'.join(cleaned_lines)

    def _process_time_period(self, period: Dict[str, Any]) -> Dict[str, Any]:
        """Process time period"""
        if not period:
            return {}

        processed_period = {}

        if 'startDate' in period:
            processed_period['startDate'] = self._normalize_date(period['startDate'])

        if 'endDate' in period:
            processed_period['endDate'] = self._normalize_date(period['endDate'])

        return processed_period

    def _normalize_date(self, date_str: str) -> str:
        """Normalize date format"""
        if not date_str:
            return ""

        date_str = str(date_str).strip()

        # Handle "to present" and similar markers
        if date_str in ['至今', '现在', '目前', 'present', 'now']:
            return 'present'

        date_patterns = [
            r'(\d{4})[年.-](\d{1,2})[月.-]?(\d{1,2})?',
            r'(\d{4})[年.-](\d{1,2})',
            r'(\d{4})',
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

    def _extract_pages_info(self, processed_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract page metadata from processed data."""
        pages_info = []
        for page_num, page_data in enumerate(processed_data):
            page_info = {
                'page_number': page_num + 1,
                'has_text': 'text' in page_data and bool(page_data['text']),
                'has_image': 'image' in page_data,
            }
            pages_info.append(page_info)
        return pages_info

    def _normalize_for_comparison(self, text: str) -> str:
        """
        Normalize text for comparison: remove special chars and spaces, lowercase.

        Args:
            text: Text to normalize

        Returns:
            str: Normalized text
        """
        if not text:
            return ""

        normalized = str(text).lower()
        normalized = re.sub(r'[^\w]', '', normalized)
        return normalized

    def _normalize_unicode(self, text: str) -> str:
        """
        Normalize Unicode text for comparison.

        Args:
            text: Text to normalize

        Returns:
            str: Normalized text
        """
        return unicodedata.normalize('NFKC', text).strip()

    def _normalize_for_basic_info(self, text: str) -> str:
        """Normalize for basicInfo (name, phone): strip
        spaces/newlines and punctuation, keep alphanumeric
        and Chinese."""
        if not text:
            return ""
        normalized = str(text).replace("\n", "").replace("\r", "")
        normalized = re.sub(r'\s+', '', normalized)
        chinese_punctuation = (
            '！？｡。＂＃＄％＆＇（）＊＋，－／：；＜＝＞＠［＼］＾＿｀｛｜｝～｟｠｢｣'
            '､、〃》「」『』【】〔〕〖〗〘〙〚〛〜〝〞〟〰〾〿–—''‛""„‟…‧﹏·'
        )
        for punct in string.punctuation + chinese_punctuation:
            normalized = normalized.replace(punct, '')
        return ''.join(c for c in normalized if c.isalnum() or '\u4e00' <= c <= '\u9fff')

    def _validate_fields_in_text(
        self, processed_data: Dict[str, Any],
        text_lines: List[str],
    ) -> None:
        """
        Validate that key fields appear in the original text; remove otherwise.
        """
        full_text = ''.join(text_lines)
        normalized_full_text = self._normalize_for_comparison(full_text)
        normalized_full_text_basic = self._normalize_for_basic_info(full_text)

        if 'basicInfo' in processed_data:
            basic_info = processed_data['basicInfo']
            if basic_info.get('name'):
                norm_name = self._normalize_for_basic_info(basic_info['name'])
                if norm_name and norm_name not in normalized_full_text_basic:
                    basic_info['name'] = ""
            if basic_info.get('phoneNumber'):
                norm_phone = self._normalize_for_basic_info(basic_info['phoneNumber'])
                if norm_phone and norm_phone not in normalized_full_text_basic:
                    basic_info['phoneNumber'] = ""

        if 'workExperience' in processed_data:
            valid_works = []
            for work in processed_data['workExperience']:
                company_name = work.get('companyName', '').strip()
                position = work.get('position', '').strip()

                normalized_company_name = self._normalize_for_comparison(company_name)
                normalized_position = self._normalize_for_comparison(position)

                nft = normalized_full_text
                company_found = normalized_company_name and normalized_company_name in nft
                position_found = normalized_position and normalized_position in nft
                if company_found or position_found:
                    valid_works.append(work)

            processed_data['workExperience'] = valid_works

        if 'education' in processed_data:
            valid_educations = []
            for edu in processed_data['education']:
                school = edu.get('school', '').strip()
                major = edu.get('major', '').strip()

                normalized_school = self._normalize_for_comparison(school)
                normalized_major = self._normalize_for_comparison(major)

                school_found = normalized_school and normalized_school in normalized_full_text
                major_found = normalized_major and normalized_major in normalized_full_text
                if school_found or major_found:
                    valid_educations.append(edu)

            processed_data['education'] = valid_educations

    def _extract_year_from_date(self, date_str: str) -> Optional[int]:
        """Extract year from date string (e.g. 2020.1, 2020)."""
        if not date_str or not str(date_str).strip():
            return None
        match = re.search(r'(\d{4})', str(date_str).strip())
        if match:
            try:
                y = int(match.group(1))
                if 1950 <= y <= 2030:
                    return y
            except ValueError:
                pass
        return None

    def _calculate_work_years(self, raw_data: Dict[str, Any], text_lines: List[str]) -> int:
        """Compute work years from earliest work start (non-internship) or latest graduation."""
        current_year = datetime.now().year
        earliest_work_year = None
        if 'workExperience' in raw_data:
            for work in raw_data['workExperience']:
                if work.get('internship', 0) == 1:
                    continue
                per = work.get('employmentPeriod', {})
                start = per.get('startDate') if isinstance(per, dict) else None
                if start and str(start).strip():
                    y = self._extract_year_from_date(start)
                    if y is not None and (earliest_work_year is None or y < earliest_work_year):
                        earliest_work_year = y
        if earliest_work_year is not None:
            return current_year - earliest_work_year
        latest_graduation_year = None
        if 'education' in raw_data:
            for edu in raw_data['education']:
                per = edu.get('period', {})
                if not isinstance(per, dict):
                    continue
                end = per.get('endDate')
                if end and str(end).strip() and str(end) not in ('至今', 'present', '现在', '目前'):
                    y = self._extract_year_from_date(end)
                    is_newer = latest_graduation_year is None or y > latest_graduation_year
                    if y is not None and is_newer:
                        latest_graduation_year = y
        if latest_graduation_year is not None:
            return current_year - latest_graduation_year
        return -1

    def _map_internal_degree(self, degree_text: str) -> str:
        """Map degree text: 专科 -> 大专/中专 by context."""
        if not degree_text:
            return ""
        d = degree_text.lower()
        if '专科' in d:
            if '大专' in d:
                return '大专'
            if '中专' in d:
                return '中专'
            return '大专'
        return degree_text

    def _standardize_education_level(
        self, degree_level: str,
        education_keywords: Dict[str, List[str]],
    ) -> str:
        """Map degree level to standard key using keyword list."""
        if not degree_level:
            return ""
        dl = degree_level.lower().strip()
        for standard_level, keywords in education_keywords.items():
            for kw in keywords:
                if kw.lower() in dl:
                    return standard_level
        return ""

    def _extract_highest_education(self, raw_data: Dict[str, Any]) -> str:
        """Extract highest education: by latest startDate first, then by degree priority."""
        if 'education' not in raw_data or not raw_data['education']:
            return ""
        educations = raw_data['education']
        education_priority = {
            'DOCTOR': 1, 'MASTER': 2, 'BACHELOR': 3, 'ASSOCIATE': 4,
            'VOCATIONAL_SECONDARY': 5, 'HIGH_SCHOOL': 6,
            'JUNIOR_HIGH_SCHOOL': 7, 'PRIMARY_SCHOOL': 8
        }
        education_keywords = {
            'DOCTOR': ['博士', 'phd', 'doctor', '博士研究生'],
            'MASTER': ['硕士', '研究生', 'master', '硕士研究生'],
            'BACHELOR': ['本科', 'bachelor', '学士', '本科生'],
            'ASSOCIATE': ['专科', '大专', 'associate', '专科生'],
            'VOCATIONAL_SECONDARY': [
                '中专', '中等专业学校',
                'vocational high school',
                'secondary vocational school',
            ],
            'HIGH_SCHOOL': ['高中', 'high', '高级中学', '中学'],
            'JUNIOR_HIGH_SCHOOL': ['初中', '初级中学'],
            'PRIMARY_SCHOOL': ['小学', '初等教育']
        }
        latest_education = None
        latest_year = None
        for edu in educations:
            per = edu.get('period', {})
            if isinstance(per, dict) and per.get('startDate'):
                y = self._extract_year_from_date(per['startDate'])
                if y is not None and (latest_year is None or y > latest_year):
                    latest_year = y
                    latest_education = edu
        if latest_education:
            std = self._standardize_education_level(
                latest_education.get('degreeLevel', ''),
                education_keywords,
            )
            if std:
                return std
        highest_priority = 999
        result = ""
        for edu in educations:
            std = self._standardize_education_level(edu.get('degreeLevel', ''), education_keywords)
            if std:
                p = education_priority.get(std, 999)
                if p < highest_priority:
                    highest_priority = p
                    result = std
        return result

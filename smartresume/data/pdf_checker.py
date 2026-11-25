from typing import Dict, List, Any, Tuple, Optional

try:
    import pdfplumber
except ImportError:
    pdfplumber = None


class PDFChecker:

    def check_pdf_abnormal(
        self, pdf_path: str
    ) -> Tuple[bool, List[Dict[str, Any]]]:

        issues: List[Dict[str, Any]] = []

        if not pdf_path or not pdfplumber:
            return False, issues

        try:
            with pdfplumber.open(pdf_path) as pdf:
                metadata = getattr(pdf, "metadata", None) or {}

            def metadata_text(name):
                value = (
                    metadata.get(name)
                    or metadata.get("/" + name)
                    or metadata.get(name.lower())
                    or ""
                )
                return (
                    value.decode("utf-8", errors="replace")
                    if isinstance(value, bytes)
                    else str(value)
                )

            producer = metadata_text("Producer")
            creator = metadata_text("Creator")
            abnormal_design, design_issue = self._check_design_tool_abnormal(
                producer, creator
            )
            if abnormal_design:
                issues.append(
                    {
                        "type": "设计工具PDF异常",
                        "description": design_issue,
                        "severity": "高",
                    }
                )

            is_producer_abnormal, producer_issue = (
                self._check_producer_abnormal(producer)
            )
            if is_producer_abnormal and producer_issue:
                issues.append(
                    {
                        "type": "Producer异常",
                        "description": producer_issue,
                        "severity": "中",
                    }
                )
        except Exception:
            pass

        return len(issues) > 0, issues

    @staticmethod
    def _check_design_tool_abnormal(
        producer: Optional[str], creator: Optional[str]
    ):

        metadata = f"{producer or ''} {creator or ''}".casefold()
        tools = ("Canva", "CorelDRAW", "Corel PDF Engine", "Adobe Illustrator")
        matched = [tool for tool in tools if tool.casefold() in metadata]
        if matched:
            return (
                True,
                "Design-tool export with potentially "
                "unreliable native geometry: "
                + ", ".join(matched),
            )
        return False, None

    def _check_producer_abnormal(
        self, producer: Optional[str]
    ) -> Tuple[bool, Optional[str]]:

        if not producer:
            return False, None

        producer = str(producer).strip()
        agpl_count = producer.count("AGPL-version")
        if agpl_count > 1:
            return True, f"AGPL-version 重复 {agpl_count} 次"
        if "Modified using iText" in producer and agpl_count > 0:
            return True, "检测到 iText 修改痕迹"
        return False, None


pdf_checker = PDFChecker()

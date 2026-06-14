#!/usr/bin/env python3
"""
PDF abnormal detection module.
Detects Producer duplication, iText fingerprint, etc. Returns (is_abnormal, issues).
Uses pdfplumber for metadata (no PyMuPDF dependency).
"""
from typing import Dict, List, Any, Tuple, Optional

try:
    import pdfplumber
except ImportError:
    pdfplumber = None


class PDFChecker:
    """PDF abnormal checker."""

    def check_pdf_abnormal(self, pdf_path: str) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        Check whether the PDF is abnormal (e.g. Producer duplication, iText fingerprint).

        Args:
            pdf_path: Path to the PDF file.

        Returns:
            Tuple[bool, List[Dict]]: (is_abnormal, list of issues).
        """
        issues: List[Dict[str, Any]] = []

        if not pdf_path or not pdfplumber:
            return False, issues

        try:
            with pdfplumber.open(pdf_path) as pdf:
                metadata = getattr(pdf, "metadata", None) or {}
            # PDF metadata keys may be with or without leading slash
            producer = metadata.get("Producer") or metadata.get("/Producer") or ""
            if isinstance(producer, bytes):
                producer = producer.decode("utf-8", errors="ignore")
            else:
                producer = str(producer or "")

            is_producer_abnormal, producer_issue = self._check_producer_abnormal(producer)
            if is_producer_abnormal and producer_issue:
                issues.append({
                    "type": "Producer异常",
                    "description": producer_issue,
                    "severity": "中",
                })
        except Exception:
            pass

        return len(issues) > 0, issues

    def _check_producer_abnormal(self, producer: Optional[str]) -> Tuple[bool, Optional[str]]:
        """
        Check Producer metadata for duplication / iText fingerprint.

        Returns:
            Tuple[bool, Optional[str]]: (is_abnormal, description).
        """
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

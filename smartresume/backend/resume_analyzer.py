"""
Resume analyzer - main analyzer class
"""
from typing import List, Dict, Any
from smartresume.data import DataProcessor, FileProcessor
from smartresume.data.text_extractor import TextExtractor
from smartresume.model.llm_client import LLMClient
from smartresume.utils.config import config


class ResumeAnalyzer:
    """Resume analyzer that integrates all modules"""

    def __init__(self, init_ocr: bool = True, init_llm: bool = True) -> None:
        """
        Initialize analyzer

        Args:
            init_ocr: Whether to initialize OCR functionality
            init_llm: Whether to initialize LLM
        """
        self.text_extractor = TextExtractor(init_ocr)
        self.file_processor = FileProcessor(self.text_extractor)
        self.llm_client = LLMClient() if init_llm else None
        self.data_processor = DataProcessor()

    def pipeline(self,
                 cv_path: str,
                 resume_id: str,
                 extract_types: List[str] = None) -> Dict[str, Any]:
        """
        Complete resume analysis pipeline.

        Args:
            cv_path: Resume file path
            resume_id: Resume ID
            extract_types: List of extraction types (e.g. basic_info, work_experience, education)

        Returns:
            Dict with extracted fields (basicInfo, workExperience,
            education, etc.), rawText, and optional error_details.

        Note:
            When PDF is abnormal (is_abnormal_pdf), uses dual-text strategy:
            basicInfo from hybrid text + OCR complement, other fields from full OCR.
        """
        if extract_types is None:
            extract_types = ["basic_info"]

        try:
            processed_data = self.file_processor.process_file(cv_path)

            is_abnormal_pdf = any(page.get("is_abnormal_pdf", False) for page in processed_data)

            if is_abnormal_pdf:
                # Dual-text strategy: full OCR text + hybrid text
                (text_lines, text_content,
                 indexed_text_content) = (
                    self.data_processor.build_text_content(
                        processed_data, resume_id
                    )
                )
                (text_lines_hybrid, text_content_hybrid,
                 indexed_text_content_hybrid) = (
                    self.data_processor.build_text_content(
                        processed_data, resume_id,
                        use_hybrid_text=True
                    )
                )

                basic_info_output = {}
                if "basic_info" in extract_types:
                    basic_info_hybrid = self.llm_client.extract_info(
                        indexed_text_content_hybrid, ["basic_info"], resume_id
                    )
                    basic_info_ocr = self.llm_client.extract_info(
                        indexed_text_content, ["basic_info"], resume_id
                    )
                    basic_info_output = basic_info_hybrid
                    hybrid_data = basic_info_hybrid.get("basicInfo", {})
                    ocr_data = basic_info_ocr.get("basicInfo", {})

                    if not hybrid_data and ocr_data:
                        basic_info_output["basicInfo"] = ocr_data
                    elif hybrid_data and ocr_data:
                        for key, value in ocr_data.items():
                            if (key not in hybrid_data or not hybrid_data[key]) and value:
                                hybrid_data[key] = value
                        basic_info_output["basicInfo"] = hybrid_data

                other_types = [t for t in extract_types if t != "basic_info"]
                other_output = {}
                if other_types:
                    other_output = self.llm_client.extract_info(
                        indexed_text_content, other_types, resume_id
                    )

                structure_output = {**other_output}
                if "basicInfo" in basic_info_output:
                    structure_output["basicInfo"] = basic_info_output["basicInfo"]

                raw_text = text_content_hybrid
            else:
                (text_lines, text_content,
                 indexed_text_content) = (
                    self.data_processor.build_text_content(
                        processed_data, resume_id
                    )
                )
                structure_output = self.llm_client.extract_info(
                    indexed_text_content, extract_types, resume_id
                )
                raw_text = text_content

            final_result = self.data_processor.post_process(
                text_lines, structure_output, processed_data
            )
            final_result["rawText"] = raw_text
            return final_result

        except Exception as e:
            error_details = {
                "error_type": type(e).__name__,
                "error_message": str(e),
                "resume_id": resume_id,
                "file_path": cv_path,
            }
            return {"error": str(e), "error_details": error_details}

    def process_file(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Process a single file.

        Args:
            file_path: File path

        Returns:
            Result of processing
        """
        if not self.file_processor:
            raise ValueError("File processor is not initialized")

        return self.file_processor.process_file(file_path)

    def extract_info_only(
        self, text_content: str, extract_types: List[str],
        resume_id: str
    ) -> Dict[str, Any]:
        """
        Extract information only (no file processing).

        Args:
            text_content: Text content
            extract_types: Extraction types
            resume_id: Resume ID

        Returns:
            Extraction result
        """
        if not self.llm_client:
            raise ValueError("LLM client is not initialized")

        try:
            result = self.llm_client.extract_info(text_content, extract_types, resume_id)
            return result
        except Exception:
            raise

    def update_config(self, **kwargs) -> None:
        """Update configuration"""
        for key, value in kwargs.items():
            if hasattr(config.processing, key):
                setattr(config.processing, key, value)
            elif hasattr(config.model, key):
                setattr(config.model, key, value)


# Create default analyzer factory
def create_analyzer(init_ocr: bool = True, init_llm: bool = True) -> ResumeAnalyzer:
    """Create analyzer instance"""
    return ResumeAnalyzer(init_ocr, init_llm)

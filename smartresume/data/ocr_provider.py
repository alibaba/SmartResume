"""
OCR provider manager
Select OCR implementations based on configuration.
Uses RapidOCR (Apache-2.0) by default.
"""
import numpy as np
from typing import List, Any, Optional


class OCRProviderManager:
    """OCR provider manager (RapidOCR)."""

    def __init__(self) -> None:
        self._engine: Optional[Any] = None

    def get_ocr_provider(self) -> Any:
        """Get OCR provider based on configuration."""
        return self._get_rapid_ocr_provider()

    def _get_rapid_ocr_provider(self) -> Any:
        """Get RapidOCR engine."""
        if self._engine is None:
            try:
                from rapidocr_onnxruntime import RapidOCR
                self._engine = RapidOCR()
            except Exception:
                raise
        return self._engine

    def ocr_extract(self, image: np.ndarray) -> List[Any]:
        """
        Perform OCR on image.

        Args:
            image: Image array (BGR or RGB, numpy ndarray)

        Returns:
            List: [[[bbox], [text, confidence]], ...]
        """
        return self._ocr_with_rapid_ocr(image)

    def _ocr_with_rapid_ocr(self, image: np.ndarray) -> List[Any]:
        """Run OCR using RapidOCR."""
        try:
            engine = self._get_rapid_ocr_provider()
            # RapidOCR accepts path, bytes, or ndarray (BGR)
            result, _ = engine(image)
            if result is None or not result:
                return []

            formatted_result = []
            for item in result:
                # RapidOCR item: [box, text, score]; box is list of 4 points [[x,y],...]
                box = item[0]
                text = item[1] if len(item) > 1 else ""
                score = float(item[2]) if len(item) > 2 else 0.0
                if isinstance(box, np.ndarray):
                    box = box.tolist()
                formatted_result.append([
                    [box],
                    [text, score]
                ])
            return formatted_result

        except Exception:
            return []

    def extract_text_from_file(self, file_path: str) -> str:
        """
        Extract text from a file (for document files).

        Args:
            file_path: File path

        Returns:
            Extracted text
        """
        return ""

    def ocr(self, image_data: bytes) -> List[Any]:
        """
        Perform OCR on image data (bytes).

        Args:
            image_data: Image data as bytes

        Returns:
            List: [[[bbox], [text, confidence]], ...]
        """
        try:
            import cv2
            nparr = np.frombuffer(image_data, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if image is None:
                return []
            return self._ocr_with_rapid_ocr(image)
        except Exception:
            return []


# Create global instance
ocr_provider_manager = OCRProviderManager()

from pathlib import Path
from typing import Any, List, Optional

import numpy as np

from smartresume.utils.onnx_runtime import (
    get_onnx_providers,
    onnx_device,
    verify_onnx_session,
)


class OCRProviderManager:
    def __init__(self) -> None:
        self._engine: Optional[Any] = None

    def get_ocr_provider(self) -> Any:
        return self._get_rapid_ocr_provider()

    def _get_rapid_ocr_provider(self) -> Any:
        if self._engine is None:
            from rapidocr import RapidOCR

            providers = get_onnx_providers()
            params = {
                "EngineConfig.onnxruntime.intra_op_num_threads": 4,
                "EngineConfig.onnxruntime.inter_op_num_threads": 1,
                "EngineConfig.onnxruntime.use_cuda": "CUDAExecutionProvider"
                in providers,
            }
            model_dir = (
                Path(__file__).resolve().parents[2] / "models" / "rapidocr"
            )
            model_files = {
                "Det": "ch_PP-OCRv4_det_infer.onnx",
                "Cls": "ch_ppocr_mobile_v2.0_cls_infer.onnx",
                "Rec": "ch_PP-OCRv4_rec_infer.onnx",
            }
            for stage, filename in model_files.items():
                model_path = model_dir / filename
                if model_path.is_file():
                    params[f"{stage}.model_path"] = str(model_path)
            engine = RapidOCR(params=params)
            sessions = {
                "detection": engine.text_det.session.session,
                "classification": engine.text_cls.session.session,
                "recognition": engine.text_rec.session.session,
            }
            for name, session in sessions.items():
                actual = verify_onnx_session(session, providers, "OCR " + name)
                print(f"OCR {name} providers: {actual}")
            self._engine = engine
        return self._engine

    def ocr_extract(self, image: np.ndarray) -> List[Any]:
        return self._ocr_with_rapid_ocr(image)

    def _ocr_with_rapid_ocr(self, image: np.ndarray) -> List[Any]:
        try:
            result = self._get_rapid_ocr_provider()(image)
            if result is None or result.boxes is None or not result.txts:
                return []
            formatted_result = []
            for box, text, score in zip(
                result.boxes, result.txts, result.scores
            ):
                if isinstance(box, np.ndarray):
                    box = box.tolist()
                formatted_result.append([[box], [text, float(score)]])
            return formatted_result
        except Exception:
            if onnx_device() == "cuda":
                raise
            return []

    def extract_text_from_file(self, file_path: str) -> str:
        return ""

    def ocr(self, image_data: bytes) -> List[Any]:
        try:
            import cv2

            nparr = np.frombuffer(image_data, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if image is None:
                return []
            return self._ocr_with_rapid_ocr(image)
        except Exception:
            if onnx_device() == "cuda":
                raise
            return []


ocr_provider_manager = OCRProviderManager()

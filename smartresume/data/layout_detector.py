import os
import cv2
import numpy as np
import json
from typing import Optional, List, Dict, Any, Tuple
from smartresume.utils.onnx_runtime import (
    get_onnx_providers,
    prepare_cuda_libraries,
    verify_onnx_session,
)

try:
    import onnxruntime as ort

    ONNX_AVAILABLE = True
except ImportError:
    ONNX_AVAILABLE = False
    print(
        "ONNX Runtime not available. Install with: "
        "pip install -e . from the project root; see README."
    )


class SimpleONNXYOLODetector:

    def __init__(self, model_path: str, providers: Optional[List[str]] = None):

        if not ONNX_AVAILABLE:
            raise ImportError(
                "ONNX Runtime not available. Install with: "
                "pip install -e . from the project root; see README."
            )

        self.model_path = model_path
        self.session = None
        self.input_name = None
        self.output_names = None
        self.input_shape = None
        self.conf_threshold = 0.5
        self.iou_threshold = 0.45

        if providers is None:
            providers = get_onnx_providers()
        elif "CUDAExecutionProvider" in providers:
            prepare_cuda_libraries()

        self.providers = providers
        self.load_model(model_path)

    def load_model(self, model_path: str):

        try:
            session_options = ort.SessionOptions()
            session_options.intra_op_num_threads = 4
            session_options.inter_op_num_threads = 1
            self.session = ort.InferenceSession(
                model_path,
                sess_options=session_options,
                providers=self.providers,
            )
            verify_onnx_session(
                self.session, self.providers, "Layout detector"
            )
            self.input_name = self.session.get_inputs()[0].name
            self.output_names = [
                output.name for output in self.session.get_outputs()
            ]
            self.input_shape = self.session.get_inputs()[0].shape

            print("ONNX model loaded successfully")
            print(f"Input shape: {self.input_shape}")
            print(f"Output names: {self.output_names}")
            print(f"Layout providers: {self.session.get_providers()}")

        except Exception as e:
            raise RuntimeError(f"Failed to load ONNX model: {e}")

    def preprocess_image(
        self, image: np.ndarray, target_size: int = 640
    ) -> Tuple[np.ndarray, float]:

        if len(image.shape) != 3:
            raise ValueError("Input must be a 3D array (H, W, C)")

        if image.shape[2] == 3:
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        h, w = image.shape[:2]
        scale = target_size / max(h, w)
        new_h, new_w = max(1, int(h * scale)), max(1, int(w * scale))

        resized = cv2.resize(image, (new_w, new_h))

        padded = np.zeros((target_size, target_size, 3), dtype=np.uint8)
        padded[:new_h, :new_w] = resized

        normalized = padded.astype(np.float32) / 255.0

        tensor = np.transpose(normalized, (2, 0, 1))
        tensor = np.expand_dims(tensor, axis=0)

        return tensor, scale

    def postprocess_output(
        self,
        outputs: List[np.ndarray],
        scale: float,
        conf_threshold: float = 0.5,
        *,
        canvas_shape: Tuple[int, int] = (640, 640),
        image_shape: Optional[Tuple[int, int]] = None,
    ) -> List[Dict[str, Any]]:

        if not outputs:
            return []

        output = outputs[0][0]
        canvas_h, canvas_w = canvas_shape
        # The bundled ONNX emits normalized cx, cy, w, h on the padded canvas.
        # The image starts in the top-left corner, with no padding offset.
        x_factor, y_factor = canvas_w / scale, canvas_h / scale

        results = []
        for detection in output:
            x_center, y_center, width, height, confidence = detection

            if confidence > conf_threshold:
                x1 = max(0, int((x_center - width / 2) * x_factor))
                y1 = max(0, int((y_center - height / 2) * y_factor))
                x2 = int((x_center + width / 2) * x_factor)
                y2 = int((y_center + height / 2) * y_factor)
                if image_shape is not None:
                    h, w = image_shape
                    x2, y2 = min(w, x2), min(h, y2)
                if x2 <= x1 or y2 <= y1:
                    continue

                results.append(
                    {
                        "score": float(confidence),
                        "x1": x1,
                        "y1": y1,
                        "x2": x2,
                        "y2": y2,
                    }
                )

        return results

    def detect(
        self, image: np.ndarray, conf_threshold: float = 0.5
    ) -> List[Dict[str, Any]]:

        if self.session is None:
            raise RuntimeError("ONNX model not loaded")

        input_tensor, scale = self.preprocess_image(image)

        try:
            outputs = self.session.run(
                self.output_names, {self.input_name: input_tensor}
            )
        except Exception as e:
            raise RuntimeError(f"ONNX inference failed: {e}")

        results = self.postprocess_output(
            outputs, scale, conf_threshold,
            canvas_shape=input_tensor.shape[-2:], image_shape=image.shape[:2],
        )

        return results


class LayoutDetector:

    def __init__(
        self, model_path: Optional[str] = None, use_onnx: bool = True
    ) -> None:

        self.use_onnx = use_onnx

        if model_path is None:
            try:
                from ..utils.config import config

                config_path = config.model_download.get("models_dir", {}).get(
                    "layout", ""
                )

                possible_paths = [
                    os.path.join(config_path, "yolov10", "best.onnx"),
                    os.path.join(config_path, "best.onnx"),
                    os.path.join("models", "yolov10", "best.onnx"),
                    os.path.join("models", "best.onnx"),
                ]

                model_path = None
                for path in possible_paths:
                    if os.path.exists(path):
                        model_path = path
                        break

                if not model_path and not config.model_download.get(
                    "auto_download", True
                ):
                    raise FileNotFoundError(
                        "Local layout weights missing; "
                        "auto_download is disabled"
                    )

                if not model_path:
                    from ..utils.models_download_utils import download_model
                    from ..utils.model_paths import ModelType, ModelSource

                    print("Layout model not found, auto-downloading...")
                    download_path = download_model(
                        ModelType.LAYOUT,
                        ModelSource.MODELSCOPE,
                        config_path or "models",
                    )
                    model_path = os.path.join(
                        download_path, "yolov10", "best.onnx"
                    )

            except Exception as e:
                raise FileNotFoundError(
                    f"Failed to get layout detection model: {e}"
                )

        if not os.path.exists(model_path):
            raise FileNotFoundError(
                f"Layout detection model file not found: {model_path}"
            )

        try:
            if model_path.endswith(".onnx"):
                self.detector = SimpleONNXYOLODetector(model_path)
            else:
                onnx_path = model_path.replace(".pt", ".onnx")
                if os.path.exists(onnx_path):
                    self.detector = SimpleONNXYOLODetector(onnx_path)
                else:
                    raise RuntimeError(
                        f"ONNX model not found. Please convert "
                        f"{model_path} to ONNX format first."
                    )

            self.original_image = None
            print("Using ONNX-based layout detector")
        except Exception as e:
            raise RuntimeError(
                f"Failed to load ONNX layout detection model: {e}"
            )

    def detect(
        self,
        image: np.ndarray,
        conf_thres: float = 0.5,
    ) -> List[Dict[str, Any]]:

        if not isinstance(image, np.ndarray) or len(image.shape) != 3:
            raise ValueError("Input must be an RGB NumPy array")

        self.original_image = image.copy()
        results = self.detector.detect(image, conf_thres)
        return results

    def save_results(
        self, results: List[Dict[str, Any]], output_path: str
    ) -> None:

        with open(output_path, "w") as f:
            json.dump(results, f, indent=2)

    def save_image(
        self,
        formatted_results: List[Dict[str, Any]],
        output_path: str = "detected_output.jpg",
    ) -> None:

        if not formatted_results:
            raise ValueError("Detection results are empty; cannot draw image")

        if self.original_image is not None:

            image_with_boxes = self.original_image.copy()
            for result in formatted_results:
                x1, y1, x2, y2 = (
                    result["x1"],
                    result["y1"],
                    result["x2"],
                    result["y2"],
                )
                color = (0, 0, 255)
                point_color1 = (255, 0, 0)
                point_color2 = (0, 255, 0)
                thickness = 2
                point_radius = 5
                cv2.rectangle(
                    image_with_boxes, (x1, y1), (x2, y2), color, thickness
                )
                cv2.circle(
                    image_with_boxes, (x1, y1), point_radius, point_color1, -1
                )
                cv2.circle(
                    image_with_boxes, (x2, y2), point_radius, point_color2, -1
                )

            cv2.imwrite(
                output_path, cv2.cvtColor(image_with_boxes, cv2.COLOR_RGB2BGR)
            )

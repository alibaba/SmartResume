import os
import cv2
import numpy as np
import json
from typing import Optional, List, Dict, Any, Tuple
import warnings
warnings.filterwarnings("ignore")

try:
    import onnxruntime as ort
    ONNX_AVAILABLE = True
except ImportError:
    ONNX_AVAILABLE = False
    print("ONNX Runtime not available. Install with: pip install onnxruntime")


class SimpleONNXYOLODetector:
    """Simple ONNX-based YOLO detector"""
    def __init__(self, model_path: str, providers: Optional[List[str]] = None):
        """Initialize ONNX YOLO detector"""
        if not ONNX_AVAILABLE:
            raise ImportError("ONNX Runtime not available. Install with: pip install onnxruntime")

        self.model_path = model_path
        self.session = None
        self.input_name = None
        self.output_names = None
        self.input_shape = None
        self.conf_threshold = 0.5
        self.iou_threshold = 0.45

        if providers is None:
            providers = (
                ['CUDAExecutionProvider', 'CPUExecutionProvider']
                if ort.get_device() == 'GPU'
                else ['CPUExecutionProvider']
            )

        self.providers = providers
        self.load_model(model_path)

    def load_model(self, model_path: str):
        """Load ONNX model"""
        try:
            self.session = ort.InferenceSession(model_path, providers=self.providers)
            self.input_name = self.session.get_inputs()[0].name
            self.output_names = [output.name for output in self.session.get_outputs()]
            self.input_shape = self.session.get_inputs()[0].shape

            print("ONNX model loaded successfully")
            print(f"Input shape: {self.input_shape}")
            print(f"Output names: {self.output_names}")
            print(f"Providers: {self.session.get_providers()}")

        except Exception as e:
            raise RuntimeError(f"Failed to load ONNX model: {e}")

    def preprocess_image(
        self, image: np.ndarray, target_size: int = 640
    ) -> Tuple[np.ndarray, float]:
        """Preprocess image for ONNX inference"""
        if len(image.shape) != 3:
            raise ValueError("Input must be a 3D array (H, W, C)")

        if image.shape[2] == 3:
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        h, w = image.shape[:2]
        scale = target_size / max(h, w)
        new_h, new_w = int(h * scale), int(w * scale)

        resized = cv2.resize(image, (new_w, new_h))

        padded = np.zeros((target_size, target_size, 3), dtype=np.uint8)
        padded[:new_h, :new_w] = resized

        normalized = padded.astype(np.float32) / 255.0

        tensor = np.transpose(normalized, (2, 0, 1))
        tensor = np.expand_dims(tensor, axis=0)

        return tensor, scale

    def postprocess_output(self, outputs: List[np.ndarray], scale: float,
                           conf_threshold: float = 0.5) -> List[Dict[str, Any]]:
        """Postprocess ONNX model output to get bounding boxes"""
        if not outputs:
            return []

        output = outputs[0][0]

        results = []
        for detection in output:
            x_center, y_center, width, height, confidence = detection

            if confidence > conf_threshold:
                x1 = int((x_center - width / 2) / scale)
                y1 = int((y_center - height / 2) / scale)
                x2 = int((x_center + width / 2) / scale)
                y2 = int((y_center + height / 2) / scale)

                results.append({
                    "score": float(confidence),
                    "x1": x1,
                    "y1": y1,
                    "x2": x2,
                    "y2": y2
                })

        return results

    def detect(self, image: np.ndarray, conf_threshold: float = 0.5) -> List[Dict[str, Any]]:
        """Detect objects in image using ONNX model"""
        if self.session is None:
            raise RuntimeError("ONNX model not loaded")

        input_tensor, scale = self.preprocess_image(image)

        try:
            outputs = self.session.run(self.output_names, {self.input_name: input_tensor})
        except Exception as e:
            raise RuntimeError(f"ONNX inference failed: {e}")

        results = self.postprocess_output(outputs, scale, conf_threshold)

        return results


class LayoutDetector:
    """Layout detector using ONNX"""

    def __init__(self, model_path: Optional[str] = None, use_onnx: bool = True) -> None:
        """Initialize detection model"""
        self.use_onnx = use_onnx

        if model_path is None:
            try:
                from ..utils.config import config
                config_path = config.model_download.get('models_dir', {}).get('layout', '')

                # Try multiple possible paths
                possible_paths = [
                    os.path.join(config_path, 'yolov10', 'best.onnx'),
                    os.path.join(config_path, 'best.onnx'),
                    os.path.join('models', 'yolov10', 'best.onnx'),
                    os.path.join('models', 'best.onnx')
                ]

                model_path = None
                for path in possible_paths:
                    if os.path.exists(path):
                        model_path = path
                        break

                if not model_path:
                    from ..utils.models_download_utils import download_model
                    from ..utils.model_paths import ModelType, ModelSource
                    print("Layout model not found, auto-downloading...")
                    download_path = download_model(
                        ModelType.LAYOUT, ModelSource.MODELSCOPE,
                        config_path or 'models'
                    )
                    model_path = os.path.join(download_path, 'yolov10', 'best.onnx')

            except Exception as e:
                raise FileNotFoundError(f"Failed to get layout detection model: {e}")

        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Layout detection model file not found: {model_path}")

        try:
            if model_path.endswith('.onnx'):
                self.detector = SimpleONNXYOLODetector(model_path)
            else:
                onnx_path = model_path.replace('.pt', '.onnx')
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
            raise RuntimeError(f"Failed to load ONNX layout detection model: {e}")

    def detect(
            self,
            image: np.ndarray,
            conf_thres: float = 0.5,
    ) -> List[Dict[str, Any]]:
        """
        :param image: Input image array (RGB)
        :param conf_thres: Confidence threshold
        :return: Formatted results list of dicts with x1, y1, x2, y2, score
        """
        if not isinstance(image, np.ndarray) or len(image.shape) != 3:
            raise ValueError("Input must be an RGB NumPy array")

        self.original_image = image.copy()
        results = self.detector.detect(image, conf_thres)
        return results

    def save_results(self, results: List[Dict[str, Any]], output_path: str) -> None:
        """Save detection results to a JSON file"""
        with open(output_path, "w") as f:
            json.dump(results, f, indent=2)

    def save_image(
        self, formatted_results: List[Dict[str, Any]],
        output_path: str = "detected_output.jpg"
    ) -> None:
        """
        Draw detection results on the original image and save it
        :param formatted_results: List of detection results with x1, y1, x2, y2
        :param output_path: Output image path (e.g., "detected_output.jpg")
        """
        if not formatted_results:
            raise ValueError("Detection results are empty; cannot draw image")

        if self.original_image is not None:
            # Draw bounding boxes
            image_with_boxes = self.original_image.copy()
            for result in formatted_results:
                x1, y1, x2, y2 = result['x1'], result['y1'], result['x2'], result['y2']
                color = (0, 0, 255)
                point_color1 = (255, 0, 0)
                point_color2 = (0, 255, 0)
                thickness = 2
                point_radius = 5
                cv2.rectangle(image_with_boxes, (x1, y1), (x2, y2), color, thickness)
                cv2.circle(image_with_boxes, (x1, y1), point_radius, point_color1, -1)
                cv2.circle(image_with_boxes, (x2, y2), point_radius, point_color2, -1)

            cv2.imwrite(output_path, cv2.cvtColor(image_with_boxes, cv2.COLOR_RGB2BGR))

"""
Model paths configuration for SmartResume
"""
from enum import Enum


class ModelPath(Enum):
    """Model path configurations for different model sources"""

    # ModelScope repositories
    SMART_RESUME_ROOT_MODELSCOPE = "Alibaba-EI/SmartResume"
    YOLOV10_ROOT_MODELSCOPE = "Alibaba-EI/SmartResume"

    # Specific model paths
    QWEN3_0_6B = "Qwen3-0.6B"
    YOLOV10_MODEL = "yolov10/best.onnx"

    # Model types
    LLM_MODEL = "llm"
    LAYOUT_MODEL = "layout"


class ModelType(Enum):
    """Model types for SmartResume"""
    LLM = "llm"           # Large Language Model for text extraction
    LAYOUT = "layout"     # Layout detection model
    ALL = "all"           # All models


class ModelSource(Enum):
    """Model download sources"""
    MODELSCOPE = "modelscope"
    HUGGINGFACE = "huggingface"
    LOCAL = "local"

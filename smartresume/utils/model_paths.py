from enum import Enum


class ModelPath(Enum):

    SMART_RESUME_ROOT_MODELSCOPE = "Alibaba-EI/SmartResume"
    YOLOV10_ROOT_MODELSCOPE = "Alibaba-EI/SmartResume"

    QWEN3_0_6B = "Qwen3-0.6B"
    QWEN3_0_6B_V2 = "Qwen3-0.6B-v2"
    YOLOV10_MODEL = "yolov10/best.onnx"

    LLM_MODEL = "llm"
    LAYOUT_MODEL = "layout"


class ModelType(Enum):

    LLM = "llm"
    LAYOUT = "layout"
    ALL = "all"


class ModelSource(Enum):

    MODELSCOPE = "modelscope"
    HUGGINGFACE = "huggingface"
    LOCAL = "local"

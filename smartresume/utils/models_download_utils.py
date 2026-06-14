"""
Model download utilities for SmartResume
"""
import os
from typing import Optional

try:
    from modelscope import snapshot_download as ms_snapshot_download
    MODELSCOPE_AVAILABLE = True
except ImportError:
    MODELSCOPE_AVAILABLE = False


from .model_paths import ModelPath, ModelType, ModelSource


def auto_download_and_get_model_path(
    relative_path: str,
    model_type: ModelType = ModelType.LLM,
    save_path: Optional[str] = None
) -> str:

    model_source = os.getenv('SMARTRESUME_MODEL_SOURCE', "modelscope")

    if model_source == 'local':
        from .config import config
        local_path = config.model_download.get('models_dir', {}).get(model_type.value, '')
        if not local_path:
            raise ValueError(f"Local path for model_type '{model_type.value}' is not configured.")
        return local_path

    repo_mapping = {
        ModelType.LLM: ModelPath.SMART_RESUME_ROOT_MODELSCOPE.value,
        ModelType.LAYOUT: ModelPath.YOLOV10_ROOT_MODELSCOPE.value
    }

    if model_type not in repo_mapping:
        raise ValueError(f"Unsupported model_type: {model_type}, must be 'llm' or 'layout'")

    repo = repo_mapping[model_type]

    if not MODELSCOPE_AVAILABLE:
        raise ImportError("ModelScope not available. Install with: pip install modelscope")
    snapshot_download = ms_snapshot_download

    cache_dir = None

    if model_type == ModelType.LLM:
        relative_path = relative_path.strip('/')
        if save_path:
            # Create the save directory if it doesn't exist
            os.makedirs(save_path, exist_ok=True)
            cache_dir = snapshot_download(
                repo,
                allow_patterns=[relative_path, relative_path + "/*"],
                local_dir=save_path
            )
        else:
            cache_dir = snapshot_download(
                repo,
                allow_patterns=[
                    relative_path, relative_path + "/*"
                ]
            )
    elif model_type == ModelType.LAYOUT:
        relative_path = relative_path.strip('/')
        if save_path:
            # Create the save directory if it doesn't exist
            os.makedirs(save_path, exist_ok=True)
            cache_dir = snapshot_download(
                repo,
                allow_patterns=[
                    relative_path, relative_path + "/*"
                ],
                local_dir=save_path
            )
        else:
            cache_dir = snapshot_download(
                repo,
                allow_patterns=[
                    relative_path, relative_path + "/*"
                ]
            )

    if not cache_dir:
        raise FileNotFoundError(f"Failed to download model: {relative_path} from {repo}")

    return cache_dir


def get_model_path(model_type: ModelType) -> Optional[str]:
    from .config import config
    return config.model_download.get('models_dir', {}).get(model_type.value)


def download_model(
    model_type: ModelType,
    model_source: Optional[ModelSource] = None,
    save_path: Optional[str] = None
) -> str:
    if model_source:
        os.environ['SMARTRESUME_MODEL_SOURCE'] = model_source.value

    if model_type == ModelType.LLM:
        return auto_download_and_get_model_path(
            ModelPath.QWEN3_0_6B.value, ModelType.LLM, save_path
        )
    elif model_type == ModelType.LAYOUT:
        return auto_download_and_get_model_path(
            ModelPath.YOLOV10_MODEL.value, ModelType.LAYOUT,
            save_path
        )
    else:
        raise ValueError(f"Unsupported model type: {model_type}")


if __name__ == '__main__':
    try:
        llm_path = auto_download_and_get_model_path(
            ModelPath.QWEN3_0_6B.value, ModelType.LLM
        )
        print(f"LLM model path: {llm_path}")

        layout_path = auto_download_and_get_model_path(
            ModelPath.YOLOV10_MODEL.value, ModelType.LAYOUT
        )
        print(f"Layout model path: {layout_path}")

    except Exception as e:
        print(f"Download failed: {e}")

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
    save_path: Optional[str] = None,
) -> str:

    model_source = os.getenv("SMARTRESUME_MODEL_SOURCE", "modelscope")

    relative_path = relative_path.strip("/")

    if model_source == "local":
        from .config import config

        local_path = config.model_download.get("models_dir", {}).get(
            model_type.value, ""
        )
        if not local_path:
            raise ValueError(
                f"Local path for model_type '{model_type.value}' "
                "is not configured."
            )
        if model_type == ModelType.LLM:
            checkpoint = os.path.join(local_path, relative_path)
            if os.path.isdir(checkpoint):
                return checkpoint
            if not os.path.isfile(os.path.join(local_path, "config.json")):
                raise FileNotFoundError(
                    f"Local checkpoint missing: {checkpoint}"
                )
        return local_path

    repo_mapping = {
        ModelType.LLM: ModelPath.SMART_RESUME_ROOT_MODELSCOPE.value,
        ModelType.LAYOUT: ModelPath.YOLOV10_ROOT_MODELSCOPE.value,
    }

    if model_type not in repo_mapping:
        raise ValueError(
            f"Unsupported model_type: {model_type}, must be 'llm' or 'layout'"
        )

    repo = repo_mapping[model_type]

    if not MODELSCOPE_AVAILABLE:
        raise ImportError(
            "ModelScope not available. Install with: pip install modelscope"
        )
    snapshot_download = ms_snapshot_download

    if save_path:
        os.makedirs(save_path, exist_ok=True)
    cache_dir = snapshot_download(
        repo,
        allow_patterns=[relative_path, relative_path + "/*"],
        local_dir=save_path or None,
    )

    if not cache_dir:
        raise FileNotFoundError(
            f"Failed to download model: {relative_path} from {repo}"
        )

    if model_type == ModelType.LLM:
        checkpoint = os.path.join(cache_dir, relative_path)
        if not os.path.isdir(checkpoint):
            raise FileNotFoundError(
                f"Downloaded checkpoint missing: {checkpoint}"
            )
        return checkpoint
    return cache_dir


def get_model_path(model_type: ModelType) -> Optional[str]:
    from .config import config

    return config.model_download.get("models_dir", {}).get(model_type.value)


def download_model(
    model_type: ModelType,
    model_source: Optional[ModelSource] = None,
    save_path: Optional[str] = None,
) -> str:
    if model_source:
        os.environ["SMARTRESUME_MODEL_SOURCE"] = model_source.value

    if model_type == ModelType.LLM:
        return auto_download_and_get_model_path(
            ModelPath.QWEN3_0_6B_V2.value, ModelType.LLM, save_path
        )
    elif model_type == ModelType.LAYOUT:
        return auto_download_and_get_model_path(
            ModelPath.YOLOV10_MODEL.value, ModelType.LAYOUT, save_path
        )
    else:
        raise ValueError(f"Unsupported model type: {model_type}")


if __name__ == "__main__":
    try:
        llm_path = auto_download_and_get_model_path(
            ModelPath.QWEN3_0_6B_V2.value, ModelType.LLM
        )
        print(f"LLM model path: {llm_path}")

        layout_path = auto_download_and_get_model_path(
            ModelPath.YOLOV10_MODEL.value, ModelType.LAYOUT
        )
        print(f"Layout model path: {layout_path}")

    except Exception as e:
        print(f"Download failed: {e}")

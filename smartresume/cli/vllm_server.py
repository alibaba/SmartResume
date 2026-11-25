import sys
from pathlib import Path


project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


try:
    from vllm.entrypoints.cli.main import main as vllm_main

    VLLM_AVAILABLE = True
except ImportError:
    VLLM_AVAILABLE = False
    print("VLLM not available. Install with: pip install vllm")


def main():
    from smartresume.utils.models_download_utils import (
        auto_download_and_get_model_path,
    )
    from smartresume.utils.model_paths import ModelPath, ModelType

    if not VLLM_AVAILABLE:
        print(
            "Error: VLLM is not installed. "
            "Please install it with: pip install vllm"
        )
        sys.exit(1)

    args = sys.argv[1:]

    has_port_arg = False
    has_gpu_memory_utilization_arg = False
    has_model_arg = False
    model_path = None
    model_arg_indices = []

    for i, arg in enumerate(args):
        if arg == "--port" or arg.startswith("--port="):
            has_port_arg = True
        if arg == "--gpu-memory-utilization" or arg.startswith(
            "--gpu-memory-utilization="
        ):
            has_gpu_memory_utilization_arg = True
        if arg == "--model":
            if i + 1 < len(args):
                model_path = args[i + 1]
                model_arg_indices.extend([i, i + 1])
                has_model_arg = True
        elif arg.startswith("--model="):
            model_path = arg.split("=", 1)[1]
            model_arg_indices.append(i)
            has_model_arg = True

    if model_arg_indices:
        for index in sorted(model_arg_indices, reverse=True):
            args.pop(index)

    if not has_port_arg:
        args.extend(["--port", "30000"])
    if not has_gpu_memory_utilization_arg:
        args.extend(["--gpu-memory-utilization", "0.8"])

    if not has_model_arg:
        try:
            print("Downloading SmartResume LLM model...")
            model_path = auto_download_and_get_model_path(
                ModelPath.QWEN3_0_6B_V2.value, ModelType.LLM
            )
            print(f"Model downloaded to: {model_path}")
        except Exception as e:
            print(f"Failed to download model: {e}")
            sys.exit(1)

    sys.argv = [sys.argv[0]] + ["serve", model_path] + args

    print(f"Starting VLLM server with model: {model_path}")
    print(f"Server arguments: {sys.argv}")
    vllm_main()


if __name__ == "__main__":
    main()

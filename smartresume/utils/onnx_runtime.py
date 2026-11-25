import logging
import os
import sys
import ctypes
from functools import lru_cache
from importlib import import_module, metadata

logger = logging.getLogger(__name__)
CUDA_PROVIDER = "CUDAExecutionProvider"
CPU_PROVIDER = "CPUExecutionProvider"


def onnx_device():

    device = os.getenv("SMARTRESUME_ONNX_DEVICE")
    if device is None:
        from smartresume.utils.config import config

        device = getattr(config.ocr, "device", None)
        if device is None:
            legacy = getattr(config.ocr, "use_cuda", None)
            device = (
                "cuda"
                if legacy is True
                else "cpu" if legacy is False else "auto"
            )
    if not isinstance(device, str) or device.strip().lower() not in {
        "auto",
        "cpu",
        "cuda",
    }:
        raise ValueError(
            "SMARTRESUME_ONNX_DEVICE / ocr.device must be auto, cpu, or cuda"
        )
    return device.strip().lower()


@lru_cache(maxsize=1)
def prepare_cuda_libraries():

    try:
        import_module("torch")
    except ImportError:
        pass
    if sys.platform != "linux":
        return ()
    bundles = {
        "nvidia-cuda-runtime-cu12": ("libcudart.so.12",),
        "nvidia-cublas-cu12": ("libcublasLt.so.12", "libcublas.so.12"),
        "nvidia-cufft-cu12": ("libcufft.so.11",),
        "nvidia-curand-cu12": ("libcurand.so.10",),
        "nvidia-cuda-nvrtc-cu12": ("libnvrtc.so.12",),
        "nvidia-cudnn-cu12": (
            "libcudnn_graph.so.9",
            "libcudnn_ops.so.9",
            "libcudnn_adv.so.9",
            "libcudnn_cnn.so.9",
            "libcudnn_heuristic.so.9",
            "libcudnn_engines_precompiled.so.9",
            "libcudnn_engines_runtime_compiled.so.9",
            "libcudnn.so.9",
        ),
    }
    handles = []
    for package, names in bundles.items():
        try:
            dist = metadata.distribution(package)
        except metadata.PackageNotFoundError:
            continue
        files = {
            path.name: dist.locate_file(path) for path in (dist.files or ())
        }
        for name in names:
            path = files.get(name)
            if path is not None:
                try:
                    handles.append(
                        ctypes.CDLL(str(path), mode=ctypes.RTLD_GLOBAL)
                    )
                except OSError as error:
                    raise RuntimeError(
                        f"Cannot preload CUDA dependency {name}: {error}"
                    ) from error
    return tuple(handles)


def get_onnx_providers():
    import onnxruntime as ort

    device = onnx_device()
    if device == "cpu":
        return [CPU_PROVIDER]
    available = ort.get_available_providers()
    if CUDA_PROVIDER in available:
        try:
            prepare_cuda_libraries()
        except RuntimeError as error:
            if device == "cuda":
                raise
            logger.warning(
                "ONNX uses CPU because CUDA dependencies could not load: %s",
                error,
            )
            return [CPU_PROVIDER]
        return [CUDA_PROVIDER, CPU_PROVIDER]
    if device == "cuda":
        raise RuntimeError(
            "CUDA requested, but this ONNX Runtime has no "
            "CUDAExecutionProvider. "
            "Install a CUDA/cuDNN-compatible onnxruntime-gpu; "
            "do not co-install onnxruntime."
        )
    logger.warning(
        "ONNX uses CPU: CUDAExecutionProvider is unavailable "
        "in the installed runtime. "
        "For NVIDIA GPU inference, install a compatible onnxruntime-gpu."
    )
    return [CPU_PROVIDER]


def verify_onnx_session(session, requested, component):

    actual = session.get_providers()
    if CUDA_PROVIDER in requested and (
        not actual or actual[0] != CUDA_PROVIDER
    ):
        message = (
            component
            + " could not initialize CUDA; actual providers: "
            + str(actual)
            + ". Check CUDA/cuDNN shared libraries and "
            "onnxruntime-gpu compatibility."
        )
        if onnx_device() == "cuda":
            raise RuntimeError(message)
        logger.warning(message)
    return actual

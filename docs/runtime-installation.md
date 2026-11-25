# Runtime installation

Use Linux x86_64 and Python 3.11 (recommended; project minimum: 3.10), with an NVIDIA driver compatible with CUDA 12.4. From a fresh environment in the repository root, run:

~~~bash
pip install -e .
~~~

The default dependencies include PyTorch 2.6.0, ONNX Runtime GPU 1.20.2, RapidOCR 3.4.1, Transformers, Accelerate, ModelScope and Flask. A separate runtime installer is not required. PyTorch dependencies supply the CUDA/cuDNN user-space libraries used by the ONNX backend; the NVIDIA driver is installed on the host. vLLM remains optional and requires a version compatible with the pinned PyTorch. Minimal Debian/Ubuntu installations may also need OpenCV system libraries: `apt-get install -y libgl1 libglib2.0-0`. The Dockerfile includes these libraries.

## Existing environments

If an older installation contains rapidocr-onnxruntime or the CPU onnxruntime package, clean up those conflicting distributions once before installing:

~~~bash
pip uninstall -y rapidocr-onnxruntime onnxruntime onnxruntime-gpu
pip install -e .
~~~

Restart Python and Web processes after changing dependencies. Do not install the CPU and GPU ONNX Runtime distributions together. New installations do not need these cleanup commands.

An existing CPU-only PyTorch build is not automatically replaced by a version constraint. If needed, select the CUDA build explicitly:

~~~bash
pip install --force-reinstall torch==2.6.0 --index-url https://download.pytorch.org/whl/cu124
~~~

## Models

Existing LLM and layout paths remain unchanged. OCR uses the preserved PP-OCRv4 files in models/rapidocr when present. Otherwise, RapidOCR 3.4.1 supplies the same bundled detection, classification and recognition weights. Installing dependencies does not replace the trained LLM checkpoint or layout model.

## Device selection

The GPU runtime also supports CPU execution; no package swap is needed. To require CUDA for OCR and layout:

~~~bash
SMARTRESUME_ONNX_DEVICE=cuda python scripts/start.py --file resume.pdf
~~~

To run the default Transformers pipeline on CPU with the same dependencies:

~~~bash
CUDA_VISIBLE_DEVICES="" SMARTRESUME_ONNX_DEVICE=cpu python scripts/start.py --file resume.pdf
~~~

Priority: SMARTRESUME_ONNX_DEVICE > ocr.device > legacy ocr.use_cuda > auto. The ONNX setting controls OCR/layout; Transformers chooses its own device from the visible GPUs.

requirements.txt explicitly lists the same default dependencies as pyproject.toml. Installing with -e also installs the project and its command-line entry points. See [configuration](configuration.md) and [local models](local-models.md).

## Docker

The Python 3.11 Dockerfile installs the same default dependencies with `pip install -e .`. Configure the host's [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html), then run from the repository root:

~~~bash
docker build -f docker/Dockerfile -t smartresume .
docker run --rm --gpus all \
  -e SMARTRESUME_ONNX_DEVICE=cuda \
  -p 4999:4999 \
  -v "$PWD/models:/app/models" \
  -v "$PWD/configs:/app/configs" \
  smartresume python demo/web_app.py
~~~

Prepare complete weights and `configs/config.yaml` first. Model paths must resolve inside the container, for example `/app/models/Qwen3-0.6B-v2`; mount external symlink targets as well. Open `http://localhost:4999`. The image's default command only displays CLI help; the command above starts Web explicitly.

For CPU execution, replace `--gpus all` and `-e SMARTRESUME_ONNX_DEVICE=cuda` with `-e CUDA_VISIBLE_DEVICES="" -e SMARTRESUME_ONNX_DEVICE=cpu`. Keep the same ONNX Runtime package.

References: [RapidOCR installation](https://rapidai.github.io/RapidOCRDocs/main/install_usage/rapidocr/install/) and [ONNX Runtime CUDA compatibility](https://onnxruntime.ai/docs/execution-providers/CUDA-ExecutionProvider.html#requirements).

The project does not require historical files in temp. Web uploads and extraction-error logs recreate their subdirectories as needed; keep model weights and configuration files when cleaning up.

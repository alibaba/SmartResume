# Local model deployment

`pip install -e .` includes GPU inference, local-model and Web dependencies. See the [runtime guide](runtime-installation.md) for existing environments and CPU execution. The default backend is Transformers. If vLLM is separately installed, it is attempted first. Both run in-process; a separate HTTP model server is optional.

The default extraction checkpoint is `Qwen3-0.6B-v2` from the ModelScope repository `Alibaba-EI/SmartResume`. To switch an existing installation, download v2 and update `direct_model_name` in your active configuration. If you serve v2 through the local HTTP channel, set `channels.local_qwen.name` to the name advertised by the server.

~~~bash
python scripts/download_models.py
~~~

Configure the checkpoint path and OCR/layout policy:

~~~yaml
use_direct_models: true
direct_model_name: models/Qwen3-0.6B-v2
ocr:
  device: auto
~~~

Parse all ten task families:

~~~bash
python scripts/start.py --file resume.pdf \
  --extract_types basic_info work_experience project_experience education \
  skills_strengths publication competition honor research_direction social_profile
~~~

For a separately managed OpenAI-compatible model server, set use_direct_models to false and configure model or channels as described in [configuration](configuration.md).

The default installation includes PyTorch, ONNX Runtime GPU, RapidOCR, Transformers, Accelerate, ModelScope and Flask. vLLM remains optional and has separate hardware and package requirements. After adding or changing dependencies, use the ONNX Runtime cleanup commands in the [installation guide](runtime-installation.md) if conflicting packages are introduced.

OCR/layout device selection and the local LLM device are separate. Setting SMARTRESUME_ONNX_DEVICE=cpu alone does not hide CUDA from Transformers.

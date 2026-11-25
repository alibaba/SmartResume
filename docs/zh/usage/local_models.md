# 本地模型部署

`pip install -e .` 默认包含 PyTorch、ONNX Runtime GPU、RapidOCR、Transformers、Accelerate、ModelScope 和 Flask；vLLM 为独立可选项。旧环境升级见[安装指南](../quick_start/installation.md)。

默认抽取模型为 ModelScope 仓库 `Alibaba-EI/SmartResume` 中的 `Qwen3-0.6B-v2`。已有环境切换到 v2 时，下载权重后，更新当前生效配置里的 `direct_model_name`。使用本地 HTTP 服务时，`channels.local_qwen.name` 应填写服务端公布的模型名。

~~~bash
python scripts/download_models.py
~~~

配置示例：

~~~yaml
use_direct_models: true
direct_model_name: models/Qwen3-0.6B-v2
ocr:
  device: auto
~~~

默认使用进程内 Transformers；另外安装了 vLLM 时会优先尝试 vLLM。无须为了进程内推理再启动独立 HTTP 服务。

~~~bash
python scripts/start.py --file resume.pdf \
  --extract_types basic_info work_experience project_experience education \
  skills_strengths publication competition honor research_direction social_profile
~~~

如已有独立的 OpenAI 兼容模型服务，可设置 use_direct_models: false，并按[配置说明](configuration.md)配置 model 或 channels。

OCR/版面与 LLM 设备分别控制。默认 Transformers 流程使用 CPU 时，设置 `CUDA_VISIBLE_DEVICES="" SMARTRESUME_ONNX_DEVICE=cpu`，无需更换依赖。vLLM 需另选与固定 PyTorch 版本兼容的版本。旧环境冲突处理见[安装指南](../quick_start/installation.md)。

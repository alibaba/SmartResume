# 本地模型部署

SmartResume 支持两种本地推理方式，既可以通过 vLLM 暴露 OpenAI 兼容接口，也可以直接加载离线模型。根据硬件条件与部署需求选择合适的方案。

## 一、环境准备

| 组件 | 最低要求 | 推荐配置 |
|------|----------|----------|
| **GPU** | NVIDIA GTX 1060 (6GB) | RTX 3080+ (10GB+) |
| **内存** | 16GB | 32GB+ |
| **存储** | 20GB 可用空间 | 50GB+ SSD |

软件要求：Python 3.9+、CUDA 11.8+（若需 GPU 推理）、`torch`、`transformers`、`vllm`（仅限方案一）。

## 二、方案一：OpenAI 兼容的本地 vLLM 服务

### 1. 安装 vLLM

```bash
pip install vllm
# 或者安装最新源码版本
pip install git+https://github.com/vllm-project/vllm.git
```

### 2. 下载模型

```bash
# 使用仓库脚本下载默认模型
python scripts/download_models.py
```

模型会存放在 `models/` 目录。请确保 GPU 显存足以加载目标模型。

### 3. 使用进程内 vLLM（推荐，无需单独服务）

在 `configs/config.yaml` 中设置 `use_direct_models: true` 和 `direct_model_name`（如 `models/Qwen3-0.6B`），SmartResume 会以库方式加载 vLLM，无需启动 API 服务。

若需以 API 方式单独启动 vLLM 服务（高级用法，通常不需要）：

```bash
python -m vllm.entrypoints.openai.api_server \
  --model ./models/Qwen3-0.6B \
  --port 8001 \
  --host 0.0.0.0 \
  --tensor-parallel-size 1 \
  --gpu-memory-utilization 0.8
```

### 4. 配置 SmartResume

在 `configs/config.yaml` 中新增或修改通道信息，并将提取任务映射到该通道：

```yaml
channels:
  local_qwen:
    name: "models/Qwen3-0.6B"
    api_url: "http://localhost:8001/v1"
    api_key: "local"
    max_tokens: 4096
    temperature: 0.1
    top_p: 0.95

extract_channels:
  basic_info: "local_qwen"
  work_experience: "local_qwen"
  education: "local_qwen"
```

保存配置后，普通命令即可启用本地服务：

```bash
python scripts/start.py --file resume.pdf
```

### 5. 验证

使用进程内模式时，直接运行解析命令即可验证：

```bash
python scripts/start.py --file resume.pdf
```

若使用独立 API 方式（高级用法），可通过以下命令检查服务：

```bash
curl http://localhost:8001/v1/models
```

## 三、方案二：直接加载离线模型

对于显存更充足或希望完全离线的场景，可让 SmartResume 直接加载 `transformers` 模型。

### 1. 准备模型

将模型权重放在 `models/` 目录下，例如 `models/Qwen3-0.6B/`。也可以填写 HuggingFace 仓库名，程序会尝试自动下载。

### 2. 修改配置

```yaml
use_direct_models: true
direct_model_name: "models/Qwen3-0.6B"
```

保存后再次运行解析命令：

```bash
python scripts/start.py --file resume.pdf
```

运行时的优先级为：**直接模型 > 自定义通道 > 默认远程 API**。若直接模型加载失败，会自动回退到其他通道。

## 四、Python API 示例

```python
from smartresume import ResumeAnalyzer

analyzer = ResumeAnalyzer(
    init_ocr=True,
    init_llm=True,
)

result = analyzer.pipeline(
    cv_path="resume.pdf",
    resume_id="resume_001",
    extract_types=["basic_info", "work_experience", "education"]
)
```

API 会读取配置文件并自动选择合适的推理模式，无需额外设置本地 URL。

## 五、故障排除

1. **连接被拒绝**：若使用进程内模式，检查 `use_direct_models` 和 `direct_model_name` 配置是否正确。
2. **显存不足**：降低 `vllm_gpu_memory_utilization`，或启用量化（如 `--quantization fp8`）。
3. **直接模型加载失败**：检查 `direct_model_name` 指向的目录是否完整，必要时删除缓存重新下载。
4. **推理耗时长**：可在 `configs/config.yaml` 中降低 `max_tokens` 或温度参数，以减少生成成本。

部署完成后，建议先用少量样例验证解析结果，再扩展到批量处理。

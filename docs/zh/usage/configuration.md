# 配置说明

SmartResume 的运行由 `configs/config.yaml` 控制。你可以复制仓库中的示例文件进行修改，下文展示了当前版本的标准结构：

## 配置文件示例

```yaml
model:
  name: "qwen-turbo"
  api_url: "https://dashscope.aliyuncs.com/compatible-mode/v1"
  api_key: ""
  max_tokens: 4096
  temperature: 0
  top_p: 1.0
  seed: 0

channels:
  local_qwen:
    name: "models/Qwen3-0.6B"
    api_url: "http://localhost:8001/v1"
    api_key: "local"
    max_tokens: 4096
    temperature: 0.1
    top_p: 0.95
    seed: 0

extract_channels:
  basic_info: "local_qwen"
  work_experience: "local_qwen"
  education: "local_qwen"

processing:
  use_force_ocr: false
  use_force_json: false
  use_pdf_raw_text: false
  remove_position_and_company_line: false

ocr:
  ocr_provider: "default"
  use_cuda: true
  confidence_threshold: 0.5

layout_detection:
  enabled: true

use_direct_models: true
direct_model_name: "models/Qwen3-0.6B"

model_download:
  source: "modelscope"
  models_dir:
    llm: "models"
    layout: "models"
  auto_download: true
```

> 📌 如果只使用远程 API，可删除 `channels`、`extract_channels` 以及 `use_direct_models` 等可选段落。

## 字段说明

### `model`
- `name`：默认使用的模型名称，通常与远程服务的模型 ID 对应。
- `api_url`：远程 OpenAI 兼容接口地址。
- `api_key`：远程接口的密钥，如走公共云必须填写。
- `max_tokens` / `temperature` / `top_p` / `seed`：生成参数，与 OpenAI 接口的含义一致。

### `channels`
- 用于配置多个备用通道（如本地 vLLM 服务或其他云服务）。
- 每个通道都可以定义自己的 `api_url`、`api_key` 与生成参数。
- 名称将用于 `extract_channels` 映射。

### `extract_channels`
- 将不同提取任务映射到指定通道。例如上例中全部走 `local_qwen`。
- 若字段缺失或指向未知通道，将自动回退到默认 `model` 通道。

### `processing`
- `use_force_ocr`：强制执行 OCR，而不读取 PDF 文本层。
- `use_force_json`：强制要求模型返回 JSON。
- `use_pdf_raw_text`：优先使用 PDF 原始文本（关闭则更依赖 OCR 结果）。
- `remove_position_and_company_line`：去掉包含职位/公司信息的行，便于结构化处理。

### `ocr`
- `ocr_provider`：OCR 服务提供方，默认为内置实现。
- `use_cuda`：是否开启 GPU OCR 加速。
- `confidence_threshold`：过滤低置信度识别结果的阈值。

### `layout_detection`
- `enabled`：是否启用版面分析模型。

### `use_direct_models` / `direct_model_name`
- `use_direct_models`：开启后，系统会尝试直接从磁盘加载模型，而不是通过 HTTP 接口调用。
- `direct_model_name`：本地模型路径或 HuggingFace 仓库名。若为相对路径，将在 `model_download.models_dir.llm` 下查找。

### `model_download`
- `source`：下载源，当前支持 `modelscope`。
- `models_dir.llm` / `models_dir.layout`：自动下载的存储目录。
- `auto_download`：缺少模型文件时是否自动下载。

## 运行模式

- **远程 API（默认）**：仅配置 `model` 段并填写有效的 `api_key`，无需其他改动。
- **本地 vLLM API**：启动 OpenAI 兼容的 vLLM 服务，将其地址配置在 `channels` 中，并在 `extract_channels` 映射到该通道。
- **直接模型模式（离线推理）**：设置 `use_direct_models: true`，并将 `direct_model_name` 指向本地模型。流程会优先使用直接加载的模型，失败时再回退到 `channels` 或远程 API。

## 验证配置

```python
from smartresume.utils.config import Config

Config.from_yaml("configs/config.yaml")
print("配置加载成功")
```

如需调试，可捕获异常并输出报错信息定位问题。

## 常见问题

1. **提示缺少 API Key**  
   - 检查 `model.api_key` 或相应通道的 `api_key` 是否配置。
2. **本地模型无法加载**  
   - 确认 `direct_model_name` 指向的路径存在且包含权重文件，必要时在 `models` 目录下创建软链接。
3. **调用本地 vLLM 通道失败**  
   - 一般为网络不可达或服务未启动，使用 `curl http://localhost:8001/v1/models` 验证即可。

## 最佳实践

- 为不同环境维护多份配置文件（例如 `configs/dev.yaml`、`configs/prod.yaml`）。
- 使用环境变量管理敏感信息，而不是直接写入 YAML。
- 变更配置后执行一次单页测试，确认响应时间与结果符合预期。

## 下一步

- [本地模型部署指南](local_models.md)
- [命令行工具](cli.md)
- [Python API 使用示例](api.md)
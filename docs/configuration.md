# Configuration Overview

SmartResume reads all runtime options from `configs/config.yaml`. The file shipped with the repository can be used as a starting point:

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

- Leave `channels` / `extract_channels` empty if you only rely on the remote API defined in `model`.
- Set `use_direct_models: true` with a valid `direct_model_name` to load a local Transformers model before falling back to HTTP channels.

After editing the file you can validate it via:

```python
from smartresume.utils.config import Config
Config.from_yaml("configs/config.yaml")
```

Next steps:

- [Local model deployment](local-models.md)
- [Command-line usage (Chinese)](zh/usage/cli.md)
- [Python API guide (Chinese)](zh/usage/api.md)
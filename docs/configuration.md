# Configuration

Create configs/config.yaml from configs/config.yaml.example only for a new installation. Preserve an existing model path/API configuration. SMARTRESUME_CONFIG can select another configuration file.

## OCR and layout device

~~~yaml
ocr:
  ocr_provider: default
  device: auto
  confidence_threshold: 0.5
layout_detection:
  enabled: true
~~~

Both OCR and layout use the same ONNX policy. Priority is SMARTRESUME_ONNX_DEVICE > ocr.device > legacy ocr.use_cuda > auto.

- auto prefers an available working GPU and permits CPU fallback.
- cuda requires CUDA and reports initialization errors instead of silently claiming GPU use.
- cpu requests CPU even if a GPU runtime is installed.
- Legacy use_cuda: true/false remains supported when device is omitted, mapping to cuda/cpu.

This policy does not select the LLM device. See [runtime installation](runtime-installation.md).

## Extraction tasks

CLI defaults to all ten tasks. EXTRACT_TYPES in smartresume/utils/extraction_schema.py is the shared task list. For an external API, channel mappings may be configured for all task names: basic_info, work_experience, project_experience, education, skills_strengths, publication, competition, honor, research_direction, social_profile.

## Model settings

For an existing local checkpoint:

~~~yaml
use_direct_models: true
direct_model_name: models/Qwen3-0.6B-v2
~~~

For a remote model set use_direct_models: false and configure model.api_url, model.api_key and model.name. Keep credentials out of version control. Full required settings are provided by configs/config.yaml.example; the snippets here are partial examples, not replacement configuration files.

~~~python
from smartresume.utils.config import Config
Config.from_yaml("configs/config.yaml")
~~~

Invalid configuration raises an error at startup. Restart the process after changing the configuration or environment; existing model sessions are cached.

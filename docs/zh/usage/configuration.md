# 配置说明

新环境从 configs/config.yaml.example 创建配置，已有环境保留自己的模型路径和 API 凭据。SMARTRESUME_CONFIG 可指定另一份配置文件。以下为部分配置片段，不可直接覆盖完整配置。

## OCR 与版面设备

~~~yaml
ocr:
  ocr_provider: default
  device: auto
  confidence_threshold: 0.5
layout_detection:
  enabled: true
~~~

优先级为 SMARTRESUME_ONNX_DEVICE > ocr.device > 旧版 ocr.use_cuda > auto。auto 优先使用可用 GPU，允许 CPU 回退；cuda 要求可用 CUDA；cpu 固定使用 CPU。旧 use_cuda 的 true/false 在未配置 device 时分别映射到 cuda/cpu。此设置不决定 LLM 设备。

## 本地模型

~~~yaml
use_direct_models: true
direct_model_name: models/Qwen3-0.6B-v2
~~~

默认使用 Transformers，独立安装 vLLM 时会优先尝试。模型配置详见[本地模型](local_models.md)。

## 远程 API 与抽取通道

设置 use_direct_models: false，并填写 model.name、model.api_url、model.api_key 和生成参数。可在 channels 中配置不同服务，并通过 extract_channels 映射以下任务：

| 任务 | JSON 根字段 |
| --- | --- |
| basic_info | basicInfo |
| work_experience | workExperience |
| project_experience | projectExperience |
| education | education |
| skills_strengths | professionalSkills, personalStrengths |
| publication | publicationList |
| competition | competitionList |
| honor | honorList |
| research_direction | researchDirectionList |
| social_profile | socialProfileList |

完整模板已列出全部任务。不要将实际 API 凭据提交到版本库。配置无效会在启动时报错；更改配置或环境变量后需重启进程，已创建的模型会话不会自动重建。

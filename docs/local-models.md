# Local Model Deployment

SmartResume supports local model inference via vLLM (in-process) or Transformers, with no separate API server required.

## Quick Setup

1. Install dependencies and download the resume model:
   ```bash
   pip install "SmartResume[local]"
   python scripts/download_models.py
   ```

2. Enable direct model loading in `configs/config.yaml`:
   ```yaml
   use_direct_models: true
   direct_model_name: "models/Qwen3-0.6B"
   ```

3. Run the parser as usual:
   ```bash
   python scripts/start.py --file resume.pdf
   ```

When `use_direct_models` is true, SmartResume loads the model in-process using vLLM (preferred) or Transformers as a fallback. No separate vLLM API server is needed.

## Python API example

```python
from smartresume import ResumeAnalyzer

analyzer = ResumeAnalyzer(init_ocr=True, init_llm=True)
result = analyzer.pipeline(
    cv_path="resume.pdf",
    resume_id="resume_001",
    extract_types=["basic_info", "work_experience", "education"],
)
```

The behavior is driven by the YAML configuration — no extra arguments are required.

## Hardware Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **GPU** | NVIDIA GTX 1060 (6GB) | RTX 3080+ (10GB+) |
| **RAM** | 16GB | 32GB+ |
| **Storage** | 20GB free | 50GB+ SSD |

Software: Python 3.9+, CUDA 11.8+ (for GPU inference).

## Troubleshooting

1. **Out of memory**: Lower `vllm_gpu_memory_utilization` in config or use quantization.
2. **Model load failure**: Check that `direct_model_name` points to a valid directory; delete cache and re-download if needed.
3. **Slow inference**: Lower `max_tokens` or temperature in config.

# SmartResume - Intelligent Resume Parsing

SmartResume combines native PDF text, OCR and layout detection, then extracts structured JSON using a local model or a remote API. The default request covers all ten task families.

~~~bash
python scripts/start.py --file resume.pdf \
  --extract_types basic_info work_experience project_experience education \
  skills_strengths publication competition honor research_direction social_profile
~~~

- [CPU/GPU installation](../runtime-installation.md)
- [Docker deployment](../runtime-installation.md#docker)
- [Configuration](../configuration.md)
- [Local models](../local-models.md)
- [PDF geometry and reading order](../pdf-processing.md)
- [Benchmark results](../benchmark-results-en.md)

## Python API

~~~python
import json
from pathlib import Path
from smartresume import ResumeAnalyzer
from smartresume.utils.extraction_schema import EXTRACT_TYPES

analyzer = ResumeAnalyzer(init_ocr=True, init_llm=True)
result = analyzer.pipeline(
    cv_path="resume.pdf",
    resume_id="resume_001",
    extract_types=list(EXTRACT_TYPES),
)
if "error" in result:
    raise RuntimeError(result["error"])
Path("result.json").write_text(
    json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
)
~~~

## Web demo

~~~bash
python demo/web_app.py
~~~

Open http://localhost:4999 to upload a resume and view or download its JSON fields.

The project uses the [Apache-2.0 license](../LICENSE). See the repository README for the technical report and citation.

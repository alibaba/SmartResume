# Python API

初始化一次分析器，通过 pipeline 解析文档。模型和设备设置来自配置文件。

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

部分抽取时将 extract_types 改为相应任务名列表。批量处理时复用 analyzer，避免反复加载模型：

~~~python
for path in Path("resumes").glob("*.pdf"):
    result = analyzer.pipeline(
        cv_path=str(path),
        resume_id=path.stem,
        extract_types=list(EXTRACT_TYPES),
    )
    output = Path("results") / (path.stem + ".json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
~~~

检查顶层 error 和 extractionErrors，区分文档处理失败与部分字段抽取失败。字段内容取决于简历原文和模型输出；空条目不能视为推断得到的经历。输出字段名称见[输出格式](../reference/output_format.md)。

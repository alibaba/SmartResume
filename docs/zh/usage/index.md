# 使用指南

| 入口 | 用途 | 文档 |
| --- | --- | --- |
| scripts/start.py | 单文件解析与任务选择 | [命令行](cli.md) |
| ResumeAnalyzer.pipeline | 保存 JSON、批量复用模型 | [Python API](api.md) |
| demo/web_app.py | 上传、预览与下载 JSON | [Web 演示](../demo/index.md) |

默认抽取个人信息、工作经历、项目经历、教育经历、技能优势、论文、竞赛、荣誉、研究方向和社会主页，共十类任务、十一个业务根字段。

~~~bash
python scripts/start.py --file resume.pdf
~~~

优先使用 PDF、PNG/JPEG 或 DOCX。其他格式的处理路径和依赖不同；批量处理前应先用代表性文件确认。

[配置说明](configuration.md) · [本地模型](local_models.md) · [输出格式](../reference/output_format.md)

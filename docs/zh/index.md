# SmartResume - 智能简历解析系统

SmartResume 融合 PDF 原生文本、OCR 和版面检测，重建阅读顺序，并通过 LLM 输出结构化 JSON。支持本地模型和远程 API。

默认抽取个人信息、工作经历、项目经历、教育经历、技能优势、论文、竞赛、荣誉、研究方向和社会主页。

~~~bash
python scripts/start.py --file resume.pdf \
  --extract_types basic_info work_experience project_experience education \
  skills_strengths publication competition honor research_direction social_profile
~~~

- [环境要求](quick_start/requirements.md)
- [安装指南](quick_start/installation.md)
- [Docker 部署](quick_start/docker.md)
- [快速开始](quick_start/index.md)
- [命令行](usage/cli.md)
- [Python API](usage/api.md)
- [配置](usage/configuration.md)
- [本地模型](usage/local_models.md)
- [Web 演示](demo/index.md)
- [输出格式](reference/output_format.md)
- [基准结果](reference/benchmark.md)
- [常见问题](reference/faq.md)

项目采用 [Apache-2.0 许可](../LICENSE)。技术报告和引用信息见仓库 README。

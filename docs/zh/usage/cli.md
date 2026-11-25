# 命令行工具

从项目根目录运行。--file 为必填文件路径；--extract_types 可选择任务，不传时默认全部十类。

~~~bash
python scripts/start.py --file resume.pdf \
  --extract_types basic_info work_experience project_experience education \
  skills_strengths publication competition honor research_direction social_profile
~~~

只提取部分条目时，例如：

~~~bash
python scripts/start.py --file resume.pdf --extract_types project_experience skills_strengths
~~~

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

CLI 输出包括运行日志和最后的 JSON。直接重定向整段标准输出不能保证得到纯 JSON 文件；文件保存和批量复用分析器请使用[Python API](api.md)。当前 CLI 不提供目录批处理、输出目录或 CSV 参数。

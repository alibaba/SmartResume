# 输出格式

结果为 JSON。默认十类抽取任务对应以下十一个业务根字段：

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

教育经历支持 degreeLevel、period、school、department、major、advisorList、labName、expectedGraduationDate、gpa 和 educationDescription。描述类字段会将模型返回的文本索引还原成原文；信息缺失时保留对应的空字符串或空数组。

结果还可包含 rawText 等处理信息；发生失败时检查 error 或 extractionErrors。业务字段和错误处理应按真实返回结果读取，不要把日志文本当成 JSON。使用[Python API](../usage/api.md)可保存完整 JSON 文件。

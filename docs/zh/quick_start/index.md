# 快速开始

先完成[安装](installation.md)，根据[配置说明](../usage/configuration.md)设置本地模型或远程 API。

默认解析全部十类字段：

~~~bash
python scripts/start.py --file resume.pdf
~~~

完整显式命令：

~~~bash
python scripts/start.py --file resume.pdf \
  --extract_types basic_info work_experience project_experience education \
  skills_strengths publication competition honor research_direction social_profile
~~~

Web 服务：

~~~bash
python demo/web_app.py
~~~

访问 http://localhost:4999，上传简历并查看或下载 JSON。

[命令行](../usage/cli.md) · [Python API](../usage/api.md) · [输出格式](../reference/output_format.md)

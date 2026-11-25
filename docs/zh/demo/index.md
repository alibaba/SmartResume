# Web 演示

执行 `pip install -e .` 后即包含 Web 依赖。配置 OCR、版面和 LLM 模型后启动：

~~~bash
python demo/web_app.py
~~~

访问 http://localhost:4999。上传简历后可查看原文件、文本和结构化字段，并下载 JSON。当前界面展示个人信息、工作、项目、教育、专业技能、个人优势、论文、竞赛、荣誉、研究方向和社会主页。

建议使用 PDF、PNG/JPEG 或 DOCX，单文件上传上限为 20 MB。上传临时文件存放在项目 temp/web_uploads 中并在请求完成后清理。删除 temp 后会按需重建目录，无需保留历史测试文件。模型在服务启动时加载并复用；更改模型或设备配置后需重启服务。

该入口使用 Flask，适合本地演示。对外部署时应自行配置认证、网络访问和生产服务入口。

[安装指南](../quick_start/installation.md) · [字段格式](../reference/output_format.md) · [配置](../usage/configuration.md)

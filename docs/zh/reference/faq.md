# 常见问题

## GPU 存在但 OCR 使用 CPU

检查是否残留旧版 `rapidocr-onnxruntime` 或 CPU 版 `onnxruntime`。按[安装指南](../quick_start/installation.md)清理后执行 `pip install -e .`，并重启进程。驱动需兼容 CUDA 12.4，CUDA/cuDNN 用户态库由 PyTorch 依赖提供。设置 `SMARTRESUME_ONNX_DEVICE=cuda` 可在 OCR/版面无法初始化 CUDA 时直接报错；本地 LLM 的设备单独选择。

## 如何只解析项目或技能

~~~bash
python scripts/start.py --file resume.pdf --extract_types project_experience skills_strengths
~~~

省略 --extract_types 默认解析全部十类。

## 如何保存纯 JSON 或批量解析

使用[Python API](../usage/api.md)。CLI 的标准输出包含日志，不能直接把整段重定向结果当作 JSON。批量处理时复用同一分析器。

## PDF 字体警告是否会导致解析失败

缺失 FontBBox 的已知重复警告会在单次 PDF 处理范围内汇总，其他错误仍会保留。是否解析成功应检查返回结果和日志，不能只依据是否出现警告。复杂扫描件和多栏文档也可能影响文本顺序，见 [PDF 处理](../../pdf-processing.md)。

## 模型加载失败

检查配置路径是否存在、权重是否完整、当前运行环境是否匹配。修改配置后重启服务。不要通过删除已有权重来替代故障定位。

## 支持哪些语言

效果取决于所配置 OCR、布局模型、LLM 和文档质量；不能把单个 OCR 模型的语言覆盖视为整个系统的统一准确率保证。

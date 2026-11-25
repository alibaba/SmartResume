# 环境要求

- 推荐 Linux x86_64 和 Python 3.11；项目声明的 Python 最低版本为 3.10。
- 默认使用 NVIDIA GPU，驱动需兼容 CUDA 12.4。PyTorch 的依赖提供 CUDA/cuDNN 用户态库。
- `pip install -e .` 安装 PyTorch 2.6.0、ONNX Runtime GPU 1.20.2、RapidOCR 3.4.1，以及本地模型和 Web 依赖；`requirements.txt` 列出相同的默认依赖。
- 同一套依赖支持 CPU 运行，无需额外安装 CPU 版 `onnxruntime`。设备切换见[运行环境说明](../../runtime-installation.md#device-selection)。
- 内存、显存需求取决于模型和文档大小。远程 API 模式需要可访问的模型服务；本地模式需要完整权重。

[安装指南](installation.md) · [Docker 部署](docker.md)

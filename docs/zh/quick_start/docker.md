# Docker 部署

在项目根目录执行。宿主机需要 Linux x86_64、兼容 CUDA 12.4 的 NVIDIA 驱动，以及已为 Docker 配置的 [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html)。

Dockerfile 基于 Python 3.11，通过 `pip install -e .` 安装 GPU 推理、本地模型和 Web 依赖；CUDA/cuDNN 用户态库由 PyTorch 的依赖提供。

先准备完整的模型和 `configs/config.yaml`。配置中的模型路径应指向容器内的 `/app/models/...`；如果权重使用符号链接，其目标也必须在容器内可访问。

~~~bash
docker build -f docker/Dockerfile -t smartresume .
docker run --rm --gpus all \
  -e SMARTRESUME_ONNX_DEVICE=cuda \
  -p 4999:4999 \
  -v "$PWD/models:/app/models" \
  -v "$PWD/configs:/app/configs" \
  smartresume python demo/web_app.py
~~~

访问 `http://localhost:4999`。镜像默认命令仅显示 CLI 帮助，上述命令显式启动 Web。

使用同一镜像在 CPU 上运行时，将 `--gpus all` 和 `-e SMARTRESUME_ONNX_DEVICE=cuda` 替换为 `-e CUDA_VISIBLE_DEVICES="" -e SMARTRESUME_ONNX_DEVICE=cpu`，无需更换 ONNX Runtime 包。

[安装指南](installation.md) · [配置说明](../usage/configuration.md)

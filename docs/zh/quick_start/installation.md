# 安装指南

推荐 Linux x86_64、Python 3.11、NVIDIA GPU 和兼容 CUDA 12.4 的驱动。

~~~bash
git clone https://github.com/alibaba/SmartResume.git
cd SmartResume
conda create -n resume_parsing python=3.11 -y
conda activate resume_parsing
pip install -e .
~~~

默认安装 GPU 推理、本地模型和 Web 所需依赖，无需单独运行安装脚本。精简系统缺少 OpenCV 系统库时，参阅[运行环境说明](../../runtime-installation.md)；容器安装见[Docker 部署](docker.md)。

## 配置与模型

~~~bash
cp -n configs/config.yaml.example configs/config.yaml
python scripts/download_models.py
~~~

已有完整模型和配置时直接复用，无需重新下载。OCR 优先使用 models/rapidocr 中保留的权重；没有该目录时使用 RapidOCR 3.4.1 自带的相同权重。

## 从旧版升级

仅当环境中残留 rapidocr-onnxruntime 或 CPU 版 onnxruntime 时，先执行一次清理：

~~~bash
pip uninstall -y rapidocr-onnxruntime onnxruntime onnxruntime-gpu
pip install -e .
~~~

依赖更新后重启 Python/Web 进程。全新环境不需要清理。CPU 运行及既有 PyTorch 环境处理见[运行环境说明](../../runtime-installation.md)。

[环境要求](requirements.md) · [本地模型](../usage/local_models.md)

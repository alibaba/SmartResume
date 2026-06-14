# 快速开始

欢迎使用 SmartResume！本指南将帮助您快速上手智能简历解析系统。

## 系统要求

### 基本要求

- **Python**: >= 3.9
- **内存**: >= 8GB
- **存储**: >= 10GB
- **操作系统**: Linux, macOS, Windows

### GPU 要求（可选）

- **CUDA**: >= 11.0
- **GPU**: NVIDIA GPU，推荐 6GB+ VRAM
- **驱动**: 最新的 NVIDIA 驱动程序

## 安装方式

### 方式一：pip 安装（推荐）

```bash
# 创建虚拟环境
conda create -n smartresume python=3.9
conda activate smartresume

# 安装 SmartResume
pip install smartresume
```

### 方式二：源码安装

```bash
# 克隆仓库
git clone https://github.com/your-username/SmartResume.git
cd SmartResume

# 安装依赖
pip install -e .
```

## 快速验证

安装完成后，运行以下命令验证安装：

```bash
# 检查版本
python -c "import smartresume; print(smartresume.__version__)"

# 运行简单测试
python scripts/start.py --help
```

## 下一步

安装完成后，您可以：

1. [查看环境要求详情](requirements.md)
2. [学习基本使用方法](../usage/index.md)
3. [配置本地模型部署](../usage/local_models.md)
4. [了解 Docker 部署方式](docker.md)

## 遇到问题？

如果您在安装过程中遇到任何问题，请查看 [常见问题解答](../reference/faq.md) 或提交 Issue。

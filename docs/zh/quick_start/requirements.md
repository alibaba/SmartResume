# 环境要求

本文档详细说明了 SmartResume 系统的环境要求。

## 硬件要求

### 最低配置

| 组件 | 要求 | 说明 |
|------|------|------|
| **CPU** | 4核心 | 推荐 Intel i5 或 AMD Ryzen 5 |
| **内存** | 8GB | 处理大型文档时需要更多内存 |
| **存储** | 10GB | 用于安装和缓存 |
| **网络** | 稳定连接 | 下载模型和API调用需要 |

### 推荐配置

| 组件 | 要求 | 说明 |
|------|------|------|
| **CPU** | 8核心+ | 推荐 Intel i7 或 AMD Ryzen 7 |
| **内存** | 16GB+ | 更好的处理性能 |
| **GPU** | NVIDIA RTX 3060+ | 6GB+ VRAM，用于本地模型推理 |
| **存储** | SSD 20GB+ | 更快的模型加载速度 |

## 软件要求

### 操作系统

- **Linux**: Ubuntu 18.04+, CentOS 7+, Debian 10+
- **macOS**: 10.15+ (Catalina 及以上)
- **Windows**: Windows 10+ (支持 WSL2)

### Python 环境

- **Python**: 3.9 - 3.11
- **pip**: >= 20.0
- **conda**: >= 4.10 (推荐)

### CUDA 环境（可选）

如果需要使用 GPU 加速，需要安装：

- **CUDA**: 11.0 - 12.1
- **cuDNN**: 对应版本
- **NVIDIA 驱动**: 450.80.02+

```bash
# 检查 CUDA 版本
nvidia-smi

# 检查 cuDNN
python -c "import torch; print(torch.backends.cudnn.version())"
```

## 依赖库

SmartResume 依赖以下主要库：

### 核心依赖

- `numpy`: >= 1.23
- `pillow`: >= 9.5
- `opencv-python`: >= 4.7
- `pdfplumber`: >= 0.10.0
- `rapidocr-onnxruntime`: >= 1.3.0
- `tiktoken`: >= 0.5.1
- `openai`: >= 1.30.0

### 文档处理

- `beautifulsoup4`: >= 4.12
- `python-docx`: >= 0.8
- `lxml`: >= 4.9

### 其他工具

- `click`: >= 8.0
- `loguru`: >= 0.6
- `requests`: >= 2.25.0
- `pyyaml`: >= 6.0
- `json-repair`: >= 0.16.0

## 云服务要求

如果使用远程 API，需要：

- **OpenAI API**: 有效的 API 密钥
- **网络连接**: 稳定的互联网连接
- **配额**: 足够的 API 调用配额

## 性能优化建议

### 内存优化

```bash
# 设置环境变量限制内存使用
export OMP_NUM_THREADS=4
export MKL_NUM_THREADS=4
```

### GPU 优化

```bash
# 设置 CUDA 设备
export CUDA_VISIBLE_DEVICES=0

# 启用混合精度训练
export TORCH_CUDNN_V8_API_ENABLED=1
```

## 故障排除

### 常见问题

1. **CUDA 版本不匹配**
   ```bash
   # 重新安装对应版本的 PyTorch
   pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
   ```

2. **内存不足**
   ```bash
   # 减少批处理大小
   python scripts/start.py --batch_size 1
   ```

3. **网络连接问题**
   ```bash
   # 使用代理
   export http_proxy=http://proxy:port
   export https_proxy=http://proxy:port
   ```

## 下一步

环境配置完成后，您可以：

1. [开始安装 SmartResume](installation.md)
2. [学习基本使用方法](../usage/index.md)
3. [配置本地模型部署](../usage/local_models.md)

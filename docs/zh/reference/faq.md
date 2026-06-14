# 常见问题解答

本文档收集了 SmartResume 使用过程中的常见问题和解决方案。

## 安装和配置

### Q: 安装时出现依赖冲突怎么办？

**A:** 建议使用虚拟环境隔离依赖：

```bash
# 创建新的虚拟环境
conda create -n smartresume python=3.9
conda activate smartresume

# 重新安装
pip install -e .
```

如果仍有冲突，可以尝试：

```bash
# 强制重新安装
pip install --force-reinstall -e .

# 或使用 conda 安装主要依赖
conda install pytorch torchvision pytorch-cuda=11.8 -c pytorch -c nvidia
```

### Q: CUDA 版本不匹配怎么解决？

**A:** 检查并安装对应版本的 PyTorch：

```bash
# 检查 CUDA 版本
nvidia-smi

# 安装对应版本的 PyTorch
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
```

### Q: 如何配置 API 密钥？

**A:** 编辑配置文件 `configs/config.yaml`：

```yaml
model:
  name: "qwen-turbo"
  api_url: "https://dashscope.aliyuncs.com/compatible-mode/v1"
  api_key: "your-api-key-here"
```

或使用环境变量：

```bash
export OPENAI_API_KEY="your-api-key-here"
```

## 使用问题

### Q: 处理 PDF 文件时出现乱码怎么办？

**A:** 这通常是因为 PDF 编码问题，可以尝试：

1. **使用 OCR 模式**：
   ```bash
   python scripts/start.py --file resume.pdf --use_ocr
   ```

2. **指定语言**：
   ```bash
   python scripts/start.py --file resume.pdf --language zh
   ```

3. **预处理 PDF**：
   ```python
   # 使用 PDFplumber 预处理
   import pdfplumber
   with pdfplumber.open("resume.pdf") as pdf:
       page = pdf.pages[0]
       text = page.extract_text()
   ```

### Q: 解析结果不准确怎么办？

**A:** 可以尝试以下优化：

1. **调整置信度阈值**：
   ```yaml
   model:
     layout:
       confidence_threshold: 0.7  # 提高阈值
   ```

2. **使用更强的模型**：
   ```yaml
   model:
     llm:
       model_name: "gpt-4"  # 使用 GPT-4
   ```

3. **优化输入文档质量**：
   - 确保文档清晰度
   - 避免复杂排版
   - 使用标准格式

### Q: 批量处理时内存不足怎么办？

**A:** 优化内存使用：

1. **减少批处理大小**：
   ```bash
   python scripts/start.py --input_dir ./resumes --batch_size 1
   ```

2. **使用流式处理**：
   ```python
   # 逐个处理文件
   for file in files:
       result = analyzer.pipeline(cv_path=file)
       # 立即保存结果，释放内存
   ```

3. **设置内存限制**：
   ```bash
   export OMP_NUM_THREADS=2
   export MKL_NUM_THREADS=2
   ```

## 性能问题

### Q: 处理速度很慢怎么办？

**A:** 可以尝试以下优化：

1. **使用 GPU 加速**：
   ```bash
   # 确保 CUDA 可用
   python -c "import torch; print(torch.cuda.is_available())"
   ```

2. **使用本地模型**：
   - 在 `configs/config.yaml` 中设置 `use_direct_models: true` 和 `direct_model_name`，进程内加载 vLLM，无需单独部署服务。

3. **并行处理**：
   ```bash
   python scripts/start.py --input_dir ./resumes --num_workers 4
   ```

### Q: GPU 利用率不高怎么办？

**A:** 优化 GPU 使用：

1. **检查 CUDA 设置**：
   ```python
   import torch
   print(f"CUDA available: {torch.cuda.is_available()}")
   print(f"CUDA devices: {torch.cuda.device_count()}")
   print(f"Current device: {torch.cuda.current_device()}")
   ```

2. **设置 CUDA 设备**：
   ```bash
   export CUDA_VISIBLE_DEVICES=0
   ```

3. **调整批处理大小**：
   ```bash
   python scripts/start.py --batch_size 8  # 增加批处理大小
   ```

## 模型相关

### Q: 如何下载和更新模型？

**A:** 使用提供的脚本：

```bash
# 下载所有模型
python scripts/download_models.py

# 下载特定模型
python scripts/download_models.py --model layout

# 强制重新下载
python scripts/download_models.py --force
```

### Q: 本地模型部署失败怎么办？

**A:** 检查以下项目：

1. **检查 GPU 内存**：
   ```bash
   nvidia-smi
   ```

2. **检查模型文件**：
   ```bash
   ls -la models/
   ```

3. **检查端口占用**：
   ```bash
   netstat -tlnp | grep 8000
   ```

4. **查看日志**：
   ```bash
   # 检查程序输出的错误信息
   python scripts/start.py --file resume.pdf 2>&1 | tail -20
   ```

## 输出问题

### Q: 输出格式不符合预期怎么办？

**A:** 检查输出配置：

1. **指定输出格式**：
   ```bash
   python scripts/start.py --file resume.pdf --output_format json
   ```

2. **自定义输出字段**：
   ```bash
   python scripts/start.py --file resume.pdf --extract_types basic_info work_experience
   ```

3. **检查配置文件**：
   ```yaml
   processing:
     output:
       format: "json"
       include_images: false
       save_intermediate: true
   ```

### Q: 如何自定义输出格式？

**A:** 使用 Python API 自定义：

```python
from smartresume import ResumeAnalyzer

analyzer = ResumeAnalyzer()

# 自定义提取类型
custom_types = ["basic_info", "work_experience", "education"]

result = analyzer.pipeline(
    cv_path="resume.pdf",
    extract_types=custom_types,
)

# 自定义输出格式
output = {
    "candidate_name": result.get("basicInfo", {}).get("name", ""),
    "experience": result.get("workExperience", []),
    "education": result.get("education", [])
}
```

## 错误排查

### Q: 如何查看详细错误信息？

**A:** 启用调试模式：

```bash
# 命令行调试
python scripts/start.py --file resume.pdf --debug

# 环境变量调试
export SMARTRESUME_DEBUG=1
python scripts/start.py --file resume.pdf
```

### Q: 常见错误代码含义？

**A:** 常见错误代码：

| 错误代码 | 含义 | 解决方案 |
|----------|------|----------|
| `CUDA_ERROR` | CUDA 相关错误 | 检查 GPU 驱动和 CUDA 版本 |
| `MODEL_LOAD_ERROR` | 模型加载失败 | 检查模型文件完整性 |
| `API_KEY_ERROR` | API 密钥错误 | 检查配置文件中的密钥 |
| `FILE_FORMAT_ERROR` | 文件格式不支持 | 转换文件格式或使用支持的格式 |

## 联系支持

如果以上解决方案无法解决您的问题，请：

1. **查看 GitHub Issues**：搜索相关问题
2. **提交新 Issue**：提供详细的错误信息和环境配置
3. **联系维护团队**：通过邮件或 Discord 联系

---

**提示**：在提交问题时，请提供以下信息：
- 操作系统和版本
- Python 版本
- 错误日志
- 复现步骤
- 配置文件内容（隐藏敏感信息）

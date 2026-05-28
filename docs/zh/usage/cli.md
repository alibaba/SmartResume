# 命令行工具

SmartResume 提供了强大的命令行工具，支持批量处理和自动化任务。

## 基本用法

### 解析单个文件

```bash
# 基本用法
python scripts/start.py --file resume.pdf

# 指定输出目录
python scripts/start.py --file resume.pdf --output_dir ./results

# 指定提取类型
python scripts/start.py --file resume.pdf --extract_types basic_info work_experience
```

### 批量处理

```bash
# 处理整个目录
python scripts/start.py --input_dir ./resumes --output_dir ./results

# 指定文件类型
python scripts/start.py --input_dir ./resumes --file_types pdf,jpg,png

# 使用多进程加速
python scripts/start.py --input_dir ./resumes --num_workers 4
```

## 命令行参数

### 输入选项

| 参数 | 说明 | 示例 |
|------|------|------|
| `--file` | 单个文件路径 | `--file resume.pdf` |
| `--input_dir` | 输入目录 | `--input_dir ./resumes` |
| `--file_types` | 文件类型过滤 | `--file_types pdf,jpg` |

### 输出选项

| 参数 | 说明 | 示例 |
|------|------|------|
| `--output_dir` | 输出目录 | `--output_dir ./results` |
| `--output_format` | 输出格式 | `--output_format json` |
| `--save_images` | 保存处理图片 | `--save_images` |

### 处理选项

| 参数 | 说明 | 示例 |
|------|------|------|
| `--extract_types` | 提取字段类型 | `--extract_types basic_info,work_experience` |
| `--language` | 文档语言 | `--language zh` |
| `--use_ocr` | 强制使用OCR | `--use_ocr` |

### 性能选项

| 参数 | 说明 | 示例 |
|------|------|------|
| `--num_workers` | 并行进程数 | `--num_workers 4` |
| `--batch_size` | 批处理大小 | `--batch_size 8` |
| `--max_memory` | 最大内存使用 | `--max_memory 8GB` |

## 使用示例

### 示例1：处理PDF简历

```bash
python scripts/start.py \
  --file resume.pdf \
  --output_dir ./output \
  --extract_types basic_info work_experience education \
  --output_format json
```

### 示例2：批量处理图片简历

```bash
python scripts/start.py \
  --input_dir ./image_resumes \
  --output_dir ./results \
  --file_types jpg,png \
  --use_ocr \
  --language zh \
  --num_workers 4
```

### 示例3：自定义配置

```bash
python scripts/start.py \
  --input_dir ./resumes \
  --config configs/custom_config.yaml \
  --output_format xml \
  --save_images \
  --verbose
```

## 配置文件

可以通过配置文件自定义默认行为：

```yaml
# config.yaml
processing:
  default_extract_types:
    - basic_info
    - work_experience
    - education
  
  output:
    format: json
    save_images: false
  
  performance:
    num_workers: 4
    batch_size: 8
```

使用配置文件：

```bash
python scripts/start.py --config config.yaml --file resume.pdf
```

## 错误处理

### 常见错误

1. **文件格式不支持**
   ```bash
   ERROR: Unsupported file format: .pptx
   SOLUTION: 使用支持的文件格式（PDF、图片、Word、TXT）
   ```

2. **内存不足**
   ```bash
   ERROR: Out of memory
   SOLUTION: 减少 --batch_size 或 --num_workers
   ```

3. **API密钥错误**
   ```bash
   ERROR: Invalid API key
   SOLUTION: 检查配置文件中的API密钥
   ```

## 性能优化

### 批量处理优化

```bash
# 使用SSD存储
python scripts/start.py --input_dir /ssd/resumes --output_dir /ssd/results

# 调整并行度
python scripts/start.py --num_workers $(nproc) --batch_size 16

# 使用GPU加速
python scripts/start.py --use_gpu --batch_size 32
```

### 内存优化

```bash
# 限制内存使用
python scripts/start.py --max_memory 4GB --batch_size 1

# 流式处理大文件
python scripts/start.py --stream_processing --chunk_size 1024
```

## 下一步

- [学习 Python API 使用方法](api.md)
- [了解配置选项详情](configuration.md)
- [查看本地模型部署指南](local_models.md)


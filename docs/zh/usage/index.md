# 使用指南

SmartResume 提供了多种使用方式，包括命令行工具、Python API 和 Web 界面。

## 使用方式概览

| 方式 | 适用场景 | 优势 | 文档链接 |
|------|----------|------|----------|
| **命令行工具** | 批量处理、脚本集成 | 简单高效、易于自动化 | [CLI 工具](cli.md) |
| **Python API** | 应用集成、自定义开发 | 灵活强大、可定制 | [Python API](api.md) |
| **Web 界面** | 交互式使用、演示 | 用户友好、可视化 | [在线演示](../demo/index.md) |

## 快速开始

### 1. 命令行使用

```bash
# 基本用法
python scripts/start.py --file resume.pdf

# 指定输出目录
python scripts/start.py --file resume.pdf --output_dir ./results

# 批量处理
python scripts/start.py --input_dir ./resumes --output_dir ./results
```

### 2. Python API 使用

```python
from smartresume import ResumeAnalyzer

# 初始化分析器
analyzer = ResumeAnalyzer(
    init_ocr=True,
    init_llm=True,
)

# 解析单个简历
result = analyzer.pipeline(
    cv_path="resume.pdf",
    resume_id="resume_001",
    extract_types=["basic_info", "work_experience", "education"]
)

print(f"解析结果: {result}")
```

### 3. Web 界面使用

启动 Web 服务：

```bash
# 启动 Gradio 界面
python -m smartresume.cli.gradio_app

# 或使用 Streamlit
streamlit run demo/streamlit_app.py
```

然后在浏览器中访问 `http://localhost:7860`。

## 配置说明

详细的配置选项请参考 [配置说明](configuration.md)。

### 环境变量

```bash
# 指定配置文件路径
export SMARTRESUME_CONFIG="configs/config.yaml"
```

## 支持的文件格式

| 格式 | 扩展名 | 支持程度 | 说明 |
|------|--------|----------|------|
| **PDF** | .pdf | ✅ 完全支持 | 推荐格式，支持多页 |
| **图片** | .jpg, .png, .bmp | ✅ 完全支持 | 单页文档 |
| **Word** | .docx, .doc | ✅ 支持 | 需要转换处理 |
| **文本** | .txt | ⚠️ 有限支持 | 纯文本格式 |

## 提取字段类型

SmartResume 支持提取以下字段类型：

### 基本信息
- 姓名、性别、年龄
- 联系方式（电话、邮箱）
- 地址信息
- 头像照片

### 教育经历
- 学校名称、专业
- 学历层次、毕业时间
- 主要课程、成绩

### 工作经历
- 公司名称、职位
- 工作时间、工作内容

## 输出格式

### JSON 格式

```json
{
  "resume_id": "resume_001",
  "basic_info": {
    "name": "张三",
    "phone": "13800138000",
    "email": "zhangsan@example.com"
  },
  "work_experience": [
    {
      "company": "ABC公司",
      "position": "软件工程师",
      "duration": "2020-2023"
    }
  ],
  "education": [
    {
      "school": "某某大学",
      "major": "计算机科学",
      "degree": "本科"
    }
  ]
}
```

### CSV 格式

```csv
resume_id,name,phone,email,company,position
resume_001,张三,13800138000,zhangsan@example.com,ABC公司,软件工程师
```

## 性能优化

### 批量处理优化

```bash
# 使用多进程处理
python scripts/start.py --input_dir ./resumes --num_workers 4

# 设置批处理大小
python scripts/start.py --batch_size 8
```

### 内存优化

```python
# 配置内存使用
analyzer = ResumeAnalyzer(
    init_ocr=True,
    init_llm=True,
    max_memory_usage="8GB"  # 限制内存使用
)
```

## 常见问题

### Q: 处理速度慢怎么办？
A: 可以尝试以下优化：
- 使用 GPU 加速
- 减少批处理大小
- 使用本地模型部署

### Q: 如何提高解析准确率？
A: 建议：
- 使用高质量的输入文档
- 调整置信度阈值
- 使用更强大的 LLM 模型

### Q: 支持哪些语言？
A: SmartResume 支持 119 种语言，包括中文、英文、日文等。

## 下一步

- [学习命令行工具详细用法](cli.md)
- [了解 Python API 开发](api.md)
- [配置本地模型部署](local_models.md)
- [查看配置选项说明](configuration.md)

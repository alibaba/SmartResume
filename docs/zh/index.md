# SmartResume - 智能简历解析系统

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Paper](https://img.shields.io/badge/Paper-KDD%202026-red.svg)]()

## 项目介绍

SmartResume 是一个面向版面结构的智能简历解析系统，基于 SmartResume 流水线构建。系统支持 PDF、图片及常见 Office 文档格式，融合 OCR 与 PDF 元数据完成文本提取，结合版面检测重建阅读顺序，并通过 LLM 将内容转换为结构化字段（如：基本信息、教育经历、工作经历等）。系统同时支持远程 API 和本地模型部署，提供灵活的使用方式。

## 核心特色

| 指标类别 | 具体指标 | 数值 | 说明 |
|---------|---------|------|------|
| **布局检测** | mAP@0.5 | **92.1%** | 高布局检测精度 |
| **信息抽取** | 整体准确率 | **93.1%** | 高准确率 |
| **处理速度** | 单页处理时间 | **1.22s** | 高性能 |
| **多语言支持** | 支持语言数 | **119种** | 覆盖全球主要语言 |

## 快速开始

### 环境要求

- Python >= 3.9
- CUDA >= 11.0 (可选，用于GPU加速)
- 内存 >= 8GB
- 存储 >= 10GB

### 安装步骤

1. **克隆项目**
```bash
git clone https://github.com/your-username/SmartResume.git
cd SmartResume
```

2. **创建conda环境**
```bash
conda create -n resume_parsing python=3.9
conda activate resume_parsing
```

3. **安装依赖**
```bash
pip install -e .
```

4. **配置环境**
```bash
# 复制配置文件模板
cp configs/config.yaml.example configs/config.yaml
# 编辑配置文件，添加API密钥
vim configs/config.yaml
```

## 基本使用

### 方法1: 使用命令行界面（推荐）

```bash
# 解析单个简历文件
python scripts/start.py --file resume.pdf

# 指定提取类型
python scripts/start.py --file resume.pdf --extract_types basic_info work_experience education
```

### 方法2: 使用Python API

```python
from smartresume import ResumeAnalyzer

# 初始化分析器
analyzer = ResumeAnalyzer(init_ocr=True, init_llm=True)

# 解析简历
result = analyzer.pipeline(
    cv_path="resume.pdf",
    resume_id="resume_001",
    extract_types=["basic_info", "work_experience", "education"]
)

print(result)
```

## 许可证信息

本项目采用 [LICENSE](LICENSE)。

## 致谢

- [PDFplumber](https://github.com/jsvine/pdfplumber)
- [RapidOCR](https://github.com/RapidAI/RapidOCR)

## 引用

```bibtex
@article{Zhu2026SmartResume,
  title={Layout-Aware Parsing Meets Efficient LLMs: A Unified, Scalable
Framework for Resume Information Extraction and Evaluation},
  author={Fanwei Zhu and Jinke Yu and Zulong Chen and Ying Zhou and Junhao Ji and Zhibo Yang and Yuxue Zhang and HaoYuan Hu and Zhenghao Liu},
  journal={KDD2026},
  year={2026}
}
```

---

**注意**: 本项目仅供学术研究使用。请确保遵守相关法律法规和隐私政策。

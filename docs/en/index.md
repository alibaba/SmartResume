# SmartResume - Intelligent Resume Parsing System

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Paper](https://img.shields.io/badge/Paper-KDD%202026-red.svg)]()

<p align="right"><a href="../zh/index.md">中文</a> | <b>English</b></p>

## Introduction

SmartResume is an intelligent resume parsing system focused on layout structure, built on the SmartResume pipeline. The system supports PDF, image, and common Office document formats, combines OCR with PDF metadata for text extraction, reconstructs reading order through layout detection, and converts content into structured fields (such as: basic information, work experience, education, etc.) through LLM. The system supports both remote API and local model deployment, providing flexible usage methods.

## Key Features

| Metric Category | Specific Metric | Value | Description |
|----------------|-----------------|-------|-------------|
| **Layout Detection** | mAP@0.5 | **92.1%** | High layout detection accuracy |
| **Information Extraction** | Overall Accuracy | **93.1%** | High accuracy |
| **Processing Speed** | Single Page Processing | **1.22s** | High performance |
| **Multi-language Support** | Supported Languages | **119 languages** | Global language coverage |

## Quick Start

### Requirements

- Python >= 3.9
- CUDA >= 11.0 (optional, for GPU acceleration)
- Memory >= 8GB
- Storage >= 10GB

### Installation Steps

1. **Clone the project**
```bash
git clone https://github.com/your-username/SmartResume.git
cd SmartResume
```

2. **Create conda environment**
```bash
conda create -n resume_parsing python=3.9
conda activate resume_parsing
```

3. **Install dependencies**
```bash
pip install -e .
```

4. **Configure environment**
```bash
# Copy configuration template
cp configs/config.yaml.example configs/config.yaml
# Edit configuration file, add API keys
vim configs/config.yaml
```

## Basic Usage

### Method 1: Command Line Interface (Recommended)

```bash
# Parse a single resume file
python scripts/start.py --file resume.pdf

# Specify extraction types
python scripts/start.py --file resume.pdf --extract_types basic_info work_experience education
```

### Method 2: Python API

```python
from smartresume import ResumeAnalyzer

# Initialize analyzer
analyzer = ResumeAnalyzer(init_ocr=True, init_llm=True)

# Parse resume
result = analyzer.pipeline(
    cv_path="resume.pdf",
    resume_id="resume_001",
    extract_types=["basic_info", "work_experience", "education"]
)

print(result)
```

## License Information

This project is licensed under [LICENSE](LICENSE).

## Acknowledgments

- [PDFplumber](https://github.com/jsvine/pdfplumber)
- [RapidOCR](https://github.com/RapidAI/RapidOCR)

## Citation

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

**Note**: This project is for academic research use only. Please ensure compliance with relevant laws and regulations and privacy policies.


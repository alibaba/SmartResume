# Python API

SmartResume 提供了完整的 Python API，支持灵活的集成和自定义开发。

## 快速开始

### 基本使用

```python
from smartresume import ResumeAnalyzer

# 初始化分析器
analyzer = ResumeAnalyzer(
    init_ocr=True,
    init_llm=True,
)

# 解析简历
result = analyzer.pipeline(
    cv_path="resume.pdf",
    resume_id="resume_001",
    extract_types=["basic_info", "work_experience", "education"]
)

print(f"解析结果: {result}")
```

### 批量处理

```python
import os
from pathlib import Path

# 处理目录中的所有文件
input_dir = Path("./resumes")
output_dir = Path("./results")

for file_path in input_dir.glob("*.pdf"):
    try:
        result = analyzer.pipeline(
            cv_path=str(file_path),
            resume_id=file_path.stem,
            extract_types=["basic_info", "work_experience", "education"]
        )
        
        # 保存结果
        output_file = output_dir / f"{file_path.stem}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
            
    except Exception as e:
        print(f"处理文件 {file_path} 时出错: {e}")
```

## 核心类和方法

### ResumeAnalyzer 类

```python
class ResumeAnalyzer:
    def __init__(
        self,
        init_ocr: bool = True,
        init_llm: bool = True,
        config_path: str = None,
        **kwargs
    ):
        """
        初始化简历分析器
        
        Args:
            init_ocr: 是否初始化OCR功能
            init_llm: 是否初始化LLM模型
            config_path: 配置文件路径
            **kwargs: 其他配置参数
        """
        pass
    
    def pipeline(
        self,
        cv_path: str,
        resume_id: str = None,
        extract_types: List[str] = None,
        **kwargs
    ) -> Dict:
        """
        执行完整的简历解析流程
        
        Args:
            cv_path: 简历文件路径
            resume_id: 简历ID（可选）
            extract_types: 要提取的字段类型列表
            **kwargs: 其他参数
            
        Returns:
            解析结果字典
        """
        pass
```

### 配置选项

配置通过 `configs/config.yaml` 文件管理，详细选项请参考 [配置说明](configuration.md)。

## 高级用法

### 自定义提取器

```python
from smartresume.extractors import BaseExtractor

class CustomExtractor(BaseExtractor):
    def extract(self, text: str, layout_info: dict) -> dict:
        """自定义提取逻辑"""
        # 实现您的提取逻辑
        return {
            "custom_field": "extracted_value"
        }

# 注册自定义提取器
analyzer.register_extractor("custom_field", CustomExtractor())

# 使用自定义提取器
result = analyzer.pipeline(
    cv_path="resume.pdf",
    extract_types=["basic_info", "custom_field"]
)
```

### 异步处理

```python
import asyncio
from smartresume import AsyncResumeAnalyzer

async def process_resumes_async(file_paths):
    analyzer = AsyncResumeAnalyzer()
    
    tasks = []
    for file_path in file_paths:
        task = analyzer.pipeline(
            cv_path=file_path,
            extract_types=["basic_info", "work_experience"]
        )
        tasks.append(task)
    
    results = await asyncio.gather(*tasks)
    return results

# 使用异步处理
file_paths = ["resume1.pdf", "resume2.pdf", "resume3.pdf"]
results = asyncio.run(process_resumes_async(file_paths))
```

### 流式处理

```python
def stream_process_large_directory(input_dir, batch_size=10):
    """流式处理大量文件"""
    analyzer = ResumeAnalyzer()
    
    for batch in get_file_batches(input_dir, batch_size):
        results = []
        for file_path in batch:
            try:
                result = analyzer.pipeline(cv_path=file_path)
                results.append(result)
            except Exception as e:
                print(f"处理失败: {file_path}, 错误: {e}")
        
        # 批量保存结果
        save_batch_results(results, batch)
        
        # 清理内存
        del results
        gc.collect()
```

## 错误处理

### 异常处理

```python
from smartresume.exceptions import (
    FileFormatError,
    ModelLoadError,
    APIError,
    ProcessingError
)

try:
    result = analyzer.pipeline(cv_path="resume.pdf")
except FileFormatError as e:
    print(f"文件格式错误: {e}")
except ModelLoadError as e:
    print(f"模型加载失败: {e}")
except APIError as e:
    print(f"API调用失败: {e}")
except ProcessingError as e:
    print(f"处理过程出错: {e}")
except Exception as e:
    print(f"未知错误: {e}")
```

### 重试机制

```python
import time
from functools import wraps

def retry_on_failure(max_retries=3, delay=1):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise e
                    print(f"尝试 {attempt + 1} 失败，{delay}秒后重试...")
                    time.sleep(delay)
            return None
        return wrapper
    return decorator

@retry_on_failure(max_retries=3, delay=2)
def robust_pipeline(analyzer, cv_path):
    return analyzer.pipeline(cv_path=cv_path)
```

## 性能优化

### 模型预热

```python
# 预热模型以提高首次处理速度
analyzer = ResumeAnalyzer()
analyzer.warmup_models()

# 现在处理速度会更快
result = analyzer.pipeline(cv_path="resume.pdf")
```

### 内存管理

```python
import gc

class MemoryEfficientAnalyzer:
    def __init__(self):
        self.analyzer = ResumeAnalyzer()
    
    def process_with_cleanup(self, cv_path):
        try:
            result = self.analyzer.pipeline(cv_path=cv_path)
            return result
        finally:
            # 清理中间结果
            gc.collect()
```

## 集成示例

### Flask Web 应用

```python
from flask import Flask, request, jsonify
from smartresume import ResumeAnalyzer

app = Flask(__name__)
analyzer = ResumeAnalyzer()

@app.route('/parse', methods=['POST'])
def parse_resume():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    extract_types = request.form.getlist('extract_types') or ['basic_info']
    
    try:
        result = analyzer.pipeline(
            cv_path=file.filename,
            extract_types=extract_types
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
```

## 下一步

- [学习命令行工具使用方法](cli.md)
- [了解配置选项详情](configuration.md)
- [查看本地模型部署指南](local_models.md)


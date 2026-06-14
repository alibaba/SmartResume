#!/usr/bin/env python3
"""
SmartResume - 模型下载脚本

使用方法:
   python scripts/download_models.py                    # 下载所有模型到models目录
   python scripts/download_models.py --model_type llm   # 下载LLM模型到models目录
   python scripts/download_models.py --source modelscope  # 从ModelScope下载到models目录
   python scripts/download_models.py --save_path /path/to/models  # 指定自定义保存路径
"""
import os
import sys
import argparse

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from smartresume.utils.models_download_utils import download_model
    from smartresume.utils.model_paths import ModelType, ModelSource
except ImportError as e:
    print(f"Import failed: {e}")
    print("Please run this script from the project root directory")
    sys.exit(1)


def download_models(model_type: str = "all", source: str = "modelscope", save_path: str = None):
    """Download models"""
    print(f"Starting to download {model_type} model from {source}")
    if save_path:
        print(f"Models will be saved to: {save_path}")

    try:
        model_source_enum = ModelSource(source)
        model_type_enum = ModelType(model_type)
    except ValueError as e:
        print(f"Parameter error: {e}")
        return False

    try:
        if model_type_enum == ModelType.ALL:
            # Download all models
            print("Downloading LLM model...")
            llm_path = download_model(ModelType.LLM, model_source_enum, save_path)
            print(f"LLM model downloaded successfully: {llm_path}")

            print("Downloading Layout model...")
            layout_path = download_model(ModelType.LAYOUT, model_source_enum, save_path)
            print(f"Layout model downloaded successfully: {layout_path}")

            print("All models downloaded successfully!")
            return True
        else:
            # Download specified model
            print(f"Downloading {model_type} model...")
            model_path = download_model(model_type_enum, model_source_enum, save_path)
            print(f"{model_type} model downloaded successfully: {model_path}")
            return True

    except Exception as e:
        print(f"Error occurred while downloading models: {str(e)}")
        return False


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description='SmartResume Model Download Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Usage examples:
  python scripts/download_models.py                    # Download all models to models directory
  python scripts/download_models.py --model_type llm   # Download LLM model to models directory
  python scripts/download_models.py --source modelscope  # Download from ModelScope
  python scripts/download_models.py --save_path /path/to/models  # Custom save path
        """
    )

    parser.add_argument(
        '--model_type',
        choices=['llm', 'layout', 'all'],
        default='all',
        help='Model type to download (default: all)'
    )

    parser.add_argument(
        '--source',
        choices=['modelscope', 'huggingface'],
        default='modelscope',
        help='Model download source (default: modelscope)'
    )

    parser.add_argument(
        '--save_path',
        type=str,
        default='models',
        help='Custom path to save downloaded models (default: models)'
    )

    args = parser.parse_args()

    # Download models
    success = download_models(args.model_type, args.source, args.save_path)

    if success:
        print("\nNow you can use the following command to analyze resumes:")
        print("python scripts/start.py --file your_resume.pdf")
        return 0
    else:
        print("\nModel download failed!")
        return 1


if __name__ == '__main__':
    exit(main())

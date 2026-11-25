import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, Any


sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from smartresume import ResumeAnalyzer
    from smartresume.utils.extraction_schema import EXTRACT_TYPES
except ImportError as e:
    print(f"Import failed: {e}")
    print("Please run this script from the project root directory")
    sys.exit(1)


def parse_single_resume(file_path: str, **kwargs) -> Dict[str, Any]:

    print(f"Parsing resume: {file_path}")

    if not os.path.exists(file_path):
        print(f"File does not exist: {file_path}")
        return {"error": "File does not exist"}

    file_path_obj = Path(file_path)
    resume_id = file_path_obj.stem

    try:
        analyzer = ResumeAnalyzer(init_ocr=True, init_llm=True)
        result = analyzer.pipeline(
            cv_path=file_path,
            resume_id=resume_id,
            extract_types=kwargs.get("extract_types", list(EXTRACT_TYPES)),
        )

        if result is None:
            print("Warning: Pipeline returned None")
            return {"error": "Pipeline returned None", "resume_id": resume_id}
        return result

    except Exception as e:
        print(f"Parsing failed: {e}")
        return {"error": str(e)}


def main():
    parser = argparse.ArgumentParser(description="SmartResume")
    parser.add_argument(
        "--file", type=str, required=True, help="Resume file path to parse"
    )
    parser.add_argument(
        "--extract_types",
        nargs="+",
        default=list(EXTRACT_TYPES),
        choices=EXTRACT_TYPES,
        help="Extraction types (default: all 10 task families)",
    )

    args = parser.parse_args()

    result = parse_single_resume(
        file_path=args.file, extract_types=args.extract_types
    )

    print("\n" + "=" * 60)
    print(json.dumps(result, ensure_ascii=False, indent=2))

    return 0 if result and "error" not in result else 1


if __name__ == "__main__":
    exit(main())

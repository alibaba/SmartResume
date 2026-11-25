# SmartResume

Layout-aware resume parsing with structured JSON output.

- [中文文档](zh/index.md)
- [English documentation](en/index.md)
- [CPU/GPU installation](runtime-installation.md)
- [Configuration](configuration.md)
- [Local models](local-models.md)
- [PDF processing](pdf-processing.md)

## Implementation modules

| Module | Responsibility |
| --- | --- |
| smartresume/utils/extraction_schema.py | Share task names, JSON roots and missing-field defaults across CLI, Web and parsing |
| smartresume/utils/onnx_runtime.py | Select providers and initialize CUDA libraries for OCR/layout |
| smartresume/data/file_processor.py | Process resume files and aggregate repeated PDF font warnings |

Runtime weights belong in models; experimental outputs, historical scripts and verification records belong in temp. They are not part of the published user guide.

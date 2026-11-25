import os
import yaml
from dataclasses import dataclass
from typing import Optional


@dataclass
class ModelConfig:

    name: str = ""
    api_url: str = ""
    api_key: str = ""
    max_tokens: int = 0
    temperature: float = 0.0
    top_p: float = 1.0
    seed: int = 0
    model_source: str = "modelscope"
    local_model_path: str = ""

    def validate(self) -> list[str]:

        errors = []
        if not self.name:
            errors.append("Model name cannot be empty")
        if not self.api_url:
            errors.append("API URL cannot be empty")

        if not self.api_key and not (
            hasattr(self, "use_direct_models") and self.use_direct_models
        ):
            errors.append("API Key cannot be empty")
        if self.max_tokens <= 0:
            errors.append("max_tokens must be greater than 0")
        if not 0 <= self.temperature <= 2:
            errors.append("temperature must be between 0 and 2")
        if not 0 <= self.top_p <= 1:
            errors.append("top_p must be between 0 and 1")
        return errors


@dataclass
class ProcessingConfig:

    use_force_ocr: bool = False
    use_force_json: bool = False
    use_pdf_raw_text: bool = False

    remove_position_and_company_line: bool = False
    page_limit: int = 10

    def validate(self) -> list[str]:

        errors = []
        if self.page_limit <= 0:
            errors.append("page_limit must be greater than 0")
        return errors


@dataclass
class OCRConfig:

    enabled: bool = True
    ocr_provider: str = "default"
    device: Optional[str] = None
    use_cuda: Optional[bool] = None
    confidence_threshold: float = 0.5

    def validate(self) -> list[str]:
        errors = []
        if self.device is not None and (
            not isinstance(self.device, str)
            or self.device.strip().lower() not in {"auto", "cpu", "cuda"}
        ):
            errors.append("ocr.device must be auto, cpu, or cuda")
        if self.use_cuda is not None and not isinstance(self.use_cuda, bool):
            errors.append("legacy ocr.use_cuda must be a boolean")
        if not 0 <= self.confidence_threshold <= 1:
            errors.append("confidence_threshold must be between 0 and 1")
        return errors


@dataclass
class LayoutDetectionConfig:

    enabled: bool = False
    protect_sparse_columns: bool = False

    def validate(self) -> list[str]:

        errors = []
        if not isinstance(self.protect_sparse_columns, bool):
            errors.append(
                "layout_detection.protect_sparse_columns must be a boolean"
            )
        return errors


class Config:

    def __init__(self):
        self.model = ModelConfig()
        self.processing = ProcessingConfig()
        self.ocr = OCRConfig()

        self.layout_detection = LayoutDetectionConfig()
        self.channels = {}
        self.extract_channels = None
        self.extract_channels_main = None
        self.extract_channels_backup = None

        self.model_download = {
            "source": "modelscope",
            "models_dir": {"llm": "", "layout": ""},
            "auto_download": True,
        }

    def validate(self) -> list[str]:

        errors = []

        if not (hasattr(self, "use_direct_models") and self.use_direct_models):
            errors.extend(self.model.validate())
        else:

            if not self.model.name:
                errors.append("Model name cannot be empty")
            if self.model.max_tokens <= 0:
                errors.append("max_tokens must be greater than 0")
            if not 0 <= self.model.temperature <= 2:
                errors.append("temperature must be between 0 and 2")
            if not 0 <= self.model.top_p <= 1:
                errors.append("top_p must be between 0 and 1")

        errors.extend(self.processing.validate())
        errors.extend(self.ocr.validate())
        errors.extend(self.layout_detection.validate())

        if hasattr(self, "channels") and self.channels:
            for channel_name, channel_config in self.channels.items():
                if (
                    not hasattr(channel_config, "name")
                    or not channel_config.name
                ):
                    errors.append(f"Channel {channel_name} is missing 'name'")
                if (
                    not hasattr(channel_config, "api_url")
                    or not channel_config.api_url
                ):
                    errors.append(
                        f"Channel {channel_name} is missing 'api_url'"
                    )

                if (
                    not hasattr(channel_config, "api_key")
                    or not channel_config.api_key
                ):
                    if not (
                        channel_name.startswith("local_")
                        or "local" in channel_name.lower()
                    ):
                        errors.append(
                            f"Channel {channel_name} is missing 'api_key'"
                        )
                if (
                    not hasattr(channel_config, "max_tokens")
                    or channel_config.max_tokens <= 0
                ):
                    errors.append(
                        f"Channel {channel_name} has invalid 'max_tokens'"
                    )

        if hasattr(self, "extract_channels") and self.extract_channels:
            for (
                extract_type,
                channel_name,
            ) in self.extract_channels.__dict__.items():
                if channel_name and channel_name not in getattr(
                    self, "channels", {}
                ):
                    errors.append(
                        f"Extract type {extract_type} references "
                        f"non-existent channel {channel_name}"
                    )

        return errors

    @classmethod
    def from_yaml(cls, config_path: str = "config.yaml") -> "Config":

        config = cls()

        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    yaml_config = yaml.safe_load(f)

                if "model" in yaml_config:
                    model_config = yaml_config["model"]
                    required_fields = [
                        "name",
                        "api_url",
                        "api_key",
                        "max_tokens",
                        "temperature",
                        "top_p",
                        "seed",
                    ]
                    missing_fields = []

                    for field_name in required_fields:
                        if field_name not in model_config:
                            missing_fields.append(field_name)
                        else:
                            setattr(
                                config.model,
                                field_name,
                                model_config[field_name],
                            )

                    if missing_fields:
                        raise ValueError(
                            "Model config missing required fields: "
                            f"{', '.join(missing_fields)}"
                        )
                else:
                    raise ValueError(
                        "Configuration file missing required 'model' section"
                    )

                if "channels" in yaml_config:
                    channels_config = yaml_config["channels"]
                    for channel_name, channel_data in channels_config.items():
                        channel_obj = type("Channel", (), {})()
                        for field, value in channel_data.items():
                            setattr(channel_obj, field, value)
                        config.channels[channel_name] = channel_obj

                if "extract_channels" in yaml_config:
                    extract_channels_config = yaml_config["extract_channels"]
                    extract_channels_obj = type("ExtractChannels", (), {})()

                    for (
                        extract_type,
                        channel_name,
                    ) in extract_channels_config.items():
                        setattr(
                            extract_channels_obj, extract_type, channel_name
                        )

                    config.extract_channels = extract_channels_obj

                if "extract_channels_main" in yaml_config:
                    extract_channels_main_config = yaml_config[
                        "extract_channels_main"
                    ]
                    extract_channels_main_obj = type(
                        "ExtractChannelsMain", {}, {}
                    )()

                    for (
                        extract_type,
                        channel_name,
                    ) in extract_channels_main_config.items():
                        setattr(
                            extract_channels_main_obj,
                            extract_type,
                            channel_name,
                        )

                    config.extract_channels_main = extract_channels_main_obj

                if "extract_channels_backup" in yaml_config:
                    extract_channels_backup_config = yaml_config[
                        "extract_channels_backup"
                    ]
                    extract_channels_backup_obj = type(
                        "ExtractChannelsBackup", {}, {}
                    )()

                    for (
                        extract_type,
                        channel_name,
                    ) in extract_channels_backup_config.items():
                        setattr(
                            extract_channels_backup_obj,
                            extract_type,
                            channel_name,
                        )

                    config.extract_channels_backup = (
                        extract_channels_backup_obj
                    )

                if "processing" in yaml_config:
                    for field, value in yaml_config["processing"].items():
                        if hasattr(config.processing, field):
                            setattr(config.processing, field, value)

                if "ocr" in yaml_config:
                    for field, value in yaml_config["ocr"].items():
                        if hasattr(config.ocr, field):
                            setattr(config.ocr, field, value)

                if "layout_detection" in yaml_config:
                    for field, value in yaml_config[
                        "layout_detection"
                    ].items():
                        if hasattr(config.layout_detection, field):
                            setattr(config.layout_detection, field, value)

                if "use_direct_models" in yaml_config:
                    config.use_direct_models = yaml_config["use_direct_models"]

                if "direct_model_name" in yaml_config:
                    config.direct_model_name = yaml_config["direct_model_name"]

                if "model_download" in yaml_config:
                    config.model_download.update(yaml_config["model_download"])

                validation_errors = config.validate()
                if validation_errors:
                    raise ValueError(
                        "Configuration validation failed: "
                        f"{'; '.join(validation_errors)}"
                    )

                return config

            except Exception as e:
                raise ValueError(f"Failed to load configuration file: {e}")
        else:
            raise FileNotFoundError(
                f"Configuration file not found: {config_path}"
            )


config = Config()


def _find_config_path():

    import os

    candidates = []
    env_path = os.environ.get("SMARTRESUME_CONFIG")
    if env_path:
        candidates.append(env_path)
    candidates.append(os.path.join(os.getcwd(), "configs", "config.yaml"))
    candidates.append(
        os.path.join(os.path.expanduser("~"), ".smartresume", "config.yaml")
    )
    package_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    candidates.append(os.path.join(package_dir, "configs", "config.yaml"))
    for path in candidates:
        if os.path.exists(path):
            return path
    return None


_config_path = _find_config_path()
if _config_path:

    config = Config.from_yaml(_config_path)

import json
import os
from typing import Dict, List, Any
from openai import OpenAI
from concurrent.futures import ThreadPoolExecutor
from smartresume.utils.config import config
from smartresume.utils.prompts import get_prompts
from smartresume.utils.extraction_schema import (
    TASK_ROOTS,
    validate_task_result,
)

import random
import json_repair


try:
    from vllm import LLM, SamplingParams

    VLLM_AVAILABLE = True
except ImportError:
    VLLM_AVAILABLE = False

try:
    from transformers import AutoTokenizer, AutoModelForCausalLM
    import torch

    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False


class LLMClient:

    def __init__(self) -> None:
        self.default_client = OpenAI(
            base_url=config.model.api_url, api_key=config.model.api_key
        )

        self.channel_clients: Dict[str, OpenAI] = {}
        self._init_channel_clients()

        self.prompts = get_prompts()

        self.use_direct_models = getattr(config, "use_direct_models", False)
        self.direct_model = None
        self.direct_tokenizer = None
        self._vllm_llm = None
        self._vllm_sampling_params = None
        self._use_vllm = False
        self._init_direct_model()

    def _init_channel_clients(self) -> None:

        if hasattr(config, "channels") and isinstance(config.channels, dict):
            channel_names = list(config.channels.keys())

            for channel_name in channel_names:
                try:
                    channel_config = config.channels[channel_name]
                    if hasattr(channel_config, "api_url") and hasattr(
                        channel_config, "api_key"
                    ):
                        self.channel_clients[channel_name] = OpenAI(
                            base_url=channel_config.api_url,
                            api_key=channel_config.api_key,
                        )

                    else:
                        pass
                except Exception:
                    pass

    def _init_direct_model(self) -> None:

        if not self.use_direct_models:
            return
        if not (VLLM_AVAILABLE or TRANSFORMERS_AVAILABLE):
            return

        try:
            direct_model_name = getattr(config, "direct_model_name", None)
            if not direct_model_name:
                print(
                    "Warning: use_direct_models is True but "
                    "direct_model_name is not configured"
                )
                return

            local_model_path = None
            models_dir = (
                getattr(config, "model_download", {})
                .get("models_dir", {})
                .get("llm", "models")
            )

            if os.path.exists(direct_model_name):
                local_model_path = direct_model_name
            else:
                possible_paths = [
                    os.path.join(models_dir, direct_model_name),
                    os.path.join(
                        models_dir, os.path.basename(direct_model_name)
                    ),
                    os.path.join("models", direct_model_name),
                    os.path.join(
                        "models", os.path.basename(direct_model_name)
                    ),
                ]
                for path in possible_paths:
                    if os.path.exists(path):
                        local_model_path = path
                        break

            if not local_model_path and not config.model_download.get(
                "auto_download", True
            ):
                raise FileNotFoundError(
                    f"Local model missing: {direct_model_name}; "
                    "auto_download is disabled"
                )

            if not local_model_path:
                print(
                    "Local model not found, attempting to download: "
                    f"{direct_model_name}"
                )
                try:
                    from smartresume.utils.models_download_utils import (
                        auto_download_and_get_model_path,
                    )
                    from smartresume.utils.model_paths import ModelType

                    checkpoint = os.path.basename(
                        os.path.normpath(direct_model_name)
                    )
                    local_model_path = auto_download_and_get_model_path(
                        checkpoint, ModelType.LLM, models_dir
                    )
                except Exception as download_error:
                    print(f"Failed to download model: {download_error}")
                    local_model_path = direct_model_name

            if not local_model_path:
                print("Could not resolve model path after download")
                return

            print(f"Loading direct model from: {local_model_path}")

            self.direct_tokenizer = AutoTokenizer.from_pretrained(
                local_model_path,
                trust_remote_code=False,
                local_files_only=not config.model_download.get(
                    "auto_download", True
                ),
            )

            if VLLM_AVAILABLE:

                gpu_count = getattr(config, "vllm_gpu_count", 1)
                max_model_len = getattr(config, "vllm_max_model_len", 32768)
                self._max_model_len = max_model_len
                max_tokens_gen = getattr(config.model, "max_tokens", 8192)
                if max_tokens_gen <= 0:
                    max_tokens_gen = 8192
                self._vllm_sampling_params = SamplingParams(
                    temperature=getattr(config.model, "temperature", 0.1),
                    top_p=getattr(config.model, "top_p", 1.0),
                    max_tokens=max_tokens_gen,
                    repetition_penalty=1.05,
                )
                self._vllm_llm = LLM(
                    model=local_model_path,
                    trust_remote_code=False,
                    tensor_parallel_size=gpu_count,
                    max_num_seqs=32,
                    gpu_memory_utilization=getattr(
                        config, "vllm_gpu_memory_utilization", 0.9
                    ),
                    max_model_len=max_model_len,
                    enforce_eager=False,
                    swap_space=4,
                    max_num_batched_tokens=max_model_len,
                )
                self._use_vllm = True
                print(
                    "Direct model loaded with vLLM "
                    "(in-process library, no API server)"
                )
                return

            if not TRANSFORMERS_AVAILABLE:
                return
            self._max_model_len = getattr(config, "vllm_max_model_len", 32768)
            device = "cuda" if torch.cuda.is_available() else "cpu"
            self.direct_model = AutoModelForCausalLM.from_pretrained(
                local_model_path,
                trust_remote_code=False,
                local_files_only=not config.model_download.get(
                    "auto_download", True
                ),
                torch_dtype=(
                    torch.float16 if device == "cuda" else torch.float32
                ),
                device_map="auto" if device == "cuda" else None,
            )
            if device == "cpu":
                self.direct_model = self.direct_model.to(device)
            self.direct_model.eval()
            print(f"Direct model loaded with transformers on {device}")

        except Exception as e:
            print(f"Failed to load direct model: {e}")
            self.direct_model = None
            self.direct_tokenizer = None
            self._vllm_llm = None
            self._vllm_sampling_params = None
            self._use_vllm = False

    def _get_client(
        self, extract_type: str, use_backup_channel: bool = False
    ) -> OpenAI:

        has_backup = (
            hasattr(config, "extract_channels_backup")
            and config.extract_channels_backup
        )
        has_main = (
            hasattr(config, "extract_channels_main")
            and config.extract_channels_main
        )
        has_default = (
            hasattr(config, "extract_channels") and config.extract_channels
        )
        if use_backup_channel and has_backup:
            channel_name = getattr(
                config.extract_channels_backup, extract_type, ""
            )
        elif has_main:
            channel_name = getattr(
                config.extract_channels_main, extract_type, ""
            )
        elif has_default:
            channel_name = getattr(config.extract_channels, extract_type, "")
        else:
            channel_name = ""

        if channel_name and channel_name in self.channel_clients:
            return self.channel_clients[channel_name]
        else:
            return self.default_client

    def _get_channel_config(
        self, extract_type: str, use_backup_channel: bool = False
    ) -> Any:

        has_backup = (
            hasattr(config, "extract_channels_backup")
            and config.extract_channels_backup
        )
        has_main = (
            hasattr(config, "extract_channels_main")
            and config.extract_channels_main
        )
        has_default = (
            hasattr(config, "extract_channels") and config.extract_channels
        )
        if use_backup_channel and has_backup:
            channel_name = getattr(
                config.extract_channels_backup, extract_type, ""
            )
        elif has_main:
            channel_name = getattr(
                config.extract_channels_main, extract_type, ""
            )
        elif has_default:
            channel_name = getattr(config.extract_channels, extract_type, "")
        else:
            channel_name = ""

        if (
            channel_name
            and hasattr(config, "channels")
            and channel_name in config.channels
        ):
            return config.channels[channel_name]
        else:
            return config.model

    def _extract_info_remote(
        self,
        text_content: str,
        extract_types: List[str],
        resume_id: str,
        use_backup_channel: bool = False,
    ) -> Dict[str, Any]:

        def call_llm(prompt_key: str) -> Dict[str, Any]:

            client = self._get_client(prompt_key, use_backup_channel)
            channel_config = self._get_channel_config(
                prompt_key, use_backup_channel
            )

            messages = [
                {"role": "system", "content": self.prompts[prompt_key]},
                {
                    "role": "user",
                    "content": [{"type": "text", "text": text_content}],
                },
            ]

            params = {
                "model": channel_config.name,
                "messages": messages,
                "max_tokens": channel_config.max_tokens,
                "temperature": channel_config.temperature,
                "top_p": channel_config.top_p,
                "seed": channel_config.seed,
                "extra_body": {
                    "chat_template_kwargs": {"enable_thinking": False},
                    "repetition_penalty": 1.01,
                },
            }

            if config.processing.use_force_json:
                params["response_format"] = {"type": "json_object"}

            max_retries = 2
            for attempt in range(max_retries + 1):
                if attempt > 0:
                    params["temperature"] = 1.0
                    params["seed"] = random.randint(0, 1000000)

                try:
                    completion = client.chat.completions.create(**params)
                    if completion.choices[0].finish_reason == "length":
                        raise ValueError(
                            "Generation reached max_tokens before completion"
                        )
                    content = completion.choices[0].message.content

                    json_start = content.find("{")
                    json_end = content.rfind("}") + 1

                    if json_start != -1 and json_end > json_start:
                        content = content[json_start:json_end]
                        try:
                            return json.loads(content)
                        except json.JSONDecodeError:
                            content = content.replace("'", '"')
                            content = content.replace("True", "true")
                            content = content.replace("False", "false")
                            content = content.replace("None", "null")
                            return json_repair.loads(content)
                    else:
                        raise ValueError("No valid JSON content found")

                except Exception as e:
                    if attempt < max_retries:
                        continue
                    else:

                        error_dir = os.path.join(
                            os.path.dirname(
                                os.path.dirname(os.path.dirname(__file__))
                            ),
                            "temp",
                            "extraction_errors",
                        )
                        os.makedirs(error_dir, exist_ok=True)
                        error_info = {
                            "error_type": type(e).__name__,
                            "error_message": str(e),
                            "prompt_key": prompt_key,
                            "channel_config": {
                                "name": channel_config.name,
                                "api_url": channel_config.api_url,
                                "max_tokens": channel_config.max_tokens,
                            },
                            "params": params,
                        }
                        with open(
                            os.path.join(
                                error_dir,
                                f"{os.path.basename(resume_id)}_"
                                f"{prompt_key}_error.json",
                            ),
                            "w",
                            encoding="utf-8",
                        ) as f:
                            json.dump(
                                error_info, f, ensure_ascii=False, indent=2
                            )
                        return {}

        with ThreadPoolExecutor() as executor:
            results = list(executor.map(call_llm, extract_types))

        combined_result = {}
        errors = []
        for task, result in zip(extract_types, results):
            try:
                combined_result.update(validate_task_result(task, result))
            except (ValueError, TypeError) as error:
                errors.append({"task": task, "message": str(error)})
        if errors:
            combined_result["extractionErrors"] = errors
        return combined_result

    def extract_info_direct(
        self,
        text_content: str,
        extract_types: List[str],
        resume_id: str,
        use_backup_channel: bool = False,
    ) -> Dict[str, Any]:

        if not self.direct_tokenizer or (
            not self.direct_model and not self._vllm_llm
        ):
            if self.use_direct_models:
                raise RuntimeError(
                    "Direct model (vLLM as library) not available. "
                    "Do not start vLLM API—fix direct_model_name "
                    "or install vLLM."
                )
            print("Direct model not available, falling back to remote API")
            return self._extract_info_remote(
                text_content=text_content,
                extract_types=extract_types,
                resume_id=resume_id,
                use_backup_channel=use_backup_channel,
            )

        def call_direct_llm(prompt_key: str) -> Dict[str, Any]:

            try:

                system_prompt = self.prompts[prompt_key]
                user_prompt = text_content

                tokenizer_has_tpl = hasattr(
                    self.direct_tokenizer, "chat_template"
                )
                has_chat_tpl = (
                    tokenizer_has_tpl and self.direct_tokenizer.chat_template
                )
                if has_chat_tpl:

                    messages = [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ]
                    prompt = self.direct_tokenizer.apply_chat_template(
                        messages,
                        tokenize=False,
                        add_generation_prompt=True,
                        enable_thinking=False,
                    )
                else:

                    prompt = (
                        f"System: {system_prompt}\n\n"
                        f"User: {user_prompt}\n\nAssistant:"
                    )

                if (
                    self._use_vllm
                    and self._vllm_llm
                    and self._vllm_sampling_params
                ):
                    max_input_len = (
                        self._max_model_len
                        - self._vllm_sampling_params.max_tokens
                    )
                    token_ids = self.direct_tokenizer.encode(prompt)
                    if max_input_len <= 0 or len(token_ids) > max_input_len:
                        raise ValueError(
                            "Resume exceeds the model context budget"
                        )
                    outputs = self._vllm_llm.generate(
                        [prompt], self._vllm_sampling_params
                    )
                    generated_output = outputs[0].outputs[0]
                    if generated_output.finish_reason == "length":
                        raise ValueError(
                            "Generation reached max_tokens before completion"
                        )
                    response = generated_output.text
                else:
                    max_new_tokens = int(config.model.max_tokens)
                    if not 0 < max_new_tokens < self._max_model_len:
                        raise ValueError("Invalid generation token budget")

                    inputs = self.direct_tokenizer(
                        prompt, return_tensors="pt", truncation=False
                    )

                    if (
                        inputs["input_ids"].shape[1] + max_new_tokens
                        > self._max_model_len
                    ):
                        raise ValueError(
                            "Resume exceeds the model context budget"
                        )

                    device = next(self.direct_model.parameters()).device
                    inputs = {k: v.to(device) for k, v in inputs.items()}

                    with torch.inference_mode():
                        outputs = self.direct_model.generate(
                            **inputs,
                            max_new_tokens=max_new_tokens,
                            temperature=None,
                            top_p=None,
                            top_k=None,
                            do_sample=False,
                            pad_token_id=self.direct_tokenizer.eos_token_id,
                            eos_token_id=self.direct_tokenizer.eos_token_id,
                        )

                    prompt_length = inputs["input_ids"].shape[1]
                    generated = outputs[0][prompt_length:]
                    if (
                        len(generated) >= max_new_tokens
                        and int(generated[-1])
                        != self.direct_tokenizer.eos_token_id
                    ):
                        raise RuntimeError(
                            "Generation reached max_tokens before EOS"
                        )

                    response = self.direct_tokenizer.decode(
                        generated,
                        skip_special_tokens=True,
                    )

                response = response.strip()

                json_start = response.find("{")
                json_end = response.rfind("}") + 1

                if json_start != -1 and json_end > json_start:
                    json_content = response[json_start:json_end]
                    try:
                        return json.loads(json_content)
                    except json.JSONDecodeError:

                        json_content = json_content.replace("'", '"')
                        json_content = json_content.replace("True", "true")
                        json_content = json_content.replace("False", "false")
                        json_content = json_content.replace("None", "null")
                        return json_repair.loads(json_content)
                else:
                    raise ValueError(f"No valid JSON found for {prompt_key}")

            except Exception as e:
                print(f"Error in direct model call for {prompt_key}: {e}")

                error_dir = os.path.join(
                    os.path.dirname(
                        os.path.dirname(os.path.dirname(__file__))
                    ),
                    "temp",
                    "extraction_errors",
                )
                os.makedirs(error_dir, exist_ok=True)
                error_info = {
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "prompt_key": prompt_key,
                    "model_name": getattr(
                        config, "direct_model_name", "unknown"
                    ),
                }
                with open(
                    os.path.join(
                        error_dir,
                        f"{os.path.basename(resume_id)}_"
                        f"{prompt_key}_direct_error.json",
                    ),
                    "w",
                    encoding="utf-8",
                ) as f:
                    json.dump(error_info, f, ensure_ascii=False, indent=2)
                raise RuntimeError(
                    f"Local extraction failed for {prompt_key}"
                ) from e

        combined_result = {}
        errors = []
        for extract_type in extract_types:
            try:
                result = call_direct_llm(extract_type)
                combined_result.update(
                    validate_task_result(extract_type, result)
                )
            except Exception as error:
                errors.append({"task": extract_type, "message": str(error)})
        if errors:
            combined_result["extractionErrors"] = errors
        return combined_result

    def extract_info(
        self,
        text_content: str,
        extract_types: List[str],
        resume_id: str,
        use_backup_channel: bool = False,
    ) -> Dict[str, Any]:

        unknown = set(extract_types) - set(TASK_ROOTS)
        if unknown:
            raise ValueError(
                "Unsupported extraction types: " + ", ".join(sorted(unknown))
            )
        extract_types = list(dict.fromkeys(extract_types))

        if self.use_direct_models:
            if self.direct_tokenizer and (self.direct_model or self._vllm_llm):
                return self.extract_info_direct(
                    text_content=text_content,
                    extract_types=extract_types,
                    resume_id=resume_id,
                    use_backup_channel=use_backup_channel,
                )

            raise RuntimeError(
                "use_direct_models is True but direct model failed to load. "
                "Please set direct_model_name in config and ensure "
                "vLLM (or transformers) is installed. "
                "Do not start vLLM API server—vLLM is used "
                "as an in-process library only."
            )

        return self._extract_info_remote(
            text_content=text_content,
            extract_types=extract_types,
            resume_id=resume_id,
            use_backup_channel=use_backup_channel,
        )

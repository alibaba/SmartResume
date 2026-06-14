"""
LLM client module
"""
import json
import os
from typing import Dict, List, Any
from openai import OpenAI
from concurrent.futures import ThreadPoolExecutor
from smartresume.utils.config import config
from smartresume.utils.prompts import get_prompts

import random
import json_repair

# Direct model: use vLLM as in-process library (no API server to start)
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
    """LLM client responsible for interacting with language models"""

    def __init__(self) -> None:
        self.default_client = OpenAI(
            base_url=config.model.api_url,
            api_key=config.model.api_key
        )

        self.channel_clients: Dict[str, OpenAI] = {}
        self._init_channel_clients()

        self.prompts = get_prompts()

        # Initialize direct model support
        self.use_direct_models = getattr(config, 'use_direct_models', False)
        self.direct_model = None
        self.direct_tokenizer = None
        self._vllm_llm = None
        self._vllm_sampling_params = None
        self._use_vllm = False
        self._init_direct_model()

    def _init_channel_clients(self) -> None:
        """Initialize multi-channel clients"""
        if hasattr(config, 'channels') and isinstance(config.channels, dict):
            channel_names = list(config.channels.keys())

            for channel_name in channel_names:
                try:
                    channel_config = config.channels[channel_name]
                    if hasattr(channel_config, 'api_url') and hasattr(channel_config, 'api_key'):
                        self.channel_clients[channel_name] = OpenAI(
                            base_url=channel_config.api_url,
                            api_key=channel_config.api_key
                        )

                    else:
                        pass
                except Exception:
                    pass

    def _init_direct_model(self) -> None:
        """Initialize direct model loading.

        Prefer vLLM (LLM, SamplingParams), fallback to transformers.
        """
        if not self.use_direct_models:
            return
        if not (VLLM_AVAILABLE or TRANSFORMERS_AVAILABLE):
            return

        try:
            direct_model_name = getattr(config, 'direct_model_name', None)
            if not direct_model_name:
                print("Warning: use_direct_models is True but direct_model_name is not configured")
                return

            local_model_path = None
            models_dir = (
                getattr(config, 'model_download', {})
                .get('models_dir', {})
                .get('llm', 'models')
            )

            if os.path.exists(direct_model_name):
                local_model_path = direct_model_name
            else:
                possible_paths = [
                    os.path.join(models_dir, direct_model_name),
                    os.path.join(models_dir, os.path.basename(direct_model_name)),
                    os.path.join('models', direct_model_name),
                    os.path.join('models', os.path.basename(direct_model_name))
                ]
                for path in possible_paths:
                    if os.path.exists(path):
                        local_model_path = path
                        break

            if not local_model_path:
                print(f"Local model not found, attempting to download: {direct_model_name}")
                try:
                    from smartresume.utils.models_download_utils import download_model
                    from smartresume.utils.model_paths import ModelType, ModelSource
                    download_model(ModelType.LLM, ModelSource.MODELSCOPE, models_dir)
                    for path in possible_paths:
                        if os.path.exists(path):
                            local_model_path = path
                            break
                except Exception as download_error:
                    print(f"Failed to download model: {download_error}")
                    local_model_path = direct_model_name

            if not local_model_path:
                print("Could not resolve model path after download")
                return

            print(f"Loading direct model from: {local_model_path}")

            self.direct_tokenizer = AutoTokenizer.from_pretrained(
                local_model_path,
                trust_remote_code=True
            )

            if VLLM_AVAILABLE:
                # vLLM as library: load model in-process, no API server needed
                gpu_count = getattr(config, 'vllm_gpu_count', 1)
                max_model_len = getattr(config, 'vllm_max_model_len', 32768)
                self._max_model_len = max_model_len
                max_tokens_gen = getattr(config.model, 'max_tokens', 8192)
                if max_tokens_gen <= 0:
                    max_tokens_gen = 8192
                self._vllm_sampling_params = SamplingParams(
                    temperature=getattr(config.model, 'temperature', 0.1),
                    top_p=getattr(config.model, 'top_p', 1.0),
                    max_tokens=max_tokens_gen,
                    repetition_penalty=1.05,
                )
                self._vllm_llm = LLM(
                    model=local_model_path,
                    trust_remote_code=True,
                    tensor_parallel_size=gpu_count,
                    max_num_seqs=32,
                    gpu_memory_utilization=getattr(config, 'vllm_gpu_memory_utilization', 0.9),
                    max_model_len=max_model_len,
                    enforce_eager=False,
                    swap_space=4,
                    max_num_batched_tokens=max_model_len,
                )
                self._use_vllm = True
                print("Direct model loaded with vLLM (in-process library, no API server)")
                return

            if not TRANSFORMERS_AVAILABLE:
                return
            self._max_model_len = getattr(config, 'vllm_max_model_len', 32768)
            device = "cuda" if torch.cuda.is_available() else "cpu"
            self.direct_model = AutoModelForCausalLM.from_pretrained(
                local_model_path,
                trust_remote_code=True,
                torch_dtype=torch.float16 if device == "cuda" else torch.float32,
                device_map="auto" if device == "cuda" else None
            )
            if device == "cpu":
                self.direct_model = self.direct_model.to(device)
            print(f"Direct model loaded with transformers on {device}")

        except Exception as e:
            print(f"Failed to load direct model: {e}")
            self.direct_model = None
            self.direct_tokenizer = None
            self._vllm_llm = None
            self._vllm_sampling_params = None
            self._use_vllm = False

    def _get_client(self, extract_type: str, use_backup_channel: bool = False) -> OpenAI:
        """Get the client for a given extraction type"""
        has_backup = hasattr(config, 'extract_channels_backup') and config.extract_channels_backup
        has_main = hasattr(config, 'extract_channels_main') and config.extract_channels_main
        has_default = hasattr(config, 'extract_channels') and config.extract_channels
        if use_backup_channel and has_backup:
            channel_name = getattr(
                config.extract_channels_backup, extract_type, ""
            )
        elif has_main:
            channel_name = getattr(
                config.extract_channels_main, extract_type, ""
            )
        elif has_default:
            channel_name = getattr(
                config.extract_channels, extract_type, ""
            )
        else:
            channel_name = ""

        if channel_name and channel_name in self.channel_clients:
            return self.channel_clients[channel_name]
        else:
            return self.default_client

    def _get_channel_config(
        self, extract_type: str,
        use_backup_channel: bool = False
    ) -> Any:
        """Get channel configuration for a given extraction type"""
        has_backup = hasattr(config, 'extract_channels_backup') and config.extract_channels_backup
        has_main = hasattr(config, 'extract_channels_main') and config.extract_channels_main
        has_default = hasattr(config, 'extract_channels') and config.extract_channels
        if use_backup_channel and has_backup:
            channel_name = getattr(
                config.extract_channels_backup, extract_type, ""
            )
        elif has_main:
            channel_name = getattr(
                config.extract_channels_main, extract_type, ""
            )
        elif has_default:
            channel_name = getattr(
                config.extract_channels, extract_type, ""
            )
        else:
            channel_name = ""

        if channel_name and hasattr(config, 'channels') and channel_name in config.channels:
            return config.channels[channel_name]
        else:
            return config.model

    def _extract_info_remote(self, text_content: str, extract_types: List[str],
                             resume_id: str, use_backup_channel: bool = False) -> Dict[str, Any]:
        """
        Extract structured information using remote LLM API.

        Args:
            text_content: The input text content.
            extract_types: List of extraction types to run.
            resume_id: Resume identifier.
            use_backup_channel: Whether to use backup channel mapping.

        Returns:
            A dictionary with extracted fields.
        """
        def call_llm(prompt_key: str) -> Dict[str, Any]:
            """Call the LLM for a single extraction type"""
            client = self._get_client(prompt_key, use_backup_channel)
            channel_config = self._get_channel_config(prompt_key, use_backup_channel)

            messages = [
                {
                    "role": "system",
                    "content": self.prompts[prompt_key]
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": text_content
                        }
                    ]
                }
            ]

            params = {
                'model': channel_config.name,
                'messages': messages,
                'max_tokens': channel_config.max_tokens,
                'temperature': channel_config.temperature,
                'top_p': channel_config.top_p,
                'seed': channel_config.seed,
                "extra_body": {
                    "chat_template_kwargs": {"enable_thinking": False},
                    "repetition_penalty": 1.01
                },
            }

            if config.processing.use_force_json:
                params['response_format'] = {"type": "json_object"}

            max_retries = 2
            for attempt in range(max_retries + 1):
                if attempt > 0:
                    params['temperature'] = 1.0
                    params['seed'] = random.randint(0, 1000000)

                try:
                    completion = client.chat.completions.create(**params)
                    content = completion.choices[0].message.content
                    content = content.replace('\\"', '"')

                    json_start = content.find("{")
                    json_end = content.rfind("}") + 1

                    if json_start != -1 and json_end > json_start:
                        content = content[json_start:json_end]
                        try:
                            return json.loads(content)
                        except json.JSONDecodeError:
                            content = content.replace("'", '"')
                            content = content.replace('True', 'true')
                            content = content.replace('False', 'false')
                            content = content.replace('None', 'null')
                            return json_repair.loads(content)
                    else:
                        raise ValueError("No valid JSON content found")

                except Exception as e:
                    if attempt < max_retries:
                        continue
                    else:
                        pass
                        os.makedirs("contents", exist_ok=True)
                        error_info = {
                            "error_type": type(e).__name__,
                            "error_message": str(e),
                            "prompt_key": prompt_key,
                            "channel_config": {
                                "name": channel_config.name,
                                "api_url": channel_config.api_url,
                                "max_tokens": channel_config.max_tokens
                            },
                            "params": params
                        }
                        with open(
                            f"contents/{resume_id}_{prompt_key}_error.json",
                            "w",
                            encoding='utf-8',
                        ) as f:
                            json.dump(error_info, f, ensure_ascii=False, indent=2)
                        return {}

        with ThreadPoolExecutor() as executor:
            results = list(executor.map(call_llm, extract_types))

        combined_result = {}
        for result in results:
            combined_result.update(result)

        return combined_result

    def extract_info_direct(self, text_content: str, extract_types: List[str],
                            resume_id: str, use_backup_channel: bool = False) -> Dict[str, Any]:
        """
        Extract structured information using directly loaded model.

        Args:
            text_content: The input text content
            extract_types: List of extraction types to run
            resume_id: Resume identifier
            use_backup_channel: Whether to use backup channel mapping (not used in direct mode)

        Returns:
            A dictionary with extracted fields
        """
        if not self.direct_tokenizer or (not self.direct_model and not self._vllm_llm):
            if self.use_direct_models:
                raise RuntimeError(
                    "Direct model (vLLM as library) not available. "
                    "Do not start vLLM API—fix direct_model_name or install vLLM."
                )
            print("Direct model not available, falling back to remote API")
            return self._extract_info_remote(
                text_content=text_content,
                extract_types=extract_types,
                resume_id=resume_id,
                use_backup_channel=use_backup_channel
            )

        def call_direct_llm(prompt_key: str) -> Dict[str, Any]:
            """Call direct model for a single extraction type"""
            try:
                # Prepare prompt
                system_prompt = self.prompts[prompt_key]
                user_prompt = text_content

                # Format prompt based on model type
                tokenizer_has_tpl = hasattr(self.direct_tokenizer, 'chat_template')
                has_chat_tpl = tokenizer_has_tpl and self.direct_tokenizer.chat_template
                if has_chat_tpl:
                    # Use chat template if available
                    messages = [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ]
                    prompt = self.direct_tokenizer.apply_chat_template(
                        messages,
                        tokenize=False,
                        add_generation_prompt=True
                    )
                else:
                    # Fallback to simple format
                    prompt = f"System: {system_prompt}\n\nUser: {user_prompt}\n\nAssistant:"

                if self._use_vllm and self._vllm_llm and self._vllm_sampling_params:
                    # Truncate prompt if it exceeds max_model_len
                    max_input_len = self._max_model_len - self._vllm_sampling_params.max_tokens
                    token_ids = self.direct_tokenizer.encode(prompt)
                    if len(token_ids) > max_input_len:
                        token_ids = token_ids[:max_input_len]
                        prompt = self.direct_tokenizer.decode(token_ids, skip_special_tokens=False)
                    outputs = self._vllm_llm.generate([prompt], self._vllm_sampling_params)
                    response = outputs[0].outputs[0].text
                else:
                    # Tokenize input
                    inputs = self.direct_tokenizer(
                        prompt,
                        return_tensors="pt",
                        truncation=True,
                        max_length=self._max_model_len
                    )

                    # Move to device
                    device = next(self.direct_model.parameters()).device
                    inputs = {k: v.to(device) for k, v in inputs.items()}

                    # Generate response
                    with torch.no_grad():
                        outputs = self.direct_model.generate(
                            **inputs,
                            max_new_tokens=1024,
                            temperature=0.1,
                            do_sample=True,
                            pad_token_id=self.direct_tokenizer.eos_token_id,
                            eos_token_id=self.direct_tokenizer.eos_token_id
                        )

                    # Decode response
                    response = self.direct_tokenizer.decode(
                        outputs[0][inputs['input_ids'].shape[1]:],
                        skip_special_tokens=True
                    )

                # Clean up response
                response = response.strip()
                response = response.replace('\\"', '"')

                # Extract JSON from response
                json_start = response.find("{")
                json_end = response.rfind("}") + 1

                if json_start != -1 and json_end > json_start:
                    json_content = response[json_start:json_end]
                    try:
                        return json.loads(json_content)
                    except json.JSONDecodeError:
                        # Try to repair JSON
                        json_content = json_content.replace("'", '"')
                        json_content = json_content.replace('True', 'true')
                        json_content = json_content.replace('False', 'false')
                        json_content = json_content.replace('None', 'null')
                        return json_repair.loads(json_content)
                else:
                    print(f"No valid JSON found in response for {prompt_key}")
                    return {}

            except Exception as e:
                print(f"Error in direct model call for {prompt_key}: {e}")
                # Save error info for debugging
                os.makedirs("contents", exist_ok=True)
                error_info = {
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "prompt_key": prompt_key,
                    "model_name": getattr(config, 'direct_model_name', 'unknown')
                }
                with open(
                    f"contents/{resume_id}_{prompt_key}_direct_error.json",
                    "w",
                    encoding='utf-8',
                ) as f:
                    json.dump(error_info, f, ensure_ascii=False, indent=2)
                return {}

        # Process all extraction types sequentially (to avoid memory issues)
        combined_result = {}
        for extract_type in extract_types:
            result = call_direct_llm(extract_type)
            combined_result.update(result)

        return combined_result

    def extract_info(self, text_content: str, extract_types: List[str],
                     resume_id: str, use_backup_channel: bool = False) -> Dict[str, Any]:
        """
        Extract structured information using LLM (direct or remote).

        When use_direct_models is True, only in-process vLLM/transformers is used;
        no vLLM API server is required or used.
        """
        # Prefer direct model (vLLM as library or transformers in-process)
        if self.use_direct_models:
            if self.direct_tokenizer and (self.direct_model or self._vllm_llm):
                return self.extract_info_direct(
                    text_content=text_content,
                    extract_types=extract_types,
                    resume_id=resume_id,
                    use_backup_channel=use_backup_channel
                )
            # Direct mode enabled but model not loaded: do not fall back to vLLM API
            raise RuntimeError(
                "use_direct_models is True but direct model failed to load. "
                "Please set direct_model_name in config and ensure "
                "vLLM (or transformers) is installed. "
                "Do not start vLLM API server—vLLM is used as an in-process library only."
            )

        # Remote API only when use_direct_models is False
        return self._extract_info_remote(
            text_content=text_content,
            extract_types=extract_types,
            resume_id=resume_id,
            use_backup_channel=use_backup_channel
        )

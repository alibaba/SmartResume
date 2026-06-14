"""
CLI module for command line interface functionality
"""

from .models_download import download_models
from .vllm_server import main as start_vllm_server

__all__ = ['download_models', 'start_vllm_server']

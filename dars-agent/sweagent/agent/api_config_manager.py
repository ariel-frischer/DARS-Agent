"""API configuration management - Single Responsibility Principle."""
from __future__ import annotations
import os
import logging
from typing import Dict, Any
from sweagent.utils.config import keys_config


class APIConfigManager:
    """Manages API configuration for different model providers."""

    @staticmethod
    def setup_openai_config() -> None:
        """Configure OpenAI API."""
        os.environ["OPENAI_API_KEY"] = keys_config.get("OPENAI_API_KEY", "")

    @staticmethod
    def setup_anthropic_config() -> None:
        """Configure Anthropic API."""
        os.environ["ANTHROPIC_API_KEY"] = keys_config.get("ANTHROPIC_API_KEY", "")

    @staticmethod
    def setup_google_config() -> None:
        """Configure Google API."""
        os.environ["GOOGLE_API_KEY"] = keys_config.get("GOOGLE_API_KEY", "")

    @staticmethod
    def setup_aws_config() -> None:
        """Configure AWS API."""
        os.environ["AWS_ACCESS_KEY_ID"] = keys_config.get("AWS_ACCESS_KEY_ID", "")
        os.environ["AWS_SECRET_ACCESS_KEY"] = keys_config.get("AWS_SECRET_ACCESS", "")
        os.environ["AWS_DEFAULT_REGION"] = keys_config.get("AWS_DEFAULT_REGION", "")

    @staticmethod
    def setup_azure_config() -> None:
        """Configure Azure API."""
        os.environ["AZURE_API_KEY"] = keys_config.get("AZURE_API_KEY", "")
        os.environ["AZURE_API_BASE"] = keys_config.get("AZURE_API_BASE", "")

    @staticmethod
    def setup_gemini_config() -> None:
        """Configure Gemini API using genai library."""
        try:
            import google.generativeai as genai
            genai.configure(api_key=keys_config.get("GEMINI_API_KEY", ""))
        except ImportError:
            pass

    @staticmethod
    def setup_all_configs() -> None:
        """Configure all supported API providers."""
        APIConfigManager.setup_openai_config()
        APIConfigManager.setup_anthropic_config()
        APIConfigManager.setup_google_config()
        APIConfigManager.setup_aws_config()
        APIConfigManager.setup_azure_config()
        logging.getLogger("litellm").setLevel(logging.WARNING)

    @staticmethod
    def setup_litellm_config() -> None:
        """Configure LiteLLM with common providers."""
        APIConfigManager.setup_all_configs()

"""
Configuration Management for Pulse IDE.

Loads environment variables from .env file and provides
a centralized configuration interface for the application.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
# Look for .env in the project root directory
project_root = Path(__file__).parent.parent.parent
dotenv_path = project_root / ".env"
load_dotenv(dotenv_path=dotenv_path)


class Config:
    """
    Application configuration class.

    Loads and validates required environment variables.
    Raises ValueError if critical configuration is missing.
    """

    # OpenAI Configuration
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL_NAME: str = os.getenv("OPENAI_MODEL_NAME", "gpt-4o")

    # Optional: Anthropic Configuration (for future multi-provider support)
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")

    # Database Configuration
    DB_PATH: Path = project_root / "data" / "pulse.db"

    # ChromaDB Configuration
    CHROMA_DB_PATH: Path = project_root / "data" / "chroma_db"

    # Workspace Configuration
    DEFAULT_WORKSPACE: Path = project_root / "workspace"

    # Feedback Configuration
    FEEDBACK_PATH: Path = project_root / "data" / "feedback" / "feedback.jsonl"

    @classmethod
    def validate(cls) -> None:
        """
        Validate that all required configuration is present.

        Raises:
            ValueError: If required configuration is missing.
        """
        if not cls.OPENAI_API_KEY:
            raise ValueError(
                "OPENAI_API_KEY is not set. "
                "Please create a .env file with your OpenAI API key. "
                "See .env.example for reference."
            )

        # Ensure data directories exist
        cls.DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        cls.CHROMA_DB_PATH.mkdir(parents=True, exist_ok=True)
        cls.FEEDBACK_PATH.parent.mkdir(parents=True, exist_ok=True)
        cls.DEFAULT_WORKSPACE.mkdir(parents=True, exist_ok=True)

    @classmethod
    def get_summary(cls) -> dict:
        """
        Get a summary of the current configuration (for debugging).

        Returns:
            dict: Configuration summary with sensitive values masked.
        """
        return {
            "openai_api_key_set": bool(cls.OPENAI_API_KEY),
            "openai_model": cls.OPENAI_MODEL_NAME,
            "anthropic_api_key_set": bool(cls.ANTHROPIC_API_KEY),
            "db_path": str(cls.DB_PATH),
            "chroma_db_path": str(cls.CHROMA_DB_PATH),
            "default_workspace": str(cls.DEFAULT_WORKSPACE),
            "feedback_path": str(cls.FEEDBACK_PATH),
        }


# Convenience exports for direct module-level access
OPENAI_API_KEY = Config.OPENAI_API_KEY
OPENAI_MODEL_NAME = Config.OPENAI_MODEL_NAME
ANTHROPIC_API_KEY = Config.ANTHROPIC_API_KEY
DB_PATH = Config.DB_PATH
CHROMA_DB_PATH = Config.CHROMA_DB_PATH
DEFAULT_WORKSPACE = Config.DEFAULT_WORKSPACE
FEEDBACK_PATH = Config.FEEDBACK_PATH


# Auto-validate on import (optional - can be disabled for testing)
if __name__ != "__main__":
    try:
        Config.validate()
    except ValueError as e:
        # Don't fail on import, but warn
        import warnings
        warnings.warn(f"Configuration validation warning: {e}")

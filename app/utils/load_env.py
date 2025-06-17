"""Environment variable loading utilities."""

import os

from dotenv import load_dotenv


def load_env():
    """Load environment variables from .env file."""
    load_dotenv()


def get_env(var_name: str, default: str = None) -> str:
    """Get an environment variable with optional default value.

    Args:
        var_name: Name of the environment variable
        default: Default value if variable is not set

    Returns:
        Value of the environment variable
    """
    return os.getenv(var_name, default)

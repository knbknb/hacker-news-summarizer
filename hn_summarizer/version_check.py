"""OpenAI version and feature detection utilities."""

import re
import openai as _openai_module
from openai import OpenAI

_REQUIRED_OPENAI_STRUCTURED_VERSION = (1, 40, 0)


def _parse_version_tuple(version_str: str) -> tuple[int, ...]:
    """Parse a version string into a tuple of integers."""
    digits = re.findall(r"\d+", version_str)
    return tuple(int(part) for part in digits)


def _has_responses_feature() -> bool:
    """Check if the OpenAI client has the responses feature."""
    if getattr(OpenAI, "responses", None) is not None:
        return True
    beta = getattr(OpenAI, "beta", None)
    return getattr(beta, "responses", None) is not None


def ensure_structured_output_support() -> None:
    """
    Ensure the installed OpenAI package supports structured outputs.
    
    Raises:
        RuntimeError: If the OpenAI package version is too old or lacks required features.
    """
    version_str = getattr(_openai_module, "__version__", None)
    if not version_str:
        raise RuntimeError(
            "Cannot determine the installed 'openai' version. "
            "Install openai>=1.40.0 to use structured outputs."
        )
    version_tuple = _parse_version_tuple(version_str)
    if not version_tuple or version_tuple < _REQUIRED_OPENAI_STRUCTURED_VERSION:
        raise RuntimeError(
            f"OpenAI {version_str} does not support structured outputs. "
            "Upgrade to openai>=1.40.0 to proceed."
        )
    if not _has_responses_feature():
        raise RuntimeError(
            "The installed OpenAI package lacks the Responses interface required for structured outputs. "
            "Please upgrade to openai>=1.40.0."
        )

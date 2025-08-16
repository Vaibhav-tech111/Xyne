# services/pollinations_service.py

import logging
from urllib.parse import quote_plus
from typing import Optional

import requests
from core.config import settings

logger = logging.getLogger(__name__)

# Default timeout for all Pollinations HTTP calls
DEFAULT_TIMEOUT = 8


def chat(prompt: str, timeout: Optional[int] = None) -> str:
    """
    Generate free text via the Pollinations Text API.

    Args:
        prompt: The user prompt to send.
        timeout: Optional HTTP timeout in seconds.

    Returns:
        The raw text response from the API.

    Raises:
        requests.RequestException on network/HTTP errors.
    """
    # Ensure exactly one slash between base URL and prompt
    base = settings.pollinations.text_url.rstrip("/") + "/"
    url = base + quote_plus(prompt)

    try:
        resp = requests.get(url, timeout=timeout or DEFAULT_TIMEOUT)
        resp.raise_for_status()
        return resp.text.strip()
    except requests.RequestException as e:
        logger.error("Pollinations text API error: %s", e)
        # Re-raise so downstream can send proper HTTPException or fallback
        raise


def generate_image(
    prompt: str,
    width: int = 1024,
    height: int = 1024,
    nologo: bool = True
) -> str:
    """
    Construct a direct image-generation URL via Pollinations Image API.

    Args:
        prompt: The prompt describing the image.
        width: Desired image width in pixels.
        height: Desired image height in pixels.
        nologo: Whether to hide Pollinations branding on the image.

    Returns:
        A fully-formed URL the client can fetch or embed.
    """
    base = settings.pollinations.image_url.rstrip("/") + "/"
    encoded = quote_plus(prompt)
    params = f"width={width}&height={height}"
    if nologo:
        params += "&nologo=true"
    return f"{base}{encoded}?{params}"

# services/hf_service.py
import os
import logging
from typing import Optional
import requests

logger = logging.getLogger(__name__)

# Config
HF_API_KEY: Optional[str] = os.getenv("HF_API_KEY")
HF_MODEL: str = os.getenv("HF_MODEL", "microsoft/DialoGPT-medium")
API_URL: str = f"https://api-inference.huggingface.co/models/{HF_MODEL}"  # ✅ Fixed: no trailing space
HF_TIMEOUT: int = int(os.getenv("HF_TIMEOUT", "30"))

def chat(prompt: str) -> str:
    """
    Sends a single-turn prompt to HF Inference API.
    Returns the generated text or a friendly fallback on error.
    """
    if not isinstance(prompt, str) or not prompt.strip():
        return "Please provide a valid prompt."

    if not HF_API_KEY:
        logger.warning("[HF] HF_API_KEY not set")
        return "Hugging Face unavailable."

    headers = {
        "Authorization": f"Bearer {HF_API_KEY}",
        "Accept": "application/json",
    }

    payload = {
        "inputs": prompt,
        "options": {"wait_for_model": True},
        "parameters": {
            "max_new_tokens": 256,
            "temperature": 0.7,
            "top_p": 0.9,
            "repetition_penalty": 1.05,
        },
    }

    try:
        resp = requests.post(API_URL, headers=headers, json=payload, timeout=HF_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()

        # 1) List of dicts: [{"generated_text": "..."}]
        if isinstance(data, list) and data:
            gen = data[0].get("generated_text", "")
            text = (gen or "").strip()
            return text or "Sorry, I couldn't generate a response."

        # 2) Dict: {"generated_text": "..."}
        if isinstance(data, dict) and "generated_text" in data:
            text = (data.get("generated_text") or "").strip()
            return text or "Sorry, I couldn't generate a response."

        # 3) Error response: {"error": "...", "estimated_time": ...}
        if isinstance(data, dict) and "error" in data:
            err = data.get("error", "Unknown error")
            eta = data.get("estimated_time")
            if eta:
                logger.info("[HF] Model loading, estimated_time=%ss: %s", eta, err)
                return "Model is warming up, please try again in a moment."
            logger.error("[HF] API error: %s", err)
            return "Sorry, HF service error."

        logger.warning("[HF] Unexpected response shape: %s", str(data)[:300])
        return "Sorry, unexpected response from Hugging Face."

    except requests.HTTPError as e:
        status = e.response.status_code if e.response is not None else "N/A"
        logger.error("[HF] HTTP error (%s): %s", status, e)
        if status == 503:
            return "Model is warming up, please try again shortly."
        return "Sorry, HF service error."
    except requests.RequestException as e:
        logger.error("[HF] Request failed: %s", e)
        return "Sorry, HF service error."
    except Exception as e:
        logger.error("[HF] Response parsing error: %s", e)
        return "Sorry, invalid response from Hugging Face."

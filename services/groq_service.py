# services/groq_service.py
import os
import logging
from typing import List, Dict

from groq import Groq

logger = logging.getLogger(__name__)

# Initialize client with API key
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    logger.error("[Groq] GROQ_API_KEY not set")
    client = None
else:
    try:
        client = Groq(api_key=GROQ_API_KEY)
        logger.info("[Groq] Client initialized successfully")
    except Exception as e:
        logger.error("[Groq] Failed to initialize client: %s", e)
        client = None

# Allow overriding via env; falls back to your default
MODEL_NAME = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")


def chat(messages: List[Dict[str, str]]) -> str:
    """
    messages: list of dicts with keys 'role' and 'content'
    Returns the generated text from Groq.
    """
    if not client:
        logger.warning("[Groq] Client not available")
        return "Sorry, the AI service is currently unavailable."

    try:
        # Normalize messages: keep only allowed fields and roles
        payload: List[Dict[str, str]] = []
        for m in messages:
            role = m.get("role")
            content = m.get("content", "")
            if not isinstance(content, str):
                content = str(content)

            if role in ("user", "assistant", "system"):
                payload.append({"role": role, "content": content})
            else:
                # Fallback unknown roles to user to avoid API errors
                payload.append({"role": "user", "content": content})

        resp = client.chat.completions.create(
            messages=payload,
            model=MODEL_NAME,
            max_tokens=1024,
            temperature=0.7,
            top_p=1,
            stream=False,
        )

        # Defensive extraction
        if not getattr(resp, "choices", None):
            logger.warning("[Groq] Empty choices in response")
            return "Sorry, I couldn't generate a response."

        content = getattr(resp.choices[0].message, "content", "") or ""
        text = content.strip()
        return text if text else "Sorry, I couldn't generate a response."

    except Exception as e:
        logger.error("[Groq] Generation failed: %s", e)
        return "Sorry, I couldn't process your request (Groq error)."
      

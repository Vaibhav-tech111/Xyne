# services/gemini_service.py
import os
import logging
from typing import List, Dict

import google.generativeai as genai

# Setup logger
logger = logging.getLogger(__name__)

# Validate API key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    logger.error("[Gemini] GEMINI_API_KEY not set")
    model = None
else:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-2.0-flash")  # ✅ Correct model name
        logger.info("[Gemini] Model loaded: gemini-2.0-flash")
    except Exception as e:
        logger.error("[Gemini] Failed to initialize model: %s", e)
        model = None


def chat(messages: List[Dict[str, str]]) -> str:
    """
    messages: list of dicts with keys 'role' and 'content'
    Returns generated text response.
    """
    if not model:
        logger.warning("[Gemini] Model not available")
        return "Sorry, the AI service is currently unavailable."

    try:
        history = []
        for m in messages:
            role = m.get("role")
            content = m.get("content", "")
            if role == "user":
                history.append({"role": "user", "parts": [content]})
            elif role == "assistant":
                history.append({"role": "model", "parts": [content]})
            elif role == "system":
                history.append({"role": "user", "parts": [f"[System] {content}"]})

        # Start chat with all but last message
        chat_session = model.start_chat(history=history[:-1])
        # Send the latest user message
        response = chat_session.send_message(messages[-1]["content"])
        return response.text.strip()

    except Exception as e:
        logger.error("[Gemini] Generation failed: %s", e)
        return "Sorry, I couldn't process your request."

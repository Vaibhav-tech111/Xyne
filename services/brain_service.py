# services/brain_service.py
import os
import json
import re
from typing import List

# Load rules once at import time
RULES_PATH = os.path.join(os.path.dirname(__file__), "..", "brain_rules.json")
try:
    with open(RULES_PATH, encoding="utf-8") as f:
        BRAIN_RULES = json.load(f)
except FileNotFoundError:
    print(f"[brain_service] Rules file not found: {RULES_PATH}")
    BRAIN_RULES = {"keywords": {}}
except Exception as e:
    print(f"[brain_service] Failed to load rules: {e}")
    BRAIN_RULES = {"keywords": {}}

KEYWORD_MAP = BRAIN_RULES.get("keywords", {})
SEARCH_KEYWORDS = {"search", "find", "look up", "google", "duckduckgo"}

def pick_model(prompt: str) -> str:
    """
    Choose the most appropriate AI model based on keywords in the prompt.
    Returns one of: gemini, groq, hf, pollinations
    """
    prompt_l = prompt.lower()
    for keyword, model in KEYWORD_MAP.items():
        if re.search(rf"\b{re.escape(keyword)}\b", prompt_l):
            return model
    return "gemini"  # default

def should_search(prompt: str) -> bool:
    """Return True if the prompt contains search triggers."""
    prompt_l = prompt.lower()
    return any(word in prompt_l for word in SEARCH_KEYWORDS)

def extract_query(prompt: str) -> str:
    """Strip search verbs to get the real query."""
    pattern = r"\b(search|find|look up|google|duckduckgo)\b"
    cleaned = re.sub(pattern, "", prompt, flags=re.IGNORECASE).strip()
    # Remove extra spaces
    return re.sub(r"\s+", " ", cleaned)

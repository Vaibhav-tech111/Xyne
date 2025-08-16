# core/env_health.py

import os
import logging
from typing import Dict, Any, Tuple, Optional
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

# Declare what you expect in the environment
REQUIRED_VARS = [
    "GEMINI_API_KEY",
    "GROQ_API_KEY",
    "HF_API_KEY",
]

OPTIONAL_VARS = [
    "GEMINI_MODEL",
    "GROQ_MODEL",
    "HF_MODEL",
    "HF_TIMEOUT",
    "POLLINATIONS_TEXT_URL",
    "POLLINATIONS_IMAGE_URL",
    "REDIS_URL",
    "PORT",
    "ENV",
]


def _mask_secret(value: Optional[str], keep: int = 4) -> str:
    if not value:
        return "<empty>"
    v = str(value)
    if len(v) <= keep:
        return "*" * len(v)
    return f"{'*' * (len(v) - keep)}{v[-keep:]}"


def _is_valid_http_url(value: str) -> bool:
    try:
        u = urlparse(value)
        return u.scheme in ("http", "https") and bool(u.netloc)
    except Exception:
        return False


def _is_valid_redis_url(value: str) -> bool:
    try:
        u = urlparse(value)
        return u.scheme.startswith("redis") and bool(u.netloc)
    except Exception:
        return False


def _as_int(value: Optional[str]) -> Tuple[bool, Optional[int]]:
    try:
        if value is None or value == "":
            return True, None
        return True, int(value)
    except Exception:
        return False, None


def collect_env_report() -> Dict[str, Any]:
    """
    Gather a structured report of env status without throwing.
    """
    env_mode = os.getenv("ENV", "development")

    # Required keys presence
    required: Dict[str, Dict[str, Any]] = {}
    for k in REQUIRED_VARS:
        val = os.getenv(k)
        required[k] = {
            "present": bool(val),
            "value_preview": _mask_secret(val) if val else "<missing>",
        }

    # Optional keys with lightweight validation
    optional: Dict[str, Dict[str, Any]] = {}
    for k in OPTIONAL_VARS:
        val = os.getenv(k)
        entry: Dict[str, Any] = {
            "present": val is not None,
            "value_preview": val if val and k not in ("HF_MODEL", "GEMINI_MODEL", "GROQ_MODEL") else (val or "<unset>"),
        }

        if k in ("POLLINATIONS_TEXT_URL", "POLLINATIONS_IMAGE_URL"):
            entry["valid_url"] = _is_valid_http_url(val) if val else True

        if k == "REDIS_URL":
            entry["valid_url"] = _is_valid_redis_url(val) if val else True

        if k in ("HF_TIMEOUT", "PORT"):
            ok, num = _as_int(val)
            entry["valid_int"] = ok
            if ok and num is not None:
                entry["int_value"] = num
                if k == "HF_TIMEOUT":
                    entry["valid_range"] = num > 0
                if k == "PORT":
                    entry["valid_range"] = 1 <= num <= 65535

        optional[k] = entry

    ok_required = all(v["present"] for v in required.values())
    ok_urls = all(
        v.get("valid_url", True)
        for v in optional.values()
    )
    ok_ints = all(
        v.get("valid_int", True) and v.get("valid_range", True)
        for v in optional.values()
    )

    overall_ok = ok_required and ok_urls and ok_ints

    return {
        "env": env_mode,
        "ok": overall_ok,
        "ok_required": ok_required,
        "ok_urls": ok_urls,
        "ok_ints": ok_ints,
        "required": required,
        "optional": optional,
    }


def log_env_report(level: int = logging.INFO) -> Dict[str, Any]:
    """
    Build and log a concise report with redacted secrets.
    """
    rpt = collect_env_report()

    logger.log(level, "ENV mode: %s", rpt["env"])
    logger.log(level, "Required vars OK: %s", rpt["ok_required"])
    for k, v in rpt["required"].items():
        logger.log(
            level,
            " - %s: present=%s, value=%s",
            k, v["present"], v["value_preview"]
        )

    logger.log(level, "Optional vars checks: urls_ok=%s, ints_ok=%s",
               rpt["ok_urls"], rpt["ok_ints"])
    for k, v in rpt["optional"].items():
        msg = f"present={v['present']}, value={v['value_preview']}"
        if "valid_url" in v:
            msg += f", valid_url={v['valid_url']}"
        if "valid_int" in v:
            msg += f", valid_int={v['valid_int']}"
        if "valid_range" in v:
            msg += f", valid_range={v['valid_range']}"
        logger.log(level, " - %s: %s", k, msg)

    logger.log(level, "Overall ENV health ok=%s", rpt["ok"])
    return rpt


def ensure_env(strict: bool = True) -> None:
    """
    Fail fast (in production) if required keys are missing or invalid.
    """
    rpt = collect_env_report()
    if not strict:
        return

    problems = []

    if not rpt["ok_required"]:
        missing = [k for k, v in rpt["required"].items() if not v["present"]]
        problems.append(f"Missing required: {', '.join(missing)}")

    bad_urls = [
        k for k, v in rpt["optional"].items()
        if ("valid_url" in v and not v["valid_url"])
    ]
    if bad_urls:
        problems.append(f"Invalid URLs: {', '.join(bad_urls)}")

    bad_ints = [
        k for k, v in rpt["optional"].items()
        if (("valid_int" in v and not v["valid_int"]) or ("valid_range" in v and not v["valid_range"]))
    ]
    if bad_ints:
        problems.append(f"Invalid integers: {', '.join(bad_ints)}")

    if problems:
        msg = "ENV health check failed: " + " | ".join(problems)
        # Log a redacted report for context
        log_env_report(level=logging.ERROR)
        raise RuntimeError(msg)

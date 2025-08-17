# core/config.py

import os
from typing import Optional

from dotenv import load_dotenv
from pydantic import (
    BaseSettings,  # For Pydantic v1
    BaseModel,
    Field,
    AnyHttpUrl,
    AnyUrl,
    validator  # Pydantic v1 validator
)

# ✅ Load the correct .env file before Pydantic reads anything
ENV = os.getenv("ENV", "development")
load_dotenv(f".env.{ENV}", override=True)


class ApiKeys(BaseModel):
    gemini: Optional[str] = Field(None, env="GEMINIAPIKEY")
    groq:   Optional[str] = Field(None, env="GROQAPIKEY")
    hf:     Optional[str] = Field(None, env="HFAPIKEY")

    @validator("*", pre=True)
    def require_unless_test(cls, v, field):
        if ENV != "test" and not v:
            raise ValueError(f"{field.name.upper()} must be set in '{ENV}' mode")
        return v


class Models(BaseModel):
    gemini:  str = Field("gemini-2.0-flash", env="GEMINI_MODEL")
    groq:    str = Field("llama-3.3-70b-versatile", env="GROQ_MODEL")
    hf:      str = Field("HuggingFaceH4/zephyr-7b-beta", env="HF_MODEL")
    timeout: int = Field(30, env="HF_TIMEOUT")


class PollinationsConfig(BaseModel):
    text_url:  AnyHttpUrl = Field(
        "https://text.pollinations.ai/", env="POLLINATIONSTEXTURL"
    )
    image_url: AnyHttpUrl = Field(
        "https://image.pollinations.ai/prompt/", env="POLLINATIONSIMAGEURL"
    )


class Settings(BaseSettings):
    api_keys:     ApiKeys            = ApiKeys()
    models:       Models             = Models()
    pollinations: PollinationsConfig = PollinationsConfig()

    redisurl: AnyUrl = Field("redis://localhost:6379", env="REDISURL")
    host:     str    = Field("0.0.0.0", env="HOST")
    port:     int    = Field(8000, env="PORT")
    env:      str    = Field(ENV, env="ENV")

    class Config:
        env_file = None  # dotenv already loaded manually
        case_sensitive = False


settings = Settings()

# core/config.py

import os
from typing import Optional

from dotenv import load_dotenv
from pydantic import (
    BaseModel,
    Field,
    AnyHttpUrl,
    AnyUrl,
    field_validator  # Pydantic v2
)
from pydantic_settings import BaseSettings  # ✅ New import for Pydantic v2

# Load the correct .env file before Pydantic reads anything
ENV = os.getenv("ENV", "development")
load_dotenv(f".env.{ENV}", override=True)


class ApiKeys(BaseModel):
    gemini: Optional[str] = Field(default=None, validation_alias="GEMINIAPIKEY")
    groq:   Optional[str] = Field(default=None, validation_alias="GROQAPIKEY")
    hf:     Optional[str] = Field(default=None, validation_alias="HFAPIKEY")

    @field_validator("*", mode="before")
    @classmethod
    def require_unless_test(cls, v, info):
        if ENV != "test" and not v:
            raise ValueError(f"{info.field_name.upper()} must be set in '{ENV}' mode")
        return v


class Models(BaseModel):
    gemini:  str = Field(default="gemini-2.0-flash", validation_alias="GEMINI_MODEL")
    groq:    str = Field(default="llama-3.3-70b-versatile", validation_alias="GROQ_MODEL")
    hf:      str = Field(default="HuggingFaceH4/zephyr-7b-beta", validation_alias="HF_MODEL")
    timeout: int = Field(default=30, validation_alias="HF_TIMEOUT")


class PollinationsConfig(BaseModel):
    text_url:  AnyHttpUrl = Field(default="https://text.pollinations.ai/", validation_alias="POLLINATIONSTEXTURL")
    image_url: AnyHttpUrl = Field(default="https://image.pollinations.ai/prompt/", validation_alias="POLLINATIONSIMAGEURL")


class Settings(BaseSettings):
    api_keys:     ApiKeys            = ApiKeys()
    models:       Models             = Models()
    pollinations: PollinationsConfig = PollinationsConfig()

    redisurl: AnyUrl = Field(default="redis://localhost:6379", validation_alias="REDISURL")
    host:     str    = Field(default="0.0.0.0", validation_alias="HOST")
    port:     int    = Field(default=8000, validation_alias="PORT")
    env:      str    = Field(default=ENV, validation_alias="ENV")

    model_config = {
        "case_sensitive": False,
        "env_file": None  # dotenv already loaded manually
    }


settings = Settings()

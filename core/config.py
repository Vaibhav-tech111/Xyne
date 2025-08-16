core/config.py

import os
from typing import Optional

from dotenv import load_dotenv
from pydantic import (
    BaseSettings,
    BaseModel,
    Field,
    AnyHttpUrl,
    AnyUrl,
    field_validator,
)

1) Load the correct .env file before Pydantic reads anything
ENV = os.getenv("ENV", "development")
load_dotenv(f".env.{ENV}", override=True)

class ApiKeys(BaseModel):
    gemini: Optional[str] = Field(None, env="GEMINIAPIKEY")
    groq:   Optional[str] = Field(None, env="GROQAPIKEY")
    hf:     Optional[str] = Field(None, env="HFAPIKEY")

    # Pydantic v2 style: validate all fields before assignment
    @field_validator("*", mode="before")
    def requireunlesstest(cls, v, info):
        if ENV != "test" and not v:
            raise ValueError(f"{info.field_name.upper()} must be set in '{ENV}' mode")
        return v


class Models(BaseModel):
    gemini:  str = Field("gemini-2.0-flash", env="GEMINI_MODEL")
    groq:    str = Field("llama-3.3-70b-versatile", env="GROQ_MODEL")
    hf:      str = Field("HuggingFaceH4/zephyr-7b-beta", env="HF_MODEL")
    timeout: int = Field(30, env="HF_TIMEOUT")


class PollinationsConfig(BaseModel):
    text_url:  AnyHttpUrl = Field(
        "https://text.pollinations.ai/", env="POLLINATIONSTEXTURL"  # ✅ Fixed - No trailing space
    )
    image_url: AnyHttpUrl = Field(
        "https://image.pollinations.ai/prompt/", env="POLLINATIONSIMAGEURL"  # ✅ Fixed - No trailing space
    )


class Settings(BaseSettings):
    api_keys:     ApiKeys            = ApiKeys()
    models:       Models             = Models()
    pollinations: PollinationsConfig = PollinationsConfig()

    # Use AnyUrl so non-http schemes like redis:// pass validation
    redisurl: AnyUrl = Field("redis://localhost:6379", env="REDISURL")

    host: str = Field("0.0.0.0", env="HOST")
    port: int = Field(8000,    env="PORT")
    env:  str = Field(ENV,      env="ENV")

    class Config:
        # We've already loaded dotenv manually, so disable automatic env_file
        env_file = None
        case_sensitive = False


settings = Settings()

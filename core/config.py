core/config.py

import os
from typing import Optional

from dotenv import load_dotenv
from pydantic import (
    BaseSettings, # Note: For Pydantic v2, consider using pydantic_settings.BaseSettings
    BaseModel,
    Field,
    AnyHttpUrl,
    AnyUrl,
    # For Pydantic v2, use field_validator. For v1, use validator.
    # field_validator, # Pydantic v2
    validator # Pydantic v1
)

1) Load the correct .env file before Pydantic reads anything
ENV = os.getenv("ENV", "development")
load_dotenv(f".env.{ENV}", override=True)


class ApiKeys(BaseModel):
    # Corrected env variable names to match standard format
    gemini: Optional[str] = Field(None, env="GEMINIAPIKEY")
    groq:   Optional[str] = Field(None, env="GROQAPIKEY")
    hf:     Optional[str] = Field(None, env="HFAPIKEY")

    # Pydantic v1 style validator (adjust decorator if using v2)
    # @field_validator("*", mode="before") # Pydantic v2 syntax
    @validator("*", pre=True) # Pydantic v1 syntax
    def requireunlesstest(cls, v, field): # Pydantic v1: field; v2: info
        if ENV != "test" and not v:
            # Pydantic v1: field.name; v2: info.field_name
            raise ValueError(f"{field.name.upper()} must be set in '{ENV}' mode")
        return v


class Models(BaseModel):
    gemini:  str = Field("gemini-2.0-flash", env="GEMINI_MODEL")
    groq:    str = Field("llama-3.3-70b-versatile", env="GROQ_MODEL")
    hf:      str = Field("HuggingFaceH4/zephyr-7b-beta", env="HF_MODEL")
    timeout: int = Field(30, env="HF_TIMEOUT")


class PollinationsConfig(BaseModel):
    # ✅ Fixed: Removed trailing spaces from default URLs
    text_url:  AnyHttpUrl = Field(
        "https://text.pollinations.ai/", env="POLLINATIONSTEXTURL"
    )
    image_url: AnyHttpUrl = Field(
        "https://image.pollinations.ai/prompt/", env="POLLINATIONSIMAGEURL"
    )


class Settings(BaseSettings): # Consider pydantic_settings.BaseSettings for Pydantic v2
    api_keys:     ApiKeys            = ApiKeys()
    models:       Models             = Models()
    pollinations: PollinationsConfig = PollinationsConfig()

    # ✅ Fixed: Corrected field name and env variable name
    redisurl: AnyUrl = Field("redis://localhost:6379", env="REDISURL")

    host: str = Field("0.0.0.0", env="HOST")
    port: int = Field(8000,    env="PORT")
    env:  str = Field(ENV,      env="ENV") # Use the loaded ENV variable

    class Config:
        # We've already loaded dotenv manually, so disable automatic env_file
        env_file = None
        case_sensitive = False


settings = Settings()

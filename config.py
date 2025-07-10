from pydantic import BaseSettings, Field


class GroqSettings(BaseSettings):
    api_key: str = Field(..., env="GROQ_API_KEY")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


settings = GroqSettings()

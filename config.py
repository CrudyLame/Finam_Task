from pydantic import BaseSettings, Field

class OpenAISettings(BaseSettings):
    api_key: str = Field(..., env="OPENAI_API_KEY")
    model: str = Field(default="gpt-4o-mini", env="OPENAI_MODEL")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, env="OPENAI_TEMPERATURE")
    max_tokens: int = Field(default=2000, ge=1, le=4096, env="OPENAI_MAX_TOKENS")
    top_p: float = Field(default=1.0, ge=0.0, le=1.0, env="OPENAI_TOP_P")
    frequency_penalty: float = Field(default=0.0, ge=-2.0, le=2.0, env="OPENAI_FREQUENCY_PENALTY")
    presence_penalty: float = Field(default=0.0, ge=-2.0, le=2.0, env="OPENAI_PRESENCE_PENALTY")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

settings = OpenAISettings()
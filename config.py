from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    openai_api_key: str = "ollama"
    openai_base_url: str = "http://localhost:11434/v1"
    model_name: str = "llama3.2"

    concurrent_users: int = 20
    requests_per_user: int = 5
    test_prompt: str = "Reply with exactly one sentence about Python."

    class Config:
        env_file = ".env"

settings = Settings()
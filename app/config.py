from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://postgres:postgres@localhost:5432/payments"
    # Fallback to in-memory when USE_MEMORY_STORE=true (Day 2 mode)
    use_memory_store: bool = False

    class Config:
        env_file = ".env"


settings = Settings()

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    tushare_token: str
    database_url: str = "postgresql://valuegraph:valuegraph123@postgres:5432/valuegraph"
    redis_url: str = "redis://redis:6379/0"
    
    class Config:
        env_file = ".env"

settings = Settings()

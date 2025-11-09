from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "MGX MVP"
    API_V1_STR: str = "/api/v1"
    
    # Redis configuration
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    
    @property
    def REDIS_URL(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}"

    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()
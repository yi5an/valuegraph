"""
配置管理模块
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """应用配置"""
    
    # 应用基础配置
    app_name: str = "ValueGraph"
    app_version: str = "1.0.0"
    debug: bool = True
    
    # 数据库配置
    database_url: str = "sqlite:///./valuegraph.db"
    
    # Redis 配置
    redis_url: str = "redis://localhost:6379/0"
    redis_enabled: bool = False  # MVP 阶段默认关闭
    
    # 缓存配置
    cache_ttl: int = 3600  # 1小时
    
    # API 配置
    api_prefix: str = "/api"
    
    # 限流配置
    rate_limit_enabled: bool = True
    rate_limit_per_minute: int = 60
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"


# 全局配置实例
settings = Settings()

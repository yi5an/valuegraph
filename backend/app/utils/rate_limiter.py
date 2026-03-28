"""
API 限流器
"""
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.config import settings


# 创建限流器实例
limiter = Limiter(
    key_func=get_remote_address,
    enabled=settings.rate_limit_enabled,
    default_limits=[f"{settings.rate_limit_per_minute}/minute"]
)


__all__ = ["limiter", "RateLimitExceeded"]

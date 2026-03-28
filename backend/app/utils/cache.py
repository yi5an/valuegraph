"""
Redis 缓存工具
"""
import json
from typing import Optional, Any
import redis
from app.config import settings


class CacheService:
    """缓存服务"""
    
    def __init__(self):
        """初始化缓存"""
        self.enabled = settings.redis_enabled
        self.client = None
        
        if self.enabled:
            try:
                self.client = redis.from_url(settings.redis_url, decode_responses=True)
                # 测试连接
                self.client.ping()
            except Exception as e:
                print(f"⚠️ Redis 连接失败: {e}")
                self.enabled = False
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        if not self.enabled or not self.client:
            return None
        
        try:
            value = self.client.get(key)
            if value:
                return json.loads(value)
        except Exception as e:
            print(f"⚠️ 缓存读取失败: {e}")
        
        return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """设置缓存"""
        if not self.enabled or not self.client:
            return False
        
        try:
            ttl = ttl or settings.cache_ttl
            self.client.setex(key, ttl, json.dumps(value, ensure_ascii=False))
            return True
        except Exception as e:
            print(f"⚠️ 缓存写入失败: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """删除缓存"""
        if not self.enabled or not self.client:
            return False
        
        try:
            self.client.delete(key)
            return True
        except Exception as e:
            print(f"⚠️ 缓存删除失败: {e}")
            return False


# 全局缓存实例
cache = CacheService()

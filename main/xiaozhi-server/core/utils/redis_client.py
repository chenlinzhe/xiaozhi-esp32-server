"""
Redis客户端工具类
"""

import json
import redis
import asyncio
from typing import Optional, Any, Dict
from config.logger import setup_logging


class RedisClient:
    """Redis客户端工具类"""
    
    def __init__(self, host: str = "localhost", port: int = 6379, 
                 password: str = None, db: int = 0):
        """初始化Redis客户端
        
        Args:
            host: Redis服务器地址
            port: Redis服务器端口
            password: Redis密码
            db: Redis数据库编号
        """
        self.logger = setup_logging()
        self.redis_client = redis.Redis(
            host=host,
            port=port,
            password=password,
            db=db,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5
        )
        
        # 测试连接
        try:
            self.redis_client.ping()
            self.logger.info("Redis连接成功")
        except Exception as e:
            self.logger.error(f"Redis连接失败: {e}")
            raise
    
    def set_chat_status(self, user_id: str, status: str, expire_seconds: int = 1800) -> bool:
        """设置用户聊天状态
        
        Args:
            user_id: 用户ID
            status: 聊天状态 ("teaching_mode" 或 "free_mode")
            expire_seconds: 过期时间（秒），默认30分钟
            
        Returns:
            bool: 设置是否成功
        """
        try:
            key = f"setting:chat_status:{user_id}"
            self.redis_client.setex(key, expire_seconds, status)
            self.logger.info(f"设置用户 {user_id} 聊天状态为: {status}")
            return True
        except Exception as e:
            self.logger.error(f"设置聊天状态失败: {e}")
            return False
    
    def get_chat_status(self, user_id: str) -> Optional[str]:
        """获取用户聊天状态
        
        Args:
            user_id: 用户ID
            
        Returns:
            str: 聊天状态，如果不存在返回None
        """
        try:
            key = f"setting:chat_status:{user_id}"
            status = self.redis_client.get(key)
            if status:
                self.logger.info(f"获取用户 {user_id} 聊天状态: {status}")
            return status
        except Exception as e:
            self.logger.error(f"获取聊天状态失败: {e}")
            return None
    
    def delete_chat_status(self, user_id: str) -> bool:
        """删除用户聊天状态
        
        Args:
            user_id: 用户ID
            
        Returns:
            bool: 删除是否成功
        """
        try:
            key = f"setting:chat_status:{user_id}"
            result = self.redis_client.delete(key)
            if result:
                self.logger.info(f"删除用户 {user_id} 聊天状态成功")
            return bool(result)
        except Exception as e:
            self.logger.error(f"删除聊天状态失败: {e}")
            return False
    
    def set_session_data(self, session_id: str, data: Dict[str, Any], 
                        expire_seconds: int = 1800) -> bool:
        """设置会话数据
        
        Args:
            session_id: 会话ID
            data: 会话数据
            expire_seconds: 过期时间（秒）
            
        Returns:
            bool: 设置是否成功
        """
        try:
            key = f"session:{session_id}"
            self.redis_client.setex(key, expire_seconds, json.dumps(data))
            return True
        except Exception as e:
            self.logger.error(f"设置会话数据失败: {e}")
            return False
    
    def get_session_data(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话数据
        
        Args:
            session_id: 会话ID
            
        Returns:
            Dict: 会话数据，如果不存在返回None
        """
        try:
            key = f"session:{session_id}"
            data = self.redis_client.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            self.logger.error(f"获取会话数据失败: {e}")
            return None
    
    def delete_session_data(self, session_id: str) -> bool:
        """删除会话数据
        
        Args:
            session_id: 会话ID
            
        Returns:
            bool: 删除是否成功
        """
        try:
            key = f"session:{session_id}"
            result = self.redis_client.delete(key)
            return bool(result)
        except Exception as e:
            self.logger.error(f"删除会话数据失败: {e}")
            return False


# 全局Redis客户端实例
_redis_client = None


def get_redis_client() -> RedisClient:
    """获取Redis客户端实例（单例模式）"""
    global _redis_client
    if _redis_client is None:
        # 从配置文件获取Redis配置
        from config.config_loader import load_config
        config = load_config()
        
        redis_config = config.get("redis", {})
        _redis_client = RedisClient(
            host=redis_config.get("host", "localhost"),
            port=redis_config.get("port", 6379),
            password=redis_config.get("password"),
            db=redis_config.get("db", 0)
        )
    return _redis_client

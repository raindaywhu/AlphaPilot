"""
qlib 单例管理器

解决 qlib.init() 在多线程环境下重复调用的问题。
使用线程安全的单例模式，确保 qlib 只初始化一次。
"""

import threading
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class QlibManager:
    """
    qlib 单例管理器
    
    使用线程锁确保 qlib.init() 只调用一次。
    所有需要使用 qlib 的代码都应该通过此管理器获取 qlib 实例。
    """
    
    _instance: Optional['QlibManager'] = None
    _lock = threading.Lock()
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def initialize(cls, provider_uri: str = "~/.qlib/qlib_data/cn_data") -> bool:
        """
        初始化 qlib（线程安全）
        
        Args:
            provider_uri: qlib 数据路径
            
        Returns:
            bool: True 表示首次初始化，False 表示已初始化
        """
        if cls._initialized:
            logger.debug("qlib 已初始化，跳过重复调用")
            return False
        
        with cls._lock:
            if cls._initialized:
                logger.debug("qlib 已初始化，跳过重复调用")
                return False
            
            try:
                import qlib
                qlib.init(provider_uri=provider_uri)
                cls._initialized = True
                logger.info(f"qlib 初始化成功: {provider_uri}")
                return True
            except Exception as e:
                logger.error(f"qlib 初始化失败: {e}")
                raise
    
    @classmethod
    def is_initialized(cls) -> bool:
        """检查 qlib 是否已初始化"""
        return cls._initialized
    
    @classmethod
    def reset(cls):
        """重置初始化状态（仅用于测试）"""
        with cls._lock:
            cls._initialized = False
            logger.info("qlib 初始化状态已重置")


# 便捷函数
def ensure_qlib_initialized(provider_uri: str = "~/.qlib/qlib_data/cn_data") -> bool:
    """
    确保 qlib 已初始化
    
    这是推荐的调用方式，线程安全且幂等。
    
    Args:
        provider_uri: qlib 数据路径
        
    Returns:
        bool: True 表示首次初始化，False 表示已初始化
    """
    return QlibManager.initialize(provider_uri)
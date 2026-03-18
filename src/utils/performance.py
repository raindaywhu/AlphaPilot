"""
性能优化工具

提供缓存、计时、连接复用等优化功能

Issue: #25 (OPT-001)
"""

import os
import json
import time
import logging
from functools import wraps, lru_cache
from typing import Dict, Any, Optional, Callable
from datetime import datetime, timedelta

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# =====================
# 计时装饰器
# =====================

def timing_decorator(func: Callable) -> Callable:
    """
    计时装饰器，记录函数执行时间
    
    Usage:
        @timing_decorator
        def my_function():
            pass
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        elapsed_time = time.time() - start_time
        
        # 添加执行时间到结果
        if isinstance(result, dict):
            result["_execution_time"] = f"{elapsed_time:.2f}s"
        
        logger.info(f"⏱️ {func.__name__} 执行耗时: {elapsed_time:.2f}s")
        return result
    
    return wrapper


# =====================
# 数据缓存
# =====================

class DataCache:
    """
    数据缓存管理器
    
    使用 LRU 缓存策略，支持过期时间设置
    """
    
    _instance = None
    
    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._cache = {}
            cls._instance._timestamps = {}
        return cls._instance
    
    def get(self, key: str, max_age_seconds: int = 3600) -> Optional[Any]:
        """
        获取缓存数据
        
        Args:
            key: 缓存键
            max_age_seconds: 最大缓存时间（秒），默认 1 小时
        
        Returns:
            缓存数据，如果不存在或过期则返回 None
        """
        if key not in self._cache:
            return None
        
        # 检查是否过期
        timestamp = self._timestamps.get(key, 0)
        if time.time() - timestamp > max_age_seconds:
            logger.info(f"🗑️ 缓存过期: {key}")
            del self._cache[key]
            del self._timestamps[key]
            return None
        
        logger.info(f"✅ 缓存命中: {key}")
        return self._cache[key]
    
    def set(self, key: str, value: Any) -> None:
        """
        设置缓存数据
        
        Args:
            key: 缓存键
            value: 缓存值
        """
        self._cache[key] = value
        self._timestamps[key] = time.time()
        logger.info(f"💾 缓存存储: {key}")
    
    def clear(self) -> None:
        """清空缓存"""
        self._cache.clear()
        self._timestamps.clear()
        logger.info("🗑️ 缓存已清空")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        return {
            "cache_size": len(self._cache),
            "keys": list(self._cache.keys()),
            "oldest_entry": min(self._timestamps.values()) if self._timestamps else None
        }


# 全局缓存实例
_cache = DataCache()


def cached(key_prefix: str, max_age_seconds: int = 3600):
    """
    缓存装饰器
    
    Usage:
        @cached("stock_data", max_age_seconds=300)
        def get_stock_data(stock_code: str):
            return fetch_data(stock_code)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 生成缓存键
            args_str = "_".join(str(arg) for arg in args)
            kwargs_str = "_".join(f"{k}={v}" for k, v in sorted(kwargs.items()))
            cache_key = f"{key_prefix}:{args_str}:{kwargs_str}"
            
            # 尝试从缓存获取
            cached_result = _cache.get(cache_key, max_age_seconds)
            if cached_result is not None:
                return cached_result
            
            # 执行函数
            result = func(*args, **kwargs)
            
            # 存入缓存
            _cache.set(cache_key, result)
            
            return result
        
        return wrapper
    
    return decorator


# =====================
# 连接复用
# =====================

class ConnectionPool:
    """
    连接池管理器
    
    复用 mootdx、数据库等连接
    """
    
    _instance = None
    _connections = {}
    
    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def get_mootdx_client(self):
        """获取 mootdx 客户端（复用连接）"""
        if 'mootdx' not in self._connections:
            logger.info("🔌 创建新的 mootdx 连接")
            os.environ['http_proxy'] = ''
            os.environ['https_proxy'] = ''
            from mootdx.quotes import Quotes
            self._connections['mootdx'] = Quotes.factory(market='std')
        else:
            logger.info("♻️ 复用 mootdx 连接")
        return self._connections['mootdx']
    
    def close_all(self):
        """关闭所有连接"""
        self._connections.clear()
        logger.info("🔌 所有连接已关闭")


# 全局连接池实例
_connection_pool = ConnectionPool()


def get_shared_mootdx_client():
    """获取共享的 mootdx 客户端"""
    return _connection_pool.get_mootdx_client()


# =====================
# 性能监控
# =====================

class PerformanceMonitor:
    """
    性能监控器
    
    记录各模块的执行时间统计
    """
    
    _instance = None
    
    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._metrics = {}
        return cls._instance
    
    def record(self, module: str, operation: str, duration: float) -> None:
        """
        记录执行时间
        
        Args:
            module: 模块名称
            operation: 操作名称
            duration: 执行时间（秒）
        """
        key = f"{module}.{operation}"
        if key not in self._metrics:
            self._metrics[key] = {
                "count": 0,
                "total_time": 0,
                "avg_time": 0,
                "min_time": float('inf'),
                "max_time": 0
            }
        
        metrics = self._metrics[key]
        metrics["count"] += 1
        metrics["total_time"] += duration
        metrics["avg_time"] = metrics["total_time"] / metrics["count"]
        metrics["min_time"] = min(metrics["min_time"], duration)
        metrics["max_time"] = max(metrics["max_time"], duration)
    
    def get_report(self) -> Dict[str, Any]:
        """获取性能报告"""
        return {
            "metrics": self._metrics,
            "generated_at": datetime.now().isoformat()
        }
    
    def get_summary(self) -> str:
        """获取性能摘要"""
        lines = ["📊 性能统计报告", "=" * 50]
        
        for key, metrics in sorted(self._metrics.items()):
            lines.append(
                f"  {key}: "
                f"次数={metrics['count']}, "
                f"平均={metrics['avg_time']:.2f}s, "
                f"最小={metrics['min_time']:.2f}s, "
                f"最大={metrics['max_time']:.2f}s"
            )
        
        return "\n".join(lines)


# 全局性能监控实例
_performance_monitor = PerformanceMonitor()


def monitor_performance(module: str):
    """
    性能监控装饰器
    
    Usage:
        @monitor_performance("mootdx_tool")
        def analyze(self, stock_code: str):
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            
            _performance_monitor.record(module, func.__name__, duration)
            
            return result
        
        return wrapper
    
    return decorator


# =====================
# 便捷函数
# =====================

def get_cache_stats() -> Dict[str, Any]:
    """获取缓存统计"""
    return _cache.get_stats()


def get_performance_report() -> Dict[str, Any]:
    """获取性能报告"""
    return _performance_monitor.get_report()


def print_performance_summary() -> None:
    """打印性能摘要"""
    print(_performance_monitor.get_summary())


def clear_cache() -> None:
    """清空缓存"""
    _cache.clear()


# =====================
# 测试
# =====================

def main():
    """测试性能优化工具"""
    print("=" * 60)
    print("性能优化工具测试")
    print("=" * 60)
    
    # 测试缓存
    print("\n1. 测试缓存")
    
    @cached("test", max_age_seconds=60)
    def expensive_operation(n: int) -> int:
        time.sleep(0.1)  # 模拟耗时操作
        return n * 2
    
    # 第一次调用（无缓存）
    start = time.time()
    result1 = expensive_operation(5)
    time1 = time.time() - start
    print(f"  第一次调用: result={result1}, time={time1:.2f}s")
    
    # 第二次调用（有缓存）
    start = time.time()
    result2 = expensive_operation(5)
    time2 = time.time() - start
    print(f"  第二次调用: result={result2}, time={time2:.2f}s (缓存命中)")
    
    # 测试计时装饰器
    print("\n2. 测试计时装饰器")
    
    @timing_decorator
    def slow_function():
        time.sleep(0.5)
        return {"status": "done"}
    
    result = slow_function()
    print(f"  结果: {result}")
    
    # 测试连接池
    print("\n3. 测试连接池")
    client1 = get_shared_mootdx_client()
    client2 = get_shared_mootdx_client()
    print(f"  客户端复用: {client1 is client2}")
    
    # 打印性能摘要
    print("\n4. 性能摘要")
    print_performance_summary()
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
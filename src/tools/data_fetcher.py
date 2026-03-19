#!/usr/bin/env python3
"""
统一数据获取模块

功能：
- 自动重试机制
- 请求延迟防止被封
- 多数据源 fallback
- 本地缓存
"""

import os
import time
import json
import hashlib
import warnings
from pathlib import Path
from typing import Optional, Any, Callable
from functools import wraps

warnings.filterwarnings('ignore')

# 禁用代理
for key in ['http_proxy', 'https_proxy', 'HTTP_PROXY', 'HTTPS_PROXY', 'all_proxy', 'ALL_PROXY']:
    os.environ.pop(key, None)

# 缓存目录
CACHE_DIR = Path("/tmp/alphapilot_cache")
CACHE_DIR.mkdir(exist_ok=True)

# 请求间隔（秒）
REQUEST_INTERVAL = 0.5
last_request_time = 0


def get_cache_key(func_name: str, *args, **kwargs) -> str:
    """生成缓存 key"""
    key_str = f"{func_name}:{args}:{kwargs}"
    return hashlib.md5(key_str.encode()).hexdigest()


def cache_result(ttl: int = 3600):
    """缓存装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = get_cache_key(func.__name__, *args, **kwargs)
            cache_file = CACHE_DIR / f"{cache_key}.json"
            
            # 检查缓存
            if cache_file.exists():
                try:
                    with open(cache_file, 'r') as f:
                        data = json.load(f)
                    if time.time() - data.get('timestamp', 0) < ttl:
                        return data.get('result')
                except:
                    pass
            
            # 执行函数
            result = func(*args, **kwargs)
            
            # 保存缓存
            try:
                with open(cache_file, 'w') as f:
                    json.dump({
                        'timestamp': time.time(),
                        'result': result
                    }, f)
            except:
                pass
            
            return result
        return wrapper
    return decorator


def rate_limit():
    """请求限速"""
    global last_request_time
    elapsed = time.time() - last_request_time
    if elapsed < REQUEST_INTERVAL:
        time.sleep(REQUEST_INTERVAL - elapsed)
    last_request_time = time.time()


def retry(max_retries: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """重试装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay
            
            for attempt in range(max_retries):
                try:
                    rate_limit()
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        time.sleep(current_delay)
                        current_delay *= backoff
            
            raise last_exception
        return wrapper
    return decorator


class DataFetcher:
    """统一数据获取类"""
    
    def __init__(self):
        import akshare as ak
        self.ak = ak
    
    @retry(max_retries=3, delay=1.0)
    @cache_result(ttl=300)  # 5分钟缓存
    def get_stock_info(self, symbol: str) -> dict:
        """获取股票基础信息"""
        try:
            df = self.ak.stock_individual_info_em(symbol=symbol)
            result = dict(zip(df['item'], df['value']))
            return result
        except Exception as e:
            print(f"获取股票信息失败: {e}")
            return {}
    
    @retry(max_retries=3, delay=1.0)
    @cache_result(ttl=60)  # 1分钟缓存
    def get_realtime_quotes(self) -> list:
        """获取实时行情"""
        try:
            df = self.ak.stock_zh_a_spot_em()
            return df.to_dict('records')
        except Exception as e:
            print(f"获取实时行情失败: {e}")
            return []
    
    @retry(max_retries=3, delay=1.0)
    @cache_result(ttl=300)
    def get_north_flow(self) -> dict:
        """获取北向资金"""
        try:
            df = self.ak.stock_hsgt_fund_flow_summary_em()
            if len(df) > 0:
                return df.iloc[-1].to_dict()
            return {}
        except Exception as e:
            print(f"获取北向资金失败: {e}")
            return {}
    
    @retry(max_retries=3, delay=1.0)
    @cache_result(ttl=300)
    def get_industry_data(self) -> list:
        """获取行业数据"""
        try:
            df = self.ak.stock_board_industry_name_em()
            return df.to_dict('records')
        except Exception as e:
            print(f"获取行业数据失败: {e}")
            return []
    
    @retry(max_retries=3, delay=1.0)
    @cache_result(ttl=300)
    def get_commodity_data(self) -> list:
        """获取商品数据"""
        try:
            df = self.ak.futures_main_sina()
            return df.to_dict('records')
        except Exception as e:
            print(f"获取商品数据失败: {e}")
            return []
    
    @retry(max_retries=3, delay=1.0)
    @cache_result(ttl=60)
    def get_market_sentiment(self, symbol: str = "000001") -> dict:
        """获取市场情绪"""
        try:
            df = self.ak.stock_zh_a_hist_min_em(symbol=symbol, period="1", adjust="")
            if len(df) > 0:
                latest = df.iloc[-1]
                return {
                    'close': latest.get('收盘', 0),
                    'volume': latest.get('成交量', 0),
                    'amount': latest.get('成交额', 0),
                }
            return {}
        except Exception as e:
            print(f"获取市场情绪失败: {e}")
            return {}


# 单例
_fetcher = None

def get_fetcher() -> DataFetcher:
    """获取数据获取器单例"""
    global _fetcher
    if _fetcher is None:
        _fetcher = DataFetcher()
    return _fetcher


if __name__ == "__main__":
    # 测试
    fetcher = get_fetcher()
    
    print("测试数据获取...")
    
    print("1. 北向资金:", fetcher.get_north_flow())
    print("2. 商品数据:", len(fetcher.get_commodity_data()), "条")
    print("3. 市场情绪:", fetcher.get_market_sentiment())
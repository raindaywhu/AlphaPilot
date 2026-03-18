"""
Qlib 数据工具

从 qlib 数据层获取 A 股行情数据。

数据流: mootdx → qlib_updater → qlib → QlibDataTool → Agent

Issue: #33 DATA-FIX
"""

import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

import qlib
from qlib.data import D
from qlib.data.dataset import DatasetH

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class QlibDataTool:
    """
    Qlib 数据工具
    
    从 qlib 数据层获取 A 股行情数据，符合设计文档的数据流架构。
    
    数据流：
    1. mootdx 获取实时数据
    2. qlib_updater 更新 qlib 数据
    3. QlibDataTool 从 qlib 获取数据
    4. Agent 使用 QlibDataTool 进行分析
    
    使用方法：
        tool = QlibDataTool()
        data = tool.get_kline_data('sh600519', days=100)
    """
    
    # qlib 标准字段映射
    QLIB_FIELDS = {
        'close': '$close',
        'open': '$open',
        'high': '$high',
        'low': '$low',
        'volume': '$volume',
        'amount': '$amount',
        'factor': '$factor',
        'change': '$change'
    }
    
    def __init__(self, provider_uri: str = '~/.qlib/qlib_data/cn_data'):
        """
        初始化 Qlib 数据工具
        
        Args:
            provider_uri: qlib 数据路径
        """
        self.provider_uri = provider_uri
        self._initialized = False
        logger.info(f"QlibDataTool 初始化: {provider_uri}")
    
    def _ensure_initialized(self):
        """确保 qlib 已初始化"""
        if not self._initialized:
            try:
                qlib.init(provider_uri=self.provider_uri)
                self._initialized = True
                logger.info("qlib 初始化成功")
            except Exception as e:
                logger.error(f"qlib 初始化失败: {e}")
                raise
    
    def get_kline_data(
        self,
        symbol: str,
        days: int = 100,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """
        获取 K 线数据
        
        Args:
            symbol: 股票代码（如 sh600519）
            days: 获取天数（如果未指定日期范围）
            start_date: 开始日期（YYYY-MM-DD）
            end_date: 结束日期（YYYY-MM-DD）
        
        Returns:
            K线数据 DataFrame
        """
        self._ensure_initialized()
        
        try:
            # 标准化股票代码
            if not symbol.startswith(('sh', 'sz')):
                symbol = symbol.lower()
                if symbol.startswith('6'):
                    symbol = f'sh{symbol}'
                else:
                    symbol = f'sz{symbol}'
            
            # 计算日期范围
            if end_date is None:
                end_date = datetime.now().strftime('%Y-%m-%d')
            if start_date is None:
                start_date = (datetime.now() - timedelta(days=days * 1.5)).strftime('%Y-%m-%d')
            
            # 获取 qlib 字段
            fields = [
                self.QLIB_FIELDS['open'],
                self.QLIB_FIELDS['close'],
                self.QLIB_FIELDS['high'],
                self.QLIB_FIELDS['low'],
                self.QLIB_FIELDS['volume']
            ]
            
            # 从 qlib 获取数据
            data = D.features(
                instruments=[symbol],
                fields=fields,
                start_time=start_date,
                end_time=end_date
            )
            
            if data is None or len(data) == 0:
                logger.warning(f"qlib 中没有 {symbol} 的数据")
                return None
            
            # 重置索引，整理列名
            df = data.reset_index()
            df.columns = ['instrument', 'datetime', 'open', 'close', 'high', 'low', 'volume']
            
            # 按日期排序
            df = df.sort_values('datetime').tail(days)
            
            logger.info(f"成功从 qlib 获取 {symbol} 的数据: {len(df)} 条")
            return df
            
        except Exception as e:
            logger.error(f"获取 qlib 数据失败: {e}")
            return None
    
    def calculate_ma(self, df: pd.DataFrame, periods: List[int] = [5, 10, 20, 60]) -> pd.DataFrame:
        """
        计算移动平均线
        
        Args:
            df: K线数据
            periods: MA 周期列表
        
        Returns:
            添加了 MA 列的 DataFrame
        """
        if df is None or len(df) == 0:
            return df
        
        for period in periods:
            df[f'MA{period}'] = df['close'].rolling(window=period).mean()
        
        return df
    
    def calculate_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        计算技术指标
        
        Args:
            df: K线数据
        
        Returns:
            添加了技术指标的 DataFrame
        """
        if df is None or len(df) == 0:
            return df
        
        # MA
        df = self.calculate_ma(df, [5, 10, 20, 60])
        
        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # MACD
        ema12 = df['close'].ewm(span=12, adjust=False).mean()
        ema26 = df['close'].ewm(span=26, adjust=False).mean()
        df['MACD'] = ema12 - ema26
        df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
        df['MACD_Hist'] = df['MACD'] - df['MACD_Signal']
        
        # Bollinger Bands
        df['BB_Middle'] = df['close'].rolling(window=20).mean()
        df['BB_Std'] = df['close'].rolling(window=20).std()
        df['BB_Upper'] = df['BB_Middle'] + 2 * df['BB_Std']
        df['BB_Lower'] = df['BB_Middle'] - 2 * df['BB_Std']
        
        return df
    
    def get_stock_info(self, symbol: str) -> Dict[str, Any]:
        """
        获取股票基本信息
        
        Args:
            symbol: 股票代码
        
        Returns:
            股票信息字典
        """
        # qlib 没有股票基本信息，这里返回基础结构
        return {
            'symbol': symbol,
            'name': 'Unknown',
            'market': 'CN'
        }
    
    def get_latest_price(self, symbol: str) -> Optional[float]:
        """
        获取最新收盘价
        
        Args:
            symbol: 股票代码
        
        Returns:
            最新收盘价
        """
        df = self.get_kline_data(symbol, days=1)
        if df is not None and len(df) > 0:
            return float(df.iloc[-1]['close'])
        return None
    
    def get_price_change(self, symbol: str, days: int = 1) -> Optional[float]:
        """
        获取价格变化百分比
        
        Args:
            symbol: 股票代码
            days: 天数
        
        Returns:
            价格变化百分比
        """
        df = self.get_kline_data(symbol, days=days + 1)
        if df is not None and len(df) >= 2:
            latest = df.iloc[-1]['close']
            previous = df.iloc[-(days + 1)]['close']
            return (latest - previous) / previous * 100
        return None


# 便捷函数
def get_kline_data(symbol: str, days: int = 100) -> pd.DataFrame:
    """获取 K 线数据（便捷函数）"""
    tool = QlibDataTool()
    return tool.get_kline_data(symbol, days)


def get_latest_price(symbol: str) -> Optional[float]:
    """获取最新价格（便捷函数）"""
    tool = QlibDataTool()
    return tool.get_latest_price(symbol)
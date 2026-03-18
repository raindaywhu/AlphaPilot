"""
Qlib 数据工具

从 qlib 数据层获取 A 股行情数据，支持回退到 mootdx。

数据流: 
1. 优先从 qlib 获取数据
2. 如果 qlib 没有数据，回退到 mootdx

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

# mootdx 回退导入
try:
    from mootdx.quotes import Quotes
    MOOTDX_AVAILABLE = True
except ImportError:
    MOOTDX_AVAILABLE = False
    logger.warning("mootdx 未安装，无法回退获取数据")


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
        
        优先从 qlib 获取，如果 qlib 没有数据则回退到 mootdx。
        
        Args:
            symbol: 股票代码（如 sh600519）
            days: 获取天数（如果未指定日期范围）
            start_date: 开始日期（YYYY-MM-DD）
            end_date: 结束日期（YYYY-MM-DD）
        
        Returns:
            K线数据 DataFrame
        """
        # 先尝试从 qlib 获取
        df = self._get_kline_from_qlib(symbol, days, start_date, end_date)
        
        if df is not None and len(df) > 0:
            return df
        
        # qlib 没有数据，回退到 mootdx
        logger.info(f"qlib 没有 {symbol} 的数据，尝试从 mootdx 获取...")
        return self._get_kline_from_mootdx(symbol, days)
    
    def _get_kline_from_qlib(
        self,
        symbol: str,
        days: int = 100,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Optional[pd.DataFrame]:
        """从 qlib 获取 K 线数据"""
        try:
            self._ensure_initialized()
            
            # 标准化股票代码
            qlib_symbol = symbol.lower()
            if not qlib_symbol.startswith(('sh', 'sz')):
                if qlib_symbol.startswith('6'):
                    qlib_symbol = f'sh{qlib_symbol}'
                else:
                    qlib_symbol = f'sz{qlib_symbol}'
            
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
                instruments=[qlib_symbol],
                fields=fields,
                start_time=start_date,
                end_time=end_date
            )
            
            if data is None or len(data) == 0:
                return None
            
            # 重置索引，整理列名
            df = data.reset_index()
            df.columns = ['instrument', 'datetime', 'open', 'close', 'high', 'low', 'volume']
            
            # 按日期排序
            df = df.sort_values('datetime').tail(days)
            
            logger.info(f"从 qlib 获取 {symbol} 的数据: {len(df)} 条")
            return df
            
        except Exception as e:
            logger.warning(f"qlib 获取数据失败: {e}")
            return None
    
    def _get_kline_from_mootdx(
        self,
        symbol: str,
        days: int = 100
    ) -> Optional[pd.DataFrame]:
        """从 mootdx 获取 K 线数据（回退方案）"""
        if not MOOTDX_AVAILABLE:
            logger.error("mootdx 不可用，无法获取数据")
            return None
        
        try:
            # 标准化股票代码
            mootdx_symbol = symbol.lower().replace('sh', '').replace('sz', '')
            market = 1 if symbol.lower().startswith('sh') or symbol.startswith('6') else 0
            
            # 创建 mootdx 客户端
            client = Quotes.factory(market='std')
            
            # 获取日K线数据
            bars = client.bars(
                code=mootdx_symbol,
                frequency=9,  # 日K
                offset=days,
                start=0
            )
            
            if bars is None or len(bars) == 0:
                logger.warning(f"mootdx 也没有 {symbol} 的数据")
                return None
            
            # 转换为 DataFrame
            df = pd.DataFrame(bars)
            
            # 重命名列
            df = df.rename(columns={
                'open': 'open',
                'close': 'close',
                'high': 'high',
                'low': 'low',
                'vol': 'volume'
            })
            
            # 添加日期列
            if 'datetime' not in df.columns:
                df['datetime'] = pd.to_datetime(df.index)
            
            # 按日期排序
            df = df.sort_values('datetime').tail(days)
            
            logger.info(f"从 mootdx 获取 {symbol} 的数据: {len(df)} 条")
            return df[['datetime', 'open', 'close', 'high', 'low', 'volume']]
            
        except Exception as e:
            logger.error(f"mootdx 获取数据失败: {e}")
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
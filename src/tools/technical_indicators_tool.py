#!/usr/bin/env python3
"""
技术指标工具

使用 mootdx 获取实时数据，计算常用技术指标
支持全 A 股

Issue: #22 (TECH-001)
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
import akshare as ak

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TechnicalIndicatorsTool:
    """
    技术指标工具
    
    使用 mootdx 获取实时行情数据，计算技术指标
    支持全 A 股
    
    使用示例：
        >>> tool = TechnicalIndicatorsTool()
        >>> indicators = tool.get_indicators('600660')
        >>> print(indicators)
    """
    
    def __init__(self):
        """初始化技术指标工具"""
        logger.info("技术指标工具初始化完成 (使用 akshare)")
    
    def get_kline_data(
        self,
        stock_code: str,
        days: int = 120
    ) -> pd.DataFrame:
        """
        获取 K 线数据
        
        Args:
            stock_code: 股票代码，如 'SH600660' 或 '600660'
            days: 获取天数
        
        Returns:
            DataFrame，包含 OHLCV 数据
        """
        # 移除前缀
        code = stock_code.replace('SH', '').replace('SZ', '').replace('sh', '').replace('sz', '')
        
        try:
            # 计算日期范围
            end_date = datetime.now().strftime('%Y%m%d')
            start_date = (datetime.now() - timedelta(days=days*2)).strftime('%Y%m%d')
            
            # 使用 akshare 获取数据
            df = ak.stock_zh_a_hist(
                symbol=code,
                period="daily",
                start_date=start_date,
                end_date=end_date,
                adjust=""  # 不复权
            )
            
            if df is None or df.empty:
                logger.warning(f"无法获取股票 {stock_code} 的 K 线数据")
                return pd.DataFrame()
            
            # 重命名列
            df = df.rename(columns={
                '开盘': 'open',
                '收盘': 'close',
                '最高': 'high',
                '最低': 'low',
                '成交量': 'volume',
                '日期': 'date'
            })
            
            # 取最近 N 天
            if len(df) > days:
                df = df.tail(days)
            
            logger.info(f"成功获取 {stock_code} 的 K 线数据: {len(df)} 天")
            return df
            
        except Exception as e:
            logger.error(f"获取 K 线数据失败: {e}")
            return pd.DataFrame()
    
    def calculate_ma(self, df: pd.DataFrame, periods: list = [5, 10, 20, 30, 60]) -> Dict[str, float]:
        """
        计算均线
        
        Args:
            df: K 线数据
            periods: 周期列表
        
        Returns:
            均线字典
        """
        result = {}
        for period in periods:
            if len(df) >= period:
                ma = df['close'].tail(period).mean()
                result[f'MA{period}'] = round(ma, 2)
        return result
    
    def calculate_macd(
        self,
        df: pd.DataFrame,
        fast: int = 12,
        slow: int = 26,
        signal: int = 9
    ) -> Dict[str, Any]:
        """
        计算 MACD
        
        Args:
            df: K 线数据
            fast: 快线周期
            slow: 慢线周期
            signal: 信号线周期
        
        Returns:
            MACD 字典
        """
        if len(df) < slow + signal:
            return {'MACD': None, 'Signal': None, 'Histogram': None}
        
        close = df['close']
        
        # 计算 EMA
        ema_fast = close.ewm(span=fast, adjust=False).mean()
        ema_slow = close.ewm(span=slow, adjust=False).mean()
        
        # 计算 MACD
        macd = ema_fast - ema_slow
        signal_line = macd.ewm(span=signal, adjust=False).mean()
        histogram = macd - signal_line
        
        return {
            'MACD': round(macd.iloc[-1], 4),
            'Signal': round(signal_line.iloc[-1], 4),
            'Histogram': round(histogram.iloc[-1], 4),
            'Trend': '多头' if histogram.iloc[-1] > 0 else '空头'
        }
    
    def calculate_rsi(self, df: pd.DataFrame, period: int = 14) -> Dict[str, Any]:
        """
        计算 RSI
        
        Args:
            df: K 线数据
            period: 周期
        
        Returns:
            RSI 字典
        """
        if len(df) < period + 1:
            return {'RSI': None, 'Signal': '数据不足'}
        
        close = df['close']
        delta = close.diff()
        
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        current_rsi = rsi.iloc[-1]
        
        # 判断信号
        if current_rsi > 70:
            signal = '超买'
        elif current_rsi < 30:
            signal = '超卖'
        else:
            signal = '正常'
        
        return {
            'RSI': round(current_rsi, 2),
            'Signal': signal
        }
    
    def calculate_kdj(
        self,
        df: pd.DataFrame,
        n: int = 9,
        m1: int = 3,
        m2: int = 3
    ) -> Dict[str, Any]:
        """
        计算 KDJ
        
        Args:
            df: K 线数据
            n: RSV 周期
            m1: K 周期
            m2: D 周期
        
        Returns:
            KDJ 字典
        """
        if len(df) < n:
            return {'K': None, 'D': None, 'J': None, 'Signal': '数据不足'}
        
        # 计算 RSV
        low_n = df['low'].rolling(window=n).min()
        high_n = df['high'].rolling(window=n).max()
        rsv = (df['close'] - low_n) / (high_n - low_n) * 100
        
        # 计算 K、D、J
        k = rsv.ewm(alpha=1/m1, adjust=False).mean()
        d = k.ewm(alpha=1/m2, adjust=False).mean()
        j = 3 * k - 2 * d
        
        current_k = k.iloc[-1]
        current_d = d.iloc[-1]
        current_j = j.iloc[-1]
        
        # 判断信号
        if current_j > 100:
            signal = '超买'
        elif current_j < 0:
            signal = '超卖'
        else:
            signal = '正常'
        
        return {
            'K': round(current_k, 2),
            'D': round(current_d, 2),
            'J': round(current_j, 2),
            'Signal': signal
        }
    
    def calculate_bollinger_bands(
        self,
        df: pd.DataFrame,
        period: int = 20,
        std_dev: int = 2
    ) -> Dict[str, Any]:
        """
        计算布林带
        
        Args:
            df: K 线数据
            period: 周期
            std_dev: 标准差倍数
        
        Returns:
            布林带字典
        """
        if len(df) < period:
            return {'Upper': None, 'Middle': None, 'Lower': None}
        
        close = df['close']
        middle = close.rolling(window=period).mean()
        std = close.rolling(window=period).std()
        
        upper = middle + std_dev * std
        lower = middle - std_dev * std
        
        current_close = close.iloc[-1]
        current_middle = middle.iloc[-1]
        
        # 判断位置
        position = (current_close - lower.iloc[-1]) / (upper.iloc[-1] - lower.iloc[-1])
        
        return {
            'Upper': round(upper.iloc[-1], 2),
            'Middle': round(current_middle, 2),
            'Lower': round(lower.iloc[-1], 2),
            'Position': round(position, 2),
            'Signal': '上轨附近' if position > 0.8 else ('下轨附近' if position < 0.2 else '中轨附近')
        }
    
    def get_indicators(self, stock_code: str) -> Dict[str, Any]:
        """
        获取所有技术指标
        
        Args:
            stock_code: 股票代码
        
        Returns:
            技术指标字典
        """
        logger.info(f"开始计算 {stock_code} 的技术指标")
        
        # 获取 K 线数据
        df = self.get_kline_data(stock_code)
        
        if df.empty:
            return {
                'error': f'无法获取 {stock_code} 的数据',
                'stock_code': stock_code
            }
        
        # 计算各项指标
        result = {
            'stock_code': stock_code,
            'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'price': {
                'current': float(df['close'].iloc[-1]),
                'high': float(df['high'].iloc[-1]),
                'low': float(df['low'].iloc[-1]),
                'volume': int(df['volume'].iloc[-1]) if 'volume' in df.columns else None
            },
            'ma': self.calculate_ma(df),
            'macd': self.calculate_macd(df),
            'rsi': self.calculate_rsi(df),
            'kdj': self.calculate_kdj(df),
            'bollinger': self.calculate_bollinger_bands(df)
        }
        
        # 生成综合信号
        signals = []
        if result['macd'].get('Trend') == '多头':
            signals.append('MACD多头')
        if result['rsi'].get('Signal') == '超卖':
            signals.append('RSI超卖')
        elif result['rsi'].get('Signal') == '超买':
            signals.append('RSI超买')
        if result['kdj'].get('Signal') == '超卖':
            signals.append('KDJ超卖')
        elif result['kdj'].get('Signal') == '超买':
            signals.append('KDJ超买')
        
        result['signals'] = signals
        
        logger.info(f"技术指标计算完成: {stock_code}")
        return result


def main():
    """测试技术指标工具"""
    print("=" * 60)
    print("技术指标工具测试")
    print("=" * 60)
    
    # 创建工具实例
    tool = TechnicalIndicatorsTool()
    
    # 测试福耀玻璃
    print("\n测试福耀玻璃 (600660):")
    indicators = tool.get_indicators('600660')
    
    import json
    print(json.dumps(indicators, indent=2, ensure_ascii=False))
    
    print("\n✅ 测试完成!")


if __name__ == "__main__":
    main()
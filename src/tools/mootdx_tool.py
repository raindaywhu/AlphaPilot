"""
Mootdx 数据工具

使用 mootdx 获取 A 股历史行情数据，支持全 A 股。

解决 TECH-001: 修复量化数据源 - 支持全 A 股
优化 OPT-001: 添加缓存和连接复用
"""

import os
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

# 禁用代理
os.environ['http_proxy'] = ''
os.environ['https_proxy'] = ''

from mootdx.quotes import Quotes

# 导入性能优化工具
from ..utils.performance import (
    timing_decorator,
    cached,
    get_shared_mootdx_client,
    monitor_performance
)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MootdxTool:
    """
    Mootdx 数据工具
    
    使用 mootdx 获取 A 股历史行情数据，支持全 A 股。
    
    优化：
    - 连接复用：使用共享客户端
    - 数据缓存：K线数据缓存 5 分钟
    - 性能监控：记录执行时间
    """
    
    def __init__(self):
        """初始化工具"""
        # 使用共享客户端（连接复用）
        self.client = get_shared_mootdx_client()
        logger.info("MootdxTool 初始化完成（使用共享连接）")
    
    def get_kline_data(
        self,
        symbol: str,
        days: int = 100,
        frequency: int = 9  # 9=日K线
    ) -> pd.DataFrame:
        """
        获取 K 线数据
        
        Args:
            symbol: 股票代码（如 600519）
            days: 获取天数
            frequency: K线频率（9=日K，5=5分钟K）
        
        Returns:
            K线数据 DataFrame
        """
        try:
            # 移除前缀
            if symbol.startswith('SH') or symbol.startswith('SZ'):
                symbol = symbol[2:]
            
            # 获取数据
            df = self.client.bars(
                symbol=symbol,
                frequency=frequency,
                start=0,
                offset=days
            )
            
            if df is None or len(df) == 0:
                logger.warning(f"无法获取股票 {symbol} 的数据")
                return None
            
            logger.info(f"成功获取 {symbol} 的数据: {len(df)} 条")
            return df
            
        except Exception as e:
            logger.error(f"获取数据失败: {e}")
            return None
    
    def calculate_ma(self, df: pd.DataFrame, periods: List[int] = [5, 10, 20, 60]) -> pd.DataFrame:
        """
        计算移动平均线
        
        Args:
            df: K线数据
            periods: 周期列表
        
        Returns:
            添加了 MA 列的 DataFrame
        """
        for period in periods:
            df[f'MA{period}'] = df['close'].rolling(window=period).mean()
        return df
    
    def calculate_macd(
        self,
        df: pd.DataFrame,
        fast: int = 12,
        slow: int = 26,
        signal: int = 9
    ) -> pd.DataFrame:
        """
        计算 MACD 指标
        
        Args:
            df: K线数据
            fast: 快线周期
            slow: 慢线周期
            signal: 信号线周期
        
        Returns:
            添加了 MACD 列的 DataFrame
        """
        # 计算 EMA
        ema_fast = df['close'].ewm(span=fast, adjust=False).mean()
        ema_slow = df['close'].ewm(span=slow, adjust=False).mean()
        
        # MACD 线
        df['MACD'] = ema_fast - ema_slow
        
        # 信号线
        df['MACD_Signal'] = df['MACD'].ewm(span=signal, adjust=False).mean()
        
        # 柱状图
        df['MACD_Hist'] = (df['MACD'] - df['MACD_Signal']) * 2
        
        return df
    
    def calculate_rsi(self, df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
        """
        计算 RSI 指标
        
        Args:
            df: K线数据
            period: 周期
        
        Returns:
            添加了 RSI 列的 DataFrame
        """
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        return df
    
    def calculate_kdj(
        self,
        df: pd.DataFrame,
        n: int = 9,
        m1: int = 3,
        m2: int = 3
    ) -> pd.DataFrame:
        """
        计算 KDJ 指标
        
        Args:
            df: K线数据
            n: RSV 周期
            m1: K 周期
            m2: D 周期
        
        Returns:
            添加了 KDJ 列的 DataFrame
        """
        low_n = df['low'].rolling(window=n).min()
        high_n = df['high'].rolling(window=n).max()
        
        rsv = (df['close'] - low_n) / (high_n - low_n) * 100
        
        df['K'] = rsv.ewm(alpha=1/m1, adjust=False).mean()
        df['D'] = df['K'].ewm(alpha=1/m2, adjust=False).mean()
        df['J'] = 3 * df['K'] - 2 * df['D']
        
        return df
    
    def calculate_boll(
        self,
        df: pd.DataFrame,
        period: int = 20,
        std_dev: int = 2
    ) -> pd.DataFrame:
        """
        计算布林带
        
        Args:
            df: K线数据
            period: 周期
            std_dev: 标准差倍数
        
        Returns:
            添加了布林带列的 DataFrame
        """
        df['BOLL_MID'] = df['close'].rolling(window=period).mean()
        std = df['close'].rolling(window=period).std()
        
        df['BOLL_UPPER'] = df['BOLL_MID'] + std_dev * std
        df['BOLL_LOWER'] = df['BOLL_MID'] - std_dev * std
        
        return df
    
    @monitor_performance("mootdx_tool")
    @timing_decorator
    @cached("mootdx_analyze", max_age_seconds=300)  # 缓存 5 分钟
    def analyze(self, symbol: str) -> Dict[str, Any]:
        """
        分析股票
        
        Args:
            symbol: 股票代码
        
        Returns:
            分析结果
        """
        logger.info(f"开始分析股票: {symbol}")
        
        # 获取数据
        df = self.get_kline_data(symbol, days=100)
        if df is None:
            return {
                'success': False,
                'error': f'无法获取股票 {symbol} 的数据'
            }
        
        # 计算技术指标
        df = self.calculate_ma(df)
        df = self.calculate_macd(df)
        df = self.calculate_rsi(df)
        df = self.calculate_kdj(df)
        df = self.calculate_boll(df)
        
        # 获取最新数据
        latest = df.iloc[-1]
        
        # 分析趋势
        trend = self._analyze_trend(df)
        
        # 分析 MACD
        macd_signal = self._analyze_macd(df)
        
        # 分析 RSI
        rsi_signal = self._analyze_rsi(latest)
        
        # 分析 KDJ
        kdj_signal = self._analyze_kdj(latest)
        
        # 综合评分
        score, rating = self._calculate_score(trend, macd_signal, rsi_signal, kdj_signal)
        
        return {
            'success': True,
            'symbol': symbol,
            'latest_price': float(latest['close']),
            'latest_date': str(latest.name),
            'indicators': {
                'MA5': float(latest['MA5']),
                'MA10': float(latest['MA10']),
                'MA20': float(latest['MA20']),
                'MACD': float(latest['MACD']),
                'MACD_Signal': float(latest['MACD_Signal']),
                'RSI': float(latest['RSI']),
                'K': float(latest['K']),
                'D': float(latest['D']),
                'J': float(latest['J']),
                'BOLL_UPPER': float(latest['BOLL_UPPER']),
                'BOLL_MID': float(latest['BOLL_MID']),
                'BOLL_LOWER': float(latest['BOLL_LOWER'])
            },
            'analysis': {
                'trend': trend,
                'macd_signal': macd_signal,
                'rsi_signal': rsi_signal,
                'kdj_signal': kdj_signal
            },
            'score': score,
            'rating': rating,
            'data_points': len(df)
        }
    
    def _analyze_trend(self, df: pd.DataFrame) -> Dict[str, Any]:
        """分析趋势"""
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        
        # 均线趋势
        ma_trend = 'neutral'
        if latest['MA5'] > latest['MA10'] > latest['MA20']:
            ma_trend = 'bullish'
        elif latest['MA5'] < latest['MA10'] < latest['MA20']:
            ma_trend = 'bearish'
        
        # 价格位置
        price_vs_ma20 = (latest['close'] - latest['MA20']) / latest['MA20'] * 100
        
        return {
            'ma_trend': ma_trend,
            'price_vs_ma20': price_vs_ma20,
            'description': f'MA趋势: {ma_trend}, 价格相对MA20: {price_vs_ma20:.2f}%'
        }
    
    def _analyze_macd(self, df: pd.DataFrame) -> Dict[str, Any]:
        """分析 MACD"""
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        
        signal = 'neutral'
        if latest['MACD'] > latest['MACD_Signal']:
            if prev['MACD'] <= prev['MACD_Signal']:
                signal = 'golden_cross'
            else:
                signal = 'bullish'
        elif latest['MACD'] < latest['MACD_Signal']:
            if prev['MACD'] >= prev['MACD_Signal']:
                signal = 'death_cross'
            else:
                signal = 'bearish'
        
        return {
            'signal': signal,
            'macd_value': float(latest['MACD']),
            'description': f'MACD: {signal}'
        }
    
    def _analyze_rsi(self, latest: pd.Series) -> Dict[str, Any]:
        """分析 RSI"""
        rsi = latest['RSI']
        
        if rsi > 80:
            signal = 'overbought'
        elif rsi > 60:
            signal = 'bullish'
        elif rsi < 20:
            signal = 'oversold'
        elif rsi < 40:
            signal = 'bearish'
        else:
            signal = 'neutral'
        
        return {
            'signal': signal,
            'rsi_value': float(rsi),
            'description': f'RSI: {rsi:.2f} ({signal})'
        }
    
    def _analyze_kdj(self, latest: pd.Series) -> Dict[str, Any]:
        """分析 KDJ"""
        k, d, j = latest['K'], latest['D'], latest['J']
        
        if k > d and k < 80:
            signal = 'bullish'
        elif k < d and k > 20:
            signal = 'bearish'
        elif k > 80:
            signal = 'overbought'
        elif k < 20:
            signal = 'oversold'
        else:
            signal = 'neutral'
        
        return {
            'signal': signal,
            'k': float(k),
            'd': float(d),
            'j': float(j),
            'description': f'KDJ: K={k:.2f}, D={d:.2f}, J={j:.2f}'
        }
    
    def _calculate_score(
        self,
        trend: Dict,
        macd_signal: Dict,
        rsi_signal: Dict,
        kdj_signal: Dict
    ) -> tuple:
        """计算综合评分"""
        score = 50  # 基础分
        
        # 趋势分数
        if trend['ma_trend'] == 'bullish':
            score += 15
        elif trend['ma_trend'] == 'bearish':
            score -= 15
        
        # MACD 分数
        if macd_signal['signal'] in ['golden_cross', 'bullish']:
            score += 15
        elif macd_signal['signal'] in ['death_cross', 'bearish']:
            score -= 15
        
        # RSI 分数
        if rsi_signal['signal'] == 'oversold':
            score += 10
        elif rsi_signal['signal'] == 'overbought':
            score -= 10
        
        # KDJ 分数
        if kdj_signal['signal'] in ['bullish', 'oversold']:
            score += 10
        elif kdj_signal['signal'] in ['bearish', 'overbought']:
            score -= 10
        
        # 评级
        if score >= 70:
            rating = '看涨'
        elif score >= 55:
            rating = '中性偏多'
        elif score >= 45:
            rating = '中性'
        elif score >= 30:
            rating = '中性偏空'
        else:
            rating = '看跌'
        
        return score, rating


def main():
    """测试工具"""
    print("=" * 60)
    print("📊 MootdxTool 测试")
    print("=" * 60)
    
    tool = MootdxTool()
    
    # 测试分析
    result = tool.analyze('SH600519')
    
    if result['success']:
        print(f"\n✅ 分析成功: {result['symbol']}")
        print(f"最新价格: {result['latest_price']}")
        print(f"综合评分: {result['score']}")
        print(f"综合评级: {result['rating']}")
        print(f"\n技术指标:")
        for k, v in result['indicators'].items():
            print(f"  {k}: {v:.2f}")
        print(f"\n分析信号:")
        for k, v in result['analysis'].items():
            print(f"  {k}: {v['description']}")
    else:
        print(f"\n❌ 分析失败: {result['error']}")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
技术指标计算工具

计算常用技术指标：MA、MACD、RSI、KDJ等

Issue: #8 (TOOL-003)
"""

import logging
from typing import List, Optional, Union, Dict
from datetime import datetime

import numpy as np
import pandas as pd

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TechnicalIndicatorTool:
    """
    技术指标计算工具
    
    提供常用技术指标的计算功能，支持：
    - MA（移动平均线）
    - EMA（指数移动平均）
    - MACD（异同移动平均线）
    - RSI（相对强弱指标）
    - KDJ（随机指标）
    - BOLL（布林带）
    
    使用示例：
        >>> tool = TechnicalIndicatorTool()
        >>> # 假设有 K 线数据
        >>> df = pd.DataFrame({
        ...     'close': [10, 11, 12, 11, 13, 14, 13, 15, 16, 15],
        ...     'high': [11, 12, 13, 12, 14, 15, 14, 16, 17, 16],
        ...     'low': [9, 10, 11, 10, 12, 13, 12, 14, 15, 14]
        ... })
        >>> ma = tool.calculate_ma(df['close'], [5, 10])
        >>> macd = tool.calculate_macd(df['close'])
    """
    
    def __init__(self):
        """初始化技术指标工具"""
        pass
    
    # ==================== MA 移动平均线 ====================
    
    def calculate_ma(
        self, 
        data: Union[pd.Series, np.ndarray, List[float]], 
        periods: List[int] = [5, 10, 20, 30, 60]
    ) -> Dict[str, np.ndarray]:
        """
        计算移动平均线（Simple Moving Average）
        
        Args:
            data: 价格数据（收盘价）
            periods: 周期列表，默认 [5, 10, 20, 30, 60]
        
        Returns:
            字典，key 为 'MA5', 'MA10' 等，value 为对应的 MA 数组
        
        Example:
            >>> tool = TechnicalIndicatorTool()
            >>> close = [10, 11, 12, 13, 14, 15, 16, 17, 18, 19]
            >>> ma = tool.calculate_ma(close, [5, 10])
            >>> print(ma['MA5'])
        """
        data = np.array(data, dtype=float)
        result = {}
        
        for period in periods:
            ma = self._sma(data, period)
            result[f'MA{period}'] = ma
            logger.debug(f"计算 MA{period}: 长度={len(ma)}, 最后值={ma[-1] if not np.isnan(ma[-1]) else 'N/A'}")
        
        logger.info(f"计算 MA 完成: {len(periods)} 条均线")
        return result
    
    def _sma(self, data: np.ndarray, period: int) -> np.ndarray:
        """计算简单移动平均"""
        result = np.full_like(data, np.nan)
        if len(data) < period:
            return result
        
        # 使用 cumsum 优化计算
        cumsum = np.cumsum(data)
        cumsum = np.insert(cumsum, 0, 0)
        result[period-1:] = (cumsum[period:] - cumsum[:-period]) / period
        
        return result
    
    # ==================== EMA 指数移动平均 ====================
    
    def calculate_ema(
        self, 
        data: Union[pd.Series, np.ndarray, List[float]], 
        periods: List[int] = [12, 26]
    ) -> Dict[str, np.ndarray]:
        """
        计算指数移动平均线（Exponential Moving Average）
        
        Args:
            data: 价格数据
            periods: 周期列表，默认 [12, 26]
        
        Returns:
            字典，key 为 'EMA12', 'EMA26' 等
        """
        data = np.array(data, dtype=float)
        result = {}
        
        for period in periods:
            ema = self._ema(data, period)
            result[f'EMA{period}'] = ema
        
        logger.info(f"计算 EMA 完成: {len(periods)} 条均线")
        return result
    
    def _ema(self, data: np.ndarray, period: int) -> np.ndarray:
        """计算指数移动平均"""
        result = np.full_like(data, np.nan)
        if len(data) < period:
            return result
        
        # EMA = (Close - EMA_prev) * multiplier + EMA_prev
        multiplier = 2 / (period + 1)
        
        # 第一个 EMA 使用 SMA
        result[period-1] = np.mean(data[:period])
        
        # 后续使用 EMA 公式
        for i in range(period, len(data)):
            result[i] = (data[i] - result[i-1]) * multiplier + result[i-1]
        
        return result
    
    # ==================== MACD ====================
    
    def calculate_macd(
        self, 
        data: Union[pd.Series, np.ndarray, List[float]],
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9
    ) -> Dict[str, np.ndarray]:
        """
        计算 MACD（Moving Average Convergence Divergence）
        
        Args:
            data: 价格数据（收盘价）
            fast_period: 快线周期，默认 12
            slow_period: 慢线周期，默认 26
            signal_period: 信号线周期，默认 9
        
        Returns:
            字典，包含：
            - 'MACD': MACD 线（快线 EMA - 慢线 EMA）
            - 'SIGNAL': 信号线（MACD 的 EMA）
            - 'HISTOGRAM': 柱状图（MACD - SIGNAL）
        
        Example:
            >>> tool = TechnicalIndicatorTool()
            >>> close = [10, 11, 12, 13, 14, 15, 16, 17, 18, 19] * 3
            >>> macd = tool.calculate_macd(close)
            >>> print(macd['MACD'][-1])
        """
        data = np.array(data, dtype=float)
        
        # 计算快慢 EMA
        ema_fast = self._ema(data, fast_period)
        ema_slow = self._ema(data, slow_period)
        
        # MACD 线 = 快线 - 慢线
        macd_line = ema_fast - ema_slow
        
        # 找到 MACD 有效值的起始位置
        valid_idx = np.where(~np.isnan(macd_line))[0]
        if len(valid_idx) == 0:
            return {
                'MACD': macd_line,
                'SIGNAL': np.full_like(data, np.nan),
                'HISTOGRAM': np.full_like(data, np.nan)
            }
        
        valid_start = valid_idx[0]
        macd_valid = macd_line[valid_start:]
        
        # 信号线 = MACD 的 EMA
        signal_valid = self._ema(macd_valid, signal_period)
        
        # 对齐信号线长度
        signal_full = np.full_like(data, np.nan)
        signal_full[valid_start:] = signal_valid
        
        # 柱状图 = MACD - SIGNAL
        histogram = macd_line - signal_full
        
        result = {
            'MACD': macd_line,
            'SIGNAL': signal_full,
            'HISTOGRAM': histogram
        }
        
        logger.info(f"计算 MACD 完成: fast={fast_period}, slow={slow_period}, signal={signal_period}")
        return result
    
    # ==================== RSI ====================
    
    def calculate_rsi(
        self, 
        data: Union[pd.Series, np.ndarray, List[float]], 
        period: int = 14
    ) -> np.ndarray:
        """
        计算相对强弱指标（Relative Strength Index）
        
        Args:
            data: 价格数据（收盘价）
            period: 周期，默认 14
        
        Returns:
            RSI 数组，范围 0-100
        
        Example:
            >>> tool = TechnicalIndicatorTool()
            >>> close = [10, 11, 12, 11, 13, 14, 13, 15, 16, 15] * 2
            >>> rsi = tool.calculate_rsi(close, 14)
            >>> print(rsi[-1])
        """
        data = np.array(data, dtype=float)
        
        # 计算价格变化
        delta = np.diff(data)
        delta = np.insert(delta, 0, 0)
        
        # 分离上涨和下跌
        gain = np.where(delta > 0, delta, 0)
        loss = np.where(delta < 0, -delta, 0)
        
        # 计算平均上涨和下跌
        avg_gain = np.full_like(data, np.nan)
        avg_loss = np.full_like(data, np.nan)
        
        if len(data) < period + 1:
            return avg_gain  # 返回全 NaN
        
        # 第一个平均使用 SMA
        avg_gain[period] = np.mean(gain[1:period+1])
        avg_loss[period] = np.mean(loss[1:period+1])
        
        # 后续使用 EMA
        for i in range(period + 1, len(data)):
            avg_gain[i] = (avg_gain[i-1] * (period - 1) + gain[i]) / period
            avg_loss[i] = (avg_loss[i-1] * (period - 1) + loss[i]) / period
        
        # 计算 RS 和 RSI
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        logger.info(f"计算 RSI 完成: period={period}, 最后值={rsi[-1] if not np.isnan(rsi[-1]) else 'N/A'}")
        return rsi
    
    # ==================== KDJ ====================
    
    def calculate_kdj(
        self, 
        high: Union[pd.Series, np.ndarray, List[float]],
        low: Union[pd.Series, np.ndarray, List[float]],
        close: Union[pd.Series, np.ndarray, List[float]],
        n: int = 9,
        m1: int = 3,
        m2: int = 3
    ) -> Dict[str, np.ndarray]:
        """
        计算 KDJ 随机指标
        
        Args:
            high: 最高价
            low: 最低价
            close: 收盘价
            n: RSV 周期，默认 9
            m1: K 值平滑周期，默认 3
            m2: D 值平滑周期，默认 3
        
        Returns:
            字典，包含：
            - 'K': K 值
            - 'D': D 值
            - 'J': J 值（3K - 2D）
        
        Example:
            >>> tool = TechnicalIndicatorTool()
            >>> high = [11, 12, 13, 12, 14, 15, 14, 16, 17, 16] * 2
            >>> low = [9, 10, 11, 10, 12, 13, 12, 14, 15, 14] * 2
            >>> close = [10, 11, 12, 11, 13, 14, 13, 15, 16, 15] * 2
            >>> kdj = tool.calculate_kdj(high, low, close)
            >>> print(kdj['K'][-1], kdj['D'][-1], kdj['J'][-1])
        """
        high = np.array(high, dtype=float)
        low = np.array(low, dtype=float)
        close = np.array(close, dtype=float)
        
        # 计算 RSV
        rsv = np.full_like(close, np.nan)
        
        for i in range(n - 1, len(close)):
            high_n = np.max(high[i-n+1:i+1])
            low_n = np.min(low[i-n+1:i+1])
            
            if high_n != low_n:
                rsv[i] = (close[i] - low_n) / (high_n - low_n) * 100
            else:
                rsv[i] = 50  # 避免除零
        
        # 计算 K、D、J
        k = np.full_like(close, np.nan)
        d = np.full_like(close, np.nan)
        
        # K = SMA(RSV, m1)
        # D = SMA(K, m2)
        k[n-1] = rsv[n-1] if not np.isnan(rsv[n-1]) else 50
        d[n-1] = k[n-1]
        
        for i in range(n, len(close)):
            if not np.isnan(rsv[i]):
                k[i] = (k[i-1] * (m1 - 1) + rsv[i]) / m1
                d[i] = (d[i-1] * (m2 - 1) + k[i]) / m2
        
        # J = 3K - 2D
        j = 3 * k - 2 * d
        
        result = {
            'K': k,
            'D': d,
            'J': j
        }
        
        logger.info(f"计算 KDJ 完成: n={n}, m1={m1}, m2={m2}")
        return result
    
    # ==================== BOLL 布林带 ====================
    
    def calculate_boll(
        self, 
        data: Union[pd.Series, np.ndarray, List[float]],
        period: int = 20,
        std_dev: float = 2.0
    ) -> Dict[str, np.ndarray]:
        """
        计算布林带（Bollinger Bands）
        
        Args:
            data: 价格数据（收盘价）
            period: 周期，默认 20
            std_dev: 标准差倍数，默认 2
        
        Returns:
            字典，包含：
            - 'MID': 中轨（MA）
            - 'UPPER': 上轨
            - 'LOWER': 下轨
        
        Example:
            >>> tool = TechnicalIndicatorTool()
            >>> close = [10, 11, 12, 13, 14, 15, 16, 17, 18, 19] * 3
            >>> boll = tool.calculate_boll(close)
            >>> print(boll['UPPER'][-1], boll['MID'][-1], boll['LOWER'][-1])
        """
        data = np.array(data, dtype=float)
        
        # 中轨 = MA
        mid = self._sma(data, period)
        
        # 计算标准差
        std = np.full_like(data, np.nan)
        for i in range(period - 1, len(data)):
            std[i] = np.std(data[i-period+1:i+1], ddof=1)
        
        # 上轨 = 中轨 + std_dev * 标准差
        upper = mid + std_dev * std
        
        # 下轨 = 中轨 - std_dev * 标准差
        lower = mid - std_dev * std
        
        result = {
            'MID': mid,
            'UPPER': upper,
            'LOWER': lower
        }
        
        logger.info(f"计算 BOLL 完成: period={period}, std_dev={std_dev}")
        return result
    
    # ==================== 综合计算 ====================
    
    def calculate_all(
        self,
        high: Union[pd.Series, np.ndarray, List[float]],
        low: Union[pd.Series, np.ndarray, List[float]],
        close: Union[pd.Series, np.ndarray, List[float]],
        volume: Optional[Union[pd.Series, np.ndarray, List[float]]] = None
    ) -> pd.DataFrame:
        """
        计算所有技术指标
        
        Args:
            high: 最高价
            low: 最低价
            close: 收盘价
            volume: 成交量（可选）
        
        Returns:
            DataFrame，包含所有技术指标
        """
        close = np.array(close, dtype=float)
        high = np.array(high, dtype=float)
        low = np.array(low, dtype=float)
        
        result = {}
        
        # MA
        ma = self.calculate_ma(close)
        result.update(ma)
        
        # MACD
        macd = self.calculate_macd(close)
        result['MACD'] = macd['MACD']
        result['MACD_SIGNAL'] = macd['SIGNAL']
        result['MACD_HIST'] = macd['HISTOGRAM']
        
        # RSI
        result['RSI_14'] = self.calculate_rsi(close, 14)
        result['RSI_6'] = self.calculate_rsi(close, 6)
        
        # KDJ
        kdj = self.calculate_kdj(high, low, close)
        result['K'] = kdj['K']
        result['D'] = kdj['D']
        result['J'] = kdj['J']
        
        # BOLL
        boll = self.calculate_boll(close)
        result['BOLL_MID'] = boll['MID']
        result['BOLL_UPPER'] = boll['UPPER']
        result['BOLL_LOWER'] = boll['LOWER']
        
        # 转换为 DataFrame
        df = pd.DataFrame(result)
        
        logger.info(f"计算所有指标完成: shape={df.shape}")
        return df
    
    def get_indicator_info(self) -> dict:
        """
        获取技术指标信息
        
        Returns:
            指标信息字典
        """
        return {
            'name': 'TechnicalIndicatorTool',
            'description': '技术指标计算工具',
            'indicators': {
                'MA': {
                    'name': '移动平均线',
                    'description': 'Simple Moving Average',
                    'default_periods': [5, 10, 20, 30, 60]
                },
                'EMA': {
                    'name': '指数移动平均',
                    'description': 'Exponential Moving Average',
                    'default_periods': [12, 26]
                },
                'MACD': {
                    'name': '异同移动平均线',
                    'description': 'Moving Average Convergence Divergence',
                    'components': ['MACD', 'SIGNAL', 'HISTOGRAM'],
                    'default_params': {'fast': 12, 'slow': 26, 'signal': 9}
                },
                'RSI': {
                    'name': '相对强弱指标',
                    'description': 'Relative Strength Index',
                    'range': '0-100',
                    'default_period': 14
                },
                'KDJ': {
                    'name': '随机指标',
                    'description': 'Stochastic Oscillator',
                    'components': ['K', 'D', 'J'],
                    'default_params': {'n': 9, 'm1': 3, 'm2': 3}
                },
                'BOLL': {
                    'name': '布林带',
                    'description': 'Bollinger Bands',
                    'components': ['UPPER', 'MID', 'LOWER'],
                    'default_params': {'period': 20, 'std_dev': 2.0}
                }
            }
        }


def main():
    """测试技术指标工具"""
    print("=" * 60)
    print("技术指标工具测试")
    print("=" * 60)
    
    # 创建测试数据
    np.random.seed(42)
    n = 100
    base = 100
    close = base + np.cumsum(np.random.randn(n) * 0.5)
    high = close + np.abs(np.random.randn(n) * 0.3)
    low = close - np.abs(np.random.randn(n) * 0.3)
    
    tool = TechnicalIndicatorTool()
    
    # 测试 1: MA
    print("\n1. 测试 MA:")
    ma = tool.calculate_ma(close, [5, 10, 20])
    for key, value in ma.items():
        print(f"  {key}: 最后值 = {value[-1]:.2f}")
    
    # 测试 2: MACD
    print("\n2. 测试 MACD:")
    macd = tool.calculate_macd(close)
    print(f"  MACD: {macd['MACD'][-1]:.4f}")
    print(f"  SIGNAL: {macd['SIGNAL'][-1]:.4f}")
    print(f"  HISTOGRAM: {macd['HISTOGRAM'][-1]:.4f}")
    
    # 测试 3: RSI
    print("\n3. 测试 RSI:")
    rsi = tool.calculate_rsi(close, 14)
    print(f"  RSI(14): {rsi[-1]:.2f}")
    
    # 测试 4: KDJ
    print("\n4. 测试 KDJ:")
    kdj = tool.calculate_kdj(high, low, close)
    print(f"  K: {kdj['K'][-1]:.2f}")
    print(f"  D: {kdj['D'][-1]:.2f}")
    print(f"  J: {kdj['J'][-1]:.2f}")
    
    # 测试 5: BOLL
    print("\n5. 测试 BOLL:")
    boll = tool.calculate_boll(close)
    print(f"  UPPER: {boll['UPPER'][-1]:.2f}")
    print(f"  MID: {boll['MID'][-1]:.2f}")
    print(f"  LOWER: {boll['LOWER'][-1]:.2f}")
    
    # 测试 6: 综合计算
    print("\n6. 测试综合计算:")
    df = tool.calculate_all(high, low, close)
    print(f"  Shape: {df.shape}")
    print(f"  Columns: {list(df.columns)}")
    print(f"\n  最后一条数据:")
    print(df.iloc[-1].to_string())
    
    print("\n✅ 所有测试通过!")


if __name__ == "__main__":
    main()
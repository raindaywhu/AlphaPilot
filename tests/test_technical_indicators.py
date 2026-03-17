#!/usr/bin/env python3
"""
技术指标工具测试

Issue: #8 (TOOL-003)
"""

import pytest
import numpy as np
import pandas as pd

from src.tools.technical_indicators import TechnicalIndicatorTool


class TestTechnicalIndicatorTool:
    """技术指标工具测试类"""
    
    @pytest.fixture
    def tool(self):
        """创建工具实例"""
        return TechnicalIndicatorTool()
    
    @pytest.fixture
    def sample_data(self):
        """创建测试数据"""
        np.random.seed(42)
        n = 100
        base = 100
        close = base + np.cumsum(np.random.randn(n) * 0.5)
        high = close + np.abs(np.random.randn(n) * 0.3)
        low = close - np.abs(np.random.randn(n) * 0.3)
        return {'close': close, 'high': high, 'low': low}
    
    # ==================== MA 测试 ====================
    
    def test_calculate_ma(self, tool, sample_data):
        """测试 MA 计算"""
        ma = tool.calculate_ma(sample_data['close'], [5, 10, 20])
        
        assert 'MA5' in ma
        assert 'MA10' in ma
        assert 'MA20' in ma
        
        # 检查长度
        for key, value in ma.items():
            assert len(value) == len(sample_data['close'])
        
        # 检查前几个值是 NaN
        assert np.isnan(ma['MA5'][:4]).all()
        assert np.isnan(ma['MA10'][:9]).all()
        assert np.isnan(ma['MA20'][:19]).all()
        
        # 检查有效值
        assert not np.isnan(ma['MA5'][-1])
    
    def test_ma_calculation(self, tool):
        """测试 MA 计算正确性"""
        # 使用简单数据验证
        data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        ma = tool.calculate_ma(data, [3, 5])
        
        # MA3: [nan, nan, 2, 3, 4, 5, 6, 7, 8, 9]
        assert np.isnan(ma['MA3'][0])
        assert np.isnan(ma['MA3'][1])
        assert ma['MA3'][2] == 2  # (1+2+3)/3
        assert ma['MA3'][3] == 3  # (2+3+4)/3
        assert ma['MA3'][-1] == 9  # (8+9+10)/3
        
        # MA5: [nan, nan, nan, nan, 3, 4, 5, 6, 7, 8]
        assert np.isnan(ma['MA5'][:4]).all()
        assert ma['MA5'][4] == 3  # (1+2+3+4+5)/5
        assert ma['MA5'][-1] == 8  # (6+7+8+9+10)/5
    
    # ==================== EMA 测试 ====================
    
    def test_calculate_ema(self, tool, sample_data):
        """测试 EMA 计算"""
        ema = tool.calculate_ema(sample_data['close'], [12, 26])
        
        assert 'EMA12' in ema
        assert 'EMA26' in ema
        
        # EMA 应该比 SMA 更快响应
        ma = tool.calculate_ma(sample_data['close'], [12])
        # 在趋势变化时，EMA 比 MA 更接近当前价格
        assert len(ema['EMA12']) == len(sample_data['close'])
    
    # ==================== MACD 测试 ====================
    
    def test_calculate_macd(self, tool, sample_data):
        """测试 MACD 计算"""
        macd = tool.calculate_macd(sample_data['close'])
        
        assert 'MACD' in macd
        assert 'SIGNAL' in macd
        assert 'HISTOGRAM' in macd
        
        # 检查长度
        for key, value in macd.items():
            assert len(value) == len(sample_data['close'])
        
        # 检查柱状图 = MACD - SIGNAL
        valid_idx = ~np.isnan(macd['MACD']) & ~np.isnan(macd['SIGNAL'])
        np.testing.assert_array_almost_equal(
            macd['HISTOGRAM'][valid_idx],
            macd['MACD'][valid_idx] - macd['SIGNAL'][valid_idx],
            decimal=10
        )
    
    def test_macd_custom_params(self, tool, sample_data):
        """测试 MACD 自定义参数"""
        macd = tool.calculate_macd(
            sample_data['close'],
            fast_period=6,
            slow_period=13,
            signal_period=5
        )
        
        assert 'MACD' in macd
        assert len(macd['MACD']) == len(sample_data['close'])
    
    # ==================== RSI 测试 ====================
    
    def test_calculate_rsi(self, tool, sample_data):
        """测试 RSI 计算"""
        rsi = tool.calculate_rsi(sample_data['close'], 14)
        
        assert len(rsi) == len(sample_data['close'])
        
        # RSI 范围应该是 0-100
        valid_rsi = rsi[~np.isnan(rsi)]
        assert (valid_rsi >= 0).all()
        assert (valid_rsi <= 100).all()
    
    def test_rsi_extreme_values(self, tool):
        """测试 RSI 极端值"""
        # 持续上涨的股票
        rising = np.arange(1, 51, dtype=float)
        rsi_rising = tool.calculate_rsi(rising, 14)
        # 持续上涨，RSI 应该接近 100
        assert rsi_rising[-1] > 90
        
        # 持续下跌的股票
        falling = np.arange(50, 0, -1, dtype=float)
        rsi_falling = tool.calculate_rsi(falling, 14)
        # 持续下跌，RSI 应该接近 0
        assert rsi_falling[-1] < 10
    
    # ==================== KDJ 测试 ====================
    
    def test_calculate_kdj(self, tool, sample_data):
        """测试 KDJ 计算"""
        kdj = tool.calculate_kdj(
            sample_data['high'],
            sample_data['low'],
            sample_data['close']
        )
        
        assert 'K' in kdj
        assert 'D' in kdj
        assert 'J' in kdj
        
        # 检查长度
        for key, value in kdj.items():
            assert len(value) == len(sample_data['close'])
        
        # 检查 J = 3K - 2D
        valid_idx = ~np.isnan(kdj['K']) & ~np.isnan(kdj['D'])
        expected_j = 3 * kdj['K'][valid_idx] - 2 * kdj['D'][valid_idx]
        np.testing.assert_array_almost_equal(
            kdj['J'][valid_idx],
            expected_j,
            decimal=10
        )
    
    def test_kdj_range(self, tool, sample_data):
        """测试 KDJ 值范围"""
        kdj = tool.calculate_kdj(
            sample_data['high'],
            sample_data['low'],
            sample_data['close']
        )
        
        # K 和 D 通常在 0-100 之间，J 可以超出这个范围
        valid_k = kdj['K'][~np.isnan(kdj['K'])]
        assert (valid_k >= 0).all()
        assert (valid_k <= 100).all()
    
    # ==================== BOLL 测试 ====================
    
    def test_calculate_boll(self, tool, sample_data):
        """测试 BOLL 计算"""
        boll = tool.calculate_boll(sample_data['close'])
        
        assert 'MID' in boll
        assert 'UPPER' in boll
        assert 'LOWER' in boll
        
        # 检查长度
        for key, value in boll.items():
            assert len(value) == len(sample_data['close'])
        
        # 检查上轨 >= 中轨 >= 下轨
        valid_idx = ~np.isnan(boll['UPPER'])
        assert (boll['UPPER'][valid_idx] >= boll['MID'][valid_idx]).all()
        assert (boll['MID'][valid_idx] >= boll['LOWER'][valid_idx]).all()
    
    def test_boll_custom_params(self, tool, sample_data):
        """测试 BOLL 自定义参数"""
        boll = tool.calculate_boll(
            sample_data['close'],
            period=10,
            std_dev=1.5
        )
        
        assert 'MID' in boll
        assert len(boll['MID']) == len(sample_data['close'])
    
    # ==================== 综合计算测试 ====================
    
    def test_calculate_all(self, tool, sample_data):
        """测试综合计算"""
        df = tool.calculate_all(
            sample_data['high'],
            sample_data['low'],
            sample_data['close']
        )
        
        # 检查返回类型
        assert isinstance(df, pd.DataFrame)
        
        # 检查必需的列
        required_columns = [
            'MA5', 'MA10', 'MA20',
            'MACD', 'MACD_SIGNAL', 'MACD_HIST',
            'RSI_14', 'RSI_6',
            'K', 'D', 'J',
            'BOLL_MID', 'BOLL_UPPER', 'BOLL_LOWER'
        ]
        for col in required_columns:
            assert col in df.columns, f"缺少列: {col}"
        
        # 检查行数
        assert len(df) == len(sample_data['close'])
    
    # ==================== 边界条件测试 ====================
    
    def test_empty_data(self, tool):
        """测试空数据"""
        with pytest.raises(Exception):
            tool.calculate_ma([], [5])
    
    def test_insufficient_data(self, tool):
        """测试数据不足"""
        data = [1, 2, 3]
        ma = tool.calculate_ma(data, [5])
        
        # 应该返回全 NaN
        assert np.isnan(ma['MA5']).all()
    
    def test_single_value(self, tool):
        """测试单一值"""
        data = [100]
        
        ma = tool.calculate_ma(data, [5])
        assert np.isnan(ma['MA5'][0])
        
        rsi = tool.calculate_rsi(data, 14)
        assert np.isnan(rsi[0])
    
    # ==================== 信息接口测试 ====================
    
    def test_get_indicator_info(self, tool):
        """测试获取指标信息"""
        info = tool.get_indicator_info()
        
        assert info['name'] == 'TechnicalIndicatorTool'
        assert 'indicators' in info
        assert 'MA' in info['indicators']
        assert 'MACD' in info['indicators']
        assert 'RSI' in info['indicators']
        assert 'KDJ' in info['indicators']
        assert 'BOLL' in info['indicators']


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
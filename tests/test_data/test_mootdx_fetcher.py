"""
mootdx 数据获取器测试

测试 DATA-002 的验收标准：
1. 能够获取实时行情数据
2. 能够获取历史 K 线数据
3. 数据格式标准化
4. 支持异常处理
"""

import os
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pandas as pd
import pytest

# 导入被测试的模块
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from data.mootdx_fetcher import MootdxDataFetcher, MOOTDX_AVAILABLE


class TestMootdxDataFetcher:
    """MootdxDataFetcher 测试类"""
    
    @pytest.fixture
    def mock_quotes(self):
        """Mock mootdx Quotes"""
        mock = MagicMock()
        return mock
    
    @pytest.fixture
    def fetcher(self, mock_quotes):
        """创建获取器实例"""
        with patch('data.mootdx_fetcher.Quotes') as MockQuotes:
            MockQuotes.factory.return_value = mock_quotes
            fetcher = MootdxDataFetcher()
            yield fetcher
    
    # ========== 初始化测试 ==========
    
    def test_init_success(self, mock_quotes):
        """测试成功初始化"""
        with patch('data.mootdx_fetcher.Quotes') as MockQuotes:
            MockQuotes.factory.return_value = mock_quotes
            fetcher = MootdxDataFetcher()
            assert fetcher.quotes is not None
    
    def test_init_with_market(self, mock_quotes):
        """测试指定市场初始化"""
        with patch('data.mootdx_fetcher.Quotes') as MockQuotes:
            MockQuotes.factory.return_value = mock_quotes
            fetcher = MootdxDataFetcher(market='ext')
            assert fetcher.quotes is not None
    
    # ========== 股票代码标准化测试 ==========
    
    def test_normalize_stock_code_sh(self, fetcher):
        """测试上海股票代码标准化"""
        assert fetcher._normalize_stock_code('sh600519') == 'sh600519'
        assert fetcher._normalize_stock_code('600519') == 'sh600519'
        assert fetcher._normalize_stock_code('SH600519') == 'sh600519'
    
    def test_normalize_stock_code_sz(self, fetcher):
        """测试深圳股票代码标准化"""
        assert fetcher._normalize_stock_code('sz000001') == 'sz000001'
        assert fetcher._normalize_stock_code('000001') == 'sz000001'
        assert fetcher._normalize_stock_code('SZ000001') == 'sz000001'
    
    def test_normalize_stock_code_invalid(self, fetcher):
        """测试无效股票代码"""
        with pytest.raises(ValueError):
            fetcher._normalize_stock_code('invalid')
    
    # ========== 实时行情测试 ==========
    
    def test_get_realtime_quote_success(self, fetcher, mock_quotes):
        """测试获取实时行情成功"""
        # Mock 返回数据
        mock_df = pd.DataFrame([{
            'code': '600519',
            'name': '贵州茅台',
            'price': 1800.0,
            'open': 1780.0,
            'high': 1810.0,
            'low': 1775.0,
            'last_close': 1790.0,
            'vol': 50000,
            'amount': 900000000,
            'bid1': 1799.0,
            'ask1': 1801.0
        }])
        mock_quotes.quotes.return_value = mock_df
        
        # 执行测试
        result = fetcher.get_realtime_quote('sh600519')
        
        # 验证结果
        assert result is not None
        assert result['code'] == 'sh600519'
        assert result['name'] == '贵州茅台'
        assert result['price'] == 1800.0
        assert result['open'] == 1780.0
        assert result['high'] == 1810.0
        assert result['low'] == 1775.0
        assert result['pre_close'] == 1790.0
        assert result['volume'] == 50000
        assert result['amount'] == 900000000
        assert 'change_pct' in result
        assert 'change' in result
        assert 'timestamp' in result
    
    def test_get_realtime_quote_change_calculation(self, fetcher, mock_quotes):
        """测试涨跌幅计算"""
        mock_df = pd.DataFrame([{
            'code': '600519',
            'name': '贵州茅台',
            'price': 1800.0,
            'open': 1780.0,
            'high': 1810.0,
            'low': 1775.0,
            'last_close': 1800.0,
            'vol': 50000,
            'amount': 900000000,
            'bid1': 1799.0,
            'ask1': 1801.0
        }])
        mock_quotes.quotes.return_value = mock_df
        
        result = fetcher.get_realtime_quote('sh600519')
        
        # 涨跌幅应为 0%
        assert result['change_pct'] == 0.0
        assert result['change'] == 0.0
    
    def test_get_realtime_quote_no_data(self, fetcher, mock_quotes):
        """测试无数据情况"""
        mock_quotes.quotes.return_value = pd.DataFrame()
        
        with pytest.raises(Exception):
            fetcher.get_realtime_quote('sh600519')
    
    # ========== K线数据测试 ==========
    
    def test_get_kline_data_success(self, fetcher, mock_quotes):
        """测试获取K线数据成功"""
        # Mock K线数据
        dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
        mock_df = pd.DataFrame({
            'datetime': dates,
            'open': [1800.0] * 30,
            'high': [1810.0] * 30,
            'low': [1790.0] * 30,
            'close': [1805.0] * 30,
            'vol': [50000] * 30,
            'amount': [900000000] * 30
        })
        mock_quotes.bars.return_value = mock_df
        
        # 执行测试
        result = fetcher.get_kline_data('sh600519', days=30)
        
        # 验证结果
        assert result is not None
        assert len(result) == 30
        assert 'date' in result.columns
        assert 'open' in result.columns
        assert 'high' in result.columns
        assert 'low' in result.columns
        assert 'close' in result.columns
        assert 'volume' in result.columns
        assert 'amount' in result.columns
        assert 'code' in result.columns
        assert result['code'].iloc[0] == 'sh600519'
    
    def test_get_kline_data_with_date_range(self, fetcher, mock_quotes):
        """测试使用日期范围获取K线数据"""
        start_date = '2026-03-01'
        end_date = '2026-03-18'
        
        dates = pd.date_range(start=start_date, end=end_date, freq='D')
        mock_df = pd.DataFrame({
            'datetime': dates,
            'open': [1800.0] * len(dates),
            'high': [1810.0] * len(dates),
            'low': [1790.0] * len(dates),
            'close': [1805.0] * len(dates),
            'vol': [50000] * len(dates),
            'amount': [900000000] * len(dates)
        })
        mock_quotes.bars.return_value = mock_df
        
        result = fetcher.get_kline_data('sh600519', start_date=start_date, end_date=end_date)
        
        assert result is not None
        assert len(result) > 0
    
    def test_get_kline_data_no_data(self, fetcher, mock_quotes):
        """测试无K线数据"""
        mock_quotes.bars.return_value = pd.DataFrame()
        
        with pytest.raises(Exception):
            fetcher.get_kline_data('sh600519', days=30)
    
    # ========== 最新价格测试 ==========
    
    def test_get_latest_price_success(self, fetcher, mock_quotes):
        """测试获取最新价格成功"""
        mock_df = pd.DataFrame([{
            'code': '600519',
            'name': '贵州茅台',
            'price': 1800.0,
            'open': 1780.0,
            'high': 1810.0,
            'low': 1775.0,
            'last_close': 1790.0,
            'vol': 50000,
            'amount': 900000000,
            'bid1': 1799.0,
            'ask1': 1801.0
        }])
        mock_quotes.quotes.return_value = mock_df
        
        price = fetcher.get_latest_price('sh600519')
        
        assert price == 1800.0
    
    # ========== 股票列表测试 ==========
    
    def test_get_stock_list_all(self, fetcher, mock_quotes):
        """测试获取全部股票列表"""
        mock_sh = pd.DataFrame({'code': ['600519'], 'name': ['贵州茅台']})
        mock_sz = pd.DataFrame({'code': ['000001'], 'name': ['平安银行']})
        
        mock_quotes.stocks.side_effect = [mock_sh, mock_sz]
        
        result = fetcher.get_stock_list(market='all')
        
        assert result is not None
        assert len(result) == 2
        assert 'code' in result.columns
        assert 'name' in result.columns
    
    def test_get_stock_list_sh(self, fetcher, mock_quotes):
        """测试获取上海股票列表"""
        mock_sh = pd.DataFrame({'code': ['600519'], 'name': ['贵州茅台']})
        mock_quotes.stocks.return_value = mock_sh
        
        result = fetcher.get_stock_list(market='sh')
        
        assert result is not None
        assert len(result) == 1
        assert result['code'].iloc[0] == 'sh600519'
    
    # ========== 指数K线测试 ==========
    
    def test_get_index_kline_success(self, fetcher, mock_quotes):
        """测试获取指数K线成功"""
        dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
        mock_df = pd.DataFrame({
            'datetime': dates,
            'open': [3000.0] * 30,
            'high': [3050.0] * 30,
            'low': [2980.0] * 30,
            'close': [3020.0] * 30,
            'vol': [1000000] * 30,
            'amount': [10000000000] * 30
        })
        mock_quotes.index_bars.return_value = mock_df
        
        result = fetcher.get_index_kline('sh000001', days=30)
        
        assert result is not None
        assert len(result) == 30
        assert 'date' in result.columns
        assert 'close' in result.columns
        assert result['code'].iloc[0] == 'sh000001'
    
    # ========== 异常处理测试 ==========
    
    def test_get_realtime_quote_exception(self, fetcher, mock_quotes):
        """测试实时行情异常处理"""
        mock_quotes.quotes.side_effect = Exception("网络错误")
        
        with pytest.raises(Exception):
            fetcher.get_realtime_quote('sh600519')
    
    def test_get_kline_data_exception(self, fetcher, mock_quotes):
        """测试K线数据异常处理"""
        mock_quotes.bars.side_effect = Exception("网络错误")
        
        with pytest.raises(Exception):
            fetcher.get_kline_data('sh600519', days=30)


class TestMootdxDataFetcherIntegration:
    """集成测试（需要真实网络连接）"""
    
    @pytest.mark.skipif(not MOOTDX_AVAILABLE, reason="mootdx 未安装")
    def test_real_fetch(self):
        """真实数据获取测试（需要网络）"""
        try:
            fetcher = MootdxDataFetcher()
            quote = fetcher.get_realtime_quote('sh600519')
            assert quote is not None
            assert 'price' in quote
            print(f"贵州茅台最新价格: {quote['price']}")
        except Exception as e:
            pytest.skip(f"网络连接失败: {str(e)}")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
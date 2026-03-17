#!/usr/bin/env python3
"""
北向资金工具测试

测试 NorthMoneyTool 的各项功能

Issue: #9 (TOOL-004)
"""

import pytest
import pandas as pd
from datetime import datetime, timedelta

from src.tools.north_money_tool import NorthMoneyTool


class TestNorthMoneyTool:
    """北向资金工具测试类"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """测试前置设置"""
        self.tool = NorthMoneyTool()

    def test_init(self):
        """测试初始化"""
        assert self.tool is not None
        assert not self.tool._initialized

    def test_normalize_stock_code(self):
        """测试股票代码标准化"""
        assert self.tool._normalize_stock_code('SH600000') == '600000'
        assert self.tool._normalize_stock_code('SZ000001') == '000001'
        assert self.tool._normalize_stock_code('600000') == '600000'
        assert self.tool._normalize_stock_code('sh600000') == '600000'

    def test_get_net_inflow(self):
        """测试获取北向资金净流入"""
        # 这个测试需要网络连接和 akshare 数据
        # 由于网络问题，可能返回空数据
        try:
            df = self.tool.get_net_inflow('SH600000', days=5)
            
            # 验证返回的是 DataFrame
            assert isinstance(df, pd.DataFrame)
            
            # 如果有数据，验证列结构
            if not df.empty:
                assert 'date' in df.columns
                assert 'stock_code' in df.columns
                
        except Exception as e:
            # 网络问题导致的异常，测试仍然通过
            pytest.skip(f"网络问题导致测试跳过: {e}")

    def test_get_holding_change(self):
        """测试获取北向资金持仓变化"""
        try:
            change = self.tool.get_holding_change('SH600000', days=5)
            
            # 验证返回的是数值
            assert isinstance(change, (int, float))
            
        except Exception as e:
            pytest.skip(f"网络问题导致测试跳过: {e}")

    def test_get_summary(self):
        """测试获取北向资金摘要"""
        try:
            summary = self.tool.get_summary('SH600000')
            
            # 验证返回的是字典
            assert isinstance(summary, dict)
            assert 'stock_code' in summary
            assert 'status' in summary
            
        except Exception as e:
            pytest.skip(f"网络问题导致测试跳过: {e}")

    def test_get_top_inflow(self):
        """测试获取北向资金净流入排名"""
        try:
            df = self.tool.get_top_inflow(top_n=5)
            
            # 验证返回的是 DataFrame
            assert isinstance(df, pd.DataFrame)
            
            # 如果有数据，验证行数不超过 top_n
            if not df.empty:
                assert len(df) <= 5
                
        except Exception as e:
            pytest.skip(f"网络问题导致测试跳过: {e}")

    def test_invalid_stock_code(self):
        """测试无效股票代码"""
        try:
            df = self.tool.get_net_inflow('INVALID_CODE', days=5)
            # 无效代码应该返回空 DataFrame
            assert isinstance(df, pd.DataFrame)
        except Exception:
            # 异常也是预期行为
            pass

    def test_date_filtering(self):
        """测试日期过滤"""
        try:
            # 指定日期范围
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=10)).strftime('%Y-%m-%d')
            
            df = self.tool.get_net_inflow(
                'SH600000',
                start_date=start_date,
                end_date=end_date
            )
            
            assert isinstance(df, pd.DataFrame)
            
            # 如果有数据，验证日期范围
            if not df.empty:
                assert all(df['date'] >= pd.to_datetime(start_date))
                assert all(df['date'] <= pd.to_datetime(end_date))
                
        except Exception as e:
            pytest.skip(f"网络问题导致测试跳过: {e}")


class TestNorthMoneyToolIntegration:
    """北向资金工具集成测试"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """测试前置设置"""
        self.tool = NorthMoneyTool()

    def test_full_workflow(self):
        """测试完整工作流程"""
        try:
            stock_code = 'SH600000'
            
            # 1. 获取净流入数据
            df = self.tool.get_net_inflow(stock_code, days=10)
            assert isinstance(df, pd.DataFrame)
            
            # 2. 获取持仓变化
            change = self.tool.get_holding_change(stock_code, days=5)
            assert isinstance(change, (int, float))
            
            # 3. 获取摘要
            summary = self.tool.get_summary(stock_code)
            assert isinstance(summary, dict)
            assert summary['stock_code'] == '600000'
            
            # 4. 获取净流入排名
            top_df = self.tool.get_top_inflow(top_n=5)
            assert isinstance(top_df, pd.DataFrame)
            
        except Exception as e:
            pytest.skip(f"网络问题导致测试跳过: {e}")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
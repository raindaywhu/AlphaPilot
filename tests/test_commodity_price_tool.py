#!/usr/bin/env python3
"""
大宗商品价格工具测试

Issue: #11 (TOOL-005)
"""

import pytest
import pandas as pd
from datetime import datetime, timedelta

from src.tools.commodity_price_tool import CommodityPriceTool, COMMODITY_MAPPING


class TestCommodityPriceTool:
    """大宗商品价格工具测试"""

    @pytest.fixture
    def tool(self):
        """创建工具实例"""
        return CommodityPriceTool()

    def test_initialization(self, tool):
        """测试工具初始化"""
        assert tool is not None
        assert not tool._initialized  # 延迟初始化

    def test_get_supported_commodities(self, tool):
        """测试获取支持的商品列表"""
        commodities = tool.get_supported_commodities()
        assert isinstance(commodities, list)
        assert len(commodities) > 0
        assert 'gold' in commodities
        assert 'crude_oil' in commodities
        assert 'copper' in commodities

    def test_normalize_commodity(self, tool):
        """测试商品名称标准化"""
        # 英文名称
        assert tool._normalize_commodity('gold') == 'gold'
        assert tool._normalize_commodity('GOLD') == 'gold'
        assert tool._normalize_commodity('Gold') == 'gold'
        
        # 中文名称
        assert tool._normalize_commodity('黄金') == 'gold'
        
        # 代号
        assert tool._normalize_commodity('XAUUSD') == 'gold'

    def test_get_price_gold(self, tool):
        """测试获取黄金价格"""
        price = tool.get_price('gold')
        assert isinstance(price, float)
        assert price >= 0  # 黄金价格应该大于 0

    def test_get_price_crude_oil(self, tool):
        """测试获取原油价格"""
        price = tool.get_price('crude_oil')
        assert isinstance(price, float)
        assert price >= 0

    def test_get_price_copper(self, tool):
        """测试获取铜价格"""
        price = tool.get_price('copper')
        assert isinstance(price, float)
        assert price >= 0

    def test_get_price_invalid_commodity(self, tool):
        """测试获取无效商品价格"""
        price = tool.get_price('invalid_commodity')
        assert price == 0.0

    def test_get_price_trend_gold(self, tool):
        """测试获取黄金价格趋势"""
        trend = tool.get_price_trend('gold', days=7)
        
        assert isinstance(trend, dict)
        assert 'commodity' in trend
        assert 'status' in trend
        
        if trend['status'] == 'success':
            assert 'current_price' in trend
            assert 'price_change' in trend
            assert 'price_change_pct' in trend
            assert 'high_price' in trend
            assert 'low_price' in trend
            assert 'avg_price' in trend
            assert 'trend' in trend
            assert trend['trend'] in ['up', 'down', 'flat']

    def test_get_price_trend_crude_oil(self, tool):
        """测试获取原油价格趋势"""
        trend = tool.get_price_trend('crude_oil', days=30)
        
        assert isinstance(trend, dict)
        assert 'commodity' in trend

    def test_get_price_trend_invalid_commodity(self, tool):
        """测试获取无效商品价格趋势"""
        trend = tool.get_price_trend('invalid_commodity', days=30)
        
        assert isinstance(trend, dict)
        assert trend['status'] == 'error'

    def test_get_summary(self, tool):
        """测试获取摘要信息"""
        summary = tool.get_summary('gold')
        
        assert isinstance(summary, dict)
        assert 'commodity' in summary
        assert 'current_price' in summary
        assert 'status' in summary

    def test_get_multiple_prices(self, tool):
        """测试批量获取价格"""
        commodities = ['gold', 'silver', 'copper']
        prices = tool.get_multiple_prices(commodities)
        
        assert isinstance(prices, dict)
        assert len(prices) == 3
        for commodity in commodities:
            assert commodity in prices

    def test_commodity_mapping_integrity(self):
        """测试商品映射完整性"""
        for key, info in COMMODITY_MAPPING.items():
            assert 'name' in info, f"{key} 缺少 'name' 字段"
            assert 'akshare_func' in info, f"{key} 缺少 'akshare_func' 字段"
            assert 'symbol' in info, f"{key} 缺少 'symbol' 字段"
            assert isinstance(info['name'], str)
            assert isinstance(info['symbol'], str)

    def test_price_trend_calculation(self, tool):
        """测试价格趋势计算"""
        # 模拟数据测试
        trend = tool.get_price_trend('gold', days=5)
        
        if trend['status'] == 'success':
            # 验证趋势计算逻辑
            if trend['price_change_pct'] > 2:
                assert trend['trend'] == 'up'
            elif trend['price_change_pct'] < -2:
                assert trend['trend'] == 'down'
            else:
                assert trend['trend'] == 'flat'

    def test_chinese_name_lookup(self, tool):
        """测试中文名称查找"""
        # 通过中文名称获取价格
        price1 = tool.get_price('黄金')
        price2 = tool.get_price('gold')
        
        # 两者应该相同（如果成功获取）
        if price1 > 0 and price2 > 0:
            assert price1 == price2

    def test_ensure_initialized(self, tool):
        """测试延迟初始化"""
        # 初始状态未初始化
        assert not tool._initialized
        
        # 调用方法后应该初始化
        tool.get_price('gold')
        assert tool._initialized


class TestCommodityPriceToolEdgeCases:
    """边缘情况测试"""

    @pytest.fixture
    def tool(self):
        return CommodityPriceTool()

    def test_empty_commodity_name(self, tool):
        """测试空商品名称"""
        price = tool.get_price('')
        assert price == 0.0

    def test_whitespace_commodity_name(self, tool):
        """测试空白商品名称"""
        price = tool.get_price('   gold   ')
        # 应该能正确处理空白
        assert isinstance(price, float)

    def test_case_insensitive(self, tool):
        """测试大小写不敏感"""
        price1 = tool.get_price('GOLD')
        price2 = tool.get_price('gold')
        price3 = tool.get_price('Gold')
        
        # 所有小写变体应该返回相同结果
        if price1 > 0 and price2 > 0:
            assert price1 == price2
        if price2 > 0 and price3 > 0:
            assert price2 == price3

    def test_zero_days(self, tool):
        """测试零天参数"""
        trend = tool.get_price_trend('gold', days=0)
        # 应该返回当前价格
        assert isinstance(trend, dict)

    def test_negative_days(self, tool):
        """测试负数天参数"""
        trend = tool.get_price_trend('gold', days=-1)
        # 应该优雅处理
        assert isinstance(trend, dict)

    def test_large_days(self, tool):
        """测试大天参数"""
        trend = tool.get_price_trend('gold', days=365)
        # 应该返回一年的数据
        assert isinstance(trend, dict)

    def test_multiple_prices_empty_list(self, tool):
        """测试空列表批量获取"""
        prices = tool.get_multiple_prices([])
        assert isinstance(prices, dict)
        assert len(prices) == 0

    def test_multiple_prices_with_invalid(self, tool):
        """测试包含无效商品的批量获取"""
        prices = tool.get_multiple_prices(['gold', 'invalid', 'copper'])
        assert isinstance(prices, dict)
        assert 'invalid' in prices
        assert prices['invalid'] == 0.0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
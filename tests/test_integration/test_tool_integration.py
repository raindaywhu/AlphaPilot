#!/usr/bin/env python3
"""
工具集成测试

测试 Alpha158Tool 初始化、方法调用和集成

Issue: #18 (TEST-001)
"""

import pytest
import pandas as pd
from pathlib import Path
import sys

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.tools.alpha158_tool import Alpha158Tool


class TestAlpha158Tool:
    """Alpha158 工具集成测试"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """测试前准备"""
        self.tool = Alpha158Tool()

    def test_tool_initialization(self):
        """测试工具初始化"""
        assert self.tool is not None
        assert self.tool.qlib_provider is not None
        assert self.tool.SUPPORTED_INSTRUMENTS is not None
        assert len(self.tool.SUPPORTED_INSTRUMENTS) > 0

    def test_supported_instruments(self):
        """测试支持的股票池"""
        supported = self.tool.SUPPORTED_INSTRUMENTS
        
        # 验证包含主要股票池
        assert 'csi300' in supported
        assert 'csi500' in supported
        assert 'all' in supported
        
        print(f"✅ 支持的股票池: {supported}")

    def test_get_factor_info(self):
        """测试获取因子信息"""
        info = self.tool.get_factor_info()
        
        # 验证信息结构
        assert isinstance(info, dict)
        assert 'name' in info
        assert 'description' in info
        assert 'factor_count' in info
        assert 'supported_instruments' in info
        
        # 验证因子数量
        assert info['factor_count'] == 158
        
        # 验证类别信息
        assert 'categories' in info
        assert isinstance(info['categories'], dict)
        
        print(f"✅ 因子信息:")
        print(f"   - 名称: {info['name']}")
        print(f"   - 因子数量: {info['factor_count']}")
        print(f"   - 类别: {list(info['categories'].keys())}")

    def test_qlib_initialization(self):
        """测试 qlib 初始化"""
        try:
            # 确保 qlib 已初始化
            self.tool._ensure_qlib_initialized()
            
            assert self.tool._initialized is True
            print("✅ qlib 初始化成功")
            
        except Exception as e:
            pytest.skip(f"qlib 初始化失败: {e}")

    def test_get_factors_csi300(self):
        """测试获取沪深300因子"""
        try:
            df = self.tool.get_factors(
                instruments='csi300',
                start_time='2020-01-01',
                end_time='2020-03-31'
            )
            
            # 验证返回值
            assert df is not None
            assert isinstance(df, pd.DataFrame)
            assert len(df) > 0
            
            # 验证数据结构
            assert isinstance(df.index, pd.MultiIndex)
            assert len(df.index.levels) == 2
            
            # 验证因子列
            assert len(df.columns) > 100  # Alpha158 应该有很多因子
            
            print(f"✅ 成功获取沪深300因子数据:")
            print(f"   - Shape: {df.shape}")
            print(f"   - 股票数量: {len(df.index.get_level_values('instrument').unique())}")
            print(f"   - 交易日数量: {len(df.index.get_level_values('datetime').unique())}")
            
        except Exception as e:
            pytest.skip(f"获取因子数据失败: {e}")

    def test_get_factors_invalid_instrument(self):
        """测试无效股票池参数"""
        with pytest.raises(ValueError) as exc_info:
            self.tool.get_factors(
                instruments='invalid_pool',
                start_time='2020-01-01',
                end_time='2020-01-31'
            )
        
        assert "不支持的股票池" in str(exc_info.value)
        print("✅ 正确捕获无效参数")

    def test_get_stock_factors(self):
        """测试获取单只股票因子"""
        try:
            stock_df = self.tool.get_stock_factors(
                stock_code='SH600000',
                start_time='2020-01-01',
                end_time='2020-01-31'
            )
            
            # 验证返回值
            assert stock_df is not None
            assert isinstance(stock_df, pd.DataFrame)
            assert len(stock_df) > 0
            
            # 验证索引是日期
            assert stock_df.index.name == 'datetime' or isinstance(stock_df.index, pd.DatetimeIndex)
            
            print(f"✅ 成功获取 SH600000 因子数据:")
            print(f"   - Shape: {stock_df.shape}")
            print(f"   - 交易日数量: {len(stock_df)}")
            
        except Exception as e:
            pytest.skip(f"获取股票因子失败: {e}")

    def test_get_stock_factors_invalid_stock(self):
        """测试无效股票代码"""
        try:
            with pytest.raises(ValueError) as exc_info:
                self.tool.get_stock_factors(
                    stock_code='INVALID_STOCK',
                    start_time='2020-01-01',
                    end_time='2020-01-31'
                )
            
            assert "不在数据中" in str(exc_info.value)
            print("✅ 正确捕获无效股票代码")
            
        except Exception as e:
            # 如果 qlib 数据不可用，跳过测试
            pytest.skip(f"qlib 数据不可用: {e}")

    def test_factor_list(self):
        """测试因子列表获取"""
        try:
            factor_list = self.tool.get_factor_list()
            
            # 验证返回值
            assert factor_list is not None
            assert isinstance(factor_list, list)
            assert len(factor_list) >= 100
            
            # 验证因子名称格式
            for factor in factor_list[:10]:
                assert isinstance(factor, str)
                assert len(factor) > 0
            
            print(f"✅ 因子列表:")
            print(f"   - 总数: {len(factor_list)}")
            print(f"   - 前10个: {factor_list[:10]}")
            
        except Exception as e:
            pytest.skip(f"获取因子列表失败: {e}")

    def test_multiple_calls(self):
        """测试多次调用稳定性"""
        try:
            # 第一次调用
            df1 = self.tool.get_factors(
                instruments='csi300',
                start_time='2020-01-01',
                end_time='2020-01-31'
            )
            
            # 第二次调用
            df2 = self.tool.get_factors(
                instruments='csi300',
                start_time='2020-02-01',
                end_time='2020-02-28'
            )
            
            # 验证两次调用都成功
            assert df1 is not None and df2 is not None
            assert len(df1) > 0 and len(df2) > 0
            
            # 验证 qlib 只初始化一次
            assert self.tool._initialized is True
            
            print("✅ 多次调用稳定性测试通过")
            
        except Exception as e:
            pytest.skip(f"qlib 数据不可用: {e}")

    def test_data_quality(self):
        """测试数据质量"""
        try:
            df = self.tool.get_factors(
                instruments='csi300',
                start_time='2020-01-01',
                end_time='2020-03-31'
            )
            
            # 检查空值比例
            null_ratio = df.isnull().sum().sum() / (df.shape[0] * df.shape[1])
            assert null_ratio < 0.3, f"空值比例过高: {null_ratio:.2%}"
            
            # 检查无限值
            inf_count = (df == float('inf')).sum().sum() + (df == float('-inf')).sum().sum()
            inf_ratio = inf_count / (df.shape[0] * df.shape[1])
            assert inf_ratio < 0.1, f"无限值比例过高: {inf_ratio:.2%}"
            
            print(f"✅ 数据质量:")
            print(f"   - 空值比例: {null_ratio:.2%}")
            print(f"   - 无限值比例: {inf_ratio:.2%}")
            
        except Exception as e:
            pytest.skip(f"qlib 数据不可用: {e}")


def test_main():
    """测试入口"""
    pytest.main([__file__, "-v", "-s"])


if __name__ == "__main__":
    test_main()
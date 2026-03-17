#!/usr/bin/env python3
"""
Alpha158 因子工具测试

测试 Alpha158Tool 的各个方法
"""

import pytest
import pandas as pd
from src.tools.alpha158_tool import Alpha158Tool


class TestAlpha158Tool:
    """Alpha158 工具测试类"""

    @pytest.fixture(scope="class")
    def tool(self):
        """创建工具实例"""
        return Alpha158Tool()

    def test_get_factor_info(self, tool):
        """测试获取因子信息"""
        info = tool.get_factor_info()

        # 验证返回类型
        assert isinstance(info, dict)

        # 验证必要字段
        assert 'name' in info
        assert 'description' in info
        assert 'factor_count' in info
        assert 'supported_instruments' in info

        # 验证值
        assert info['name'] == 'Alpha158'
        assert info['factor_count'] == 158
        assert 'csi300' in info['supported_instruments']

    def test_get_factors(self, tool):
        """测试获取因子数据"""
        # 获取小范围数据
        df = tool.get_factors(
            instruments='csi300',
            start_time='2020-01-01',
            end_time='2020-01-31'
        )

        # 验证返回类型
        assert isinstance(df, pd.DataFrame)

        # 验证数据形状
        assert df.shape[0] > 0  # 有数据行
        assert df.shape[1] >= 158  # 至少有 158 个因子

        # 验证索引
        assert df.index.names == ['datetime', 'instrument']

        # 验证列名
        assert 'KMID' in df.columns
        assert 'KLEN' in df.columns

    def test_get_factor_list(self, tool):
        """测试获取因子列表"""
        factor_list = tool.get_factor_list()

        # 验证返回类型
        assert isinstance(factor_list, list)

        # 验证因子数量
        assert len(factor_list) >= 158

        # 验证因子名称
        assert 'KMID' in factor_list
        assert 'KLEN' in factor_list

    def test_get_stock_factors(self, tool):
        """测试获取单只股票因子"""
        # 获取 SH600000 的因子数据
        stock_df = tool.get_stock_factors(
            stock_code='SH600000',
            start_time='2020-01-01',
            end_time='2020-03-31'
        )

        # 验证返回类型
        assert isinstance(stock_df, pd.DataFrame)

        # 验证数据形状
        assert stock_df.shape[0] > 0
        assert stock_df.shape[1] >= 158

        # 验证索引是 datetime
        assert stock_df.index.name == 'datetime'

    def test_invalid_instruments(self, tool):
        """测试无效股票池"""
        with pytest.raises(ValueError) as excinfo:
            tool.get_factors(instruments='invalid_pool')
        
        assert "不支持的股票池" in str(excinfo.value)

    def test_invalid_stock_code(self, tool):
        """测试无效股票代码"""
        with pytest.raises(ValueError) as excinfo:
            tool.get_stock_factors(
                stock_code='INVALID123',
                start_time='2020-01-01',
                end_time='2020-01-31'
            )
        
        assert "不在数据中" in str(excinfo.value)


def test_tool_initialization():
    """测试工具初始化"""
    tool = Alpha158Tool()
    assert tool is not None
    assert tool.qlib_provider == '~/.qlib/qlib_data/cn_data'


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, '-v'])
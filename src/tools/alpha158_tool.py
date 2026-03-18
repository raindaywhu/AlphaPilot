#!/usr/bin/env python3
"""
Alpha158 因子工具

封装 qlib Alpha158 因子的获取和处理

Issue: #4 (TOOL-001)
"""

import logging
from typing import List, Optional, Union
from datetime import datetime

import pandas as pd

# 使用 qlib 单例管理器，避免多线程重复初始化
from ..utils.qlib_manager import ensure_qlib_initialized
from qlib.contrib.data.handler import Alpha158

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Alpha158Tool:
    """
    Alpha158 因子工具

    封装 qlib Alpha158 因子的获取和处理，提供简洁的 API 供 Agent 使用。

    使用示例：
        >>> tool = Alpha158Tool()
        >>> df = tool.get_factors(
        ...     instruments='csi300',
        ...     start_time='2020-01-01',
        ...     end_time='2020-12-31'
        ... )
        >>> print(df.shape)
    """

    # 支持的股票池
    SUPPORTED_INSTRUMENTS = ['csi300', 'csi500', 'csi100', 'all']

    def __init__(self, qlib_provider: str = '~/.qlib/qlib_data/cn_data'):
        """
        初始化 Alpha158 因子工具

        Args:
            qlib_provider: qlib 数据提供者路径
        """
        self.qlib_provider = qlib_provider
        self._initialized = False

    def _ensure_qlib_initialized(self):
        """确保 qlib 已初始化（使用单例管理器，线程安全）"""
        ensure_qlib_initialized(self.qlib_provider)

    def get_factors(
        self,
        instruments: str = 'csi300',
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        freq: str = 'day'
    ) -> pd.DataFrame:
        """
        获取 Alpha158 因子数据

        Args:
            instruments: 股票池，支持 'csi300', 'csi500', 'csi100', 'all'
            start_time: 开始时间，格式 'YYYY-MM-DD'
            end_time: 结束时间，格式 'YYYY-MM-DD'
            freq: 频率，默认 'day'

        Returns:
            DataFrame，包含 Alpha158 因子数据
            Index: MultiIndex(datetime, instrument)
            Columns: 因子名 + label

        Raises:
            ValueError: 参数错误
            RuntimeError: qlib 操作失败
        """
        # 参数验证
        if instruments not in self.SUPPORTED_INSTRUMENTS:
            raise ValueError(
                f"不支持的股票池: {instruments}, "
                f"支持的股票池: {self.SUPPORTED_INSTRUMENTS}"
            )

        # 确保 qlib 已初始化
        self._ensure_qlib_initialized()

        # 创建 Alpha158 实例
        logger.info(
            f"创建 Alpha158 实例: instruments={instruments}, "
            f"start_time={start_time}, end_time={end_time}"
        )

        try:
            handler = Alpha158(
                instruments=instruments,
                start_time=start_time,
                end_time=end_time,
                freq=freq
            )

            # 获取数据
            df = handler.fetch()

            logger.info(f"成功获取 Alpha158 因子数据: shape={df.shape}")
            return df

        except Exception as e:
            logger.error(f"获取 Alpha158 因子数据失败: {e}")
            raise RuntimeError(f"获取 Alpha158 因子数据失败: {e}")

    def get_factor_list(self) -> List[str]:
        """
        获取 Alpha158 因子名称列表

        Returns:
            因子名称列表（不包含 label）
        """
        # 使用默认参数获取一个小数据集
        df = self.get_factors(
            instruments='csi300',
            start_time='2020-01-01',
            end_time='2020-01-31'
        )

        # 排除 label 列
        factor_list = [col for col in df.columns if col != 'label']
        return factor_list

    def get_factor_info(self) -> dict:
        """
        获取 Alpha158 因子信息

        Returns:
            因子信息字典
        """
        return {
            'name': 'Alpha158',
            'description': 'qlib 提供的 158 个量化因子',
            'factor_count': 158,
            'categories': {
                'K线形态': ['KMID', 'KLEN', 'KMID2', 'KUP', 'KUP2', 'KLOW', 'KLOW2', 'KSFT', 'KSFT2'],
                '价格': ['OPEN0', 'HIGH0', 'LOW0', 'VWAP0'],
                '动量': ['ROC5', 'ROC10', 'ROC20', 'ROC30', 'ROC60'],
                '均线': ['MA5', 'MA10', 'MA20', 'MA30', 'MA60'],
                '波动率': ['STD5', 'STD10', 'STD20', 'STD30', 'STD60'],
                '成交量': ['VOLUME5', 'VOLUME10', 'VOLUME20', 'VOLUME30', 'VOLUME60'],
                '相关性': ['CORR5', 'CORR10', 'CORR20', 'CORR30', 'CORR60'],
                '其他': ['BETA5', 'BETA10', 'BETA20', 'BETA30', 'BETA60']
            },
            'supported_instruments': self.SUPPORTED_INSTRUMENTS,
            'data_source': 'qlib'
        }

    def get_stock_factors(
        self,
        stock_code: str,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None
    ) -> pd.DataFrame:
        """
        获取单只股票的 Alpha158 因子数据

        Args:
            stock_code: 股票代码，如 'SH600000'
            start_time: 开始时间
            end_time: 结束时间

        Returns:
            DataFrame，包含该股票的 Alpha158 因子数据
        """
        # 使用 all 股票池获取数据
        df = self.get_factors(
            instruments='all',
            start_time=start_time,
            end_time=end_time
        )

        # 筛选指定股票
        if stock_code in df.index.get_level_values('instrument'):
            stock_df = df.xs(stock_code, level='instrument')
            logger.info(f"成功获取股票 {stock_code} 的因子数据: shape={stock_df.shape}")
            return stock_df
        else:
            raise ValueError(f"股票 {stock_code} 不在数据中")


def main():
    """测试 Alpha158 因子工具"""
    print("=" * 60)
    print("Alpha158 因子工具测试")
    print("=" * 60)

    # 创建工具实例
    tool = Alpha158Tool()

    # 测试 1: 获取因子信息
    print("\n1. 获取因子信息:")
    info = tool.get_factor_info()
    print(f"  - 名称: {info['name']}")
    print(f"  - 描述: {info['description']}")
    print(f"  - 因子数量: {info['factor_count']}")
    print(f"  - 支持的股票池: {info['supported_instruments']}")

    # 测试 2: 获取因子数据
    print("\n2. 获取因子数据:")
    df = tool.get_factors(
        instruments='csi300',
        start_time='2020-01-01',
        end_time='2020-03-31'
    )
    print(f"  - Shape: {df.shape}")
    print(f"  - Columns (前 10): {list(df.columns[:10])}")

    # 测试 3: 获取因子列表
    print("\n3. 获取因子列表 (前 20):")
    factor_list = tool.get_factor_list()
    for i, factor in enumerate(factor_list[:20]):
        print(f"  {i+1:2d}. {factor}")

    print("\n✅ 所有测试通过!")


if __name__ == "__main__":
    main()
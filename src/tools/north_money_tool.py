#!/usr/bin/env python3
"""
北向资金工具

获取北向资金流向数据

Issue: #9 (TOOL-004)
"""

import logging
from typing import Optional
from datetime import datetime, timedelta

import pandas as pd
import numpy as np

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NorthMoneyTool:
    """
    北向资金工具

    获取北向资金流向数据，包括净流入和持仓变化。

    使用示例：
        >>> tool = NorthMoneyTool()
        >>> df = tool.get_net_inflow('SH600000', days=30)
        >>> print(df)
        >>> change = tool.get_holding_change('SH600000')
        >>> print(f"持仓变化: {change}")
    """

    def __init__(self):
        """初始化北向资金工具"""
        self._ak = None
        self._initialized = False

    def _ensure_initialized(self):
        """确保 akshare 已初始化"""
        if not self._initialized:
            try:
                import akshare as ak
                self._ak = ak
                self._initialized = True
                logger.info("北向资金工具初始化成功")
            except ImportError:
                logger.error("akshare 未安装，请运行: pip install akshare")
                raise

    def _normalize_stock_code(self, stock_code: str) -> str:
        """
        标准化股票代码

        Args:
            stock_code: 股票代码，如 'SH600000' 或 '600000'

        Returns:
            标准化后的股票代码，如 '600000'
        """
        # 移除前缀
        code = stock_code.upper().replace('SH', '').replace('SZ', '').replace('BJ', '')
        return code

    def get_net_inflow(
        self,
        stock_code: str,
        days: int = 30,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """
        获取北向资金净流入数据

        Args:
            stock_code: 股票代码，如 'SH600000' 或 '600000'
            days: 获取最近多少天的数据，默认 30 天
            start_date: 开始日期，格式 'YYYY-MM-DD'
            end_date: 结束日期，格式 'YYYY-MM-DD'

        Returns:
            DataFrame，包含以下列：
            - date: 日期
            - stock_code: 股票代码
            - net_inflow: 净流入金额（万元）
            - buy_amount: 买入金额（万元）
            - sell_amount: 卖出金额（万元）
        """
        self._ensure_initialized()

        # 标准化股票代码
        code = self._normalize_stock_code(stock_code)

        try:
            # 使用 akshare 获取个股北向资金净流入
            # stock_hsgt_individual_em 返回个股的北向资金流向
            df = self._ak.stock_hsgt_individual_em(symbol=code)

            if df is None or df.empty:
                logger.warning(f"未找到股票 {code} 的北向资金数据")
                return pd.DataFrame()

            # 重命名列
            # akshare 返回的列名可能包括：日期、收盘价、涨跌幅、持股数量、持股变化、持股市值、持股变化市值
            df = df.rename(columns={
                '日期': 'date',
                '收盘价': 'close_price',
                '涨跌幅': 'change_pct',
                '持股数量': 'holding_shares',
                '持股变化': 'holding_change',
                '持股市值': 'holding_value',
                '持股变化市值': 'holding_value_change'
            })

            # 转换日期格式
            df['date'] = pd.to_datetime(df['date'])

            # 计算净流入（使用持股变化市值作为净流入）
            # 注意：持股变化市值可能为负，表示净流出
            df['net_inflow'] = df['holding_value_change'].fillna(0)

            # 按日期排序
            df = df.sort_values('date', ascending=False)

            # 根据日期过滤
            if start_date:
                start_dt = pd.to_datetime(start_date)
                df = df[df['date'] >= start_dt]
            if end_date:
                end_dt = pd.to_datetime(end_date)
                df = df[df['date'] <= end_dt]

            # 如果没有指定日期范围，使用 days 参数
            if not start_date and not end_date:
                cutoff_date = datetime.now() - timedelta(days=days)
                df = df[df['date'] >= cutoff_date]

            # 添加股票代码列
            df['stock_code'] = code

            # 选择需要的列
            result_columns = ['date', 'stock_code', 'net_inflow', 'holding_shares', 'holding_change', 'holding_value']
            result = df[[col for col in result_columns if col in df.columns]].copy()

            logger.info(f"获取到 {len(result)} 条北向资金记录")
            return result

        except Exception as e:
            logger.error(f"获取北向资金净流入失败: {e}")
            return pd.DataFrame()

    def get_holding_change(
        self,
        stock_code: str,
        days: int = 5
    ) -> float:
        """
        获取北向资金持仓变化

        Args:
            stock_code: 股票代码，如 'SH600000' 或 '600000'
            days: 计算最近多少天的持仓变化，默认 5 天

        Returns:
            持仓变化金额（万元），正数表示增持，负数表示减持
        """
        self._ensure_initialized()

        # 标准化股票代码
        code = self._normalize_stock_code(stock_code)

        try:
            # 获取最近的北向资金数据
            df = self.get_net_inflow(code, days=days)

            if df.empty:
                logger.warning(f"未找到股票 {code} 的北向资金持仓数据")
                return 0.0

            # 计算最近 N 天的持仓变化总和
            if 'holding_value_change' in df.columns:
                total_change = df['holding_value_change'].sum()
            elif 'net_inflow' in df.columns:
                total_change = df['net_inflow'].sum()
            else:
                logger.warning("无法计算持仓变化，缺少必要列")
                return 0.0

            logger.info(f"股票 {code} 最近 {days} 天持仓变化: {total_change:.2f} 万元")
            return total_change

        except Exception as e:
            logger.error(f"获取北向资金持仓变化失败: {e}")
            return 0.0

    def get_top_inflow(
        self,
        top_n: int = 10,
        date: Optional[str] = None
    ) -> pd.DataFrame:
        """
        获取北向资金净流入前 N 名股票

        Args:
            top_n: 返回前 N 名，默认 10
            date: 指定日期，格式 'YYYY-MM-DD'，默认最新日期

        Returns:
            DataFrame，包含股票代码、净流入金额等信息
        """
        self._ensure_initialized()

        try:
            # 使用 akshare 获取北向资金个股净流入排名
            df = self._ak.stock_hsgt_north_net_flow_in_individual(symbol="北向", indicator="今日")

            if df is None or df.empty:
                logger.warning("未获取到北向资金净流入排名数据")
                return pd.DataFrame()

            # 重命名列
            df = df.rename(columns={
                '代码': 'stock_code',
                '名称': 'stock_name',
                '今日净流入': 'net_inflow',
                '今日净流入占比': 'net_inflow_pct'
            })

            # 按净流入排序
            df = df.sort_values('net_inflow', ascending=False)

            # 返回前 N 名
            result = df.head(top_n).copy()

            logger.info(f"获取到北向资金净流入前 {len(result)} 名")
            return result

        except Exception as e:
            logger.error(f"获取北向资金净流入排名失败: {e}")
            return pd.DataFrame()

    def get_summary(self, stock_code: str) -> dict:
        """
        获取北向资金摘要信息

        Args:
            stock_code: 股票代码，如 'SH600000' 或 '600000'

        Returns:
            字典，包含北向资金摘要信息
        """
        self._ensure_initialized()

        code = self._normalize_stock_code(stock_code)

        try:
            # 获取最近 30 天的数据
            df = self.get_net_inflow(code, days=30)

            if df.empty:
                return {
                    'stock_code': code,
                    'status': 'no_data',
                    'message': '未找到北向资金数据'
                }

            # 计算统计信息
            latest = df.iloc[0] if len(df) > 0 else None

            summary = {
                'stock_code': code,
                'status': 'success',
                'latest_date': latest['date'].strftime('%Y-%m-%d') if latest is not None else None,
                'latest_holding_value': latest.get('holding_value', 0) if latest is not None else 0,
                'latest_holding_shares': latest.get('holding_shares', 0) if latest is not None else 0,
                'days_5_change': self.get_holding_change(code, days=5),
                'days_10_change': self.get_holding_change(code, days=10),
                'days_30_change': self.get_holding_change(code, days=30),
                'avg_daily_inflow': df['net_inflow'].mean() if 'net_inflow' in df.columns else 0,
                'total_inflow_30d': df['net_inflow'].sum() if 'net_inflow' in df.columns else 0,
            }

            return summary

        except Exception as e:
            logger.error(f"获取北向资金摘要失败: {e}")
            return {
                'stock_code': code,
                'status': 'error',
                'message': str(e)
            }


# 供测试使用
if __name__ == '__main__':
    tool = NorthMoneyTool()
    
    # 测试获取净流入
    print("=" * 50)
    print("测试获取北向资金净流入")
    df = tool.get_net_inflow('SH600000', days=10)
    print(df)
    
    # 测试获取持仓变化
    print("=" * 50)
    print("测试获取北向资金持仓变化")
    change = tool.get_holding_change('SH600000', days=5)
    print(f"最近 5 天持仓变化: {change:.2f} 万元")
    
    # 测试获取摘要
    print("=" * 50)
    print("测试获取北向资金摘要")
    summary = tool.get_summary('SH600000')
    for key, value in summary.items():
        print(f"{key}: {value}")
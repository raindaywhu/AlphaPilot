"""
投资策略回测工具

实现策略回测、收益计算、风险指标

Issue: #26 (BACKTEST-001)
"""

import os
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple

# 导入性能优化工具
from ..utils.performance import timing_decorator, monitor_performance

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BacktestEngine:
    """
    回测引擎
    
    实现投资策略的回测功能，计算收益和风险指标
    """
    
    def __init__(self, initial_capital: float = 100000.0):
        """
        初始化回测引擎
        
        Args:
            initial_capital: 初始资金（默认 10 万）
        """
        self.initial_capital = initial_capital
        logger.info(f"回测引擎初始化完成，初始资金: {initial_capital}")
    
    @monitor_performance("backtest")
    @timing_decorator
    def run_backtest(
        self,
        price_data: pd.DataFrame,
        signals: List[Dict[str, Any]],
        commission_rate: float = 0.0003
    ) -> Dict[str, Any]:
        """
        运行回测
        
        Args:
            price_data: 价格数据，需包含 date, close 列
            signals: 交易信号列表，格式: [{"date": "2024-01-01", "action": "buy", "shares": 100}, ...]
            commission_rate: 手续费率（默认 0.03%）
        
        Returns:
            回测结果
        """
        logger.info(f"开始回测，信号数量: {len(signals)}")
        
        # 初始化账户
        cash = self.initial_capital
        shares = 0
        trades = []
        equity_curve = []
        
        # 将价格数据转为字典便于查找
        price_dict = dict(zip(price_data['date'], price_data['close']))
        
        # 按日期排序信号
        sorted_signals = sorted(signals, key=lambda x: x['date'])
        
        # 执行交易
        for signal in sorted_signals:
            date = signal['date']
            action = signal['action']
            signal_shares = signal.get('shares', 0)
            
            if date not in price_dict:
                logger.warning(f"日期 {date} 无价格数据")
                continue
            
            price = price_dict[date]
            
            if action == 'buy' and cash > 0:
                # 买入
                max_shares = int(cash / price / 100) * 100  # 整手
                buy_shares = min(signal_shares, max_shares) if signal_shares > 0 else max_shares
                
                if buy_shares > 0:
                    cost = buy_shares * price * (1 + commission_rate)
                    cash -= cost
                    shares += buy_shares
                    
                    trades.append({
                        "date": date,
                        "action": "buy",
                        "price": price,
                        "shares": buy_shares,
                        "cost": cost
                    })
                    
                    logger.info(f"买入: {date}, 价格: {price:.2f}, 数量: {buy_shares}")
            
            elif action == 'sell' and shares > 0:
                # 卖出
                sell_shares = min(signal_shares, shares) if signal_shares > 0 else shares
                
                if sell_shares > 0:
                    revenue = sell_shares * price * (1 - commission_rate)
                    cash += revenue
                    shares -= sell_shares
                    
                    trades.append({
                        "date": date,
                        "action": "sell",
                        "price": price,
                        "shares": sell_shares,
                        "revenue": revenue
                    })
                    
                    logger.info(f"卖出: {date}, 价格: {price:.2f}, 数量: {sell_shares}")
            
            # 记录每日权益
            total_value = cash + shares * price
            equity_curve.append({
                "date": date,
                "cash": cash,
                "shares": shares,
                "price": price,
                "total_value": total_value
            })
        
        # 计算最终价值
        if shares > 0:
            last_date = price_data['date'].iloc[-1]
            last_price = price_data['close'].iloc[-1]
            final_value = cash + shares * last_price
        else:
            final_value = cash
        
        # 计算收益和风险指标
        returns = self._calculate_returns(equity_curve)
        risk_metrics = self._calculate_risk_metrics(returns, equity_curve)
        
        return {
            "initial_capital": self.initial_capital,
            "final_value": final_value,
            "total_return": (final_value - self.initial_capital) / self.initial_capital,
            "total_trades": len(trades),
            "trades": trades,
            "equity_curve": equity_curve,
            "risk_metrics": risk_metrics
        }
    
    def _calculate_returns(self, equity_curve: List[Dict]) -> pd.Series:
        """计算收益率序列"""
        if not equity_curve:
            return pd.Series()
        
        df = pd.DataFrame(equity_curve)
        df['return'] = df['total_value'].pct_change()
        return df['return'].dropna()
    
    def _calculate_risk_metrics(
        self,
        returns: pd.Series,
        equity_curve: List[Dict]
    ) -> Dict[str, Any]:
        """
        计算风险指标
        
        - 年化收益率
        - 夏普比率
        - 最大回撤
        - 胜率
        """
        if returns.empty or not equity_curve:
            return {}
        
        # 年化收益率
        total_days = len(equity_curve)
        total_return = (equity_curve[-1]['total_value'] - self.initial_capital) / self.initial_capital
        annualized_return = (1 + total_return) ** (252 / total_days) - 1 if total_days > 0 else 0
        
        # 夏普比率（假设无风险利率 3%）
        risk_free_rate = 0.03 / 252
        excess_returns = returns - risk_free_rate
        sharpe_ratio = (excess_returns.mean() / returns.std()) * np.sqrt(252) if returns.std() > 0 else 0
        
        # 最大回撤
        df = pd.DataFrame(equity_curve)
        df['peak'] = df['total_value'].cummax()
        df['drawdown'] = (df['total_value'] - df['peak']) / df['peak']
        max_drawdown = df['drawdown'].min()
        
        # 找到最大回撤的日期
        max_dd_idx = df['drawdown'].idxmin()
        max_dd_date = df.loc[max_dd_idx, 'date'] if max_dd_idx in df.index else None
        
        return {
            "annualized_return": f"{annualized_return * 100:.2f}%",
            "sharpe_ratio": round(sharpe_ratio, 2),
            "max_drawdown": f"{max_drawdown * 100:.2f}%",
            "max_drawdown_date": max_dd_date,
            "volatility": f"{returns.std() * np.sqrt(252) * 100:.2f}%",
            "win_rate": f"{(returns > 0).sum() / len(returns) * 100:.2f}%" if len(returns) > 0 else "0%"
        }
    
    def generate_signals_from_analysis(
        self,
        analysis_result: Dict[str, Any],
        stock_code: str
    ) -> List[Dict[str, Any]]:
        """
        从分析结果生成交易信号
        
        Args:
            analysis_result: InvestmentCrew 的分析结果
            stock_code: 股票代码
        
        Returns:
            交易信号列表
        """
        signals = []
        
        overall_rating = analysis_result.get("overall_rating", "中性")
        confidence = analysis_result.get("confidence", 0.5)
        
        # 根据评级和置信度生成信号
        if overall_rating == "看涨" and confidence > 0.6:
            signals.append({
                "date": datetime.now().strftime("%Y-%m-%d"),
                "action": "buy",
                "shares": 0,  # 自动计算
                "reason": f"综合评级: {overall_rating}, 置信度: {confidence}"
            })
        elif overall_rating == "看跌" and confidence > 0.6:
            signals.append({
                "date": datetime.now().strftime("%Y-%m-%d"),
                "action": "sell",
                "shares": 0,  # 全部卖出
                "reason": f"综合评级: {overall_rating}, 置信度: {confidence}"
            })
        
        return signals
    
    def generate_report(
        self,
        backtest_result: Dict[str, Any],
        stock_code: str
    ) -> str:
        """
        生成回测报告
        
        Args:
            backtest_result: 回测结果
            stock_code: 股票代码
        
        Returns:
            报告文本
        """
        risk = backtest_result.get("risk_metrics", {})
        
        report = f"""
# 回测报告 - {stock_code}

## 基本信息

| 指标 | 值 |
|------|-----|
| 初始资金 | ¥{backtest_result['initial_capital']:,.2f} |
| 最终价值 | ¥{backtest_result['final_value']:,.2f} |
| 总收益率 | {backtest_result['total_return'] * 100:.2f}% |
| 交易次数 | {backtest_result['total_trades']} |

## 风险指标

| 指标 | 值 |
|------|-----|
| 年化收益率 | {risk.get('annualized_return', 'N/A')} |
| 夏普比率 | {risk.get('sharpe_ratio', 'N/A')} |
| 最大回撤 | {risk.get('max_drawdown', 'N/A')} |
| 波动率 | {risk.get('volatility', 'N/A')} |
| 胜率 | {risk.get('win_rate', 'N/A')} |

## 交易记录

"""
        
        trades = backtest_result.get("trades", [])
        for trade in trades[:10]:  # 只显示前 10 条
            action_emoji = "🟢" if trade['action'] == 'buy' else "🔴"
            report += f"- {action_emoji} {trade['date']}: {trade['action']} {trade['shares']} 股 @ ¥{trade['price']:.2f}\n"
        
        if len(trades) > 10:
            report += f"\n... 共 {len(trades)} 条交易记录\n"
        
        return report


def main():
    """测试回测引擎"""
    print("=" * 60)
    print("回测引擎测试")
    print("=" * 60)
    
    # 创建测试数据
    dates = pd.date_range(start="2024-01-01", periods=100, freq="D")
    prices = 10 + np.cumsum(np.random.randn(100) * 0.1)
    
    price_data = pd.DataFrame({
        "date": dates.strftime("%Y-%m-%d"),
        "close": prices
    })
    
    # 创建测试信号
    signals = [
        {"date": "2024-01-05", "action": "buy", "shares": 1000},
        {"date": "2024-02-01", "action": "sell", "shares": 500},
        {"date": "2024-03-01", "action": "buy", "shares": 500},
        {"date": "2024-04-01", "action": "sell", "shares": 1000},
    ]
    
    # 运行回测
    engine = BacktestEngine(initial_capital=100000)
    result = engine.run_backtest(price_data, signals)
    
    # 生成报告
    report = engine.generate_report(result, "SH600519")
    print(report)
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
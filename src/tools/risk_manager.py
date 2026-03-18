"""
风控系统

实现风险评估、仓位建议、止损策略

Issue: #27 (RISK-001)
"""

import os
import logging
import numpy as np
from datetime import datetime
from typing import Dict, Any, Optional, List

# 导入性能优化工具
from ..utils.performance import timing_decorator, monitor_performance

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RiskManager:
    """
    风险管理器
    
    提供风险评估、仓位建议、止损策略
    """
    
    def __init__(
        self,
        max_position_pct: float = 0.3,  # 单只股票最大仓位
        max_drawdown_pct: float = 0.15,  # 最大回撤限制
        risk_free_rate: float = 0.03     # 无风险利率
    ):
        """
        初始化风险管理器
        
        Args:
            max_position_pct: 单只股票最大仓位比例
            max_drawdown_pct: 最大回撤限制
            risk_free_rate: 无风险利率
        """
        self.max_position_pct = max_position_pct
        self.max_drawdown_pct = max_drawdown_pct
        self.risk_free_rate = risk_free_rate
        logger.info(f"风险管理器初始化完成，最大仓位: {max_position_pct*100}%")
    
    @monitor_performance("risk")
    @timing_decorator
    def assess_risk(
        self,
        analysis_result: Dict[str, Any] = None,
        stock_code: str = None,
        portfolio_value: float = 100000,
        current_positions: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        风险评估
        
        Args:
            analysis_result: 分析结果（可选）
            stock_code: 股票代码（可选，如果未提供 analysis_result）
            portfolio_value: 投资组合总值
            current_positions: 当前持仓
        
        Returns:
            风险评估结果
        """
        logger.info("开始风险评估")
        
        # 支持直接传入 stock_code
        if analysis_result is None:
            analysis_result = {
                "stock_code": stock_code or "Unknown",
                "overall_rating": "中性",
                "confidence": 0.5
            }
        elif isinstance(analysis_result, str):
            # 如果传入的是字符串，作为 stock_code 处理
            analysis_result = {
                "stock_code": analysis_result,
                "overall_rating": "中性",
                "confidence": 0.5
            }
        
        stock_code = analysis_result.get("stock_code", "Unknown")
        overall_rating = analysis_result.get("overall_rating", "中性")
        confidence = analysis_result.get("confidence", 0.5)
        
        # 1. 计算风险等级
        risk_level = self._calculate_risk_level(overall_rating, confidence)
        
        # 2. 计算建议仓位
        position_advice = self._calculate_position(
            overall_rating,
            confidence,
            portfolio_value,
            current_positions
        )
        
        # 3. 计算止损点位
        stop_loss = self._calculate_stop_loss(analysis_result)
        
        # 4. 风险警告
        warnings = self._generate_warnings(
            analysis_result,
            current_positions
        )
        
        return {
            "stock_code": stock_code,
            "risk_level": risk_level,
            "position_advice": position_advice,
            "stop_loss": stop_loss,
            "warnings": warnings,
            "risk_metrics": {
                "confidence": confidence,
                "rating_risk": self._rating_to_risk(overall_rating),
                "volatility_risk": "中等"  # 简化处理
            }
        }
    
    def _calculate_risk_level(
        self,
        overall_rating: str,
        confidence: float
    ) -> str:
        """
        计算风险等级
        
        Args:
            overall_rating: 综合评级
            confidence: 置信度
        
        Returns:
            风险等级：低/中/高/极高
        """
        # 评级风险映射
        rating_risk = {
            "看涨": "低",
            "中性偏多": "中低",
            "中性": "中",
            "中性偏空": "中高",
            "看跌": "高"
        }
        
        base_risk = rating_risk.get(overall_rating, "中")
        
        # 置信度调整
        if confidence < 0.4:
            # 低置信度，风险升级
            risk_levels = ["低", "中低", "中", "中高", "高"]
            current_idx = risk_levels.index(base_risk) if base_risk in risk_levels else 2
            adjusted_idx = min(current_idx + 1, len(risk_levels) - 1)
            return risk_levels[adjusted_idx]
        
        return base_risk
    
    def _calculate_position(
        self,
        overall_rating: str,
        confidence: float,
        portfolio_value: float,
        current_positions: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        计算建议仓位
        
        Args:
            overall_rating: 综合评级
            confidence: 置信度
            portfolio_value: 投资组合总值
            current_positions: 当前持仓
        
        Returns:
            仓位建议
        """
        # 基础仓位（根据评级）
        base_position = {
            "看涨": 0.25,
            "中性偏多": 0.20,
            "中性": 0.15,
            "中性偏空": 0.10,
            "看跌": 0.0
        }
        
        position_pct = base_position.get(overall_rating, 0.15)
        
        # 置信度调整
        position_pct *= confidence
        
        # 限制最大仓位
        position_pct = min(position_pct, self.max_position_pct)
        
        # 计算金额
        position_value = portfolio_value * position_pct
        
        return {
            "position_pct": f"{position_pct * 100:.1f}%",
            "position_value": f"¥{position_value:,.0f}",
            "reason": f"基于评级'{overall_rating}'和置信度{confidence:.0%}",
            "max_allowed": f"{self.max_position_pct * 100:.0f}%"
        }
    
    def _calculate_stop_loss(
        self,
        analysis_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        计算止损点位
        
        Args:
            analysis_result: 分析结果
        
        Returns:
            止损建议
        """
        overall_rating = analysis_result.get("overall_rating", "中性")
        confidence = analysis_result.get("confidence", 0.5)
        
        # 止损比例（根据风险等级）
        stop_loss_pct = {
            "看涨": 0.08,      # 8% 止损
            "中性偏多": 0.10,  # 10% 止损
            "中性": 0.12,      # 12% 止损
            "中性偏空": 0.15,  # 15% 止损
            "看跌": 0.20      # 20% 止损（或直接清仓）
        }
        
        stop_pct = stop_loss_pct.get(overall_rating, 0.10)
        
        # 置信度调整
        if confidence < 0.5:
            stop_pct *= 0.8  # 低置信度，收紧止损
        
        return {
            "stop_loss_pct": f"{stop_pct * 100:.1f}%",
            "trailing_stop": f"{stop_pct * 0.8 * 100:.1f}%",
            "take_profit_pct": f"{stop_pct * 2 * 100:.1f}%",  # 盈亏比 2:1
            "reason": f"基于评级'{overall_rating}'，盈亏比设置为 2:1"
        }
    
    def _generate_warnings(
        self,
        analysis_result: Dict[str, Any],
        current_positions: Optional[List[Dict]] = None
    ) -> List[str]:
        """
        生成风险警告
        
        Args:
            analysis_result: 分析结果
            current_positions: 当前持仓
        
        Returns:
            风险警告列表
        """
        warnings = []
        
        overall_rating = analysis_result.get("overall_rating", "中性")
        confidence = analysis_result.get("confidence", 0.5)
        
        # 低置信度警告
        if confidence < 0.5:
            warnings.append(f"⚠️ 置信度较低({confidence:.0%})，建议谨慎操作")
        
        # 评级警告
        if overall_rating == "看跌":
            warnings.append("⚠️ 综合评级看跌，建议观望或减仓")
        elif overall_rating == "中性偏空":
            warnings.append("⚠️ 综合评级偏空，建议控制仓位")
        
        # 持仓集中度警告
        if current_positions and len(current_positions) > 5:
            warnings.append("⚠️ 持仓过于分散，建议集中优质标的")
        
        # Agent 分歧警告
        agent_ratings = analysis_result.get("agent_ratings", {})
        if len(set(agent_ratings.values())) > 2:
            warnings.append("⚠️ 各分析师观点分歧较大，建议等待更多信号")
        
        return warnings
    
    def _rating_to_risk(self, overall_rating: str) -> str:
        """评级转风险等级"""
        mapping = {
            "看涨": "低风险",
            "中性偏多": "中低风险",
            "中性": "中风险",
            "中性偏空": "中高风险",
            "看跌": "高风险"
        }
        return mapping.get(overall_rating, "中风险")
    
    def generate_risk_report(
        self,
        risk_assessment: Dict[str, Any]
    ) -> str:
        """
        生成风险报告
        
        Args:
            risk_assessment: 风险评估结果
        
        Returns:
            报告文本
        """
        stock_code = risk_assessment.get("stock_code", "Unknown")
        risk_level = risk_assessment.get("risk_level", "中")
        position = risk_assessment.get("position_advice", {})
        stop_loss = risk_assessment.get("stop_loss", {})
        warnings = risk_assessment.get("warnings", [])
        
        report = f"""
# 风险评估报告 - {stock_code}

## 风险等级

**{risk_level}**

## 仓位建议

| 指标 | 值 |
|------|-----|
| 建议仓位 | {position.get('position_pct', 'N/A')} |
| 建议金额 | {position.get('position_value', 'N/A')} |
| 最大允许 | {position.get('max_allowed', 'N/A')} |

**原因**: {position.get('reason', 'N/A')}

## 止损止盈

| 指标 | 值 |
|------|-----|
| 止损位 | {stop_loss.get('stop_loss_pct', 'N/A')} |
| 移动止损 | {stop_loss.get('trailing_stop', 'N/A')} |
| 止盈位 | {stop_loss.get('take_profit_pct', 'N/A')} |

**原因**: {stop_loss.get('reason', 'N/A')}

## 风险警告

"""
        
        if warnings:
            for warning in warnings:
                report += f"{warning}\n"
        else:
            report += "暂无风险警告 ✅\n"
        
        return report


def main():
    """测试风险管理器"""
    print("=" * 60)
    print("风险管理器测试")
    print("=" * 60)
    
    # 创建测试数据
    analysis_result = {
        "stock_code": "SH600519",
        "overall_rating": "看涨",
        "confidence": 0.75,
        "agent_ratings": {
            "quantitative": "看涨",
            "macro": "中性偏多",
            "alternative": "看涨"
        }
    }
    
    # 风险评估
    manager = RiskManager()
    result = manager.assess_risk(analysis_result, portfolio_value=100000)
    
    # 生成报告
    report = manager.generate_risk_report(result)
    print(report)
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
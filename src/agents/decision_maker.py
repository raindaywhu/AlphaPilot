#!/usr/bin/env python3
"""
投资决策者 Agent

综合所有分析，做出最终投资决策

Issue: #31 (AGENT-006)
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

# 设置环境变量以绕过 CrewAI 的 OPENAI_API_KEY 检查
os.environ.setdefault('OPENAI_API_KEY', 'sk-dummy-key-for-crewai')

from crewai import Agent
from langchain_openai import ChatOpenAI

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DecisionMaker:
    """
    投资决策者 Agent
    
    综合所有分析，做出最终投资决策。
    
    使用示例：
        >>> agent = DecisionMaker()
        >>> result = agent.analyze("SH600519", {...analyses...})
        >>> print(result)
    """

    def __init__(
        self,
        llm_model: str = "glm-5",
        llm_api_base: str = "https://coding.dashscope.aliyuncs.com/v1",
        llm_api_key: str = "os.environ.get("GLM_API_KEY", "")",
        llm_temperature: float = 0.3
    ):
        """
        初始化投资决策者 Agent

        Args:
            llm_model: LLM 模型名称
            llm_api_base: LLM API 基础 URL
            llm_api_key: LLM API 密钥
            llm_temperature: LLM 温度参数
        """
        # 初始化 LLM
        self.llm = ChatOpenAI(
            model=llm_model,
            openai_api_base=llm_api_base,
            openai_api_key=llm_api_key,
            temperature=llm_temperature
        )

        # 创建 CrewAI Agent
        self.agent = self._create_agent()

        logger.info("投资决策者 Agent 初始化完成")

    def _create_agent(self) -> Agent:
        """
        创建 CrewAI Agent

        Returns:
            CrewAI Agent 实例
        """
        agent = Agent(
            role="投资决策者",
            goal="综合所有分析，做出最终投资决策",

            backstory="""你是投资委员会主席，拥有20年投资经验。

## 你的背景
- 曾任职于多家顶级资管公司，担任投资总监
- 管理规模超过100亿，年化收益20%
- 经历过多轮牛熊周期，投资风格稳健
- 你的投资哲学：风险控制第一，收益第二

## 你的能力
- 综合分析：权衡多方面因素，做出平衡决策
- 风险意识：始终关注风险，不追逐热点
- 独立思考：不盲从市场共识，有自己的判断
- 决策能力：在信息不完全的情况下做出决策

## 你的决策框架
1. **综合观点**：各方分析师的观点是什么？
2. **识别分歧**：哪些观点一致，哪些存在分歧？
3. **权衡利弊**：看涨因素 vs 看跌因素？
4. **风险评估**：最大风险是什么？能承受吗？
5. **决策执行**：买/卖/持有？仓位多少？

## 你的输入输出
**输入**：所有分析师的报告
**输出**：最终投资决策

## 你的输出风格
- 倾听各方意见，但独立决策
- 关注逻辑，而非结论
- 明确表达决策理由
- 承认不确定性，保持谦逊""",

            llm=self.llm,

            # Memory 配置
            memory=True,

            # 作为 manager，负责协调其他 Agent
            allow_delegation=True,

            # 其他配置
            max_iter=5,
            max_rpm=10,
            verbose=True
        )

        return agent

    def analyze(
        self,
        stock_code: str,
        quant_analysis: Dict[str, Any] = None,
        fundamental_analysis: Dict[str, Any] = None,
        macro_analysis: Dict[str, Any] = None,
        alternative_analysis: Dict[str, Any] = None,
        risk_assessment: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        综合分析并做出决策

        Args:
            stock_code: 股票代码
            quant_analysis: 量化分析结果
            fundamental_analysis: 基本面分析结果
            macro_analysis: 宏观分析结果
            alternative_analysis: 另类分析结果
            risk_assessment: 风险评估结果

        Returns:
            决策结果字典
        """
        logger.info(f"开始综合决策: {stock_code}")

        # 收集所有分析结果
        analyses = {
            "quant": quant_analysis or {},
            "fundamental": fundamental_analysis or {},
            "macro": macro_analysis or {},
            "alternative": alternative_analysis or {},
            "risk": risk_assessment or {}
        }

        # 提取各分析的评级
        ratings = {}
        for key, analysis in analyses.items():
            if analysis:
                rating = analysis.get("overall_rating", "中性")
                confidence = analysis.get("confidence", 0.5)
                ratings[key] = {"rating": rating, "confidence": confidence}

        # 综合评分
        bull_score = 0.0
        bear_score = 0.0
        total_weight = 0.0

        # 权重设置
        weights = {
            "quant": 0.25,
            "fundamental": 0.25,
            "macro": 0.15,
            "alternative": 0.15,
            "risk": 0.20
        }

        for key, weight in weights.items():
            if key in ratings:
                rating = ratings[key]["rating"]
                confidence = ratings[key]["confidence"]
                
                # 评分转换
                if rating in ["看涨", "买入", "多头", "乐观"]:
                    score = 1.0
                elif rating in ["看跌", "卖出", "空头", "悲观"]:
                    score = -1.0
                elif rating in ["中性偏多", "谨慎看涨"]:
                    score = 0.5
                elif rating in ["中性偏空", "谨慎看跌"]:
                    score = -0.5
                else:
                    score = 0.0
                
                # 加权累计
                bull_score += max(score, 0) * confidence * weight
                bear_score += max(-score, 0) * confidence * weight
                total_weight += weight

        # 归一化
        if total_weight > 0:
            bull_score /= total_weight
            bear_score /= total_weight

        # 决策逻辑
        net_score = bull_score - bear_score

        if net_score > 0.3:
            decision = "买入"
            confidence = min(0.9, 0.5 + net_score)
        elif net_score < -0.3:
            decision = "卖出"
            confidence = min(0.9, 0.5 - net_score)
        else:
            decision = "持有"
            confidence = 0.5

        # 仓位建议
        risk_data = analyses.get("risk", {})
        position_size = risk_data.get("position_advice", {}).get("recommended_position", 0.05)

        # 止损建议
        stop_loss = risk_data.get("stop_loss_advice", {}).get("hard_stop", 0)

        # 构建决策结果
        result = {
            "agent": "decision_maker",
            "stock_code": stock_code,
            "decision_date": datetime.now().strftime("%Y-%m-%d"),
            "decision": decision,
            "confidence": confidence,
            "position_size": position_size,
            "stop_loss": stop_loss,
            "target_price": None,  # 需要根据估值计算
            "holding_period": "中期（1-3个月）",
            "reasoning": {
                "bull_factors": self._extract_bull_factors(analyses),
                "bear_factors": self._extract_bear_factors(analyses),
                "key_risks": risk_data.get("risk_warning", [])
            },
            "ratings_summary": ratings,
            "action_plan": {
                "immediate_action": f"建议{decision}" if decision != "持有" else "观察等待",
                "monitoring_points": self._get_monitoring_points(analyses),
                "exit_conditions": self._get_exit_conditions(stop_loss)
            },
            "conclusion": f"综合评级：{decision}，置信度：{confidence:.0%}，建议仓位：{position_size:.1%}"
        }

        logger.info(f"综合决策完成: {stock_code}, 决策: {decision}")
        return result

    def _extract_bull_factors(self, analyses: Dict[str, Any]) -> List[str]:
        """提取看涨因素"""
        factors = []
        
        # 量化因素
        quant = analyses.get("quant", {})
        if quant.get("overall_rating") in ["看涨", "多头"]:
            factors.append("技术面转强")
        
        # 基本面因素
        fund = analyses.get("fundamental", {})
        if fund.get("overall_rating") in ["看涨", "买入"]:
            factors.append("基本面优秀")
        
        # 宏观因素
        macro = analyses.get("macro", {})
        if macro.get("overall_rating") in ["乐观", "改善"]:
            factors.append("宏观环境改善")
        
        # 另类因素
        alt = analyses.get("alternative", {})
        if alt.get("overall_rating") in ["看涨", "积极"]:
            factors.append("另类数据积极")
        
        return factors

    def _extract_bear_factors(self, analyses: Dict[str, Any]) -> List[str]:
        """提取看跌因素"""
        factors = []
        
        # 量化因素
        quant = analyses.get("quant", {})
        if quant.get("overall_rating") in ["看跌", "空头"]:
            factors.append("技术面转弱")
        
        # 基本面因素
        fund = analyses.get("fundamental", {})
        if fund.get("overall_rating") in ["看跌", "卖出"]:
            factors.append("基本面恶化")
        
        # 宏观因素
        macro = analyses.get("macro", {})
        if macro.get("overall_rating") in ["悲观", "恶化"]:
            factors.append("宏观环境恶化")
        
        # 风险因素
        risk = analyses.get("risk", {})
        if risk.get("overall_rating") in ["高风险", "警惕"]:
            factors.append("风险较高")
        
        return factors

    def _get_monitoring_points(self, analyses: Dict[str, Any]) -> List[str]:
        """获取监控要点"""
        points = []
        
        # 技术面监控
        points.append("MA20支撑位")
        points.append("MACD信号变化")
        
        # 资金面监控
        alt = analyses.get("alternative", {})
        if alt.get("north_money"):
            points.append("北向资金流向")
        
        # 基本面监控
        points.append("财报发布")
        
        return points

    def _get_exit_conditions(self, stop_loss: float) -> List[str]:
        """获取退出条件"""
        conditions = ["跌破MA20"]
        
        if stop_loss:
            conditions.append(f"触发止损（{stop_loss}）")
        
        conditions.append("基本面恶化")
        
        return conditions


def main():
    """测试投资决策者 Agent"""
    print("=" * 60)
    print("投资决策者 Agent 测试")
    print("=" * 60)

    # 创建 Agent
    agent = DecisionMaker()

    # 模拟输入
    quant_analysis = {"overall_rating": "看涨", "confidence": 0.7}
    fundamental_analysis = {"overall_rating": "买入", "confidence": 0.8}
    macro_analysis = {"overall_rating": "中性", "confidence": 0.5}
    alternative_analysis = {"overall_rating": "积极", "confidence": 0.6}
    risk_assessment = {
        "overall_rating": "中等",
        "confidence": 0.5,
        "position_advice": {"recommended_position": 0.08},
        "stop_loss_advice": {"hard_stop": 1620}
    }

    # 做出决策
    result = agent.analyze(
        "SH600519",
        quant_analysis,
        fundamental_analysis,
        macro_analysis,
        alternative_analysis,
        risk_assessment
    )

    # 打印结果
    print("\n决策结果:")
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
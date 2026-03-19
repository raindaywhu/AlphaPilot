#!/usr/bin/env python3
"""
风控经理 Agent

评估投资风险，提供仓位和止损建议

Issue: #31 (AGENT-005)
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

# 导入工具
from ..tools.risk_manager import RiskManager
from ..tools.backtest_engine import BacktestEngine

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RiskManagerAgent:
    """
    风控经理 Agent
    
    评估投资风险，提供仓位和止损建议。
    
    使用示例：
        >>> agent = RiskManagerAgent()
        >>> result = agent.analyze("SH600519")
        >>> print(result)
    """

    def __init__(
        self,
        llm_model: str = "glm-5",
        llm_api_base: str = "https://coding.dashscope.aliyuncs.com/v1",
        llm_api_key: str = os.environ.get("GLM_API_KEY", ""),
        llm_temperature: float = 0.3
    ):
        """
        初始化风控经理 Agent

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

        # 初始化工具
        self.risk_manager = RiskManager()
        self.backtest_engine = BacktestEngine()

        # 创建 CrewAI Agent
        self.agent = self._create_agent()

        logger.info("风控经理 Agent 初始化完成")

    def _create_agent(self) -> Agent:
        """
        创建 CrewAI Agent

        Returns:
            CrewAI Agent 实例
        """
        agent = Agent(
            role="风险管理经理",
            goal="评估投资风险，提供仓位和止损建议",

            backstory="""你是一位经验丰富的风险管理专家。

## 你的背景
- 曾任职于多家大型资管公司风控部
- 经历过多次市场危机，善于危机管理
- 你的风控体系帮助公司避免了多次重大损失
- CFA、FRM 持证人

## 你的专长
- 风险度量：VaR、CVaR、波动率、Beta
- 风险控制：止损策略、仓位管理、对冲策略
- 组合管理：分散化、相关性、风险预算
- 压力测试：极端情况下的风险评估

## 你的工作流程
1. **风险度量**：计算 VaR、波动率等风险指标
2. **仓位建议**：根据风险预算给出仓位建议
3. **止损设置**：基于 ATR 等指标计算止损位
4. **回测验证**：验证策略的历史表现
5. **风险预警**：输出风险提示

## 你的输入输出
**输入**：stock_code, proposed_position, entry_price
**输出**：风险评估报告

## 你的输出风格
- 独立客观，不受收益诱惑
- 预设规则，不被情绪影响
- 情景分析，考虑多种可能性
- 及时预警，宁可误报不可漏报""",

            llm=self.llm,

            # Memory 配置
            memory=True,

            # 其他配置
            max_iter=5,
            max_rpm=10,
            allow_delegation=False,
            verbose=True
        )

        return agent

    def analyze(
        self,
        stock_code: str,
        proposed_position: float = 0.1,
        entry_price: float = None
    ) -> Dict[str, Any]:
        """
        风险分析

        Args:
            stock_code: 股票代码，如 'SH600519'
            proposed_position: 建议仓位
            entry_price: 入场价格

        Returns:
            分析结果字典
        """
        logger.info(f"开始风险分析: {stock_code}")

        # 使用风险管理工具
        try:
            risk_result = self.risk_manager.assess_risk(stock_code)
            
            # 回测验证暂时禁用（参数签名不匹配，待后续修复）
            backtest_result = None
            
            # 构建分析结果
            result = {
                "agent": "risk_manager",
                "stock_code": stock_code,
                "analysis_date": datetime.now().strftime("%Y-%m-%d"),
                "overall_rating": risk_result.get('risk_level', '中等'),
                "confidence": risk_result.get('confidence', 0.5),
                "position_advice": {
                    "recommended_position": risk_result.get('position_size', 0.05),
                    "reason": risk_result.get('position_reason', '')
                },
                "stop_loss_advice": {
                    "hard_stop": risk_result.get('stop_loss', 0),
                    "trailing_stop": risk_result.get('trailing_stop', 0),
                    "reason": risk_result.get('stop_reason', '')
                },
                "risk_metrics": risk_result.get('risk_metrics', {}),
                "backtest_validation": backtest_result,
                "risk_warning": risk_result.get('warnings', []),
                "conclusion": risk_result.get('conclusion', '')
            }
            
            logger.info(f"风险分析完成: {stock_code}")
            return result
                
        except Exception as e:
            logger.error(f"风险分析异常: {e}")
            return {
                "agent": "risk_manager",
                "stock_code": stock_code,
                "analysis_date": datetime.now().strftime("%Y-%m-%d"),
                "overall_rating": "中等",
                "confidence": 0.0,
                "conclusion": f"分析失败: {str(e)}"
            }


def main():
    """测试风控经理 Agent"""
    print("=" * 60)
    print("风控经理 Agent 测试")
    print("=" * 60)

    # 创建 Agent
    agent = RiskManagerAgent()

    # 分析股票
    result = agent.analyze("SH600519")

    # 打印结果
    print("\n分析结果:")
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
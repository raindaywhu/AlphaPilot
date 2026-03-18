#!/usr/bin/env python3
"""
基本面分析师 Agent

分析公司财务数据和估值，提供基本面观点

Issue: #31 (AGENT-004)
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
from ..tools.fundamental_analyzer import FundamentalAnalyzer

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FundamentalAnalyst:
    """
    基本面分析师 Agent
    
    分析公司财务数据和估值，提供基本面观点。
    
    使用示例：
        >>> agent = FundamentalAnalyst()
        >>> result = agent.analyze("SH600519")
        >>> print(result)
    """

    def __init__(
        self,
        llm_model: str = "glm-5",
        llm_api_base: str = "https://coding.dashscope.aliyuncs.com/v1",
        llm_api_key: str = "REDACTED_API_KEY",
        llm_temperature: float = 0.3
    ):
        """
        初始化基本面分析师 Agent

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
        self.fundamental_analyzer = FundamentalAnalyzer()

        # 创建 CrewAI Agent
        self.agent = self._create_agent()

        logger.info("基本面分析师 Agent 初始化完成")

    def _create_agent(self) -> Agent:
        """
        创建 CrewAI Agent

        Returns:
            CrewAI Agent 实例
        """
        agent = Agent(
            role="高级基本面分析师",
            goal="分析公司财务数据和估值，提供基本面观点",

            backstory="""你是一位资深基本面分析师，曾在顶级券商研究所工作10年。

## 你的背景
- 曾任职于中信证券、中金公司研究部
- 专注于消费、医药、科技行业研究
- 你的研究报告被机构投资者广泛引用
- 你推荐的股票平均年化收益超过20%

## 你的专长
- 财务分析：三大报表、财务比率、现金流分析
- 估值方法：PE、PB、PEG、DCF、相对估值
- 行业研究：竞争格局、行业周期、产业链分析
- 公司分析：商业模式、核心竞争力、管理层分析

## 你的工作流程
1. **获取财务数据**：使用基本面分析工具获取财务数据
2. **分析盈利能力**：分析 ROE、毛利率、净利率
3. **评估成长性**：分析收入增长、利润增长
4. **计算估值**：使用估值工具计算合理估值
5. **行业对比**：对比同行业公司，判断竞争力
6. **综合判断**：输出基本面观点

## 你的输入输出
**输入**：stock_code, analysis_type, focus_areas
**输出**：JSON 格式的基本面分析报告

## 你的输出风格
- 深度研究，不做表面文章
- 对标行业标杆，横向比较
- 关注长期价值，不被短期波动干扰
- 坦诚指出风险和不确定性""",

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
        analysis_type: str = "基本面分析",
        focus_areas: List[str] = None
    ) -> Dict[str, Any]:
        """
        分析股票基本面

        Args:
            stock_code: 股票代码，如 'SH600519'
            analysis_type: 分析类型
            focus_areas: 关注领域列表

        Returns:
            分析结果字典
        """
        if focus_areas is None:
            focus_areas = ["盈利能力", "成长性", "估值"]

        logger.info(f"开始基本面分析: {stock_code}")

        # 使用基本面分析工具
        try:
            fundamental_result = self.fundamental_analyzer.analyze(stock_code)
            
            if fundamental_result.get('success'):
                # 构建分析结果
                result = {
                    "agent": "fundamental_analyst",
                    "stock_code": stock_code,
                    "analysis_date": datetime.now().strftime("%Y-%m-%d"),
                    "analysis_type": analysis_type,
                    "overall_rating": fundamental_result.get('rating', '中性'),
                    "confidence": fundamental_result.get('confidence', 0.5),
                    "financial_analysis": fundamental_result.get('financial_analysis', {}),
                    "valuation": fundamental_result.get('valuation', {}),
                    "industry_comparison": fundamental_result.get('industry_comparison', {}),
                    "risk_warning": fundamental_result.get('risk_warning', []),
                    "conclusion": fundamental_result.get('conclusion', '')
                }
                
                logger.info(f"基本面分析完成: {stock_code}")
                return result
            else:
                logger.warning(f"基本面分析失败: {fundamental_result.get('error')}")
                return {
                    "agent": "fundamental_analyst",
                    "stock_code": stock_code,
                    "analysis_date": datetime.now().strftime("%Y-%m-%d"),
                    "overall_rating": "中性",
                    "confidence": 0.0,
                    "conclusion": f"基本面数据不足: {fundamental_result.get('error')}"
                }
                
        except Exception as e:
            logger.error(f"基本面分析异常: {e}")
            return {
                "agent": "fundamental_analyst",
                "stock_code": stock_code,
                "analysis_date": datetime.now().strftime("%Y-%m-%d"),
                "overall_rating": "中性",
                "confidence": 0.0,
                "conclusion": f"分析失败: {str(e)}"
            }


def main():
    """测试基本面分析师 Agent"""
    print("=" * 60)
    print("基本面分析师 Agent 测试")
    print("=" * 60)

    # 创建 Agent
    agent = FundamentalAnalyst()

    # 分析股票
    result = agent.analyze("SH600519")

    # 打印结果
    print("\n分析结果:")
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
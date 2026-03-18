#!/usr/bin/env python3
"""
另类数据分析师 Agent

分析北向资金、市场情绪、大宗商品等另类数据

Issue: (AGENT-003)
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import re

# 设置环境变量以绕过 CrewAI 的 OPENAI_API_KEY 检查
os.environ.setdefault('OPENAI_API_KEY', 'sk-dummy-key-for-crewai')

from crewai import Agent
from langchain_openai import ChatOpenAI

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AlternativeAnalyst:
    """
    另类数据分析师 Agent

    分析北向资金流向、市场情绪、大宗商品价格等另类数据。

    使用示例：
        >>> agent = AlternativeAnalyst()
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
        初始化另类数据分析师 Agent

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

        # 知识库路径
        self.knowledge_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "knowledge"
        )

        # 加载知识库
        self.knowledge = self._load_knowledge()

        # 创建 CrewAI Agent
        self.agent = self._create_agent()

        logger.info("另类数据分析师 Agent 初始化完成")

    def _load_knowledge(self) -> Dict[str, str]:
        """
        加载知识库内容

        Returns:
            知识库内容字典
        """
        knowledge = {}

        knowledge_files = {
            "alternative_data": "alternative_data.txt",
            "north_money_analysis": "north_money_analysis.txt",
            "commodity_analysis": "commodity_analysis.txt"
        }

        for name, filename in knowledge_files.items():
            filepath = os.path.join(self.knowledge_dir, filename)
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    knowledge[name] = f.read()
                logger.info(f"已加载知识库: {name}")
            else:
                logger.warning(f"知识库文件不存在: {filepath}")

        return knowledge

    def _create_agent(self) -> Agent:
        """
        创建 CrewAI Agent

        Returns:
            CrewAI Agent 实例
        """
        # 构建背景故事
        backstory = f"""你是一位资深的另类数据分析师，专注于通过非传统数据洞察市场。

你的专长领域：
1. **北向资金分析**：追踪外资流向，识别聪明钱的动向
2. **市场情绪分析**：通过舆情、资金流向等指标判断市场热度
3. **大宗商品分析**：分析铜、铝、原油、黄金等商品价格对股市的影响

你的分析方法论：
- 北向资金连续净流入 → 外资看好，可能预示上涨
- 北向资金大幅流出 → 外资撤离，需警惕风险
- 大宗商品价格上涨 → 相关板块可能受益（如铜涨价利好铜企）
- 市场情绪过热 → 需警惕回调风险

你的知识库内容：
{self.knowledge.get('alternative_data', '暂无')}
{self.knowledge.get('north_money_analysis', '暂无')}
{self.knowledge.get('commodity_analysis', '暂无')}

你的分析原则：
1. 数据驱动：基于真实数据分析，不凭感觉
2. 逻辑严谨：每个结论都有清晰的推导过程
3. 风险提示：及时识别潜在风险
4. 时效性：关注最新数据变化

你善于从另类数据中发现市场信号，为投资决策提供独特视角。"""

        agent = Agent(
            role="资深另类数据分析师",
            goal="通过北向资金、市场情绪、大宗商品等另类数据，提供独特的市场洞察",
            backstory=backstory,
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )

        return agent

    def analyze(
        self,
        stock_code: str,
        north_money_data: Optional[Dict] = None,
        commodity_data: Optional[Dict] = None,
        sentiment_data: Optional[Dict] = None,
        use_mock: bool = False
    ) -> Dict[str, Any]:
        """
        分析另类数据

        Args:
            stock_code: 股票代码（如 SH600519）
            north_money_data: 北向资金数据（可选）
            commodity_data: 大宗商品数据（可选）
            sentiment_data: 市场情绪数据（可选）
            use_mock: 是否使用模拟数据

        Returns:
            分析结果字典，包含：
            - stock_code: 股票代码
            - rating: 评级（1-10分）
            - confidence: 置信度（0-1）
            - logic_derivation: 逻辑推导
            - north_money_analysis: 北向资金分析
            - commodity_analysis: 大宗商品分析
            - sentiment_analysis: 市场情绪分析
            - risk_warning: 风险提示
        """
        logger.info(f"开始分析股票: {stock_code}")

        # 如果没有提供数据，使用模拟数据
        if use_mock or north_money_data is None:
            north_money_data = self._get_mock_north_money_data(stock_code)
        if use_mock or commodity_data is None:
            commodity_data = self._get_mock_commodity_data()
        if use_mock or sentiment_data is None:
            sentiment_data = self._get_mock_sentiment_data()

        # 构建分析提示
        prompt = f"""请分析股票 {stock_code} 的另类数据信号。

## 北向资金数据
{json.dumps(north_money_data, ensure_ascii=False, indent=2)}

## 大宗商品数据
{json.dumps(commodity_data, ensure_ascii=False, indent=2)}

## 市场情绪数据
{json.dumps(sentiment_data, ensure_ascii=False, indent=2)}

## 分析要求

请提供：
1. **北向资金分析**（2-3句话）：
   - 资金流向趋势
   - 对股价的影响判断
   - 风险提示

2. **大宗商品分析**（2-3句话）：
   - 主要商品价格走势
   - 对相关行业的影响
   - 投资启示

3. **市场情绪分析**（2-3句话）：
   - 当前市场情绪状态
   - 可能的风险或机会
   - 投资建议

4. **综合评级**（1-10分）：
   - 基于另类数据的综合评分
   - 评分理由

5. **置信度**（0-1）：
   - 分析结论的可信程度

6. **风险提示**：
   - 主要风险点

请以 JSON 格式返回结果，格式如下：
{{
    "rating": 8,
    "confidence": 0.8,
    "logic_derivation": "综合分析逻辑...",
    "north_money_analysis": "北向资金分析...",
    "commodity_analysis": "大宗商品分析...",
    "sentiment_analysis": "市场情绪分析...",
    "risk_warning": "风险提示..."
}}"""

        try:
            # 调用 LLM 进行分析
            response = self.llm.invoke(prompt)
            result_text = response.content

            # 提取 JSON 结果
            result = self._extract_json(result_text)

            # 添加股票代码
            result["stock_code"] = stock_code

            # 确保必要字段存在
            result.setdefault("rating", 5)
            result.setdefault("confidence", 0.5)
            result.setdefault("logic_derivation", "分析中...")
            result.setdefault("north_money_analysis", "数据不足")
            result.setdefault("commodity_analysis", "数据不足")
            result.setdefault("sentiment_analysis", "数据不足")
            result.setdefault("risk_warning", "数据有限，需谨慎决策")

            logger.info(f"分析完成，评级: {result['rating']}, 置信度: {result['confidence']}")

            return result

        except Exception as e:
            logger.error(f"分析失败: {e}")
            return {
                "stock_code": stock_code,
                "rating": 5,
                "confidence": 0.3,
                "logic_derivation": f"分析失败: {str(e)}",
                "north_money_analysis": "分析失败",
                "commodity_analysis": "分析失败",
                "sentiment_analysis": "分析失败",
                "risk_warning": "分析异常，请重试"
            }

    def _get_mock_north_money_data(self, stock_code: str) -> Dict[str, Any]:
        """
        获取模拟北向资金数据

        Args:
            stock_code: 股票代码

        Returns:
            模拟数据字典
        """
        return {
            "stock_code": stock_code,
            "net_inflow_5d": 150000000,  # 5日净流入（元）
            "net_inflow_20d": 520000000,  # 20日净流入（元）
            "holding_change": 0.05,  # 持仓变化（5%）
            "trend": "连续流入",
            "signal": "外资看好"
        }

    def _get_mock_commodity_data(self) -> Dict[str, Any]:
        """
        获取模拟大宗商品数据

        Returns:
            模拟数据字典
        """
        return {
            "copper": {
                "price": 75000,  # 铜价（元/吨）
                "change_5d": 0.03,  # 5日涨跌幅（3%）
                "trend": "上涨"
            },
            "aluminum": {
                "price": 20000,
                "change_5d": 0.02,
                "trend": "上涨"
            },
            "oil": {
                "price": 580,
                "change_5d": -0.01,
                "trend": "震荡"
            },
            "gold": {
                "price": 480,
                "change_5d": 0.01,
                "trend": "上涨"
            }
        }

    def _get_mock_sentiment_data(self) -> Dict[str, Any]:
        """
        获取模拟市场情绪数据

        Returns:
            模拟数据字典
        """
        return {
            "market_sentiment": "偏乐观",
            "fear_greed_index": 65,  # 恐惧贪婪指数（0-100）
            "volume_ratio": 1.2,  # 量比
            "hot_sectors": ["AI", "新能源", "医药"]
        }

    def _extract_json(self, text: str) -> Dict[str, Any]:
        """
        从文本中提取 JSON

        Args:
            text: 包含 JSON 的文本

        Returns:
            解析后的字典
        """
        # 尝试直接解析
        try:
            return json.loads(text)
        except:
            pass

        # 尝试提取 JSON 块
        json_pattern = r'\{[^{}]*\}'
        matches = re.findall(json_pattern, text, re.DOTALL)
        
        for match in matches:
            try:
                return json.loads(match)
            except:
                continue

        # 尝试提取 ```json ... ``` 格式
        json_block_pattern = r'```json\s*(\{.*?\})\s*```'
        matches = re.findall(json_block_pattern, text, re.DOTALL)
        
        for match in matches:
            try:
                return json.loads(match)
            except:
                continue

        logger.warning("无法提取有效 JSON，返回默认值")
        return {}

    def get_agent(self) -> Agent:
        """
        获取 CrewAI Agent 实例

        Returns:
            CrewAI Agent
        """
        return self.agent


# 主函数用于测试
if __name__ == "__main__":
    # 创建 Agent
    analyst = AlternativeAnalyst()
    
    # 测试分析
    result = analyst.analyze("SH600519", use_mock=True)
    
    print("\n" + "=" * 60)
    print("另类数据分析结果")
    print("=" * 60)
    print(json.dumps(result, ensure_ascii=False, indent=2))
#!/usr/bin/env python3
"""
量化分析师 Agent

基于 qlib 因子和模型预测，提供技术面分析观点

Issue: #12 (AGENT-001)
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

# 设置环境变量以绕过 CrewAI 的 OPENAI_API_KEY 检查
# 我们使用自定义 LLM（GLM-5），不需要 OpenAI
os.environ.setdefault('OPENAI_API_KEY', 'sk-dummy-key-for-crewai')

from crewai import Agent
from langchain_openai import ChatOpenAI

# 导入工具
from ..tools.alpha158_tool import Alpha158Tool
from ..tools.mootdx_tool import MootdxTool

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class QuantitativeAnalyst:
    """
    量化分析师 Agent

    基于 qlib 因子和模型预测，提供技术面分析观点。

    使用示例：
        >>> agent = QuantitativeAnalyst()
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
        初始化量化分析师 Agent

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
        self.alpha158_tool = Alpha158Tool()
        self.mootdx_tool = MootdxTool()  # 新增：全 A 股数据工具

        # 创建 CrewAI Agent
        self.agent = self._create_agent()

        logger.info("量化分析师 Agent 初始化完成")

    def _create_agent(self) -> Agent:
        """
        创建 CrewAI Agent

        Returns:
            CrewAI Agent 实例
        """
        agent = Agent(
            role="资深量化分析师",
            goal="基于 qlib 因子和模型预测，提供技术面分析观点",

            backstory="""你是一位拥有15年A股实战经验的量化分析师。

## 你的背景
- 曾任职于顶级量化私募，管理规模超过50亿
- 精通技术分析、因子投资、GBDT 模型
- 擅长从数据中发现交易机会
- 你的量化策略在过去5年实现了年化25%的收益

## 你的专长
- 技术指标：MA、MACD、RSI、KDJ、布林带、ATR等
- 因子分析：Alpha158 因子（动量、波动率、流动性、质量、价值）
- 模型预测：GBDT/XGBoost 预测模型
- 量化信号：买卖点识别、趋势判断

## 你的工作流程
1. **数据验证**：
   - 检查数据是否为最新（当日或前一交易日）
   - 如果数据过期，要求重新获取最新数据
   - 如果数据缺失，明确指出并尝试补充

2. **获取数据**：使用 qlib 工具获取因子数据和模型预测
3. **计算指标**：使用技术指标工具计算 MA、MACD、RSI 等
4. **回测验证**：使用回测工具验证历史信号有效性
5. **综合判断**：权衡多个信号，输出最终观点
6. **风险评估**：明确指出不确定性和风险

## ⚠️ 数据验证要求（必须执行）
在开始分析前，**必须验证数据时效性**：
- 检查日期：数据日期是否为最新交易日？
- 如果数据过期：输出警告，要求重新获取
- 如果数据缺失：明确指出缺失项，尝试补充
- **不要使用过期数据做决策！**

## 你的输入输出
**输入**：stock_code（股票代码）, analysis_type（分析类型）, time_horizon（预测周期）
**输出**：JSON 格式的技术面分析报告（包含详细评级和逻辑推导）

## 你的输出风格
- 数据驱动，每个结论都有数据支撑
- 简洁明了，直击要点
- 明确的观点，不模棱两可
- 风险提示，负责任的分析
- **详细展示评级结果和逻辑推导**""",

            # 注意：不使用 tools 参数，因为 Alpha158Tool 不是 CrewAI BaseTool
            # 直接在 analyze() 方法中调用 self.alpha158_tool

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
        analysis_type: str = "技术面分析",
        time_horizon: int = 5
    ) -> Dict[str, Any]:
        """
        分析股票技术面

        Args:
            stock_code: 股票代码，如 'SH600519'
            analysis_type: 分析类型，如 '技术面分析', '趋势判断', '买卖点识别'
            time_horizon: 预测周期（天）

        Returns:
            分析结果字典
        """
        logger.info(f"开始分析股票: {stock_code}")

        # 优先使用 MootdxTool（支持全 A 股）
        try:
            logger.info(f"使用 MootdxTool 获取数据...")
            mootdx_result = self.mootdx_tool.analyze(stock_code)
            
            if mootdx_result.get('success'):
                logger.info(f"MootdxTool 分析成功")
                
                # 构建 MootdxTool 的分析结果
                result = {
                    "agent": "quant_analyst",
                    "stock_code": stock_code,
                    "analysis_date": datetime.now().strftime("%Y-%m-%d"),
                    "analysis_type": analysis_type,
                    "time_horizon": time_horizon,
                    "data_validation": {
                        "status": "valid",
                        "latest_data_date": mootdx_result.get('latest_date'),
                        "data_points": mootdx_result.get('data_points'),
                        "warnings": []
                    },
                    "overall_rating": mootdx_result.get('rating', '中性'),
                    "confidence": mootdx_result.get('score', 50) / 100.0,
                    "factor_analysis": {
                        "technical_indicators": mootdx_result.get('indicators', {}),
                        "trend": mootdx_result.get('analysis', {}).get('trend', {}),
                        "macd": mootdx_result.get('analysis', {}).get('macd_signal', {}),
                        "rsi": mootdx_result.get('analysis', {}).get('rsi_signal', {}),
                        "kdj": mootdx_result.get('analysis', {}).get('kdj_signal', {})
                    },
                    "signals": self._extract_signals(mootdx_result),
                    "risk_warning": [
                        "MootdxTool 基于技术指标分析",
                        "建议结合基本面分析"
                    ],
                    "conclusion": self._build_conclusion(mootdx_result)
                }
                
                logger.info(f"分析完成: {stock_code}")
                return result
                
        except Exception as e:
            logger.warning(f"MootdxTool 分析失败: {e}，尝试使用 Alpha158Tool...")

        # 回退到 Alpha158Tool（仅支持 csi300）
        # 获取 Alpha158 因子数据
        try:
            # 使用最近3个月的数据
            end_date = datetime.now().strftime("%Y-%m-%d")
            start_date = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")

            factors_df = self.alpha158_tool.get_factors(
                instruments='csi300',
                start_time=start_date,
                end_time=end_date
            )

            # 筛选目标股票
            if stock_code in factors_df.index.get_level_values('instrument'):
                stock_factors = factors_df.xs(stock_code, level='instrument')
                logger.info(f"成功获取股票 {stock_code} 的因子数据")
            else:
                logger.warning(f"股票 {stock_code} 不在数据中")
                stock_factors = None

        except Exception as e:
            logger.error(f"获取因子数据失败: {e}")
            stock_factors = None

        # 构建分析结果
        result = {
            "agent": "quant_analyst",
            "stock_code": stock_code,
            "analysis_date": datetime.now().strftime("%Y-%m-%d"),
            "analysis_type": analysis_type,
            "time_horizon": time_horizon,
            "data_validation": {
                "status": "valid" if stock_factors is not None else "missing",
                "latest_data_date": end_date,
                "warnings": []
            },
            "overall_rating": "待分析",
            "confidence": 0.0,
            "factor_analysis": {},
            "signals": [],
            "risk_warning": [],
            "conclusion": "数据不足，无法完成分析"
        }

        # 如果有因子数据，进行分析
        if stock_factors is not None:
            # 分析因子
            factor_analysis = self._analyze_factors(stock_factors)
            result["factor_analysis"] = factor_analysis

            # 生成信号
            signals = self._generate_signals(stock_factors)
            result["signals"] = signals

            # 计算综合评分
            overall_rating, confidence = self._calculate_rating(factor_analysis, signals)
            result["overall_rating"] = overall_rating
            result["confidence"] = confidence

            # 生成结论
            result["conclusion"] = self._generate_conclusion(overall_rating, factor_analysis, signals)

            # 风险提示
            result["risk_warning"] = [
                "qlib 数据可能过期（截止 2020-09-25）",
                "GBDT 模型尚未训练",
                "技术指标工具尚未实现"
            ]

        logger.info(f"分析完成: {stock_code}")
        return result

    def _analyze_factors(self, factors_df) -> Dict[str, Any]:
        """
        分析因子数据

        Args:
            factors_df: 因子数据 DataFrame

        Returns:
            因子分析结果
        """
        # 获取最新一天的因子值
        latest = factors_df.iloc[-1]

        # 分析动量因子
        momentum_factors = ['ROC5', 'ROC10', 'ROC20', 'ROC30', 'ROC60']
        momentum_score = self._calculate_factor_score(latest, momentum_factors)

        # 分析波动率因子
        volatility_factors = ['STD5', 'STD10', 'STD20', 'STD30', 'STD60']
        volatility_score = self._calculate_factor_score(latest, volatility_factors)

        # 分析均线因子
        ma_factors = ['MA5', 'MA10', 'MA20', 'MA30', 'MA60']
        ma_score = self._calculate_factor_score(latest, ma_factors)

        return {
            "momentum": {
                "score": momentum_score,
                "rating": "看涨" if momentum_score > 0.5 else "看跌",
                "factors": {f: float(latest.get(f, 0)) for f in momentum_factors if f in latest.index}
            },
            "volatility": {
                "score": volatility_score,
                "rating": "适中" if 0.3 < volatility_score < 0.7 else "偏高",
                "factors": {f: float(latest.get(f, 0)) for f in volatility_factors if f in latest.index}
            },
            "moving_average": {
                "score": ma_score,
                "rating": "看涨" if ma_score > 0.5 else "看跌",
                "factors": {f: float(latest.get(f, 0)) for f in ma_factors if f in latest.index}
            }
        }

    def _calculate_factor_score(self, latest, factor_names: List[str]) -> float:
        """
        计算因子得分

        Args:
            latest: 最新因子数据
            factor_names: 因子名称列表

        Returns:
            因子得分（0-1）
        """
        values = [latest.get(f, 0) for f in factor_names if f in latest.index]
        if not values:
            return 0.5

        # 简单平均
        avg = sum(values) / len(values)

        # 归一化到 0-1
        # 这里使用简单的 sigmoid 函数
        import math
        score = 1 / (1 + math.exp(-avg))

        return score

    def _generate_signals(self, factors_df) -> List[Dict[str, Any]]:
        """
        生成交易信号

        Args:
            factors_df: 因子数据 DataFrame

        Returns:
            信号列表
        """
        signals = []

        # 获取最新两天的数据
        if len(factors_df) >= 2:
            latest = factors_df.iloc[-1]
            previous = factors_df.iloc[-2]

            # MA 信号
            if 'MA5' in latest.index and 'MA20' in latest.index:
                ma5_latest = latest['MA5']
                ma20_latest = latest['MA20']
                ma5_previous = previous['MA5']
                ma20_previous = previous['MA20']

                # 金叉检测
                if ma5_previous < ma20_previous and ma5_latest > ma20_latest:
                    signals.append({
                        "indicator": "MA",
                        "signal": "金叉",
                        "strength": "强",
                        "description": "MA5上穿MA20，短期趋势转强"
                    })
                # 死叉检测
                elif ma5_previous > ma20_previous and ma5_latest < ma20_latest:
                    signals.append({
                        "indicator": "MA",
                        "signal": "死叉",
                        "strength": "强",
                        "description": "MA5下穿MA20，短期趋势转弱"
                    })

            # ROC 信号
            if 'ROC5' in latest.index:
                roc5 = latest['ROC5']
                if roc5 > 0.05:
                    signals.append({
                        "indicator": "ROC",
                        "signal": "强势",
                        "strength": "中",
                        "description": f"ROC5 = {roc5:.2%}，动量强劲"
                    })
                elif roc5 < -0.05:
                    signals.append({
                        "indicator": "ROC",
                        "signal": "弱势",
                        "strength": "中",
                        "description": f"ROC5 = {roc5:.2%}，动量疲弱"
                    })

        return signals

    def _calculate_rating(
        self,
        factor_analysis: Dict[str, Any],
        signals: List[Dict[str, Any]]
    ) -> tuple:
        """
        计算综合评级

        Args:
            factor_analysis: 因子分析结果
            signals: 信号列表

        Returns:
            (评级, 置信度)
        """
        # 计算因子得分
        momentum_score = factor_analysis.get("momentum", {}).get("score", 0.5)
        volatility_score = factor_analysis.get("volatility", {}).get("score", 0.5)
        ma_score = factor_analysis.get("moving_average", {}).get("score", 0.5)

        # 综合得分
        total_score = (momentum_score * 0.4 + ma_score * 0.4 + (1 - volatility_score) * 0.2)

        # 信号加权
        signal_score = 0.5
        for signal in signals:
            if signal["signal"] in ["金叉", "强势"]:
                signal_score += 0.1
            elif signal["signal"] in ["死叉", "弱势"]:
                signal_score -= 0.1

        # 最终得分
        final_score = total_score * 0.7 + signal_score * 0.3

        # 确定评级
        if final_score > 0.65:
            rating = "看涨"
        elif final_score < 0.35:
            rating = "看跌"
        else:
            rating = "中性"

        # 置信度
        confidence = abs(final_score - 0.5) * 2

        return rating, confidence

    def _generate_conclusion(
        self,
        overall_rating: str,
        factor_analysis: Dict[str, Any],
        signals: List[Dict[str, Any]]
    ) -> str:
        """
        生成结论

        Args:
            overall_rating: 综合评级
            factor_analysis: 因子分析结果
            signals: 信号列表

        Returns:
            结论文本
        """
        # 构建结论
        parts = [f"技术面{overall_rating}"]

        # 添加因子分析
        momentum_rating = factor_analysis.get("momentum", {}).get("rating", "中性")
        parts.append(f"动量因子{momentum_rating}")

        # 添加信号
        if signals:
            signal_desc = "、".join([s["signal"] for s in signals[:3]])
            parts.append(f"信号：{signal_desc}")

        return "，".join(parts)
    
    def _extract_signals(self, mootdx_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        从 MootdxTool 结果中提取信号
        
        Args:
            mootdx_result: MootdxTool 分析结果
        
        Returns:
            信号列表
        """
        signals = []
        analysis = mootdx_result.get('analysis', {})
        
        # 趋势信号
        trend = analysis.get('trend', {})
        if trend.get('ma_trend') == 'bullish':
            signals.append({
                "indicator": "MA",
                "signal": "多头排列",
                "strength": "强",
                "description": trend.get('description', '')
            })
        elif trend.get('ma_trend') == 'bearish':
            signals.append({
                "indicator": "MA",
                "signal": "空头排列",
                "strength": "强",
                "description": trend.get('description', '')
            })
        
        # MACD 信号
        macd = analysis.get('macd_signal', {})
        if macd.get('signal') == 'golden_cross':
            signals.append({
                "indicator": "MACD",
                "signal": "金叉",
                "strength": "强",
                "description": macd.get('description', '')
            })
        elif macd.get('signal') == 'death_cross':
            signals.append({
                "indicator": "MACD",
                "signal": "死叉",
                "strength": "强",
                "description": macd.get('description', '')
            })
        
        # RSI 信号
        rsi = analysis.get('rsi_signal', {})
        if rsi.get('signal') == 'oversold':
            signals.append({
                "indicator": "RSI",
                "signal": "超卖",
                "strength": "中",
                "description": rsi.get('description', '')
            })
        elif rsi.get('signal') == 'overbought':
            signals.append({
                "indicator": "RSI",
                "signal": "超买",
                "strength": "中",
                "description": rsi.get('description', '')
            })
        
        # KDJ 信号
        kdj = analysis.get('kdj_signal', {})
        if kdj.get('signal') == 'bullish':
            signals.append({
                "indicator": "KDJ",
                "signal": "看涨",
                "strength": "中",
                "description": kdj.get('description', '')
            })
        elif kdj.get('signal') == 'bearish':
            signals.append({
                "indicator": "KDJ",
                "signal": "看跌",
                "strength": "中",
                "description": kdj.get('description', '')
            })
        
        return signals
    
    def _build_conclusion(self, mootdx_result: Dict[str, Any]) -> str:
        """
        构建 MootdxTool 分析的结论
        
        Args:
            mootdx_result: MootdxTool 分析结果
        
        Returns:
            结论文本
        """
        rating = mootdx_result.get('rating', '中性')
        score = mootdx_result.get('score', 50)
        analysis = mootdx_result.get('analysis', {})
        
        parts = [f"技术面{rating}"]
        
        # 添加趋势
        trend = analysis.get('trend', {})
        if trend.get('ma_trend'):
            parts.append(f"均线{trend['ma_trend']}")
        
        # 添加 MACD
        macd = analysis.get('macd_signal', {})
        if macd.get('signal'):
            parts.append(f"MACD{macd['signal']}")
        
        # 添加评分
        parts.append(f"综合评分{score}分")
        
        return "，".join(parts)


def main():
    """测试量化分析师 Agent"""
    print("=" * 60)
    print("量化分析师 Agent 测试")
    print("=" * 60)

    # 创建 Agent
    agent = QuantitativeAnalyst()

    # 分析股票
    result = agent.analyze("SH600000")

    # 打印结果
    print("\n分析结果:")
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
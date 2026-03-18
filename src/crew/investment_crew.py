#!/usr/bin/env python3
"""
投资分析 Crew

组装所有 Agent，实现投资分析流程

Issue: #7 (CREW-001)
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# 设置环境变量以绕过 CrewAI 的 OPENAI_API_KEY 检查
os.environ.setdefault('OPENAI_API_KEY', 'sk-dummy-key-for-crewai')

from crewai import Crew, Task, Agent

# 导入真实的 Agent
from ..agents.quantitative import QuantitativeAnalyst
from ..agents.macro import MacroAnalyst
from ..agents.alternative import AlternativeAnalyst

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MacroAnalystMock:
    """
    宏观分析师 Agent - Mock 实现（备用）
    """

    def __init__(self):
        logger.info("宏观分析师 Agent (Mock) 初始化完成")

    def analyze(self, stock_code: str, **kwargs) -> Dict[str, Any]:
        """Mock 分析宏观经济"""
        logger.info(f"[Mock] 宏观分析师分析: {stock_code}")
        return {
            "agent": "macro_analyst",
            "stock_code": stock_code,
            "rating": 5,
            "confidence": 0.5,
            "logic_derivation": "Mock 数据",
            "risk_warning": "Mock 数据，仅供参考"
        }


class AlternativeAnalystMock:
    """
    另类分析师 Agent - Mock 实现（备用）
    """

    def __init__(self):
        logger.info("另类分析师 Agent (Mock) 初始化完成")

    def analyze(self, stock_code: str, **kwargs) -> Dict[str, Any]:
        """Mock 分析另类数据"""
        logger.info(f"[Mock] 另类分析师分析: {stock_code}")
        return {
            "agent": "alternative_analyst",
            "stock_code": stock_code,
            "rating": 6,
            "confidence": 0.6,
            "logic_derivation": "Mock 数据",
            "risk_warning": "Mock 数据，仅供参考"
        }


class InvestmentCrew:
    """
    投资分析 Crew

    组装多个 Agent，实现完整的投资分析流程

    使用示例：
        >>> crew = InvestmentCrew()
        >>> result = crew.analyze("SH600519")
        >>> print(result)
    """

    def __init__(self, use_mock: bool = False):
        """
        初始化投资分析 Crew

        Args:
            use_mock: 是否使用 Mock Agent（默认 False，使用真实 Agent）
        """
        # 初始化量化分析师（真实）
        self.quant_analyst = QuantitativeAnalyst()

        # 初始化宏观分析师
        if use_mock:
            self.macro_analyst = MacroAnalystMock()
            logger.info("使用 Mock 宏观分析师")
        else:
            # 使用真实 Agent (AGENT-002)
            try:
                self.macro_analyst = MacroAnalyst()
                logger.info("使用真实宏观分析师 ✅")
            except Exception as e:
                logger.warning(f"宏观分析师初始化失败: {e}，使用 Mock")
                self.macro_analyst = MacroAnalystMock()

        # 初始化另类分析师
        if use_mock:
            self.alternative_analyst = AlternativeAnalystMock()
            logger.info("使用 Mock 另类分析师")
        else:
            # 使用真实 Agent (AGENT-003)
            try:
                self.alternative_analyst = AlternativeAnalyst()
                logger.info("使用真实另类分析师 ✅")
            except Exception as e:
                logger.warning(f"另类分析师初始化失败: {e}，使用 Mock")
                self.alternative_analyst = AlternativeAnalystMock()

        logger.info("投资分析 Crew 初始化完成")

    def analyze(
        self,
        stock_code: str,
        parallel: bool = True,
        time_horizon: int = 5
    ) -> Dict[str, Any]:
        """
        分析股票

        Args:
            stock_code: 股票代码，如 'SH600519'
            parallel: 是否并行分析（默认 True）
            time_horizon: 预测周期（天）

        Returns:
            综合分析结果
        """
        logger.info(f"开始投资分析: {stock_code}, 并行={parallel}")

        start_time = datetime.now()

        # 执行各 Agent 分析
        if parallel:
            # 并行分析
            results = self._analyze_parallel(stock_code, time_horizon)
        else:
            # 串行分析
            results = self._analyze_serial(stock_code, time_horizon)

        # 整合结果
        integrated_result = self._integrate_results(stock_code, results)

        # 计算耗时
        elapsed_time = (datetime.now() - start_time).total_seconds()
        integrated_result["execution_time"] = f"{elapsed_time:.2f}s"

        logger.info(f"投资分析完成: {stock_code}, 耗时 {elapsed_time:.2f}s")

        return integrated_result

    def _analyze_parallel(
        self,
        stock_code: str,
        time_horizon: int
    ) -> Dict[str, Any]:
        """
        并行执行所有 Agent 分析

        Args:
            stock_code: 股票代码
            time_horizon: 预测周期

        Returns:
            各 Agent 的分析结果
        """
        logger.info("执行并行分析")

        results = {}

        with ThreadPoolExecutor(max_workers=3) as executor:
            # 提交任务
            futures = {
                executor.submit(
                    self.quant_analyst.analyze,
                    stock_code,
                    "技术面分析",
                    time_horizon
                ): "quantitative",
                executor.submit(
                    self.macro_analyst.analyze,
                    stock_code
                ): "macro",
                executor.submit(
                    self.alternative_analyst.analyze,
                    stock_code
                ): "alternative"
            }

            # 收集结果
            for future in as_completed(futures):
                agent_name = futures[future]
                try:
                    results[agent_name] = future.result()
                    logger.info(f"{agent_name} 分析完成")
                except Exception as e:
                    logger.error(f"{agent_name} 分析失败: {e}")
                    results[agent_name] = {
                        "error": str(e),
                        "agent": agent_name,
                        "stock_code": stock_code
                    }

        return results

    def _analyze_serial(
        self,
        stock_code: str,
        time_horizon: int
    ) -> Dict[str, Any]:
        """
        串行执行所有 Agent 分析

        Args:
            stock_code: 股票代码
            time_horizon: 预测周期

        Returns:
            各 Agent 的分析结果
        """
        logger.info("执行串行分析")

        results = {}

        # 量化分析
        try:
            results["quantitative"] = self.quant_analyst.analyze(
                stock_code,
                "技术面分析",
                time_horizon
            )
            logger.info("量化分析完成")
        except Exception as e:
            logger.error(f"量化分析失败: {e}")
            results["quantitative"] = {"error": str(e)}

        # 宏观分析
        try:
            results["macro"] = self.macro_analyst.analyze(stock_code)
            logger.info("宏观分析完成")
        except Exception as e:
            logger.error(f"宏观分析失败: {e}")
            results["macro"] = {"error": str(e)}

        # 另类分析
        try:
            results["alternative"] = self.alternative_analyst.analyze(stock_code)
            logger.info("另类分析完成")
        except Exception as e:
            logger.error(f"另类分析失败: {e}")
            results["alternative"] = {"error": str(e)}

        return results

    def _integrate_results(
        self,
        stock_code: str,
        results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        整合所有 Agent 的分析结果

        Args:
            stock_code: 股票代码
            results: 各 Agent 的分析结果

        Returns:
            整合后的综合分析结果
        """
        logger.info("整合分析结果")

        # 提取各 Agent 的评级和置信度
        ratings = {}
        confidences = {}
        conclusions = {}

        for agent_name, result in results.items():
            if "error" not in result:
                ratings[agent_name] = result.get("overall_rating", "中性")
                confidences[agent_name] = result.get("confidence", 0.5)
                conclusions[agent_name] = result.get("conclusion", "无结论")
            else:
                ratings[agent_name] = "无法分析"
                confidences[agent_name] = 0.0
                conclusions[agent_name] = f"分析失败: {result['error']}"

        # 计算综合评级
        # 权重：量化 50%，宏观 25%，另类 25%
        weights = {
            "quantitative": 0.5,
            "macro": 0.25,
            "alternative": 0.25
        }

        # 将评级转换为分数
        rating_scores = {
            "看涨": 1.0,
            "中性偏多": 0.75,
            "中性": 0.5,
            "中性偏空": 0.25,
            "看跌": 0.0,
            "无法分析": 0.5
        }

        # 计算加权得分
        total_score = 0.0
        total_weight = 0.0

        for agent_name, rating in ratings.items():
            score = rating_scores.get(rating, 0.5)
            confidence = confidences.get(agent_name, 0.5)
            weight = weights.get(agent_name, 0.33) * confidence

            total_score += score * weight
            total_weight += weight

        # 归一化得分
        if total_weight > 0:
            final_score = total_score / total_weight
        else:
            final_score = 0.5

        # 确定最终评级
        if final_score >= 0.75:
            overall_rating = "看涨"
        elif final_score >= 0.6:
            overall_rating = "中性偏多"
        elif final_score >= 0.4:
            overall_rating = "中性"
        elif final_score >= 0.25:
            overall_rating = "中性偏空"
        else:
            overall_rating = "看跌"

        # 计算置信度
        avg_confidence = sum(confidences.values()) / len(confidences) if confidences else 0.5

        # 构建整合结果
        integrated = {
            "stock_code": stock_code,
            "analysis_date": datetime.now().strftime("%Y-%m-%d"),
            "overall_rating": overall_rating,
            "confidence": round(avg_confidence, 2),
            "score": round(final_score, 2),
            "agent_results": results,
            "agent_ratings": ratings,
            "agent_confidences": confidences,
            "agent_conclusions": conclusions,
            "summary": self._generate_summary(overall_rating, conclusions),
            "risk_warnings": [
                "量化分析师使用 qlib 数据（截止 2020-09-25），可能过期",
                "宏观分析师和另类分析师为 Mock 实现",
                "GBDT 模型尚未训练",
                "投资决策需谨慎，本分析仅供参考"
            ],
            "disclaimer": "本分析报告由 AI 系统自动生成，不构成投资建议"
        }

        return integrated

    def _generate_summary(
        self,
        overall_rating: str,
        conclusions: Dict[str, str]
    ) -> str:
        """
        生成分析摘要

        Args:
            overall_rating: 综合评级
            conclusions: 各 Agent 的结论

        Returns:
            摘要文本
        """
        parts = [f"综合评级：{overall_rating}"]

        for agent_name, conclusion in conclusions.items():
            agent_names = {
                "quantitative": "量化分析",
                "macro": "宏观分析",
                "alternative": "另类分析"
            }
            name = agent_names.get(agent_name, agent_name)
            parts.append(f"{name}：{conclusion}")

        return " | ".join(parts)


def main():
    """测试投资分析 Crew"""
    print("=" * 60)
    print("投资分析 Crew 测试")
    print("=" * 60)

    # 创建 Crew
    crew = InvestmentCrew(use_mock=True)

    # 分析股票
    result = crew.analyze("SH600000", parallel=True)

    # 打印结果
    print("\n综合分析结果:")
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
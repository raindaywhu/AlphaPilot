#!/usr/bin/env python3
"""
投资分析 Crew

组装所有 Agent，实现投资分析流程

Issue: #7 (CREW-001), #31 (补齐 3 个 Agent)
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

# 导入所有 Agent
from ..agents.quantitative import QuantitativeAnalyst
from ..agents.macro import MacroAnalyst
from ..agents.alternative import AlternativeAnalyst
from ..agents.fundamental import FundamentalAnalyst
from ..agents.risk_manager import RiskManagerAgent
from ..agents.decision_maker import DecisionMaker

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class InvestmentCrew:
    """
    投资分析 Crew

    组装 6 个 Agent，实现完整的投资分析流程：
    1. 量化分析师 - 技术面分析
    2. 基本面分析师 - 财务和估值分析
    3. 宏观分析师 - 宏观环境分析
    4. 另类分析师 - 另类数据分析
    5. 风控经理 - 风险评估
    6. 投资决策者 - 综合决策

    使用示例：
        >>> crew = InvestmentCrew()
        >>> result = crew.analyze("SH600519")
        >>> print(result)
    """

    def __init__(self):
        """
        初始化投资分析 Crew
        
        所有 Agent 使用真实数据分析，不使用 mock 数据。
        """
        # 初始化 6 个 Agent
        self._init_agents()
        
        logger.info("投资分析 Crew 初始化完成（6 Agent）")

    def _init_agents(self):
        """初始化所有 Agent"""
        
        # 1. 量化分析师（真实）
        self.quant_analyst = QuantitativeAnalyst()
        logger.info("量化分析师初始化 ✅")

        # 2. 基本面分析师
        try:
            self.fundamental_analyst = FundamentalAnalyst()
            logger.info("基本面分析师初始化 ✅")
        except Exception as e:
            logger.warning(f"基本面分析师初始化失败: {e}")
            self.fundamental_analyst = None

        # 3. 宏观分析师
        try:
            self.macro_analyst = MacroAnalyst()
            logger.info("宏观分析师初始化 ✅")
        except Exception as e:
            logger.warning(f"宏观分析师初始化失败: {e}")
            self.macro_analyst = None

        # 4. 另类分析师
        try:
            self.alternative_analyst = AlternativeAnalyst()
            logger.info("另类分析师初始化 ✅")
        except Exception as e:
            logger.warning(f"另类分析师初始化失败: {e}")
            self.alternative_analyst = None

        # 5. 风控经理
        try:
            self.risk_manager = RiskManagerAgent()
            logger.info("风控经理初始化 ✅")
        except Exception as e:
            logger.warning(f"风控经理初始化失败: {e}")
            self.risk_manager = None

        # 6. 投资决策者
        try:
            self.decision_maker = DecisionMaker()
            logger.info("投资决策者初始化 ✅")
        except Exception as e:
            logger.warning(f"投资决策者初始化失败: {e}")
            self.decision_maker = None

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

        # 第一阶段：并行执行 5 个分析 Agent
        if parallel:
            results = self._analyze_parallel(stock_code, time_horizon)
        else:
            results = self._analyze_serial(stock_code, time_horizon)

        # 第二阶段：风控评估
        risk_result = self._risk_analysis(stock_code, results)
        results["risk"] = risk_result

        # 第三阶段：投资决策者综合决策
        final_decision = self._make_decision(stock_code, results)

        # 计算耗时
        elapsed_time = (datetime.now() - start_time).total_seconds()
        final_decision["execution_time"] = f"{elapsed_time:.2f}s"

        logger.info(f"投资分析完成: {stock_code}, 耗时 {elapsed_time:.2f}s")

        return final_decision

    def _analyze_parallel(
        self,
        stock_code: str,
        time_horizon: int
    ) -> Dict[str, Any]:
        """并行执行分析"""
        logger.info("执行并行分析")

        results = {}

        # 准备任务
        tasks = {}
        if self.quant_analyst:
            tasks["quantitative"] = lambda: self.quant_analyst.analyze(
                stock_code, "技术面分析", time_horizon
            )
        if self.fundamental_analyst:
            tasks["fundamental"] = lambda: self.fundamental_analyst.analyze(stock_code)
        if self.macro_analyst:
            tasks["macro"] = lambda: self.macro_analyst.analyze(stock_code)
        if self.alternative_analyst:
            tasks["alternative"] = lambda: self.alternative_analyst.analyze(stock_code)

        # 并行执行
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {
                executor.submit(task): name
                for name, task in tasks.items()
            }

            for future in as_completed(futures):
                agent_name = futures[future]
                try:
                    results[agent_name] = future.result()
                    logger.info(f"{agent_name} 分析完成")
                except Exception as e:
                    logger.error(f"{agent_name} 分析失败: {e}")
                    results[agent_name] = {"error": str(e)}

        return results

    def _analyze_serial(
        self,
        stock_code: str,
        time_horizon: int
    ) -> Dict[str, Any]:
        """串行执行分析"""
        logger.info("执行串行分析")

        results = {}

        # 量化分析
        if self.quant_analyst:
            try:
                results["quantitative"] = self.quant_analyst.analyze(
                    stock_code, "技术面分析", time_horizon
                )
                logger.info("量化分析完成")
            except Exception as e:
                results["quantitative"] = {"error": str(e)}

        # 基本面分析
        if self.fundamental_analyst:
            try:
                results["fundamental"] = self.fundamental_analyst.analyze(stock_code)
                logger.info("基本面分析完成")
            except Exception as e:
                results["fundamental"] = {"error": str(e)}

        # 宏观分析
        if self.macro_analyst:
            try:
                results["macro"] = self.macro_analyst.analyze(stock_code)
                logger.info("宏观分析完成")
            except Exception as e:
                results["macro"] = {"error": str(e)}

        # 另类分析
        if self.alternative_analyst:
            try:
                results["alternative"] = self.alternative_analyst.analyze(stock_code)
                logger.info("另类分析完成")
            except Exception as e:
                results["alternative"] = {"error": str(e)}

        return results

    def _risk_analysis(
        self,
        stock_code: str,
        results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """风险分析"""
        if not self.risk_manager:
            return {"error": "风控经理未初始化"}

        try:
            risk_result = self.risk_manager.analyze(stock_code)
            logger.info("风险分析完成")
            return risk_result
        except Exception as e:
            logger.error(f"风险分析失败: {e}")
            return {"error": str(e)}

    def _make_decision(
        self,
        stock_code: str,
        results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """综合决策"""
        if not self.decision_maker:
            # 如果决策者未初始化，使用简单整合逻辑
            return self._simple_integrate(stock_code, results)

        try:
            decision = self.decision_maker.analyze(
                stock_code,
                quant_analysis=results.get("quantitative"),
                fundamental_analysis=results.get("fundamental"),
                macro_analysis=results.get("macro"),
                alternative_analysis=results.get("alternative"),
                risk_assessment=results.get("risk")
            )
            logger.info("投资决策完成")
            
            # 添加详细信息
            decision["agent_results"] = results
            return decision
            
        except Exception as e:
            logger.error(f"决策失败: {e}")
            return self._simple_integrate(stock_code, results)

    def _simple_integrate(
        self,
        stock_code: str,
        results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """简单整合结果（备用）"""
        
        # 提取评级
        ratings = {}
        for name, result in results.items():
            if isinstance(result, dict) and "error" not in result:
                ratings[name] = result.get("overall_rating", "中性")

        # 简单投票
        bull_count = sum(1 for r in ratings.values() if r in ["看涨", "买入", "多头"])
        bear_count = sum(1 for r in ratings.values() if r in ["看跌", "卖出", "空头"])
        
        if bull_count > bear_count:
            overall_rating = "看涨"
        elif bear_count > bull_count:
            overall_rating = "看跌"
        else:
            overall_rating = "中性"

        return {
            "stock_code": stock_code,
            "analysis_date": datetime.now().strftime("%Y-%m-%d"),
            "overall_rating": overall_rating,
            "confidence": 0.5,
            "agent_results": results,
            "agent_ratings": ratings,
            "conclusion": f"综合评级：{overall_rating}"
        }


def main():
    """测试投资分析 Crew"""
    print("=" * 60)
    print("投资分析 Crew 测试（6 Agent）")
    print("=" * 60)

    # 创建 Crew
    crew = InvestmentCrew()

    # 分析股票
    result = crew.analyze("SH600519")

    # 打印结果
    print("\n综合分析结果:")
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
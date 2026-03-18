"""
投资分析工作流

协调 Agent 执行的编排层

Issue: #36 (FLOW-001)
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from typing import Dict, Any, List, Optional
from datetime import datetime
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor

# 导入 Agents
from src.agents.quantitative import QuantitativeAnalyst
from src.agents.fundamental import FundamentalAnalyst
from src.agents.macro import MacroAnalyst
from src.agents.alternative import AlternativeAnalyst
from src.agents.risk_manager import RiskManagerAgent
from src.agents.decision_maker import DecisionMaker

# 导入 Tools
from src.tools.qlib_data_tool import QlibDataTool
from src.tools.report_generator import ReportGenerator
from src.tools.stock_lookup import StockLookupTool

logger = logging.getLogger(__name__)


class InvestmentAnalysisFlow:
    """
    投资分析工作流
    
    流程:
    1. 数据准备 → 2. 并行分析 → 3. 风险评估 → 4. 综合决策 → 5. 生成报告
    """
    
    def __init__(self, use_mock: bool = False):
        """
        初始化工作流
        
        Args:
            use_mock: 是否使用模拟数据
        """
        self.use_mock = use_mock
        
        # 初始化 Agent
        self.quant_analyst = QuantitativeAnalyst()
        self.fund_analyst = FundamentalAnalyst()
        self.macro_analyst = MacroAnalyst()
        self.alt_analyst = AlternativeAnalyst()
        self.risk_manager = RiskManagerAgent()
        self.decision_maker = DecisionMaker()
        
        # 初始化工具
        self.data_tool = QlibDataTool()
        self.report_generator = ReportGenerator()
        
        # 工作流状态
        self.state = {
            "stock_code": None,
            "stock_name": None,
            "data_ready": False,
            "analysis_results": {},
            "risk_assessment": {},
            "final_decision": {},
            "report_path": None
        }
    
    def run(self, stock_code: str, parallel: bool = True) -> Dict[str, Any]:
        """
        执行完整工作流
        
        Args:
            stock_code: 股票代码
            parallel: 是否并行执行分析
        
        Returns:
            分析结果
        """
        logger.info(f"开始投资分析工作流: {stock_code}")
        start_time = datetime.now()
        
        try:
            # 阶段 1: 数据准备
            self._prepare_data(stock_code)
            
            # 阶段 2: 并行分析
            if parallel:
                self._parallel_analysis()
            else:
                self._sequential_analysis()
            
            # 阶段 3: 风险评估
            self._risk_assessment()
            
            # 阶段 4: 综合决策
            self._final_decision()
            
            # 阶段 5: 生成报告
            self._generate_report()
            
            # 计算耗时
            end_time = datetime.now()
            execution_time = str(end_time - start_time)
            
            return {
                "status": "success",
                "stock_code": stock_code,
                "stock_name": self.state["stock_name"],
                "analysis_date": datetime.now().strftime("%Y-%m-%d"),
                "agent_results": self.state["analysis_results"],
                "risk_assessment": self.state["risk_assessment"],
                "overall_rating": self.state["final_decision"].get("decision", "持有"),
                "confidence": self.state["final_decision"].get("confidence", 0.5),
                "recommendation": self.state["final_decision"].get("conclusion", ""),
                "report_path": self.state["report_path"],
                "execution_time": execution_time
            }
            
        except Exception as e:
            logger.error(f"工作流执行失败: {e}")
            return {
                "status": "error",
                "stock_code": stock_code,
                "error": str(e)
            }
    
    def _prepare_data(self, stock_code: str):
        """
        阶段 1: 数据准备
        
        - 检查数据时效性
        - 获取股票名称
        - 准备分析所需数据
        """
        logger.info(f"[阶段1] 数据准备: {stock_code}")
        
        # 设置股票代码
        self.state["stock_code"] = stock_code
        
        # 使用 StockLookupTool 获取股票名称
        stock_info = StockLookupTool.lookup(stock_code)
        if stock_info:
            self.state["stock_code"] = stock_info["code"]  # 标准化代码
            self.state["stock_name"] = stock_info["name"]
        else:
            self.state["stock_name"] = stock_code
        
        # 检查 qlib 数据
        try:
            data = self.data_tool.get_kline_data(stock_code, days=30)
            if data is not None and len(data) > 0:
                self.state["data_ready"] = True
                logger.info(f"数据准备完成，获取到 {len(data)} 天数据")
            else:
                logger.warning("qlib 数据不足，将使用备选数据源")
                self.state["data_ready"] = False
        except Exception as e:
            logger.warning(f"数据检查失败: {e}")
            self.state["data_ready"] = False
    
    def _parallel_analysis(self):
        """
        阶段 2a: 并行分析
        
        4 个 Agent 并行执行
        """
        logger.info("[阶段2] 并行分析开始")
        
        stock_code = self.state["stock_code"]
        
        with ThreadPoolExecutor(max_workers=4) as executor:
            # 提交任务
            future_quant = executor.submit(self.quant_analyst.analyze, stock_code)
            future_fund = executor.submit(self.fund_analyst.analyze, stock_code)
            future_macro = executor.submit(self.macro_analyst.analyze, stock_code)
            future_alt = executor.submit(self.alt_analyst.analyze, stock_code)
            
            # 收集结果
            self.state["analysis_results"] = {
                "quantitative": future_quant.result(),
                "fundamental": future_fund.result(),
                "macro": future_macro.result(),
                "alternative": future_alt.result()
            }
        
        logger.info("并行分析完成")
    
    def _sequential_analysis(self):
        """
        阶段 2b: 顺序分析
        
        4 个 Agent 顺序执行
        """
        logger.info("[阶段2] 顺序分析开始")
        
        stock_code = self.state["stock_code"]
        
        self.state["analysis_results"] = {
            "quantitative": self.quant_analyst.analyze(stock_code),
            "fundamental": self.fund_analyst.analyze(stock_code),
            "macro": self.macro_analyst.analyze(stock_code),
            "alternative": self.alt_analyst.analyze(stock_code)
        }
        
        logger.info("顺序分析完成")
    
    def _risk_assessment(self):
        """
        阶段 3: 风险评估
        
        风控经理评估风险
        """
        logger.info("[阶段3] 风险评估")
        
        # 风险分析
        self.state["risk_assessment"] = self.risk_manager.analyze(
            stock_code=self.state["stock_code"]
        )
        
        logger.info("风险评估完成")
    
    def _final_decision(self):
        """
        阶段 4: 综合决策
        
        投资决策者综合判断
        """
        logger.info("[阶段4] 综合决策")
        
        # 传入各分析结果
        agent_results = self.state["analysis_results"]
        self.state["final_decision"] = self.decision_maker.analyze(
            stock_code=self.state["stock_code"],
            quant_analysis=agent_results.get("quantitative"),
            fundamental_analysis=agent_results.get("fundamental"),
            macro_analysis=agent_results.get("macro"),
            alternative_analysis=agent_results.get("alternative"),
            risk_assessment=self.state["risk_assessment"]
        )
        
        logger.info("综合决策完成")
    
    def _generate_report(self):
        """
        阶段 5: 生成报告
        
        生成 PDF 报告
        """
        logger.info("[阶段5] 生成报告")
        
        try:
            # 准备报告数据
            report_data = {
                "stock_code": self.state["stock_code"],
                "stock_name": self.state["stock_name"],
                "analysis_date": datetime.now().strftime("%Y-%m-%d"),
                "analysis_results": self.state["analysis_results"],
                "risk_assessment": self.state["risk_assessment"],
                "final_decision": self.state["final_decision"]
            }
            
            # 生成报告
            report_path = self.report_generator.generate_pdf(report_data)
            self.state["report_path"] = report_path
            
            logger.info(f"报告生成完成: {report_path}")
            
        except Exception as e:
            logger.warning(f"报告生成失败: {e}")
            self.state["report_path"] = None


# 测试代码
if __name__ == "__main__":
    flow = InvestmentAnalysisFlow(use_mock=True)
    result = flow.run("sh600519")
    
    import json
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
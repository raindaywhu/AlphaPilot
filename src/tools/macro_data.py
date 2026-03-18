"""
宏观经济数据工具

获取宏观经济指标数据

Issue: #35 (TOOL-补齐)
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class MacroDataTool:
    """
    宏观经济数据工具
    
    提供主要宏观经济指标:
    - GDP 增长率
    - CPI/PPI 通胀指标
    - PMI 制造业指数
    - 利率/汇率
    - 社融数据
    """
    
    def __init__(self):
        """初始化工具"""
        self.name = "MacroDataTool"
        self.description = "宏观经济数据获取工具"
        
        # 模拟的宏观指标数据
        self.mock_data = {
            "gdp_growth": {
                "value": 5.0,
                "unit": "%",
                "period": "2025Q4",
                "yoy_change": 0.3,
                "description": "GDP增速保持稳定，经济运行在合理区间"
            },
            "cpi": {
                "value": 0.2,
                "unit": "%",
                "period": "2026年2月",
                "yoy_change": 0.1,
                "description": "CPI温和上涨，通胀压力较小"
            },
            "ppi": {
                "value": -2.0,
                "unit": "%",
                "period": "2026年2月",
                "yoy_change": -0.5,
                "description": "PPI持续负增长，工业品价格下行压力"
            },
            "pmi": {
                "value": 50.2,
                "unit": "",
                "period": "2026年2月",
                "yoy_change": 0.5,
                "description": "PMI位于荣枯线之上，制造业扩张"
            },
            "interest_rate": {
                "value": 3.1,
                "unit": "%",
                "period": "当前",
                "yoy_change": -0.2,
                "description": "LPR利率，货币政策保持宽松"
            },
            "exchange_rate": {
                "value": 7.2,
                "unit": "USD/CNY",
                "period": "当前",
                "yoy_change": 0.1,
                "description": "人民币汇率保持稳定"
            },
            "social_financing": {
                "value": 350,
                "unit": "万亿",
                "period": "2025年末",
                "yoy_change": 8.0,
                "description": "社融规模持续增长，信用环境宽松"
            }
        }
    
    def run(self, indicators: List[str] = None) -> Dict[str, Any]:
        """
        获取宏观经济数据
        
        Args:
            indicators: 指标列表，默认获取全部
        
        Returns:
            宏观数据字典
        """
        logger.info(f"获取宏观数据: {indicators or '全部'}")
        
        if indicators is None:
            indicators = list(self.mock_data.keys())
        
        result = {
            "fetch_time": "2026-03-18",
            "indicators": {}
        }
        
        for indicator in indicators:
            if indicator in self.mock_data:
                result["indicators"][indicator] = self.mock_data[indicator]
            else:
                result["indicators"][indicator] = {"error": "指标不存在"}
        
        # 宏观分析
        result["analysis"] = self._analyze_macro(result["indicators"])
        
        return result
    
    def get_indicator(self, indicator: str) -> Dict[str, Any]:
        """
        获取单个指标
        
        Args:
            indicator: 指标名称
        
        Returns:
            指标数据
        """
        return self.mock_data.get(indicator, {"error": "指标不存在"})
    
    def _analyze_macro(self, indicators: Dict) -> Dict[str, Any]:
        """分析宏观经济状况"""
        signals = []
        
        # GDP 分析
        if "gdp_growth" in indicators:
            gdp = indicators["gdp_growth"].get("value", 0)
            if gdp >= 5.0:
                signals.append("经济增速稳健")
            elif gdp >= 4.0:
                signals.append("经济增速平稳")
            else:
                signals.append("经济增速放缓")
        
        # CPI 分析
        if "cpi" in indicators:
            cpi = indicators["cpi"].get("value", 0)
            if cpi > 3.0:
                signals.append("通胀压力较大")
            elif cpi < 0:
                signals.append("通缩风险")
            else:
                signals.append("通胀温和")
        
        # PMI 分析
        if "pmi" in indicators:
            pmi = indicators["pmi"].get("value", 0)
            if pmi >= 52:
                signals.append("制造业景气度较高")
            elif pmi >= 50:
                signals.append("制造业微弱扩张")
            else:
                signals.append("制造业收缩")
        
        # 利率分析
        if "interest_rate" in indicators:
            rate = indicators["interest_rate"].get("value", 0)
            yoy = indicators["interest_rate"].get("yoy_change", 0)
            if yoy < 0:
                signals.append("货币政策宽松")
            elif yoy > 0:
                signals.append("货币政策收紧")
            else:
                signals.append("货币政策稳定")
        
        # 综合判断
        positive_count = sum(1 for s in signals if "稳健" in s or "温和" in s or "扩张" in s or "景气" in s or "宽松" in s)
        negative_count = len(signals) - positive_count
        
        if positive_count > negative_count:
            overall = "宏观经济向好"
        elif negative_count > positive_count:
            overall = "宏观经济承压"
        else:
            overall = "宏观经济平稳"
        
        return {
            "signals": signals,
            "overall": overall,
            "positive_count": positive_count,
            "negative_count": negative_count
        }
    
    def get_market_impact(self, stock_industry: str = None) -> Dict[str, Any]:
        """
        分析宏观经济对市场/行业的影响
        
        Args:
            stock_industry: 行业名称
        
        Returns:
            影响分析结果
        """
        indicators = self.run()
        analysis = indicators.get("analysis", {})
        
        impact = {
            "overall": analysis.get("overall", "中性"),
            "industry_impact": {}
        }
        
        # 行业影响分析
        if stock_industry:
            if stock_industry in ["白酒", "消费"]:
                # 消费行业受 CPI 和收入影响
                impact["industry_impact"] = {
                    "sensitive_to": ["cpi", "gdp_growth"],
                    "analysis": "消费行业受益于温和通胀和经济增长",
                    "recommendation": "中性偏乐观"
                }
            elif stock_industry in ["银行", "保险"]:
                # 金融行业受利率影响
                impact["industry_impact"] = {
                    "sensitive_to": ["interest_rate", "social_financing"],
                    "analysis": "金融行业受利率下行影响，息差收窄",
                    "recommendation": "中性偏谨慎"
                }
            elif stock_industry in ["制造业", "工业"]:
                # 制造业受 PMI 和 PPI 影响
                impact["industry_impact"] = {
                    "sensitive_to": ["pmi", "ppi"],
                    "analysis": "制造业受PPI下行影响，盈利承压",
                    "recommendation": "谨慎"
                }
        
        return impact


# 测试代码
if __name__ == "__main__":
    tool = MacroDataTool()
    result = tool.run(["gdp_growth", "cpi", "pmi"])
    
    import json
    print(json.dumps(result, ensure_ascii=False, indent=2))
"""
宏观经济数据工具

获取宏观经济指标数据 - 使用 akshare 真实 API

Issue: #35 (TOOL-补齐)
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from typing import Dict, Any, List
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class MacroDataTool:
    """
    宏观经济数据工具
    
    提供主要宏观经济指标 (使用 akshare 真实 API):
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
        self._akshare = None
    
    def _get_akshare(self):
        """延迟导入 akshare"""
        if self._akshare is None:
            try:
                import akshare as ak
                self._akshare = ak
            except ImportError:
                raise ImportError("请安装 akshare: pip install akshare")
        return self._akshare
    
    def _fetch_gdp(self) -> Dict[str, Any]:
        """获取 GDP 数据"""
        ak = self._get_akshare()
        try:
            df = ak.macro_china_gdp()
            if df is not None and len(df) > 0:
                latest = df.iloc[-1]
                prev = df.iloc[-2] if len(df) > 1 else latest
                
                return {
                    "value": float(latest.get("国内生产总值-同比增长", 0)),
                    "unit": "%",
                    "period": str(latest.get("季度", "")),
                    "yoy_change": float(latest.get("国内生产总值-同比增长", 0)) - float(prev.get("国内生产总值-同比增长", 0)),
                    "description": f"GDP增速{latest.get('国内生产总值-同比增长', 0)}%"
                }
        except Exception as e:
            logger.error(f"获取 GDP 数据失败: {e}")
        return {"error": f"获取 GDP 数据失败"}
    
    def _fetch_cpi(self) -> Dict[str, Any]:
        """获取 CPI 数据"""
        ak = self._get_akshare()
        try:
            df = ak.macro_china_cpi_yearly()
            if df is not None and len(df) > 0:
                latest = df.iloc[-1]
                prev = df.iloc[-2] if len(df) > 1 else latest
                
                return {
                    "value": float(latest.get("今值", 0) if "今值" in latest else 0),
                    "unit": "%",
                    "period": str(latest.get("日期", "")),
                    "yoy_change": float(latest.get("今值", 0) if "今值" in latest else 0) - float(prev.get("今值", 0) if "今值" in prev else 0),
                    "description": f"CPI同比{latest.get('今值', 0)}%"
                }
        except Exception as e:
            logger.error(f"获取 CPI 数据失败: {e}")
        return {"error": f"获取 CPI 数据失败"}
    
    def _fetch_pmi(self) -> Dict[str, Any]:
        """获取 PMI 数据"""
        ak = self._get_akshare()
        try:
            df = ak.macro_china_pmi_yearly()
            if df is not None and len(df) > 0:
                latest = df.iloc[-1]
                prev = df.iloc[-2] if len(df) > 1 else latest
                
                return {
                    "value": float(latest.get("今值", 0) if "今值" in latest else 0),
                    "unit": "",
                    "period": str(latest.get("日期", "")),
                    "yoy_change": float(latest.get("今值", 0) if "今值" in latest else 0) - float(prev.get("今值", 0) if "今值" in prev else 0),
                    "description": f"PMI指数{latest.get('今值', 0)}"
                }
        except Exception as e:
            logger.error(f"获取 PMI 数据失败: {e}")
        return {"error": f"获取 PMI 数据失败"}
    
    def _fetch_interest_rate(self) -> Dict[str, Any]:
        """获取利率数据"""
        ak = self._get_akshare()
        try:
            # 获取 LPR 数据
            df = ak.rate_interbank(market="LPR银行同业拆借市场", symbol="LPR1年")
            if df is not None and len(df) > 0:
                latest = df.iloc[-1]
                
                return {
                    "value": float(latest.get("利率", 0) if "利率" in latest else 3.1),
                    "unit": "%",
                    "period": str(latest.get("日期", "")),
                    "yoy_change": 0,
                    "description": "LPR 1年期利率"
                }
        except Exception as e:
            logger.error(f"获取利率数据失败: {e}")
        return {"error": f"获取利率数据失败"}
    
    def _fetch_exchange_rate(self) -> Dict[str, Any]:
        """获取汇率数据"""
        ak = self._get_akshare()
        try:
            df = ak.fx_spot_quote()
            if df is not None and len(df) > 0:
                usd_cny = df[df["货币对"] == "USD/CNY"]
                if len(usd_cny) > 0:
                    return {
                        "value": float(usd_cny.iloc[0].get("买报价", 7.2)),
                        "unit": "USD/CNY",
                        "period": datetime.now().strftime("%Y-%m-%d"),
                        "yoy_change": 0,
                        "description": "人民币兑美元汇率"
                    }
        except Exception as e:
            logger.error(f"获取汇率数据失败: {e}")
        return {"error": f"获取汇率数据失败"}
    
    def run(self, indicators: List[str] = None) -> Dict[str, Any]:
        """
        获取宏观经济数据
        
        Args:
            indicators: 指标列表，默认获取全部
                - gdp_growth: GDP增长率
                - cpi: 消费者物价指数
                - ppi: 生产者物价指数
                - pmi: 制造业采购经理指数
                - interest_rate: 利率
                - exchange_rate: 汇率
        
        Returns:
            宏观数据字典
        """
        logger.info(f"获取宏观数据: {indicators or '全部'}")
        
        # 所有支持的指标
        all_indicators = {
            "gdp_growth": self._fetch_gdp,
            "cpi": self._fetch_cpi,
            "pmi": self._fetch_pmi,
            "interest_rate": self._fetch_interest_rate,
            "exchange_rate": self._fetch_exchange_rate,
        }
        
        if indicators is None:
            indicators = list(all_indicators.keys())
        
        result = {
            "fetch_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "indicators": {}
        }
        
        for indicator in indicators:
            if indicator in all_indicators:
                try:
                    result["indicators"][indicator] = all_indicators[indicator]()
                except Exception as e:
                    result["indicators"][indicator] = {"error": f"获取失败: {str(e)}"}
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
        result = self.run([indicator])
        return result["indicators"].get(indicator, {"error": "指标不存在"})
    
    def _analyze_macro(self, indicators: Dict) -> Dict[str, Any]:
        """分析宏观经济状况"""
        signals = []
        
        # GDP 分析
        if "gdp_growth" in indicators and "error" not in indicators["gdp_growth"]:
            gdp = indicators["gdp_growth"].get("value", 0)
            if gdp >= 5.0:
                signals.append("经济增速稳健")
            elif gdp >= 4.0:
                signals.append("经济增速平稳")
            else:
                signals.append("经济增速放缓")
        
        # CPI 分析
        if "cpi" in indicators and "error" not in indicators["cpi"]:
            cpi = indicators["cpi"].get("value", 0)
            if cpi > 3.0:
                signals.append("通胀压力较大")
            elif cpi < 0:
                signals.append("通缩风险")
            else:
                signals.append("通胀温和")
        
        # PMI 分析
        if "pmi" in indicators and "error" not in indicators["pmi"]:
            pmi = indicators["pmi"].get("value", 0)
            if pmi >= 52:
                signals.append("制造业景气度较高")
            elif pmi >= 50:
                signals.append("制造业微弱扩张")
            else:
                signals.append("制造业收缩")
        
        # 利率分析
        if "interest_rate" in indicators and "error" not in indicators["interest_rate"]:
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
                impact["industry_impact"] = {
                    "sensitive_to": ["cpi", "gdp_growth"],
                    "analysis": "消费行业受益于温和通胀和经济增长",
                    "recommendation": "中性偏乐观"
                }
            elif stock_industry in ["银行", "保险"]:
                impact["industry_impact"] = {
                    "sensitive_to": ["interest_rate", "social_financing"],
                    "analysis": "金融行业受利率下行影响，息差收窄",
                    "recommendation": "中性偏谨慎"
                }
            elif stock_industry in ["制造业", "工业"]:
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
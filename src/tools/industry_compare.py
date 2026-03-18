"""
行业对比工具

用于比较股票与同行业其他公司的估值和财务指标

Issue: #35 (TOOL-补齐)
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


class IndustryCompareTool:
    """
    行业对比工具
    
    对比股票与同行业公司的:
    - PE/PB 估值
    - ROE/毛利率 盈利能力
    - 营收增长率
    """
    
    def __init__(self):
        """初始化工具"""
        self.name = "IndustryCompareTool"
        self.description = "行业对比分析，比较估值和财务指标"
        
        # 行业分类（简化版）
        self.industry_map = {
            "sh600519": "白酒",
            "sz000858": "白酒",
            "sh600036": "银行",
            "sh601318": "保险",
            "sz000001": "银行",
            "sh601166": "银行"
        }
        
        # 行业基准数据
        self.industry_benchmarks = {
            "白酒": {
                "avg_pe": 35.0,
                "avg_pb": 8.0,
                "avg_roe": 0.25,
                "avg_gross_margin": 0.75
            },
            "银行": {
                "avg_pe": 6.0,
                "avg_pb": 0.6,
                "avg_roe": 0.12,
                "avg_gross_margin": 0.40
            },
            "保险": {
                "avg_pe": 12.0,
                "avg_pb": 1.2,
                "avg_roe": 0.10,
                "avg_gross_margin": 0.30
            }
        }
    
    def run(self, stock_code: str, metrics: List[str] = None) -> Dict[str, Any]:
        """
        执行行业对比
        
        Args:
            stock_code: 股票代码
            metrics: 对比指标列表，默认全部
        
        Returns:
            对比结果
        """
        logger.info(f"行业对比分析: {stock_code}")
        
        if metrics is None:
            metrics = ["pe", "pb", "roe", "gross_margin"]
        
        result = {
            "stock_code": stock_code,
            "industry": self._get_industry(stock_code),
            "comparison": {}
        }
        
        # 获取股票数据
        stock_data = self._get_stock_data(stock_code)
        
        # 获取行业基准
        industry = result["industry"]
        if industry in self.industry_benchmarks:
            benchmark = self.industry_benchmarks[industry]
            
            for metric in metrics:
                if metric in ["pe", "pb"]:
                    result["comparison"][f"{metric}_ratio"] = self._compare_valuation(
                        stock_data.get(metric, 0),
                        benchmark.get(f"avg_{metric}", 0),
                        metric
                    )
                elif metric in ["roe", "gross_margin"]:
                    result["comparison"][metric] = self._compare_profitability(
                        stock_data.get(metric, 0),
                        benchmark.get(f"avg_{metric}", 0),
                        metric
                    )
        else:
            result["comparison"]["note"] = "该股票暂无行业基准数据"
        
        # 综合评价
        result["summary"] = self._summarize(result["comparison"])
        
        return result
    
    def _get_industry(self, stock_code: str) -> str:
        """获取股票所属行业"""
        return self.industry_map.get(stock_code.lower(), "其他")
    
    def _get_stock_data(self, stock_code: str) -> Dict[str, float]:
        """获取股票财务数据（简化版）"""
        # 模拟数据，实际应从 API 获取
        mock_data = {
            "sh600519": {"pe": 30.0, "pb": 7.5, "roe": 0.28, "gross_margin": 0.91},
            "sz000858": {"pe": 25.0, "pb": 6.0, "roe": 0.22, "gross_margin": 0.75},
            "sh600036": {"pe": 5.5, "pb": 0.8, "roe": 0.15, "gross_margin": 0.45},
            "sh601318": {"pe": 10.0, "pb": 1.0, "roe": 0.12, "gross_margin": 0.35}
        }
        
        return mock_data.get(stock_code.lower(), {"pe": 20.0, "pb": 2.0, "roe": 0.10, "gross_margin": 0.30})
    
    def _compare_valuation(self, stock_value: float, industry_avg: float, metric: str) -> Dict[str, Any]:
        """对比估值"""
        if industry_avg <= 0:
            return {"status": "无法比较"}
        
        ratio = stock_value / industry_avg
        diff_pct = (stock_value - industry_avg) / industry_avg * 100
        
        if metric == "pe":
            if ratio < 0.8:
                status = "低于行业平均，可能低估"
            elif ratio > 1.2:
                status = "高于行业平均，可能高估"
            else:
                status = "与行业平均接近"
        else:  # pb
            if ratio < 0.8:
                status = "低于行业平均"
            elif ratio > 1.2:
                status = "高于行业平均"
            else:
                status = "与行业平均接近"
        
        return {
            "stock_value": round(stock_value, 2),
            "industry_avg": round(industry_avg, 2),
            "ratio": round(ratio, 2),
            "diff_pct": round(diff_pct, 1),
            "status": status
        }
    
    def _compare_profitability(self, stock_value: float, industry_avg: float, metric: str) -> Dict[str, Any]:
        """对比盈利能力"""
        if industry_avg <= 0:
            return {"status": "无法比较"}
        
        ratio = stock_value / industry_avg
        diff_pct = (stock_value - industry_avg) / industry_avg * 100
        
        metric_name = "ROE" if metric == "roe" else "毛利率"
        
        if ratio > 1.2:
            status = f"{metric_name}优于行业平均"
        elif ratio < 0.8:
            status = f"{metric_name}低于行业平均"
        else:
            status = f"{metric_name}与行业平均接近"
        
        return {
            "stock_value": f"{stock_value*100:.1f}%",
            "industry_avg": f"{industry_avg*100:.1f}%",
            "ratio": round(ratio, 2),
            "diff_pct": round(diff_pct, 1),
            "status": status
        }
    
    def _summarize(self, comparison: Dict) -> str:
        """总结对比结果"""
        signals = []
        
        if "pe_ratio" in comparison:
            pe_status = comparison["pe_ratio"].get("status", "")
            if "低估" in pe_status:
                signals.append("PE低于行业平均")
            elif "高估" in pe_status:
                signals.append("PE高于行业平均")
        
        if "pb_ratio" in comparison:
            pb_status = comparison["pb_ratio"].get("status", "")
            if "低于" in pb_status:
                signals.append("PB低于行业平均")
            elif "高于" in pb_status:
                signals.append("PB高于行业平均")
        
        if "roe" in comparison:
            roe_status = comparison["roe"].get("status", "")
            if "优于" in roe_status:
                signals.append("盈利能力较强")
            elif "低于" in roe_status:
                signals.append("盈利能力较弱")
        
        if not signals:
            return "各项指标与行业平均接近"
        
        return "；".join(signals)


# 测试代码
if __name__ == "__main__":
    tool = IndustryCompareTool()
    result = tool.run("sh600519")
    
    import json
    print(json.dumps(result, ensure_ascii=False, indent=2))
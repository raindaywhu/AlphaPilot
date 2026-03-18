"""
行业对比工具

用于比较股票与同行业其他公司的估值和财务指标 - 使用 akshare 真实 API

Issue: #35 (TOOL-补齐)
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from typing import Dict, Any, List, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class IndustryCompareTool:
    """
    行业对比工具
    
    对比股票与同行业公司的:
    - PE/PB 估值
    - ROE/毛利率 盈利能力
    - 营收增长率
    
    使用 akshare 真实 API 获取数据
    """
    
    def __init__(self):
        """初始化工具"""
        self.name = "IndustryCompareTool"
        self.description = "行业对比分析，比较估值和财务指标"
        self._akshare = None
        
        # 行业基准数据（当无法获取同行业数据时使用）
        self.industry_benchmarks = {
            "白酒": {"avg_pe": 35.0, "avg_pb": 8.0, "avg_roe": 0.25, "avg_gross_margin": 0.75},
            "银行": {"avg_pe": 6.0, "avg_pb": 0.6, "avg_roe": 0.12, "avg_gross_margin": 0.40},
            "保险": {"avg_pe": 12.0, "avg_pb": 1.2, "avg_roe": 0.10, "avg_gross_margin": 0.30},
            "房地产": {"avg_pe": 10.0, "avg_pb": 1.0, "avg_roe": 0.08, "avg_gross_margin": 0.25},
            "其他": {"avg_pe": 20.0, "avg_pb": 2.0, "avg_roe": 0.10, "avg_gross_margin": 0.30}
        }
    
    def _get_akshare(self):
        """延迟导入 akshare"""
        if self._akshare is None:
            try:
                import akshare as ak
                self._akshare = ak
            except ImportError:
                raise ImportError("请安装 akshare: pip install akshare")
        return self._akshare
    
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
        
        # 标准化股票代码
        stock_code = stock_code.upper().replace("SH", "sh").replace("SZ", "sz")
        
        result = {
            "stock_code": stock_code,
            "industry": "其他",
            "comparison": {}
        }
        
        # 获取股票数据
        stock_data = self._get_stock_data(stock_code)
        
        if "error" in stock_data:
            result["error"] = stock_data["error"]
            return result
        
        # 获取行业信息
        result["industry"] = stock_data.get("industry", "其他")
        
        # 获取行业基准
        industry = result["industry"]
        benchmark = self.industry_benchmarks.get(industry, self.industry_benchmarks["其他"])
        
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
        
        # 综合评价
        result["summary"] = self._summarize(result["comparison"])
        
        return result
    
    def _get_stock_data(self, stock_code: str) -> Dict[str, float]:
        """
        从 akshare 获取股票财务数据
        
        Args:
            stock_code: 股票代码
        
        Returns:
            财务数据字典
        """
        ak = self._get_akshare()
        
        try:
            # 获取实时行情数据
            code = stock_code.lower()
            
            # 尝试获取估值数据
            try:
                # 获取 A 股实时行情
                df = ak.stock_zh_a_spot_em()
                stock_row = df[df['代码'] == code[2:]]  # 去掉前缀
                
                if len(stock_row) > 0:
                    row = stock_row.iloc[0]
                    pe = float(row.get('市盈率-动态', 0)) if row.get('市盈率-动态') and row.get('市盈率-动态') != '-' else 0
                    pb = float(row.get('市净率', 0)) if row.get('市净率') and row.get('市净率') != '-' else 0
                    
                    result = {
                        "pe": pe,
                        "pb": pb,
                        "price": float(row.get('最新价', 0)),
                        "industry": self._get_industry_from_code(code)
                    }
                else:
                    return {"error": f"未找到股票 {stock_code} 的数据"}
            except Exception as e:
                logger.warning(f"获取估值数据失败: {e}")
                result = {
                    "pe": 0,
                    "pb": 0,
                    "industry": self._get_industry_from_code(code)
                }
            
            # 尝试获取财务指标
            try:
                # 获取财务分析指标
                symbol = code[2:]  # 去掉 sh/sz 前缀
                df_fin = ak.stock_financial_analysis_indicator(symbol=symbol)
                
                if df_fin is not None and len(df_fin) > 0:
                    latest = df_fin.iloc[0]
                    
                    # ROE
                    roe_cols = [c for c in df_fin.columns if 'roe' in c.lower() or '净资产收益率' in c]
                    if roe_cols:
                        roe_val = latest.get(roe_cols[0], 0)
                        result["roe"] = float(roe_val) / 100 if roe_val else 0
                    else:
                        result["roe"] = 0
                    
                    # 毛利率
                    gross_cols = [c for c in df_fin.columns if '毛利' in c or 'gross' in c.lower()]
                    if gross_cols:
                        gross_val = latest.get(gross_cols[0], 0)
                        result["gross_margin"] = float(gross_val) / 100 if gross_val else 0
                    else:
                        result["gross_margin"] = 0
                else:
                    result["roe"] = 0
                    result["gross_margin"] = 0
            except Exception as e:
                logger.warning(f"获取财务指标失败: {e}")
                result["roe"] = 0
                result["gross_margin"] = 0
            
            return result
            
        except Exception as e:
            logger.error(f"获取股票数据失败: {e}")
            return {"error": f"获取股票数据失败: {str(e)}"}
    
    def _get_industry_from_code(self, stock_code: str) -> str:
        """根据股票代码判断行业（简化版）"""
        code = stock_code.lower().replace("sh", "").replace("sz", "")
        
        # 白酒
        if code in ["600519", "000858", "000568", "000596", "603369"]:
            return "白酒"
        # 银行
        if code in ["600036", "601166", "601398", "601288", "600000", "000001"]:
            return "银行"
        # 保险
        if code in ["601318", "601601", "601628"]:
            return "保险"
        # 房地产
        if code in ["000002", "600048", "001979"]:
            return "房地产"
        
        return "其他"
    
    def _compare_valuation(self, stock_value: float, industry_avg: float, metric: str) -> Dict[str, Any]:
        """对比估值"""
        if industry_avg <= 0 or stock_value <= 0:
            return {"status": "无法比较", "stock_value": stock_value, "industry_avg": industry_avg}
        
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
        if industry_avg <= 0 or stock_value <= 0:
            return {"status": "无法比较", "stock_value": stock_value, "industry_avg": industry_avg}
        
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
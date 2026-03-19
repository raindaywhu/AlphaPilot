"""
基本面分析工具

获取财务数据、估值分析、行业对比

Issue: #28 (FUND-001)
"""

import os
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List

# 导入性能优化工具
from ..utils.performance import timing_decorator, cached, monitor_performance

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FundamentalAnalyzer:
    """
    基本面分析器
    
    分析财务数据、估值、行业对比
    """
    
    def __init__(self):
        """初始化分析器"""
        logger.info("基本面分析器初始化完成")
    
    @monitor_performance("fundamental")
    @timing_decorator
    @cached("fundamental_analysis", max_age_seconds=3600)  # 缓存 1 小时
    def analyze(self, stock_code: str) -> Dict[str, Any]:
        """
        基本面分析
        
        Args:
            stock_code: 股票代码
        
        Returns:
            分析结果
        """
        logger.info(f"开始基本面分析: {stock_code}")
        
        # 1. 获取财务数据
        financial_data = self._get_financial_data(stock_code)
        
        # 2. 估值分析
        valuation = self._analyze_valuation(stock_code, financial_data)
        
        # 3. 行业对比
        industry_comparison = self._compare_industry(stock_code, financial_data)
        
        # 4. 综合评级
        overall_rating = self._calculate_rating(financial_data, valuation)
        
        return {
            "stock_code": stock_code,
            "financial_data": financial_data,
            "valuation": valuation,
            "industry_comparison": industry_comparison,
            "overall_rating": overall_rating["rating"],
            "confidence": overall_rating["confidence"],
            "conclusion": overall_rating["conclusion"],
            "analysis_date": datetime.now().strftime("%Y-%m-%d")
        }
    
    def _get_financial_data(self, stock_code: str) -> Dict[str, Any]:
        """
        获取财务数据 - 使用 mootdx 获取真实数据
        """
        logger.info(f"获取财务数据: {stock_code}")
        
        try:
            # 使用 mootdx 获取财务数据
            from mootdx.quotes import Quotes
            
            client = Quotes.factory(market='std')
            
            # 标准化股票代码（去掉前缀）
            code = stock_code.replace('SH', '').replace('SZ', '').replace('sh', '').replace('sz', '')
            
            # 获取财务数据
            finance_data = client.finance(code=code)
            
            if finance_data is not None and not finance_data.empty:
                row = finance_data.iloc[0]
                
                # 提取关键字段
                bps = row.get('meigujingzichan', 0)  # 每股净资产
                net_assets = row.get('jingzichan', 0)  # 净资产
                net_profit = row.get('jinglirun', 0)  # 净利润
                total_assets = row.get('zongzichan', 0)  # 总资产
                revenue = row.get('zhuyingshouru', 0)  # 主营收入
                
                # 获取实时价格计算 PE/PB
                quote = client.quotes(code=code)
                price = quote.iloc[0].get('price', 0) if quote is not None and not quote.empty else 0
                
                # 计算财务指标
                eps = net_profit / (row.get('liutongguben', 1) / 10) if row.get('liutongguben', 0) > 0 else 0
                pe_ratio = price / eps if eps > 0 else 0
                pb_ratio = price / bps if bps > 0 else 0
                roe = net_profit / net_assets if net_assets > 0 else 0
                net_profit_margin = net_profit / revenue if revenue > 0 else 0
                debt_ratio = (total_assets - net_assets) / total_assets if total_assets > 0 else 0
                
                logger.info(f"从 mootdx 获取真实财务数据: PE={pe_ratio:.2f}, PB={pb_ratio:.2f}, ROE={roe:.2%}")
                
                return {
                    "pe_ratio": round(pe_ratio, 2),
                    "pb_ratio": round(pb_ratio, 2),
                    "roe": round(roe, 4),
                    "net_profit_margin": round(net_profit_margin, 4),
                    "debt_ratio": round(debt_ratio, 4),
                    "current_ratio": 1.5,  # 需要其他接口
                    "revenue_growth": 0.1,  # 需要历史数据
                    "profit_growth": 0.1,
                    "dividend_yield": 0.03,
                    "eps": round(eps, 2),
                    "bps": round(bps, 2),
                    "data_source": "mootdx"
                }
        except Exception as e:
            logger.warning(f"mootdx 获取财务数据失败: {e}，使用默认值")
        
        # 回退默认值
        return {
            "pe_ratio": 15.0,
            "pb_ratio": 2.0,
            "roe": 0.10,
            "net_profit_margin": 0.15,
            "debt_ratio": 0.40,
            "current_ratio": 1.5,
            "revenue_growth": 0.05,
            "profit_growth": 0.05,
            "dividend_yield": 0.02,
            "eps": 1.0,
            "bps": 5.0,
            "data_source": "default"
        }
    
    def _analyze_valuation(
        self,
        stock_code: str,
        financial_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        估值分析
        
        Args:
            stock_code: 股票代码
            financial_data: 财务数据
        
        Returns:
            估值分析结果
        """
        pe = financial_data.get("pe_ratio", 0)
        pb = financial_data.get("pb_ratio", 0)
        roe = financial_data.get("roe", 0)
        
        # PE 估值判断
        if pe < 10:
            pe_rating = "低估"
        elif pe < 20:
            pe_rating = "合理"
        elif pe < 30:
            pe_rating = "偏高"
        else:
            pe_rating = "高估"
        
        # PB 估值判断
        if pb < 1:
            pb_rating = "低估"
        elif pb < 3:
            pb_rating = "合理"
        elif pb < 5:
            pb_rating = "偏高"
        else:
            pb_rating = "高估"
        
        # PEG 指标（PE / 盈利增长率）
        profit_growth = financial_data.get("profit_growth", 0.1)
        peg = pe / (profit_growth * 100) if profit_growth > 0 else float('inf')
        
        if peg < 1:
            peg_rating = "低估"
        elif peg < 2:
            peg_rating = "合理"
        else:
            peg_rating = "高估"
        
        # 综合估值
        valuations = [pe_rating, pb_rating, peg_rating]
        if valuations.count("低估") >= 2:
            overall = "低估"
        elif valuations.count("高估") >= 2:
            overall = "高估"
        else:
            overall = "合理"
        
        return {
            "pe_rating": pe_rating,
            "pb_rating": pb_rating,
            "peg": round(peg, 2),
            "peg_rating": peg_rating,
            "overall_valuation": overall,
            "reason": f"PE={pe}({pe_rating}), PB={pb}({pb_rating}), PEG={peg:.2f}({peg_rating})"
        }
    
    def _compare_industry(
        self,
        stock_code: str,
        financial_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        行业对比
        
        Args:
            stock_code: 股票代码
            financial_data: 财务数据
        
        Returns:
            行业对比结果
        """
        # 模拟行业平均数据
        industry_avg = {
            "pe_ratio": 18.0,
            "pb_ratio": 2.5,
            "roe": 0.12,
            "net_profit_margin": 0.15,
            "debt_ratio": 0.40
        }
        
        # 对比分析
        comparison = {}
        
        for key, industry_value in industry_avg.items():
            stock_value = financial_data.get(key, 0)
            
            if key == "debt_ratio":
                # 负债率越低越好
                if stock_value < industry_value:
                    comparison[key] = "优于行业"
                else:
                    comparison[key] = "劣于行业"
            else:
                # 其他指标越高越好
                if stock_value > industry_value:
                    comparison[key] = "优于行业"
                else:
                    comparison[key] = "劣于行业"
        
        # 计算优势项数量
        advantages = sum(1 for v in comparison.values() if v == "优于行业")
        
        return {
            "industry": "消费品",  # 简化处理
            "comparison": comparison,
            "advantages_count": advantages,
            "total_metrics": len(comparison),
            "overall": "领先行业" if advantages >= 3 else "行业中等"
        }
    
    def _calculate_rating(
        self,
        financial_data: Dict[str, Any],
        valuation: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        计算综合评级
        
        Args:
            financial_data: 财务数据
            valuation: 估值分析
        
        Returns:
            评级结果
        """
        score = 0
        reasons = []
        
        # ROE 评分（权重 25%）
        roe = financial_data.get("roe", 0)
        if roe >= 0.20:
            score += 25
            reasons.append("ROE优秀(>20%)")
        elif roe >= 0.15:
            score += 20
            reasons.append("ROE良好(15-20%)")
        elif roe >= 0.10:
            score += 15
            reasons.append("ROE一般(10-15%)")
        else:
            score += 5
            reasons.append("ROE较低(<10%)")
        
        # 估值评分（权重 25%）
        val_rating = valuation.get("overall_valuation", "合理")
        if val_rating == "低估":
            score += 25
            reasons.append("估值低估")
        elif val_rating == "合理":
            score += 15
            reasons.append("估值合理")
        else:
            score += 5
            reasons.append("估值偏高")
        
        # 成长性评分（权重 25%）
        revenue_growth = financial_data.get("revenue_growth", 0)
        profit_growth = financial_data.get("profit_growth", 0)
        avg_growth = (revenue_growth + profit_growth) / 2
        
        if avg_growth >= 0.20:
            score += 25
            reasons.append("高成长(>20%)")
        elif avg_growth >= 0.10:
            score += 15
            reasons.append("稳健增长(10-20%)")
        else:
            score += 5
            reasons.append("增长较慢(<10%)")
        
        # 财务健康评分（权重 25%）
        debt_ratio = financial_data.get("debt_ratio", 0)
        current_ratio = financial_data.get("current_ratio", 0)
        
        if debt_ratio < 0.4 and current_ratio > 1.5:
            score += 25
            reasons.append("财务健康")
        elif debt_ratio < 0.6 and current_ratio > 1.0:
            score += 15
            reasons.append("财务稳健")
        else:
            score += 5
            reasons.append("财务风险")
        
        # 确定评级
        if score >= 80:
            rating = "优秀"
            confidence = 0.85
        elif score >= 60:
            rating = "良好"
            confidence = 0.70
        elif score >= 40:
            rating = "一般"
            confidence = 0.50
        else:
            rating = "较差"
            confidence = 0.35
        
        conclusion = f"基本面{rating}，" + "；".join(reasons[:3])
        
        return {
            "rating": rating,
            "score": score,
            "confidence": confidence,
            "conclusion": conclusion,
            "details": reasons
        }
    
    def generate_report(self, analysis: Dict[str, Any]) -> str:
        """生成基本面分析报告"""
        stock_code = analysis.get("stock_code", "Unknown")
        financial = analysis.get("financial_data", {})
        valuation = analysis.get("valuation", {})
        industry = analysis.get("industry_comparison", {})
        
        report = f"""
# 基本面分析报告 - {stock_code}

## 综合评级

**{analysis.get('overall_rating', 'N/A')}** (置信度: {analysis.get('confidence', 0):.0%})

{analysis.get('conclusion', '')}

## 财务指标

| 指标 | 值 |
|------|-----|
| 市盈率(PE) | {financial.get('pe_ratio', 'N/A')} |
| 市净率(PB) | {financial.get('pb_ratio', 'N/A')} |
| ROE | {financial.get('roe', 0):.1%} |
| 净利率 | {financial.get('net_profit_margin', 0):.1%} |
| 资产负债率 | {financial.get('debt_ratio', 0):.1%} |
| 营收增长 | {financial.get('revenue_growth', 0):.1%} |
| 利润增长 | {financial.get('profit_growth', 0):.1%} |

## 估值分析

| 指标 | 评级 |
|------|-----|
| PE估值 | {valuation.get('pe_rating', 'N/A')} |
| PB估值 | {valuation.get('pb_rating', 'N/A')} |
| PEG | {valuation.get('peg', 'N/A')} |
| **综合估值** | **{valuation.get('overall_valuation', 'N/A')}** |

## 行业对比

行业: {industry.get('industry', 'N/A')}

| 指标 | 对比 |
|------|-----|
| PE对比 | {industry.get('comparison', {}).get('pe_ratio', 'N/A')} |
| ROE对比 | {industry.get('comparison', {}).get('roe', 'N/A')} |
| 净利率对比 | {industry.get('comparison', {}).get('net_profit_margin', 'N/A')} |

**综合**: {industry.get('overall', 'N/A')}
"""
        return report


def main():
    """测试基本面分析器"""
    print("=" * 60)
    print("基本面分析器测试")
    print("=" * 60)
    
    analyzer = FundamentalAnalyzer()
    result = analyzer.analyze("SH600519")
    
    report = analyzer.generate_report(result)
    print(report)
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
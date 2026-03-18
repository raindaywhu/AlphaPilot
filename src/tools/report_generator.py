"""
PDF 报告生成器

生成专业的投资分析 PDF 报告

Issue: #29 (REPORT-001)
"""

import os
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from io import BytesIO

# 导入性能优化工具
from ..utils.performance import timing_decorator, monitor_performance

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 尝试导入 PDF 库
try:
    from fpdf import FPDF
    HAS_FPDF = True
    logger.info("FPDF 库可用")
except ImportError:
    HAS_FPDF = False
    logger.warning("FPDF 库不可用，PDF 生成功能受限")


class ChinesePDF(FPDF):
    """
    支持中文的 PDF 类
    """
    
    def __init__(self):
        super().__init__()
        
        # 尝试加载中文字体
        self.chinese_font_loaded = False
        
        # macOS 系统字体路径
        font_paths = [
            "/System/Library/Fonts/PingFang.ttc",
            "/System/Library/Fonts/STHeiti Light.ttc",
            "/Library/Fonts/Arial Unicode.ttf",
        ]
        
        for font_path in font_paths:
            if os.path.exists(font_path):
                try:
                    self.add_font("Chinese", "", font_path, uni=True)
                    self.chinese_font_loaded = True
                    logger.info(f"加载中文字体成功: {font_path}")
                    break
                except Exception as e:
                    logger.warning(f"加载字体失败 {font_path}: {e}")
    
    def header(self):
        """页眉"""
        if self.chinese_font_loaded:
            self.set_font("Chinese", "", 10)
        else:
            self.set_font("Helvetica", "", 10)
        
        self.cell(0, 10, "AlphaPilot 投资分析报告", 0, 1, "C")
        self.ln(5)
    
    def footer(self):
        """页脚"""
        self.set_y(-15)
        if self.chinese_font_loaded:
            self.set_font("Chinese", "", 8)
        else:
            self.set_font("Helvetica", "", 8)
        
        self.cell(0, 10, f"第 {self.page_no()} 页", 0, 0, "C")


class ReportGenerator:
    """
    PDF 报告生成器
    
    生成专业的投资分析报告
    """
    
    def __init__(self):
        """初始化生成器"""
        self.output_dir = "/tmp/alphapilot/reports"
        os.makedirs(self.output_dir, exist_ok=True)
        logger.info(f"报告生成器初始化完成，输出目录: {self.output_dir}")
    
    @monitor_performance("report")
    @timing_decorator
    def generate_pdf(
        self,
        analysis_result: Dict[str, Any],
        filename: Optional[str] = None
    ) -> str:
        """
        生成 PDF 报告
        
        Args:
            analysis_result: 分析结果
            filename: 文件名（可选）
        
        Returns:
            PDF 文件路径
        """
        if not HAS_FPDF:
            logger.warning("FPDF 不可用，生成 Markdown 报告")
            return self._generate_markdown(analysis_result, filename)
        
        logger.info("开始生成 PDF 报告")
        
        stock_code = analysis_result.get("stock_code", "Unknown")
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{stock_code}_{timestamp}.pdf"
        
        output_path = os.path.join(self.output_dir, filename)
        
        # 创建 PDF
        pdf = ChinesePDF()
        pdf.add_page()
        
        # 标题
        if pdf.chinese_font_loaded:
            pdf.set_font("Chinese", "", 20)
        else:
            pdf.set_font("Helvetica", "", 20)
        
        pdf.cell(0, 15, f"{stock_code} 投资分析报告", 0, 1, "C")
        pdf.ln(10)
        
        # 日期
        if pdf.chinese_font_loaded:
            pdf.set_font("Chinese", "", 12)
        else:
            pdf.set_font("Helvetica", "", 12)
        
        analysis_date = analysis_result.get("analysis_date", datetime.now().strftime("%Y-%m-%d"))
        pdf.cell(0, 10, f"分析日期: {analysis_date}", 0, 1, "C")
        pdf.ln(10)
        
        # 综合评级
        overall_rating = analysis_result.get("overall_rating", "中性")
        confidence = analysis_result.get("confidence", 0)
        
        if pdf.chinese_font_loaded:
            pdf.set_font("Chinese", "", 14)
        else:
            pdf.set_font("Helvetica", "", 14)
        
        pdf.cell(0, 10, "=== 综合评级 ===", 0, 1)
        pdf.cell(0, 8, f"评级: {overall_rating}", 0, 1)
        pdf.cell(0, 8, f"置信度: {confidence:.0%}", 0, 1)
        pdf.ln(5)
        
        # Agent 分析结果
        agent_results = analysis_result.get("agent_results", {})
        if agent_results:
            pdf.cell(0, 10, "=== 分项分析 ===", 0, 1)
            
            for agent_name, result in agent_results.items():
                if isinstance(result, dict) and "error" not in result:
                    rating = result.get("overall_rating", "N/A")
                    pdf.cell(0, 8, f"{agent_name}: {rating}", 0, 1)
        
        pdf.ln(5)
        
        # 风险提示
        pdf.cell(0, 10, "=== 风险提示 ===", 0, 1)
        risk_warnings = analysis_result.get("risk_warnings", [])
        for warning in risk_warnings[:5]:
            # 截断过长的警告
            if len(warning) > 80:
                warning = warning[:77] + "..."
            pdf.cell(0, 8, f"- {warning}", 0, 1)
        
        # 免责声明
        pdf.ln(10)
        if pdf.chinese_font_loaded:
            pdf.set_font("Chinese", "", 8)
        else:
            pdf.set_font("Helvetica", "", 8)
        disclaimer = analysis_result.get("disclaimer", "本报告由 AI 系统自动生成，不构成投资建议")
        pdf.cell(0, 6, disclaimer, 0, 1, "C")
        
        # 保存
        pdf.output(output_path)
        logger.info(f"PDF 报告已生成: {output_path}")
        
        return output_path
    
    def _generate_markdown(
        self,
        analysis_result: Dict[str, Any],
        filename: Optional[str] = None
    ) -> str:
        """
        生成 Markdown 报告（主方案）
        
        Args:
            analysis_result: 分析结果
            filename: 文件名
        
        Returns:
            Markdown 文件路径
        """
        stock_code = analysis_result.get("stock_code", "Unknown")
        stock_name = analysis_result.get("stock_name", stock_code)
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{stock_code}_{timestamp}.md"
        
        output_path = os.path.join(self.output_dir, filename)
        
        # 生成 Markdown 内容
        content = f"""# {stock_name} ({stock_code}) 投资分析报告

**分析日期**: {analysis_result.get('analysis_date', datetime.now().strftime('%Y-%m-%d'))}

---

## 📊 综合评级

| 指标 | 值 |
|------|-----|
| **评级** | **{analysis_result.get('overall_rating', 'N/A')}** |
| **置信度** | {analysis_result.get('confidence', 0):.0%} |

---

## 📈 分项分析详情

"""
        
        agent_results = analysis_result.get("agent_results", {})
        
        # 定义 Agent 显示名称
        agent_names = {
            "quantitative": "📊 量化分析师",
            "fundamental": "💰 基本面分析师", 
            "macro": "🌍 宏观分析师",
            "alternative": "🔮 另类数据分析师",
            "risk": "⚠️ 风控经理",
            "decision": "🎯 投资决策者"
        }
        
        for agent_key, result in agent_results.items():
            if isinstance(result, dict) and "error" not in result:
                agent_display = agent_names.get(agent_key, agent_key)
                content += f"### {agent_display}\n\n"
                
                # 基本信息
                rating = result.get("overall_rating") or result.get("rating", "N/A")
                confidence = result.get("confidence", 0)
                
                content += f"| 指标 | 值 |\n|------|-----|\n"
                content += f"| **评级** | **{rating}** |\n"
                if confidence > 0:
                    content += f"| **置信度** | {confidence:.0%} |\n"
                content += "\n"
                
                # 结论
                conclusion = result.get("conclusion")
                if conclusion:
                    content += f"**结论**: {conclusion}\n\n"
                
                # 技术指标（量化）
                if "factor_analysis" in result:
                    tech = result["factor_analysis"].get("technical_indicators", {})
                    if tech:
                        content += "**技术指标**:\n"
                        content += f"- 收盘价: {tech.get('close', 'N/A')}\n"
                        content += f"- MA5: {tech.get('MA5', 'N/A')}\n"
                        content += f"- MA10: {tech.get('MA10', 'N/A')}\n"
                        content += f"- RSI: {tech.get('RSI', 'N/A'):.1f}\n" if isinstance(tech.get('RSI'), (int, float)) else ""
                        content += "\n"
                
                # 财务分析（基本面）
                if "financial_analysis" in result:
                    fin = result["financial_analysis"]
                    content += "**财务指标**:\n"
                    content += f"- PE: {fin.get('pe_ratio', 'N/A')}\n"
                    content += f"- PB: {fin.get('pb_ratio', 'N/A')}\n"
                    content += f"- ROE: {fin.get('roe', 0):.1%}\n" if isinstance(fin.get('roe'), (int, float)) else ""
                    content += f"- 净利率: {fin.get('net_profit_margin', 0):.1%}\n" if isinstance(fin.get('net_profit_margin'), (int, float)) else ""
                    content += "\n"
                
                # 估值（基本面）
                if "valuation" in result:
                    val = result["valuation"]
                    content += "**估值分析**:\n"
                    content += f"- PE评价: {val.get('pe_rating', 'N/A')}\n"
                    content += f"- PB评价: {val.get('pb_rating', 'N/A')}\n"
                    content += f"- PEG: {val.get('peg', 'N/A')}\n"
                    content += f"- 综合估值: {val.get('overall_valuation', 'N/A')}\n"
                    content += "\n"
                
                # 行业比较
                if "industry_comparison" in result:
                    ind = result["industry_comparison"]
                    content += f"**行业比较** ({ind.get('industry', 'N/A')}):\n"
                    comp = ind.get("comparison", {})
                    for metric, status in comp.items():
                        content += f"- {metric}: {status}\n"
                    content += f"- 综合评价: {ind.get('overall', 'N/A')}\n\n"
                
                # 北向资金分析（另类）
                if "north_money_analysis" in result:
                    content += f"**北向资金分析**: {result['north_money_analysis']}\n\n"
                
                # 大宗商品分析（另类）
                if "commodity_analysis" in result:
                    content += f"**大宗商品分析**: {result['commodity_analysis']}\n\n"
                
                # 逻辑推导
                if "logic_derivation" in result:
                    content += f"**分析逻辑**: {result['logic_derivation']}\n\n"
                
                # 风险警告
                warnings = result.get("risk_warning", [])
                if warnings:
                    content += "**风险提示**:\n"
                    for w in warnings[:3]:
                        content += f"- {w}\n"
                    content += "\n"
                
                content += "---\n\n"
        
        # 风险提示
        content += "## ⚠️ 风险提示\n\n"
        risk_warnings = analysis_result.get("risk_warnings", [])
        if risk_warnings:
            for warning in risk_warnings:
                content += f"- {warning}\n"
        else:
            content += "- 投资有风险，入市需谨慎\n"
        
        content += f"""
---

## 免责声明

{analysis_result.get('disclaimer', '本报告由 AI 系统自动生成，不构成投资建议')}

---

*报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
        
        # 保存
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
        
        logger.info(f"Markdown 报告已生成: {output_path}")
        
        return output_path


def main():
    """测试报告生成器"""
    print("=" * 60)
    print("报告生成器测试")
    print("=" * 60)
    
    # 创建测试数据
    analysis_result = {
        "stock_code": "SH600519",
        "analysis_date": "2026-03-18",
        "overall_rating": "看涨",
        "confidence": 0.75,
        "agent_results": {
            "quantitative": {
                "overall_rating": "看涨",
                "confidence": 0.8
            },
            "macro": {
                "overall_rating": "中性偏多",
                "confidence": 0.7
            },
            "alternative": {
                "overall_rating": "看涨",
                "confidence": 0.75
            }
        },
        "risk_warnings": [
            "量化分析师使用 qlib 数据（截止 2020-09-25），可能过期",
            "投资决策需谨慎，本分析仅供参考"
        ],
        "disclaimer": "本分析报告由 AI 系统自动生成，不构成投资建议"
    }
    
    generator = ReportGenerator()
    output_path = generator.generate_pdf(analysis_result)
    
    print(f"\n✅ 报告已生成: {output_path}")
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
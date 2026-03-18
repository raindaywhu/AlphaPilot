"""
消息卡片构建器

构建飞书消息卡片
"""

import json
from typing import Dict, Any, Optional


class CardBuilder:
    """
    消息卡片构建器
    
    构建美观的飞书消息卡片
    """
    
    @staticmethod
    def build_analysis_card(
        command: str,
        stock_code: str,
        result: Dict[str, Any],
        elapsed_time: float
    ) -> Dict[str, Any]:
        """
        构建分析结果卡片
        
        Args:
            command: 命令类型
            stock_code: 股票代码
            result: 分析结果
            elapsed_time: 耗时
        
        Returns:
            消息卡片 JSON
        """
        # 根据命令类型选择不同的卡片模板
        if command == 'analyze':
            return CardBuilder._build_full_analysis_card(stock_code, result, elapsed_time)
        elif command == 'quant':
            return CardBuilder._build_quant_card(stock_code, result, elapsed_time)
        elif command == 'macro':
            return CardBuilder._build_macro_card(stock_code, result, elapsed_time)
        elif command == 'alt':
            return CardBuilder._build_alt_card(stock_code, result, elapsed_time)
        else:
            return CardBuilder._build_simple_card(stock_code, result)
    
    @staticmethod
    def _build_full_analysis_card(
        stock_code: str,
        result: Dict[str, Any],
        elapsed_time: float
    ) -> Dict[str, Any]:
        """构建综合分析卡片"""
        overall_rating = result.get('overall_rating', 'N/A')
        confidence = result.get('confidence', 0)
        summary = result.get('summary', '无分析结果')
        
        # 获取各 Agent 结果
        agent_results = result.get('agent_results', {})
        quant = agent_results.get('quantitative', {})
        macro = agent_results.get('macro', {})
        alt = agent_results.get('alternative', {})
        
        # 评级颜色
        rating_colors = {
            '看涨': 'green',
            '中性偏多': 'blue',
            '中性': 'grey',
            '中性偏空': 'orange',
            '看跌': 'red'
        }
        rating_color = rating_colors.get(overall_rating, 'grey')
        
        card = {
            "type": "template",
            "data": {
                "template_id": "AAqk8BpGpR",  # 飞书官方卡片模板
                "template_variable": {
                    "title": f"📊 {stock_code} 投资分析报告",
                    "rating": overall_rating,
                    "rating_color": rating_color,
                    "confidence": f"{confidence:.0%}",
                    "elapsed_time": f"{elapsed_time:.1f}秒",
                    "summary": summary,
                    "quant_rating": quant.get('overall_rating', 'N/A'),
                    "quant_confidence": f"{quant.get('confidence', 0):.0%}",
                    "quant_conclusion": quant.get('conclusion', '无')[:50] + '...' if len(quant.get('conclusion', '')) > 50 else quant.get('conclusion', '无'),
                    "macro_rating": macro.get('overall_rating', 'N/A'),
                    "macro_confidence": f"{macro.get('confidence', 0):.0%}",
                    "macro_conclusion": macro.get('conclusion', '无')[:50] + '...' if len(macro.get('conclusion', '')) > 50 else macro.get('conclusion', '无'),
                    "alt_rating": alt.get('overall_rating', 'N/A'),
                    "alt_confidence": f"{alt.get('confidence', 0):.0%}",
                    "alt_conclusion": alt.get('conclusion', '无')[:50] + '...' if len(alt.get('conclusion', '')) > 50 else alt.get('conclusion', '无')
                }
            }
        }
        
        return card
    
    @staticmethod
    def _build_quant_card(
        stock_code: str,
        result: Dict[str, Any],
        elapsed_time: float
    ) -> Dict[str, Any]:
        """构建量化分析卡片"""
        overall_rating = result.get('overall_rating', 'N/A')
        confidence = result.get('confidence', 0)
        conclusion = result.get('conclusion', '无分析结果')
        factor_analysis = result.get('factor_analysis', {})
        
        # 构建简化的卡片
        return {
            "type": "template",
            "data": {
                "template_id": "AAqk8BpGpR",
                "template_variable": {
                    "title": f"📈 {stock_code} 量化分析",
                    "rating": overall_rating,
                    "confidence": f"{confidence:.0%}",
                    "elapsed_time": f"{elapsed_time:.1f}秒",
                    "summary": conclusion,
                    "factor_count": str(len(factor_analysis))
                }
            }
        }
    
    @staticmethod
    def _build_macro_card(
        stock_code: str,
        result: Dict[str, Any],
        elapsed_time: float
    ) -> Dict[str, Any]:
        """构建宏观分析卡片"""
        overall_rating = result.get('overall_rating', 'N/A')
        confidence = result.get('confidence', 0)
        conclusion = result.get('conclusion', '无分析结果')
        
        return {
            "type": "template",
            "data": {
                "template_id": "AAqk8BpGpR",
                "template_variable": {
                    "title": f"🌍 {stock_code} 宏观分析",
                    "rating": overall_rating,
                    "confidence": f"{confidence:.0%}",
                    "elapsed_time": f"{elapsed_time:.1f}秒",
                    "summary": conclusion
                }
            }
        }
    
    @staticmethod
    def _build_alt_card(
        stock_code: str,
        result: Dict[str, Any],
        elapsed_time: float
    ) -> Dict[str, Any]:
        """构建另类分析卡片"""
        overall_rating = result.get('overall_rating', 'N/A')
        confidence = result.get('confidence', 0)
        conclusion = result.get('conclusion', '无分析结果')
        
        return {
            "type": "template",
            "data": {
                "template_id": "AAqk8BpGpR",
                "template_variable": {
                    "title": f"🔬 {stock_code} 另类分析",
                    "rating": overall_rating,
                    "confidence": f"{confidence:.0%}",
                    "elapsed_time": f"{elapsed_time:.1f}秒",
                    "summary": conclusion
                }
            }
        }
    
    @staticmethod
    def _build_simple_card(
        stock_code: str,
        result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """构建简单卡片"""
        return {
            "type": "template",
            "data": {
                "template_id": "AAqk8BpGpR",
                "template_variable": {
                    "title": f"📊 {stock_code} 分析结果",
                    "summary": json.dumps(result, ensure_ascii=False, indent=2)
                }
            }
        }
    
    @staticmethod
    def build_help_card() -> Dict[str, Any]:
        """构建帮助卡片"""
        return {
            "type": "template",
            "data": {
                "template_id": "AAqk8BpGpR",
                "template_variable": {
                    "title": "📊 AlphaPilot 帮助",
                    "content": """
**可用命令：**

• `/analyze <股票代码>` - 综合分析
• `/quant <股票代码>` - 量化分析
• `/macro <股票代码>` - 宏观分析
• `/alt <股票代码>` - 另类分析
• `/help` - 显示帮助

**示例：** `/analyze 600519`
"""
                }
            }
        }
    
    @staticmethod
    def build_error_card(error: str, help_text: str = None) -> Dict[str, Any]:
        """构建错误卡片"""
        content = f"❌ **错误**\n\n{error}"
        if help_text:
            content += f"\n\n{help_text}"
        
        return {
            "type": "template",
            "data": {
                "template_id": "AAqk8BpGpR",
                "template_variable": {
                    "title": "⚠️ 处理失败",
                    "content": content
                }
            }
        }
    
    @staticmethod
    def build_text_message(text: str) -> str:
        """
        构建纯文本消息
        
        Args:
            text: 消息文本
        
        Returns:
            JSON 字符串
        """
        return json.dumps({
            "zh_cn": {
                "title": "",
                "content": [[{"tag": "text", "text": text}]]
            }
        }, ensure_ascii=False)
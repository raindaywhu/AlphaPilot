"""
AlphaPilot Bot - 消息卡片构建器

构建飞书消息卡片

Issue: #21 (UI-001)
"""

import json
from typing import Dict, Any, List, Optional
from datetime import datetime


class CardBuilder:
    """
    消息卡片构建器
    
    构建各种类型的飞书消息卡片
    """
    
    # 评级颜色映射
    RATING_COLORS = {
        "看涨": "green",
        "中性偏多": "blue",
        "中性": "grey",
        "中性偏空": "orange",
        "看跌": "red"
    }
    
    # 评级 emoji 映射
    RATING_EMOJIS = {
        "看涨": "📈",
        "中性偏多": "📊",
        "中性": "➖",
        "中性偏空": "📉",
        "看跌": "🔻"
    }
    
    def build_analyze_card(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        构建综合分析卡片
        
        Args:
            result: API 返回的分析结果
            
        Returns:
            飞书消息卡片内容
        """
        stock_code = result.get("stock_code", "")
        overall_rating = result.get("overall_rating", "中性")
        confidence = result.get("confidence", 0.5)
        score = result.get("score", 0.5)
        summary = result.get("summary", "")
        risk_warnings = result.get("risk_warnings", [])
        execution_time = result.get("execution_time", "")
        
        rating_color = self.RATING_COLORS.get(overall_rating, "grey")
        rating_emoji = self.RATING_EMOJIS.get(overall_rating, "📊")
        
        # 构建风险提示
        risk_elements = []
        if risk_warnings:
            risk_elements = [
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"⚠️ **风险提示**\n" + "\n".join([f"• {r}" for r in risk_warnings])
                    }
                }
            ]
        
        card = {
            "type": "template",
            "data": {
                "template_id": "AAqk3R9pBzKa",
                "template_variable": {
                    "stock_code": stock_code,
                    "rating_emoji": rating_emoji,
                    "overall_rating": overall_rating,
                    "confidence": f"{confidence * 100:.1f}%",
                    "score": f"{score:.2f}",
                    "summary": summary,
                    "execution_time": execution_time,
                    "risk_warnings": risk_warnings
                }
            }
        }
        
        # 如果没有模板，使用自定义卡片
        card = self._build_custom_analyze_card(result)
        
        return card
    
    def _build_custom_analyze_card(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """构建自定义分析卡片"""
        stock_code = result.get("stock_code", "")
        overall_rating = result.get("overall_rating", "中性")
        confidence = result.get("confidence", 0.5)
        score = result.get("score", 0.5)
        summary = result.get("summary", "")
        risk_warnings = result.get("risk_warnings", [])
        execution_time = result.get("execution_time", "")
        
        rating_color = self.RATING_COLORS.get(overall_rating, "grey")
        rating_emoji = self.RATING_EMOJIS.get(overall_rating, "📊")
        
        # 构建卡片元素
        elements = [
            # 标题
            {
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"# {rating_emoji} {stock_code} 投资分析报告\n\n**分析日期**: {datetime.now().strftime('%Y-%m-%d')}"
                }
            },
            # 分割线
            {"tag": "hr"},
            # 综合评级
            {
                "tag": "div",
                "fields": [
                    {
                        "is_short": True,
                        "text": {
                            "tag": "lark_md",
                            "content": f"**综合评级**\n{overall_rating}"
                        }
                    },
                    {
                        "is_short": True,
                        "text": {
                            "tag": "lark_md",
                            "content": f"**置信度**\n{confidence * 100:.1f}%"
                        }
                    },
                    {
                        "is_short": True,
                        "text": {
                            "tag": "lark_md",
                            "content": f"**得分**\n{score:.2f}"
                        }
                    },
                    {
                        "is_short": True,
                        "text": {
                            "tag": "lark_md",
                            "content": f"**耗时**\n{execution_time}"
                        }
                    }
                ]
            },
            {"tag": "hr"},
            # 摘要
            {
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"**分析摘要**\n{summary}"
                }
            }
        ]
        
        # 添加风险提示
        if risk_warnings:
            elements.extend([
                {"tag": "hr"},
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": "⚠️ **风险提示**\n" + "\n".join([f"• {r}" for r in risk_warnings])
                    }
                }
            ])
        
        # 添加免责声明
        elements.extend([
            {"tag": "hr"},
            {
                "tag": "note",
                "elements": [
                    {
                        "tag": "plain_text",
                        "content": "免责声明：本分析结果仅供参考，不构成投资建议。投资有风险，入市需谨慎。"
                    }
                ]
            }
        ])
        
        return {
            "config": {
                "wide_screen_mode": True
            },
            "elements": elements
        }
    
    def build_quant_card(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """构建量化分析卡片"""
        stock_code = result.get("stock_code", "")
        quant_result = result.get("result", {})
        
        elements = [
            {
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"# 📈 {stock_code} 量化分析报告"
                }
            },
            {"tag": "hr"},
            {
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"```\n{json.dumps(quant_result, ensure_ascii=False, indent=2)}\n```"
                }
            }
        ]
        
        return {
            "config": {"wide_screen_mode": True},
            "elements": elements
        }
    
    def build_macro_card(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """构建宏观分析卡片"""
        stock_code = result.get("stock_code", "")
        macro_result = result.get("result", {})
        
        elements = [
            {
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"# 🌍 {stock_code} 宏观分析报告"
                }
            },
            {"tag": "hr"},
            {
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"```\n{json.dumps(macro_result, ensure_ascii=False, indent=2)}\n```"
                }
            }
        ]
        
        return {
            "config": {"wide_screen_mode": True},
            "elements": elements
        }
    
    def build_alt_card(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """构建另类分析卡片"""
        stock_code = result.get("stock_code", "")
        alt_result = result.get("result", {})
        
        elements = [
            {
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"# 💰 {stock_code} 另类分析报告"
                }
            },
            {"tag": "hr"},
            {
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"```\n{json.dumps(alt_result, ensure_ascii=False, indent=2)}\n```"
                }
            }
        ]
        
        return {
            "config": {"wide_screen_mode": True},
            "elements": elements
        }
    
    def build_error_card(self, error_message: str) -> Dict[str, Any]:
        """构建错误卡片"""
        return {
            "config": {"wide_screen_mode": True},
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"# ❌ 错误\n\n{error_message}"
                    }
                }
            ]
        }
    
    def build_loading_card(self, stock_code: str, analysis_type: str = "综合") -> Dict[str, Any]:
        """构建加载中卡片"""
        return {
            "config": {"wide_screen_mode": True},
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"⏳ 正在进行{analysis_type}分析...\n\n股票代码: {stock_code}"
                    }
                }
            ]
        }
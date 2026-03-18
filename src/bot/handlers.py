"""
AlphaPilot Bot - 命令处理器

处理飞书机器人的各种命令

Issue: #21 (UI-001)
"""

import asyncio
import logging
import re
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass

from .bot import AlphaPilotBot
from .cards import CardBuilder

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class Command:
    """命令对象"""
    name: str
    args: str
    raw_text: str
    
    @classmethod
    def parse(cls, text: str) -> Optional["Command"]:
        """
        解析命令文本
        
        支持格式：
        - /analyze SH600519
        - /quant SH600519
        - /macro SH600519
        - /alt SH600519
        - /help
        """
        text = text.strip()
        
        # 匹配命令模式
        match = re.match(r'^/(\w+)\s*(.*)', text)
        if not match:
            return None
        
        command_name = match.group(1).lower()
        args = match.group(2).strip()
        
        return cls(
            name=command_name,
            args=args,
            raw_text=text
        )


class CommandHandler:
    """
    命令处理器
    
    处理各种飞书机器人命令
    """
    
    SUPPORTED_COMMANDS = {
        "analyze": "综合分析 - 分析股票的综合投资价值",
        "quant": "量化分析 - 基于量化模型的股票分析",
        "macro": "宏观分析 - 基于宏观经济视角的股票分析",
        "alt": "另类分析 - 基于北向资金、市场情绪等的分析",
        "help": "帮助信息 - 显示支持的命令列表"
    }
    
    # 股票代码验证正则
    STOCK_CODE_PATTERN = re.compile(r'^(SH|SZ|sh|sz)\d{6}$')
    
    def __init__(self, bot: AlphaPilotBot):
        self.bot = bot
        self.card_builder = CardBuilder()
    
    def validate_stock_code(self, code: str) -> Tuple[bool, str]:
        """
        验证股票代码格式
        
        返回: (是否有效, 标准化后的代码或错误信息)
        """
        # 标准化代码
        code = code.upper().strip()
        
        # 如果没有前缀，尝试添加
        if code.isdigit() and len(code) == 6:
            # 默认假设上海交易所
            code = f"SH{code}"
        
        # 验证格式
        if not self.STOCK_CODE_PATTERN.match(code):
            return False, f"无效的股票代码格式: {code}\n请使用格式: SH600519 或 SZ000001"
        
        return True, code
    
    async def handle_command(
        self,
        command: Command,
        message_id: str,
        receive_id: str,
        receive_id_type: str = "open_id"
    ) -> Dict[str, Any]:
        """
        处理命令
        
        Args:
            command: 命令对象
            message_id: 原始消息 ID（用于回复）
            receive_id: 接收者 ID
            receive_id_type: 接收者 ID 类型
            
        Returns:
            处理结果
        """
        logger.info(f"处理命令: {command.name}, 参数: {command.args}")
        
        # 分发到对应的处理器
        handler = getattr(self, f"_handle_{command.name}", None)
        if handler is None:
            return await self._handle_unknown(command, message_id, receive_id, receive_id_type)
        
        return await handler(command, message_id, receive_id, receive_id_type)
    
    async def _handle_analyze(
        self,
        command: Command,
        message_id: str,
        receive_id: str,
        receive_id_type: str
    ) -> Dict[str, Any]:
        """处理 /analyze 命令"""
        # 验证股票代码
        valid, code_or_error = self.validate_stock_code(command.args)
        if not valid:
            return await self.bot.reply_message(message_id, code_or_error)
        
        stock_code = code_or_error
        
        # 发送处理中提示
        await self.bot.reply_message(
            message_id,
            f"📊 正在分析 {stock_code}，请稍候..."
        )
        
        try:
            # 调用 API
            result = await self.bot.call_analyze_api(stock_code)
            
            # 构建分析结果卡片
            card = self.card_builder.build_analyze_card(result)
            
            # 发送卡片
            return await self.bot.send_card_message(
                receive_id,
                receive_id_type,
                card
            )
            
        except Exception as e:
            logger.error(f"分析失败: {e}")
            return await self.bot.reply_message(
                message_id,
                f"❌ 分析失败: {str(e)}"
            )
    
    async def _handle_quant(
        self,
        command: Command,
        message_id: str,
        receive_id: str,
        receive_id_type: str
    ) -> Dict[str, Any]:
        """处理 /quant 命令"""
        valid, code_or_error = self.validate_stock_code(command.args)
        if not valid:
            return await self.bot.reply_message(message_id, code_or_error)
        
        stock_code = code_or_error
        
        await self.bot.reply_message(
            message_id,
            f"📈 正在量化分析 {stock_code}..."
        )
        
        try:
            result = await self.bot.call_quant_api(stock_code)
            card = self.card_builder.build_quant_card(result)
            return await self.bot.send_card_message(receive_id, receive_id_type, card)
        except Exception as e:
            logger.error(f"量化分析失败: {e}")
            return await self.bot.reply_message(message_id, f"❌ 量化分析失败: {str(e)}")
    
    async def _handle_macro(
        self,
        command: Command,
        message_id: str,
        receive_id: str,
        receive_id_type: str
    ) -> Dict[str, Any]:
        """处理 /macro 命令"""
        valid, code_or_error = self.validate_stock_code(command.args)
        if not valid:
            return await self.bot.reply_message(message_id, code_or_error)
        
        stock_code = code_or_error
        
        await self.bot.reply_message(
            message_id,
            f"🌍 正在宏观分析 {stock_code}..."
        )
        
        try:
            result = await self.bot.call_macro_api(stock_code)
            card = self.card_builder.build_macro_card(result)
            return await self.bot.send_card_message(receive_id, receive_id_type, card)
        except Exception as e:
            logger.error(f"宏观分析失败: {e}")
            return await self.bot.reply_message(message_id, f"❌ 宏观分析失败: {str(e)}")
    
    async def _handle_alt(
        self,
        command: Command,
        message_id: str,
        receive_id: str,
        receive_id_type: str
    ) -> Dict[str, Any]:
        """处理 /alt 命令"""
        valid, code_or_error = self.validate_stock_code(command.args)
        if not valid:
            return await self.bot.reply_message(message_id, code_or_error)
        
        stock_code = code_or_error
        
        await self.bot.reply_message(
            message_id,
            f"💰 正在另类分析 {stock_code}..."
        )
        
        try:
            result = await self.bot.call_alt_api(stock_code)
            card = self.card_builder.build_alt_card(result)
            return await self.bot.send_card_message(receive_id, receive_id_type, card)
        except Exception as e:
            logger.error(f"另类分析失败: {e}")
            return await self.bot.reply_message(message_id, f"❌ 另类分析失败: {str(e)}")
    
    async def _handle_help(
        self,
        command: Command,
        message_id: str,
        receive_id: str,
        receive_id_type: str
    ) -> Dict[str, Any]:
        """处理 /help 命令"""
        help_text = """🤖 AlphaPilot - A股智能投资分析助手

📋 支持的命令：

/analyze <股票代码> - 综合分析
  示例: /analyze SH600519
  
/quant <股票代码> - 量化分析
  示例: /quant SH600519
  
/macro <股票代码> - 宏观分析
  示例: /macro SH600519
  
/alt <股票代码> - 另类分析
  示例: /alt SH600519

💡 股票代码格式：
  - 上海交易所: SH + 6位数字 (如 SH600519)
  - 深圳交易所: SZ + 6位数字 (如 SZ000001)

⚠️ 免责声明：
本系统提供的分析结果仅供参考，不构成投资建议。
投资有风险，入市需谨慎。"""
        
        return await self.bot.reply_message(message_id, help_text)
    
    async def _handle_unknown(
        self,
        command: Command,
        message_id: str,
        receive_id: str,
        receive_id_type: str
    ) -> Dict[str, Any]:
        """处理未知命令"""
        return await self.bot.reply_message(
            message_id,
            f"❓ 未知命令: {command.name}\n请使用 /help 查看支持的命令列表"
        )
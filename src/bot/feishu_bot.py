#!/usr/bin/env python3
"""
飞书机器人

UI-001: 飞书机器人开发

支持命令：
- /analyze <股票代码> - 综合分析
- /quant <股票代码> - 量化分析
- /macro <股票代码> - 宏观分析
- /alt <股票代码> - 另类分析
- /help - 显示帮助
"""

import os
import json
import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FeishuBot:
    """
    飞书机器人
    
    处理飞书消息，执行股票分析
    """
    
    def __init__(
        self,
        app_id: str = None,
        app_secret: str = None,
        use_mock: bool = False
    ):
        """
        初始化飞书机器人
        
        Args:
            app_id: 飞书应用 ID
            app_secret: 飞书应用密钥
            use_mock: 是否使用模拟模式
        """
        self.app_id = app_id or os.environ.get('FEISHU_APP_ID', '')
        self.app_secret = app_secret or os.environ.get('FEISHU_APP_SECRET', '')
        self.use_mock = use_mock
        
        # 初始化分析器
        if not use_mock:
            from ..crew.investment_crew import InvestmentCrew
            self.crew = InvestmentCrew()
        else:
            self.crew = None
        
        # 初始化消息处理器
        from .message_handler import MessageHandler
        self.handler = MessageHandler(self.crew)
        
        # 初始化卡片构建器
        from .card_builder import CardBuilder
        self.card_builder = CardBuilder()
        
        logger.info(f"飞书机器人初始化完成 (mock={use_mock})")
    
    def process_message(self, message: str, user_id: str = None) -> Dict[str, Any]:
        """
        处理消息
        
        这是主要的入口点，接收消息并返回响应
        
        Args:
            message: 消息文本
            user_id: 用户 ID
        
        Returns:
            响应字典，包含：
            - success: 是否成功
            - message_type: 消息类型 (text/interactive)
            - content: 消息内容
        """
        logger.info(f"处理消息: {message}")
        
        # 处理消息
        result = self.handler.handle(message, user_id)
        
        if not result.get('success'):
            # 返回错误消息
            return {
                'success': False,
                'message_type': 'text',
                'content': result.get('error', '处理失败')
            }
        
        command = result.get('command')
        
        if command == 'help':
            # 返回帮助文本
            return {
                'success': True,
                'message_type': 'text',
                'content': result.get('help_text')
            }
        
        # 构建分析结果卡片
        card = self.card_builder.build_analysis_card(
            command=command,
            stock_code=result.get('stock_code'),
            result=result.get('result'),
            elapsed_time=result.get('elapsed_time', 0)
        )
        
        return {
            'success': True,
            'message_type': 'interactive',
            'content': card
        }
    
    def handle_event(self, event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        处理飞书事件
        
        Args:
            event: 飞书事件数据
        
        Returns:
            响应数据
        """
        event_type = event.get('header', {}).get('event_type')
        
        if event_type == 'im.message.receive_v1':
            # 接收消息事件
            return self._handle_message_event(event)
        
        logger.warning(f"未处理的事件类型: {event_type}")
        return None
    
    def _handle_message_event(self, event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """处理消息事件"""
        # 提取消息内容
        event_body = event.get('event', {})
        message = event_body.get('message', {})
        
        message_type = message.get('message_type')
        if message_type != 'text':
            logger.warning(f"不支持的消息类型: {message_type}")
            return None
        
        # 解析消息内容
        content = json.loads(message.get('content', '{}'))
        text = content.get('text', '')
        
        # 获取发送者信息
        sender = event_body.get('sender', {})
        sender_id = sender.get('sender_id', {}).get('user_id', '')
        
        # 处理消息
        return self.process_message(text, sender_id)


def main():
    """测试飞书机器人"""
    print("=" * 60)
    print("🤖 AlphaPilot 飞书机器人测试")
    print("=" * 60)
    
    # 创建机器人
    bot = FeishuBot(use_mock=True)
    
    # 测试命令
    test_commands = [
        "/help",
        "/analyze 600519",
        "/quant SH600519",
        "/macro 600519",
        "/alt SH600519"
    ]
    
    for cmd in test_commands:
        print(f"\n测试命令: {cmd}")
        print("-" * 40)
        result = bot.process_message(cmd)
        print(f"成功: {result.get('success')}")
        print(f"消息类型: {result.get('message_type')}")
        if result.get('message_type') == 'text':
            print(f"内容: {result.get('content')[:100]}...")
    
    print("\n" + "=" * 60)
    print("✅ 测试完成")
    print("=" * 60)


if __name__ == "__main__":
    main()
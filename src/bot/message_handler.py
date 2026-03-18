"""
消息处理器

处理飞书机器人接收到的消息
"""

import re
import logging
from typing import Dict, Any, Optional, Tuple
from datetime import datetime

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MessageHandler:
    """
    消息处理器
    
    解析和处理飞书消息，执行相应的分析任务
    """
    
    # 命令模式
    COMMAND_PATTERNS = {
        'analyze': r'^/analyze\s+(\S+)',
        'quant': r'^/quant\s+(\S+)',
        'macro': r'^/macro\s+(\S+)',
        'alt': r'^/alt\s+(\S+)',
        'help': r'^/help'
    }
    
    def __init__(self, crew_analyzer):
        """
        初始化消息处理器
        
        Args:
            crew_analyzer: InvestmentCrew 实例，用于执行分析
        """
        self.crew = crew_analyzer
        logger.info("消息处理器初始化完成")
    
    def parse_command(self, message: str) -> Tuple[Optional[str], Optional[str]]:
        """
        解析命令
        
        Args:
            message: 消息文本
        
        Returns:
            (command, stock_code) 元组
        """
        message = message.strip()
        
        for command, pattern in self.COMMAND_PATTERNS.items():
            match = re.match(pattern, message, re.IGNORECASE)
            if match:
                if command == 'help':
                    return command, None
                else:
                    stock_code = match.group(1)
                    # 标准化股票代码
                    stock_code = self._normalize_stock_code(stock_code)
                    return command, stock_code
        
        return None, None
    
    def _normalize_stock_code(self, code: str) -> str:
        """
        标准化股票代码
        
        Args:
            code: 股票代码
        
        Returns:
            标准化后的股票代码（如 SH600519）
        """
        # 移除空格
        code = code.strip().upper()
        
        # 如果没有前缀，添加前缀
        if code.isdigit() or (len(code) == 6 and code[0].isdigit()):
            # 判断市场
            if code.startswith('6'):
                return f"SH{code}"
            else:
                return f"SZ{code}"
        
        # 如果已有前缀，标准化
        if code.startswith('SH') or code.startswith('SZ'):
            return code
        
        return code
    
    def handle(self, message: str, user_id: str = None) -> Dict[str, Any]:
        """
        处理消息
        
        Args:
            message: 消息文本
            user_id: 用户 ID
        
        Returns:
            处理结果
        """
        logger.info(f"处理消息: {message}")
        
        # 解析命令
        command, stock_code = self.parse_command(message)
        
        if command is None:
            return {
                'success': False,
                'error': '无法识别的命令。使用 /help 查看帮助。',
                'help_text': self._get_help_text()
            }
        
        # 处理帮助命令
        if command == 'help':
            return {
                'success': True,
                'command': 'help',
                'help_text': self._get_help_text()
            }
        
        # 执行分析
        try:
            start_time = datetime.now()
            
            if command == 'analyze':
                # 综合分析
                result = self.crew.analyze(stock_code, parallel=False)
            elif command == 'quant':
                # 量化分析
                from ..agents.quantitative import QuantitativeAnalyst
                agent = QuantitativeAnalyst()
                result = agent.analyze(stock_code)
            elif command == 'macro':
                # 宏观分析
                from ..agents.macro import MacroAnalyst
                agent = MacroAnalyst()
                result = agent.analyze(stock_code)
            elif command == 'alt':
                # 另类分析
                from ..agents.alternative import AlternativeAnalyst
                agent = AlternativeAnalyst()
                result = agent.analyze(stock_code)
            
            elapsed = (datetime.now() - start_time).total_seconds()
            
            return {
                'success': True,
                'command': command,
                'stock_code': stock_code,
                'result': result,
                'elapsed_time': elapsed
            }
            
        except Exception as e:
            logger.error(f"分析失败: {e}")
            return {
                'success': False,
                'command': command,
                'stock_code': stock_code,
                'error': str(e)
            }
    
    def _get_help_text(self) -> str:
        """获取帮助文本"""
        return """
📊 **AlphaPilot 股票分析机器人**

**可用命令：**

• `/analyze <股票代码>` - 综合分析
  示例：`/analyze SH600519` 或 `/analyze 600519`

• `/quant <股票代码>` - 量化分析
  技术指标、因子分析、趋势判断

• `/macro <股票代码>` - 宏观分析
  经济环境、政策影响、地缘风险

• `/alt <股票代码>` - 另类分析
  北向资金、大宗商品、市场情绪

• `/help` - 显示帮助信息

**示例：**
```
/analyze 600519
/quant SH600519
/macro 600519
```

**注意事项：**
• 股票代码支持 6 位数字或带前缀格式（SH/SZ）
• 分析时间约 30-60 秒，请耐心等待
• 本分析仅供参考，不构成投资建议
"""
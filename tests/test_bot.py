"""
AlphaPilot Bot - 测试

测试飞书机器人功能

Issue: #21 (UI-001)
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import json

from src.bot.bot import AlphaPilotBot, BotConfig
from src.bot.handlers import CommandHandler, Command
from src.bot.cards import CardBuilder


class TestCommand:
    """测试命令解析"""
    
    def test_parse_analyze_command(self):
        """测试解析 /analyze 命令"""
        cmd = Command.parse("/analyze SH600519")
        assert cmd is not None
        assert cmd.name == "analyze"
        assert cmd.args == "SH600519"
    
    def test_parse_quant_command(self):
        """测试解析 /quant 命令"""
        cmd = Command.parse("/quant SH600519")
        assert cmd is not None
        assert cmd.name == "quant"
        assert cmd.args == "SH600519"
    
    def test_parse_help_command(self):
        """测试解析 /help 命令"""
        cmd = Command.parse("/help")
        assert cmd is not None
        assert cmd.name == "help"
        assert cmd.args == ""
    
    def test_parse_no_command(self):
        """测试非命令文本"""
        cmd = Command.parse("这是一条普通消息")
        assert cmd is None
    
    def test_parse_command_with_extra_spaces(self):
        """测试带额外空格的命令"""
        cmd = Command.parse("  /analyze   SH600519  ")
        assert cmd is not None
        assert cmd.name == "analyze"
        assert cmd.args == "SH600519"


class TestCommandHandler:
    """测试命令处理器"""
    
    @pytest.fixture
    def bot(self):
        """创建模拟机器人"""
        bot = MagicMock(spec=AlphaPilotBot)
        bot.reply_message = AsyncMock(return_value={"code": 0})
        bot.send_card_message = AsyncMock(return_value={"code": 0})
        bot.call_analyze_api = AsyncMock(return_value={
            "stock_code": "SH600519",
            "overall_rating": "中性偏多",
            "confidence": 0.65,
            "score": 0.62,
            "summary": "测试摘要",
            "risk_warnings": [],
            "execution_time": "5s"
        })
        return bot
    
    @pytest.fixture
    def handler(self, bot):
        """创建命令处理器"""
        return CommandHandler(bot)
    
    def test_validate_stock_code_valid(self, handler):
        """测试有效的股票代码"""
        valid, code = handler.validate_stock_code("SH600519")
        assert valid is True
        assert code == "SH600519"
    
    def test_validate_stock_code_lowercase(self, handler):
        """测试小写的股票代码"""
        valid, code = handler.validate_stock_code("sh600519")
        assert valid is True
        assert code == "SH600519"
    
    def test_validate_stock_code_no_prefix(self, handler):
        """测试无前缀的股票代码"""
        valid, code = handler.validate_stock_code("600519")
        assert valid is True
        assert code == "SH600519"
    
    def test_validate_stock_code_invalid(self, handler):
        """测试无效的股票代码"""
        valid, error = handler.validate_stock_code("invalid")
        assert valid is False
        assert "无效" in error
    
    @pytest.mark.asyncio
    async def test_handle_help(self, handler, bot):
        """测试处理 /help 命令"""
        cmd = Command(name="help", args="", raw_text="/help")
        result = await handler.handle_command(
            cmd, "msg_123", "ou_123", "open_id"
        )
        bot.reply_message.assert_called_once()
        call_args = bot.reply_message.call_args
        assert "支持的命令" in call_args[0][1]


class TestCardBuilder:
    """测试卡片构建器"""
    
    @pytest.fixture
    def builder(self):
        return CardBuilder()
    
    def test_build_analyze_card(self, builder):
        """测试构建分析卡片"""
        result = {
            "stock_code": "SH600519",
            "overall_rating": "中性偏多",
            "confidence": 0.65,
            "score": 0.62,
            "summary": "测试摘要",
            "risk_warnings": ["风险1"],
            "execution_time": "5s"
        }
        
        card = builder.build_analyze_card(result)
        
        assert "config" in card
        assert "elements" in card
        assert card["config"]["wide_screen_mode"] is True
    
    def test_build_error_card(self, builder):
        """测试构建错误卡片"""
        card = builder.build_error_card("测试错误")
        
        assert "elements" in card
        assert len(card["elements"]) > 0
    
    def test_rating_colors(self, builder):
        """测试评级颜色映射"""
        assert builder.RATING_COLORS["看涨"] == "green"
        assert builder.RATING_COLORS["看跌"] == "red"
        assert builder.RATING_COLORS["中性"] == "grey"


class TestBotConfig:
    """测试机器人配置"""
    
    def test_default_config(self):
        """测试默认配置"""
        config = BotConfig(
            app_id="test_app_id",
            app_secret="test_secret"
        )
        assert config.app_id == "test_app_id"
        assert config.api_base_url == "http://localhost:8000"
    
    def test_from_env(self, monkeypatch):
        """测试从环境变量加载"""
        monkeypatch.setenv("LARK_APP_ID", "env_app_id")
        monkeypatch.setenv("LARK_APP_SECRET", "env_secret")
        
        config = BotConfig.from_env()
        assert config.app_id == "env_app_id"
        assert config.app_secret == "env_secret"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
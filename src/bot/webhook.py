"""
AlphaPilot Bot - Webhook 服务器

接收和处理飞书事件回调

Issue: #21 (UI-001)
"""

import asyncio
import json
import logging
import hashlib
from typing import Optional, Dict, Any
from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from .bot import AlphaPilotBot, BotConfig
from .handlers import CommandHandler, Command

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============== 事件模型 ==============

class EventHeader(BaseModel):
    """事件头"""
    event_id: str
    event_type: str
    create_time: str
    token: Optional[str] = None
    app_id: Optional[str] = None
    tenant_key: Optional[str] = None


class EventSender(BaseModel):
    """事件发送者"""
    sender_id: Dict[str, str]
    sender_type: str
    tenant_key: str


class EventMessage(BaseModel):
    """事件消息"""
    message_id: str
    root_id: Optional[str] = None
    parent_id: Optional[str] = None
    create_time: str
    chat_id: str
    message_type: str
    content: str
    mentions: Optional[list] = None


class EventBody(BaseModel):
    """事件体"""
    sender: EventSender
    message: Optional[EventMessage] = None


class LarkEvent(BaseModel):
    """飞书事件"""
    schema: str
    header: EventHeader
    event: EventBody


# ============== Webhook 应用 ==============

def create_webhook_app(config: Optional[BotConfig] = None) -> FastAPI:
    """
    创建 Webhook FastAPI 应用
    
    Args:
        config: 机器人配置
        
    Returns:
        FastAPI 应用实例
    """
    app = FastAPI(
        title="AlphaPilot Bot Webhook",
        description="飞书机器人事件回调服务",
        version="1.0.0"
    )
    
    # 初始化机器人和处理器
    bot = AlphaPilotBot(config)
    command_handler = CommandHandler(bot)
    
    @app.on_event("startup")
    async def startup():
        """启动事件"""
        logger.info("AlphaPilot Bot Webhook 服务启动")
    
    @app.on_event("shutdown")
    async def shutdown():
        """关闭事件"""
        await bot.close()
        logger.info("AlphaPilot Bot Webhook 服务关闭")
    
    @app.get("/health")
    async def health():
        """健康检查"""
        return {"status": "healthy", "service": "alphapilot-bot"}
    
    @app.post("/webhook")
    async def webhook(request: Request, background_tasks: BackgroundTasks):
        """
        飞书事件回调处理
        
        文档：https://open.feishu.cn/document/ukTMukTMukTM/uUTNz4SN1MjL1UzM
        """
        try:
            # 获取原始请求体
            body = await request.body()
            data = json.loads(body)
            
            logger.info(f"收到 webhook 事件: {data.get('header', {}).get('event_type')}")
            
            # 处理 URL 验证
            if data.get("type") == "url_verification":
                challenge = data.get("challenge", "")
                logger.info(f"URL 验证请求: challenge={challenge}")
                return JSONResponse(content={"challenge": challenge})
            
            # 解析事件
            event = LarkEvent(**data)
            
            # 验证 token
            if bot.config.verification_token:
                if event.header.token != bot.config.verification_token:
                    logger.warning(f"无效的 verification_token: {event.header.token}")
                    raise HTTPException(status_code=401, detail="Invalid token")
            
            # 处理消息事件
            if event.header.event_type == "im.message.receive_v1":
                background_tasks.add_task(
                    handle_message_event,
                    bot,
                    command_handler,
                    event
                )
            
            return JSONResponse(content={"code": 0, "msg": "success"})
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON 解析错误: {e}")
            raise HTTPException(status_code=400, detail="Invalid JSON")
        except Exception as e:
            logger.error(f"处理 webhook 错误: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))
    
    return app


async def handle_message_event(
    bot: AlphaPilotBot,
    handler: CommandHandler,
    event: LarkEvent
):
    """
    处理消息事件
    
    Args:
        bot: 机器人实例
        handler: 命令处理器
        event: 飞书事件
    """
    try:
        message = event.event.message
        if not message:
            return
        
        # 只处理文本消息
        if message.message_type != "text":
            return
        
        # 解析消息内容
        content = json.loads(message.content)
        text = content.get("text", "").strip()
        
        logger.info(f"收到消息: {text}")
        
        # 解析命令
        command = Command.parse(text)
        if not command:
            # 不是命令，忽略
            return
        
        # 获取发送者信息
        sender_id = event.event.sender.sender_id
        receive_id = sender_id.get("open_id") or sender_id.get("user_id")
        receive_id_type = "open_id" if sender_id.get("open_id") else "user_id"
        
        # 处理命令
        await handler.handle_command(
            command=command,
            message_id=message.message_id,
            receive_id=receive_id,
            receive_id_type=receive_id_type
        )
        
    except Exception as e:
        logger.error(f"处理消息事件错误: {e}", exc_info=True)


# ============== 启动脚本 ==============

if __name__ == "__main__":
    import uvicorn
    import os
    
    # 从环境变量加载配置
    config = BotConfig.from_env()
    
    # 创建应用
    app = create_webhook_app(config)
    
    # 启动服务
    port = int(os.getenv("BOT_PORT", "8080"))
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
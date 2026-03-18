"""
AlphaPilot Bot - 飞书机器人核心实现

基于飞书开放平台 API 实现股票分析机器人

Issue: #21 (UI-001)
"""

import asyncio
import logging
import re
import httpx
from typing import Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class BotConfig:
    """机器人配置"""
    app_id: str
    app_secret: str
    encrypt_key: Optional[str] = None
    verification_token: Optional[str] = None
    api_base_url: str = "http://localhost:8000"
    
    @classmethod
    def from_env(cls) -> "BotConfig":
        """从环境变量加载配置"""
        import os
        return cls(
            app_id=os.getenv("LARK_APP_ID", ""),
            app_secret=os.getenv("LARK_APP_SECRET", ""),
            encrypt_key=os.getenv("LARK_ENCRYPT_KEY"),
            verification_token=os.getenv("LARK_VERIFICATION_TOKEN"),
            api_base_url=os.getenv("API_BASE_URL", "http://localhost:8000")
        )


class AlphaPilotBot:
    """
    AlphaPilot 飞书机器人
    
    支持命令：
    - /analyze <股票代码> - 综合分析
    - /quant <股票代码> - 量化分析
    - /macro <股票代码> - 宏观分析
    - /alt <股票代码> - 另类分析
    - /help - 帮助信息
    """
    
    def __init__(self, config: Optional[BotConfig] = None):
        self.config = config or BotConfig.from_env()
        self.access_token: Optional[str] = None
        self.token_expire_time: int = 0
        self.http_client = httpx.AsyncClient(timeout=60.0)
        
    async def close(self):
        """关闭 HTTP 客户端"""
        await self.http_client.aclose()
    
    # ============== 认证相关 ==============
    
    async def get_tenant_access_token(self) -> str:
        """
        获取 tenant_access_token
        
        文档：https://open.feishu.cn/document/ukTMukTMukTM/ukDNz4SO0MjL5QzM/auth-v3/auth/tenant_access_token/internal
        """
        # 检查缓存
        if self.access_token and datetime.now().timestamp() < self.token_expire_time - 300:
            return self.access_token
        
        url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
        payload = {
            "app_id": self.config.app_id,
            "app_secret": self.config.app_secret
        }
        
        try:
            response = await self.http_client.post(url, json=payload)
            result = response.json()
            
            if result.get("code") == 0:
                self.access_token = result["tenant_access_token"]
                self.token_expire_time = result["expire"] + datetime.now().timestamp()
                logger.info("成功获取 tenant_access_token")
                return self.access_token
            else:
                logger.error(f"获取 token 失败: {result}")
                raise Exception(f"获取 token 失败: {result.get('msg')}")
                
        except Exception as e:
            logger.error(f"认证请求失败: {e}")
            raise
    
    # ============== 消息发送 ==============
    
    async def send_text_message(
        self,
        receive_id: str,
        receive_id_type: str,
        content: str,
        msg_type: str = "text"
    ) -> Dict[str, Any]:
        """
        发送文本消息
        
        文档：https://open.feishu.cn/document/ukTMukTMukTM/uUjNz4SN2MjL1YzM
        """
        token = await self.get_tenant_access_token()
        
        url = "https://open.feishu.cn/open-apis/im/v1/messages"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # 构造消息内容
        if msg_type == "text":
            message_content = {"text": content}
        else:
            message_content = content
        
        params = {
            "receive_id_type": receive_id_type
        }
        
        payload = {
            "receive_id": receive_id_id,
            "msg_type": msg_type,
            "content": message_content if isinstance(message_content, str) else str(message_content).replace("'", '"')
        }
        
        try:
            response = await self.http_client.post(
                url,
                headers=headers,
                params=params,
                json={
                    "receive_id": receive_id,
                    "msg_type": msg_type,
                    "content": message_content if isinstance(message_content, str) else str(message_content).replace("'", '"')
                }
            )
            result = response.json()
            
            if result.get("code") == 0:
                logger.info(f"消息发送成功: {receive_id}")
                return result
            else:
                logger.error(f"消息发送失败: {result}")
                raise Exception(f"消息发送失败: {result.get('msg')}")
                
        except Exception as e:
            logger.error(f"发送消息请求失败: {e}")
            raise
    
    async def send_card_message(
        self,
        receive_id: str,
        receive_id_type: str,
        card_content: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        发送消息卡片
        
        文档：https://open.feishu.cn/document/ukTMukTMukTM/uYjNwUjL2YDM14iN2ATN
        """
        token = await self.get_tenant_access_token()
        
        url = "https://open.feishu.cn/open-apis/im/v1/messages"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        params = {
            "receive_id_type": receive_id_type
        }
        
        payload = {
            "receive_id": receive_id,
            "msg_type": "interactive",
            "content": card_content
        }
        
        try:
            response = await self.http_client.post(
                url,
                headers=headers,
                params=params,
                json=payload
            )
            result = response.json()
            
            if result.get("code") == 0:
                logger.info(f"卡片消息发送成功: {receive_id}")
                return result
            else:
                logger.error(f"卡片消息发送失败: {result}")
                raise Exception(f"卡片消息发送失败: {result.get('msg')}")
                
        except Exception as e:
            logger.error(f"发送卡片请求失败: {e}")
            raise
    
    async def reply_message(
        self,
        message_id: str,
        content: str,
        msg_type: str = "text"
    ) -> Dict[str, Any]:
        """
        回复消息
        
        文档：https://open.feishu.cn/document/ukTMukTMukTM/uUjNz4SN2MjL1YzM
        """
        token = await self.get_tenant_access_token()
        
        url = f"https://open.feishu.cn/open-apis/im/v1/messages/{message_id}/reply"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        if msg_type == "text":
            message_content = {"text": content}
        else:
            message_content = content
        
        payload = {
            "msg_type": msg_type,
            "content": message_content
        }
        
        try:
            response = await self.http_client.post(
                url,
                headers=headers,
                json=payload
            )
            result = response.json()
            
            if result.get("code") == 0:
                logger.info(f"回复消息成功: {message_id}")
                return result
            else:
                logger.error(f"回复消息失败: {result}")
                raise Exception(f"回复消息失败: {result.get('msg')}")
                
        except Exception as e:
            logger.error(f"回复消息请求失败: {e}")
            raise
    
    # ============== API 调用 ==============
    
    async def call_analyze_api(self, stock_code: str) -> Dict[str, Any]:
        """调用分析 API"""
        url = f"{self.config.api_base_url}/api/analyze"
        payload = {
            "stock_code": stock_code,
            "parallel": True,
            "time_horizon": 5
        }
        
        try:
            response = await self.http_client.post(url, json=payload)
            result = response.json()
            logger.info(f"分析 API 调用成功: {stock_code}")
            return result
        except Exception as e:
            logger.error(f"分析 API 调用失败: {e}")
            raise
    
    async def call_quant_api(self, stock_code: str) -> Dict[str, Any]:
        """调用量化分析 API"""
        url = f"{self.config.api_base_url}/api/analyze/quantitative"
        payload = {
            "stock_code": stock_code,
            "parallel": True,
            "time_horizon": 5
        }
        
        try:
            response = await self.http_client.post(url, json=payload)
            result = response.json()
            return result
        except Exception as e:
            logger.error(f"量化分析 API 调用失败: {e}")
            raise
    
    async def call_macro_api(self, stock_code: str) -> Dict[str, Any]:
        """调用宏观分析 API"""
        url = f"{self.config.api_base_url}/api/analyze/macro"
        payload = {
            "stock_code": stock_code,
            "parallel": True,
            "time_horizon": 5
        }
        
        try:
            response = await self.http_client.post(url, json=payload)
            result = response.json()
            return result
        except Exception as e:
            logger.error(f"宏观分析 API 调用失败: {e}")
            raise
    
    async def call_alt_api(self, stock_code: str) -> Dict[str, Any]:
        """调用另类分析 API"""
        url = f"{self.config.api_base_url}/api/analyze/alternative"
        payload = {
            "stock_code": stock_code,
            "parallel": True,
            "time_horizon": 5
        }
        
        try:
            response = await self.http_client.post(url, json=payload)
            result = response.json()
            return result
        except Exception as e:
            logger.error(f"另类分析 API 调用失败: {e}")
            raise
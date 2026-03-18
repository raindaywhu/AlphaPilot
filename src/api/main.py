"""
AlphaPilot API - 分析接口

提供股票分析 REST API + 飞书机器人 Webhook

Issue: #20 (API-001), #21 (UI-001)
"""

from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
import logging
from datetime import datetime
import json
import re

# 导入 Crew
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from src.crew.investment_crew import InvestmentCrew

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建 FastAPI 应用
app = FastAPI(
    title="AlphaPilot API",
    description="A股智能投资分析系统 API",
    version="1.0.0"
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============== 数据模型 ==============

class AnalyzeRequest(BaseModel):
    """股票分析请求"""
    stock_code: str = Field(..., description="股票代码，如 SH600519", example="SH600519")
    parallel: bool = Field(True, description="是否并行分析")
    time_horizon: int = Field(5, description="预测周期（天）", ge=1, le=30)


class AnalyzeResponse(BaseModel):
    """股票分析响应"""
    stock_code: str
    analysis_date: str
    overall_rating: str  # 综合评级：看涨/中性偏多/中性/中性偏空/看跌
    confidence: float
    score: float = Field(0.5, description="数值化得分 0-1")
    quantitative: Dict[str, Any]
    macro: Dict[str, Any]
    alternative: Dict[str, Any]
    summary: str
    risk_warnings: List[str] = Field(default_factory=list)
    disclaimer: str = ""
    execution_time: str


class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str
    timestamp: str
    version: str


# ============== API 接口 ==============

@app.get("/api/health", response_model=HealthResponse, tags=["系统"])
async def health_check():
    """
    健康检查接口
    
    检查 API 服务是否正常运行
    """
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        version="1.0.0"
    )


@app.post("/api/analyze", response_model=AnalyzeResponse, tags=["分析"])
async def analyze_stock(request: AnalyzeRequest):
    """
    股票综合分析接口
    
    执行量化、宏观、另类三维分析
    
    - **stock_code**: 股票代码，如 SH600519
    - **parallel**: 是否并行分析（默认 True）
    - **time_horizon**: 预测周期（天）
    """
    logger.info(f"开始分析股票: {request.stock_code}")
    
    try:
        # 初始化 Crew
        crew = InvestmentCrew(use_mock=False)
        
        # 执行分析
        result = crew.analyze(
            stock_code=request.stock_code,
            parallel=request.parallel,
            time_horizon=request.time_horizon
        )
        
        # 构造响应
        response = AnalyzeResponse(
            stock_code=result.get("stock_code", request.stock_code),
            analysis_date=result.get("analysis_date", datetime.now().strftime("%Y-%m-%d")),
            overall_rating=result.get("overall_rating", "中性"),
            confidence=result.get("confidence", 0.5),
            score=result.get("score", 0.5),
            quantitative=result.get("agent_results", {}).get("quantitative", {}),
            macro=result.get("agent_results", {}).get("macro", {}),
            alternative=result.get("agent_results", {}).get("alternative", {}),
            summary=result.get("summary", ""),
            risk_warnings=result.get("risk_warnings", []),
            disclaimer=result.get("disclaimer", ""),
            execution_time=result.get("execution_time", "0s")
        )
        
        logger.info(f"分析完成: {request.stock_code}, 耗时 {response.execution_time}")
        return response
        
    except Exception as e:
        logger.error(f"分析失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}")


@app.post("/api/analyze/quantitative", tags=["分析"])
async def analyze_quantitative(request: AnalyzeRequest):
    """
    量化分析接口
    
    仅执行量化分析师 Agent 的分析
    """
    logger.info(f"开始量化分析: {request.stock_code}")
    
    try:
        from src.agents.quantitative import QuantitativeAnalyst
        
        analyst = QuantitativeAnalyst()
        result = analyst.analyze(
            stock_code=request.stock_code,
            time_horizon=request.time_horizon
        )
        
        return {
            "stock_code": request.stock_code,
            "analysis_type": "quantitative",
            "result": result
        }
        
    except Exception as e:
        logger.error(f"量化分析失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"量化分析失败: {str(e)}")


@app.post("/api/analyze/macro", tags=["分析"])
async def analyze_macro(request: AnalyzeRequest):
    """
    宏观分析接口
    
    仅执行宏观分析师 Agent 的分析
    """
    logger.info(f"开始宏观分析: {request.stock_code}")
    
    try:
        from src.agents.macro import MacroAnalyst
        
        analyst = MacroAnalyst()
        result = analyst.analyze(stock_code=request.stock_code)
        
        return {
            "stock_code": request.stock_code,
            "analysis_type": "macro",
            "result": result
        }
        
    except Exception as e:
        logger.error(f"宏观分析失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"宏观分析失败: {str(e)}")


@app.post("/api/analyze/alternative", tags=["分析"])
async def analyze_alternative(request: AnalyzeRequest):
    """
    另类分析接口
    
    仅执行另类分析师 Agent 的分析
    """
    logger.info(f"开始另类分析: {request.stock_code}")
    
    try:
        from src.agents.alternative import AlternativeAnalyst
        
        analyst = AlternativeAnalyst()
        result = analyst.analyze(stock_code=request.stock_code)
        
        return {
            "stock_code": request.stock_code,
            "analysis_type": "alternative",
            "result": result
        }
        
    except Exception as e:
        logger.error(f"另类分析失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"另类分析失败: {str(e)}")


# ============== 飞书机器人 Webhook ==============

# 命令模式
COMMAND_PATTERNS = {
    'analyze': r'^/analyze\s+(\S+)',
    'quant': r'^/quant\s+(\S+)',
    'macro': r'^/macro\s+(\S+)',
    'alt': r'^/alt\s+(\S+)',
    'help': r'^/help'
}

def parse_command(message: str):
    """解析飞书命令"""
    message = message.strip()
    for command, pattern in COMMAND_PATTERNS.items():
        match = re.match(pattern, message, re.IGNORECASE)
        if match:
            if command == 'help':
                return command, None
            else:
                stock_code = match.group(1)
                # 标准化股票代码
                stock_code = stock_code.strip().upper()
                if stock_code.isdigit() or (len(stock_code) == 6 and stock_code[0].isdigit()):
                    if stock_code.startswith('6'):
                        stock_code = f"SH{stock_code}"
                    else:
                        stock_code = f"SZ{stock_code}"
                return command, stock_code
    return None, None

def get_help_text():
    """获取帮助文本"""
    return """🤖 AlphaPilot - A股智能投资分析助手

📋 支持的命令：

/analyze <股票代码> - 综合分析
  示例: /analyze 600519
  
/quant <股票代码> - 量化分析
  示例: /quant 600519
  
/macro <股票代码> - 宏观分析
  示例: /macro 600519

/alt <股票代码> - 另类分析
  示例: /alt 600519

💡 股票代码支持 6 位数字格式（自动识别沪/深）

⚠️ 免责声明：本分析仅供参考，不构成投资建议。"""

@app.post("/webhook", tags=["飞书机器人"])
async def feishu_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    飞书机器人 Webhook 端点
    
    处理飞书消息事件，识别并执行股票分析命令
    
    支持命令：
    - /analyze <股票代码> - 综合分析
    - /quant <股票代码> - 量化分析
    - /macro <股票代码> - 宏观分析
    - /alt <股票代码> - 另类分析
    - /help - 帮助信息
    """
    try:
        # 获取请求体
        body = await request.body()
        data = json.loads(body)
        
        logger.info(f"收到飞书 Webhook 事件: {data.get('header', {}).get('event_type')}")
        
        # 处理 URL 验证
        if data.get("type") == "url_verification":
            challenge = data.get("challenge", "")
            logger.info(f"飞书 URL 验证请求: challenge={challenge}")
            return JSONResponse(content={"challenge": challenge})
        
        # 解析事件
        event_type = data.get('header', {}).get('event_type')
        
        if event_type != 'im.message.receive_v1':
            logger.debug(f"忽略非消息事件: {event_type}")
            return JSONResponse(content={"code": 0, "msg": "ignored"})
        
        # 提取消息内容
        event_body = data.get('event', {})
        message = event_body.get('message', {})
        
        if message.get('message_type') != 'text':
            logger.debug(f"忽略非文本消息: {message.get('message_type')}")
            return JSONResponse(content={"code": 0, "msg": "ignored"})
        
        # 解析消息内容
        content = json.loads(message.get('content', '{}'))
        text = content.get('text', '').strip()
        
        logger.info(f"收到飞书消息: {text}")
        
        # 解析命令
        command, stock_code = parse_command(text)
        
        if command is None:
            # 不是命令，忽略
            return JSONResponse(content={"code": 0, "msg": "ignored"})
        
        # 处理帮助命令
        if command == 'help':
            return JSONResponse(content={
                "code": 0,
                "msg": "success",
                "reply": get_help_text()
            })
        
        # 异步执行分析
        background_tasks.add_task(
            execute_analysis,
            command=command,
            stock_code=stock_code,
            message_id=message.get('message_id')
        )
        
        return JSONResponse(content={
            "code": 0,
            "msg": "processing",
            "reply": f"📊 正在分析 {stock_code}，请稍候..."
        })
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON 解析错误: {e}")
        raise HTTPException(status_code=400, detail="Invalid JSON")
    except Exception as e:
        logger.error(f"处理飞书 Webhook 错误: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

async def execute_analysis(command: str, stock_code: str, message_id: str = None):
    """
    异步执行分析任务
    
    Args:
        command: 命令类型 (analyze/quant/macro/alt)
        stock_code: 股票代码
        message_id: 消息 ID（用于回复）
    """
    try:
        logger.info(f"开始执行分析: {command} {stock_code}")
        
        if command == 'analyze':
            crew = InvestmentCrew(use_mock=False)
            result = crew.analyze(stock_code, parallel=False)
        elif command == 'quant':
            from src.agents.quantitative import QuantitativeAnalyst
            analyst = QuantitativeAnalyst()
            result = analyst.analyze(stock_code)
        elif command == 'macro':
            from src.agents.macro import MacroAnalyst
            analyst = MacroAnalyst()
            result = analyst.analyze(stock_code)
        elif command == 'alt':
            from src.agents.alternative import AlternativeAnalyst
            analyst = AlternativeAnalyst()
            result = analyst.analyze(stock_code)
        else:
            logger.error(f"未知命令: {command}")
            return
        
        logger.info(f"分析完成: {command} {stock_code}")
        logger.info(f"结果: {result.get('overall_rating', 'N/A') if isinstance(result, dict) else 'N/A'}")
        
    except Exception as e:
        logger.error(f"分析执行失败: {e}", exc_info=True)


# ============== 启动脚本 ==============

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
"""
AlphaPilot API - 分析接口

提供股票分析 REST API + Web UI

Issue: #20 (API-001), #21 (UI-001), #32 (UI-002)
"""

from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
import logging
from datetime import datetime
import json
import re
import os
from pathlib import Path

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

# 配置静态文件服务 (Web UI)
WEB_DIR = Path(__file__).parent.parent / "web"
if WEB_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(WEB_DIR)), name="static")


# ============== 数据模型 ==============

class AnalyzeRequest(BaseModel):
    """股票分析请求"""
    stock_code: str = Field(..., description="股票代码，如 SH600519", example="SH600519")
    parallel: bool = Field(True, description="是否并行分析")
    time_horizon: int = Field(5, description="预测周期（天）", ge=1, le=30)


class AnalyzeResponse(BaseModel):
    """股票分析响应"""
    stock_code: str
    stock_name: str = ""
    analysis_date: str
    overall_rating: str  # buy/hold/sell
    confidence: float
    recommendation: str = ""
    quantitative: Dict[str, Any] = {}
    fundamental: Dict[str, Any] = {}
    macro: Dict[str, Any] = {}
    alternative: Dict[str, Any] = {}
    risk: Dict[str, Any] = {}
    summary: str = ""
    risk_warnings: List[str] = Field(default_factory=list)
    disclaimer: str = ""
    execution_time: str = ""


class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str
    timestamp: str
    version: str


# ============== Web UI ==============

@app.get("/", response_class=HTMLResponse, tags=["Web UI"])
async def root():
    """
    Web UI 入口
    
    返回分析界面 HTML
    """
    index_file = WEB_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file), media_type="text/html")
    return HTMLResponse(content="<h1>AlphaPilot Web UI</h1><p>请访问 /docs 查看 API 文档</p>")


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
    
    执行量化、基本面、宏观、另类、风控五维分析
    
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
        agent_results = result.get("agent_results", {})
        
        # 映射评级
        rating_map = {
            "看涨": "buy",
            "中性偏多": "buy",
            "中性": "hold",
            "中性偏空": "sell",
            "看跌": "sell"
        }
        overall = result.get("overall_rating", "中性")
        rating = rating_map.get(overall, "hold")
        
        response = AnalyzeResponse(
            stock_code=result.get("stock_code", request.stock_code),
            stock_name=result.get("stock_name", ""),
            analysis_date=result.get("analysis_date", datetime.now().strftime("%Y-%m-%d")),
            overall_rating=rating,
            confidence=result.get("confidence", 0.5),
            recommendation=result.get("recommendation", ""),
            quantitative=agent_results.get("quantitative", {}),
            fundamental=agent_results.get("fundamental", {}),
            macro=agent_results.get("macro", {}),
            alternative=agent_results.get("alternative", {}),
            risk=agent_results.get("risk", {}),
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

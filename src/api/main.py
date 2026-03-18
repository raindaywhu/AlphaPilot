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

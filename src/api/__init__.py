"""AlphaPilot API - REST API 接口"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import sys
import os

# 添加项目根目录到 sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.crew.investment_crew import InvestmentCrew

# 创建 FastAPI 应用
app = FastAPI(
    title="AlphaPilot API",
    description="A股智能投资分析系统 REST API",
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


# ============== 请求模型 ==============

class AnalyzeRequest(BaseModel):
    """股票分析请求"""
    stock_code: str = Field(..., description="股票代码，如 SH600519")
    parallel: Optional[bool] = Field(True, description="是否并行分析")
    time_horizon: Optional[int] = Field(5, description="预测周期（天）", ge=1, le=30)


class QuantitativeRequest(BaseModel):
    """量化分析请求"""
    stock_code: str = Field(..., description="股票代码")
    time_horizon: Optional[int] = Field(5, description="预测周期（天）")


class MacroRequest(BaseModel):
    """宏观分析请求"""
    stock_code: str = Field(..., description="股票代码")


class AlternativeRequest(BaseModel):
    """另类分析请求"""
    stock_code: str = Field(..., description="股票代码")


# ============== 响应模型 ==============

class AnalyzeResponse(BaseModel):
    """股票分析响应"""
    stock_code: str
    analysis_date: str
    analysis_type: str
    overall_view: str
    confidence: float
    quantitative_analysis: Optional[Dict[str, Any]] = None
    macro_analysis: Optional[Dict[str, Any]] = None
    alternative_analysis: Optional[Dict[str, Any]] = None
    risk_warnings: list
    conclusion: str


class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str
    version: str
    qlib_initialized: bool
    crew_ready: bool


# ============== API 路由 ==============

@app.get("/api/health", response_model=HealthResponse, tags=["系统"])
async def health_check():
    """
    健康检查接口
    
    返回系统状态信息
    """
    try:
        # 检查 qlib 是否初始化
        from qlib import config as qlib_config
        qlib_initialized = qlib_config.QLIB_DATA_PATH is not None
    except:
        qlib_initialized = False
    
    # 检查 Crew 是否就绪
    try:
        crew = InvestmentCrew()
        crew_ready = crew is not None
    except:
        crew_ready = False
    
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        qlib_initialized=qlib_initialized,
        crew_ready=crew_ready
    )


@app.post("/api/analyze", tags=["分析"])
async def analyze_stock(request: AnalyzeRequest):
    """
    股票综合分析接口
    
    返回量化+宏观+另类的综合分析结果
    """
    try:
        # 创建 Crew 实例
        crew = InvestmentCrew()
        
        # 执行分析
        result = crew.analyze(
            stock_code=request.stock_code,
            parallel=request.parallel,
            time_horizon=request.time_horizon
        )
        
        # 直接返回结果（已经包含所有需要的字段）
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}")


@app.post("/api/analyze/quantitative", tags=["分析"])
async def analyze_quantitative(request: QuantitativeRequest):
    """
    量化分析接口
    
    仅执行量化分析师 Agent 的分析
    """
    try:
        from src.agents.quantitative import QuantitativeAnalyst
        
        agent = QuantitativeAnalyst()
        result = agent.analyze(
            stock_code=request.stock_code,
            time_horizon=request.time_horizon
        )
        
        return {
            "stock_code": request.stock_code,
            "analysis_type": "量化分析",
            **result
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"量化分析失败: {str(e)}")


@app.post("/api/analyze/macro", tags=["分析"])
async def analyze_macro(request: MacroRequest):
    """
    宏观分析接口
    
    仅执行宏观分析师 Agent 的分析
    """
    try:
        from src.agents.macro import MacroAnalyst
        
        agent = MacroAnalyst()
        result = agent.analyze(stock_code=request.stock_code)
        
        return {
            "stock_code": request.stock_code,
            "analysis_type": "宏观分析",
            **result
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"宏观分析失败: {str(e)}")


@app.post("/api/analyze/alternative", tags=["分析"])
async def analyze_alternative(request: AlternativeRequest):
    """
    另类分析接口
    
    仅执行另类分析师 Agent 的分析
    """
    try:
        from src.agents.alternative import AlternativeAnalyst
        
        agent = AlternativeAnalyst()
        result = agent.analyze(stock_code=request.stock_code)
        
        return {
            "stock_code": request.stock_code,
            "analysis_type": "另类分析",
            **result
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"另类分析失败: {str(e)}")


# ============== 启动配置 ==============

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
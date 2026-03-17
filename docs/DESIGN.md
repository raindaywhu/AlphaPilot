# A股智能投资系统 - 详细设计方案 V5

> 版本：5.0  
> 日期：2026-03-17  
> 产品经理：Jack  
> 开发：mac

---

## 一、决策总结

| 决策项 | 选择 | 理由 |
|--------|------|------|
| qlib 模型 | **GBDT/XGBoost** | 适合小数据集（5年有效数据），快速稳定可解释 |
| Agent 数量 | **6 个** | 专业分工，一次性到位 |
| CrewAI LLM | **GLM-5** | 保持现有配置，不换 GPT-4 |
| RAG 能力 | **每个 Agent 独立 RAG** | 专业化知识库，提高分析质量 |

---

## 二、系统目标

### 核心指标
- 年化收益：20-30%
- 最大回撤：<15%
- 夏普比率：>1.5
- 胜率：>55%

---

## 三、系统架构

### 3.1 整体架构

```
┌─────────────────────────────────────────────────────────┐
│                    用户交互层                            │
│  Web界面 + 飞书机器人 + REST API                         │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│                    CrewAI Flow 层                        │
│  ┌──────────────────────────────────────────────────┐  │
│  │          InvestmentAnalysisFlow                   │  │
│  │                                                   │  │
│  │  ┌─────────┐   ┌─────────┐   ┌─────────┐        │  │
│  │  │ 数据准备 │ → │ 并行分析 │ → │ 综合决策 │        │  │
│  │  └─────────┘   └─────────┘   └─────────┘        │  │
│  │                     ↓                            │  │
│  │              ┌─────────────┐                     │  │
│  │              │ 生成报告    │                     │  │
│  │              └─────────────┘                     │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│                    CrewAI Agent 层                       │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │                InvestmentCrew                     │  │
│  │                                                   │  │
│  │  量化分析师 ←→ 基本面分析师 ←→ 宏观分析师        │  │
│  │       ↓              ↓              ↓            │  │
│  │  另类分析师 ←→ 风控经理 ←→ 投资决策者            │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
│  每个 Agent 配置：                                      │
│  - 独立的 RAG 知识库（CrewAI Knowledge）               │
│  - 独立的 Memory 记忆（CrewAI Memory）                 │
│  - 专业化的 Tools 工具                                │
│                                                         │
│  LLM: GLM-5（所有 Agent 统一使用）                     │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│                    qlib 模型层                           │
│                                                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │ Alpha158    │  │ GBDT/XGBoost│  │ 策略回测    │    │
│  │ 因子计算    │  │ 模型预测    │  │ 自动验证    │    │
│  └─────────────┘  └─────────────┘  └─────────────┘    │
│                                                         │
│  充分利用 qlib 内置能力：                               │
│  - Alpha158/Alpha360 预置因子                          │
│  - SignalStrategy/TopkDropoutStrategy 策略框架         │
│  - 自动回测 + 报告生成                                 │
│  - 超参数调优 + 在线学习                               │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│                    qlib 数据层                           │
│  历史行情 + 因子数据 + 财务数据 + 定时更新              │
│  数据源：mootdx（实时）+ qlib（历史，需更新）           │
│  数据更新：每日 17:00自动更新                           │
└─────────────────────────────────────────────────────────┘
```

---

## 四、qlib 详细设计

### 4.1 充分利用 qlib 内置能力

qlib 提供了丰富的内置功能，我们应充分利用：

| qlib 能力 | 如何使用 | 价值 |
|-----------|----------|------|
| **Alpha158** | 直接使用 158 个预置因子 | 无需自己定义因子 |
| **Alpha360** | 可选使用 360 个预置因子 | 更丰富的因子库 |
| **GBDT/XGBoost/CatBoost** | 模型预测 | 适合小数据集 |
| **SignalStrategy** | 信号策略框架 | 标准化策略实现 |
| **TopkDropoutStrategy** | Topk 轮动策略 | 可直接使用 |
| **backtest()** | 回测引擎 | 自动验证策略 |
| **backtest_executor** | 回测执行器 | 支持多种执行逻辑 |
| **report()** | 报告生成 | 自动生成分析报告 |
| **在线学习** | 增量更新模型 | 适应市场变化 |
| **超参数调优** | 自动调参 | 优化模型性能 |

### 4.2 数据更新机制

**问题**：当前 qlib 数据只到 2020-09-25，需要增量更新到最新。

**解决方案**：使用 mootdx 获取实时数据，同步到 qlib 数据格式。

```python
import qlib
from qlib.data import D
from mootdx.quotes import Quotes
import pandas as pd
from datetime import datetime, timedelta

class QlibDataUpdater:
    """qlib 数据更新器"""
    
    def __init__(self):
        # 初始化 mootdx
        selfQuotes = Quotes.factory(market='std')
        
        # qlib 数据目录
        self.qlib_data_dir = "~/.qlib/qlib_data/cn_data"
    
    def update_daily(self):
        """
        每日更新数据
        
        执行时间：每个交易日 17:00
        """
        # 1. 获取最新交易日
        latest_date = self._get_latest_trade_date()
        
        # 2. 获取 qlib 数据最新日期
        qlib_latest = self._get_qlib_latest_date()
        
        # 3. 计算需要更新的日期范围
        if latest_date > qlib_latest:
            start_date = qlib_latest + timedelta(days=1)
            end_date = latest_date
            
            # 4. 下载增量数据
            self._download_incremental_data(start_date, end_date)
            
            # 5. 转换为 qlib 格式
            self._convert_to_qlib_format(start_date, end_date)
            
            print(f"数据更新完成：{start_date} - {end_date}")
        else:
            print("数据已是最新，无需更新")
    
    def _get_latest_trade_date(self) -> datetime:
        """获取最新交易日"""
        # 使用 mootdx 获取交易日历
        calendar = self.quotes.trade_calendar()
        latest = calendar[-1]
        return datetime.strptime(latest, "%Y-%m-%d")
    
    def _get_qlib_latest_date(self) -> datetime:
        """获取 qlib 数据最新日期"""
        # 读取 qlib 数据目录下的最新日期
        import os
        data_dir = os.path.expanduser(self.qlib_data_dir)
        
        # 检查 features 目录
        features_dir = os.path.join(data_dir, "features")
        if os.path.exists(features_dir):
            stocks = os.listdir(features_dir)
            if stocks:
                # 取第一个股票的最新日期
                stock_dir = os.path.join(features_dir, stocks[0])
                files = os.listdir(stock_dir)
                if files:
                    latest_file = sorted(files)[-1]
                    # 文件名格式：sh600519_2020-09-25.bin
                    date_str = latest_file.split('_')[1].replace('.bin', '')
                    return datetime.strptime(date_str, "%Y-%m-%d")
        
        return datetime(2020, 9, 25)  # 默认值
    
    def _download_incremental_data(self, start_date: datetime, end_date: datetime):
        """下载增量数据"""
        # 使用 mootdx 下载日线数据
        stocks = self._get_stock_list()
        
        for stock in stocks:
            # 下载日线数据
            data = self.quotes.bars(
                code=stock,
                frequency=9,  # 日线
                start=0,
                offset=100
            )
            
            # 过滤日期范围
            data = data[
                (data['datetime'] >= start_date.strftime("%Y-%m-%d")) &
                (data['datetime'] <= end_date.strftime("%Y-%m-%d"))
            ]
            
            # 保存到临时文件
            self._save_temp_data(stock, data)
    
    def _convert_to_qlib_format(self, start_date: datetime, end_date: datetime):
        """转换为 qlib 格式"""
        # qlib 使用二进制格式存储数据
        # 需要将 mootdx 数据转换为 qlib 格式
        
        import struct
        import os
        
        stocks = self._get_stock_list()
        data_dir = os.path.expanduser(self.qlib_data_dir)
        
        for stock in stocks:
            # 读取临时数据
            temp_data = self._read_temp_data(stock)
            
            # 转换为 qlib 格式
            for _, row in temp_data.iterrows():
                date = row['datetime']
                features = [
                    row['open'],
                    row['high'],
                    row['low'],
                    row['close'],
                    row['volume'],
                    row['amount']
                ]
                
                # 写入二进制文件
                file_path = os.path.join(
                    data_dir,
                    "features",
                    stock,
                    f"{stock}_{date}.bin"
                )
                
                with open(file_path, 'wb') as f:
                    for feature in features:
                        f.write(struct.pack('f', feature))
    
    def _get_stock_list(self) -> list:
        """获取股票列表"""
        # 使用 qlib 内置的股票列表
        from qlib.data import D
        
        instruments = D.instruments(market="cn")
        return [inst for inst in instruments]
    
    def _save_temp_data(self, stock: str, data: pd.DataFrame):
        """保存临时数据"""
        import os
        temp_dir = "/tmp/qlib_update"
        os.makedirs(temp_dir, exist_ok=True)
        
        data.to_csv(f"{temp_dir}/{stock}.csv", index=False)
    
    def _read_temp_data(self, stock: str) -> pd.DataFrame:
        """读取临时数据"""
        temp_dir = "/tmp/qlib_update"
        return pd.read_csv(f"{temp_dir}/{stock}.csv")


# ============== 定时任务 ==============

def setup_data_update_cron():
    """
    设置数据更新定时任务
    
    每个交易日 17:00 执行
    """
    from openclaw import cron
    
    cron.add_job(
        name="qlib_data_update",
        schedule={"kind": "cron", "expr": "0 17 * * 1-5"},  # 周一到周五 17:00
        payload={"kind": "systemEvent", "text": "更新 qlib 数据"},
        sessionTarget="main"
    )
```

### 4.3 因子系统

```python
from qlib.contrib.data.handler import Alpha158, Alpha360
from qlib.data import D

class QlibFactorEngine:
    """qlib 因子引擎 - 充分利用内置因子"""
    
    def __init__(self):
        # 使用 Alpha158 因子（推荐）
        self.alpha158 = Alpha158()
        
        # 可选：Alpha360 更丰富的因子
        self.alpha360 = Alpha360()
    
    def get_alpha158_factors(self, stock_code: str, date: str = None):
        """
        获取 Alpha158 因子数据
        
        Alpha158 包含：
        - 动量因子（Momentum）
        - 波动率因子（Volatility）
        - 流动性因子（Liquidity）
        - 质量因子（Quality）
        - 价值因子（Value）
        - 成长因子（Growth）
        - 技术因子（Technical）
        """
        return self.alpha158.fetch(stock_code, date)
    
    def get_factor_by_category(self, stock_code: str, category: str):
        """
        按类别获取因子
        
        Args:
            category: momentum, volatility, liquidity, quality, value, growth
        """
        all_factors = self.get_alpha158_factors(stock_code)
        # 根据 qlib 因子定义分类返回
        return self._filter_by_category(all_factors, category)
```

### 4.4 模型系统（只用 GBDT/XGBoost）

```python
from qlib.contrib.model.gbdt import LGBModel
from qlib.contrib.model.xgboost import XGBoostModel
from qlib.workflow import R
from qlib.workflow.record_temp import SignalRecord

class QlibModelEngine:
    """qlib 模型引擎 - 使用 GBDT/XGBoost"""
    
    def __init__(self):
        # 可用模型
        self.models = {
            "lightgbm": LGBModel,
            "xgboost": XGBoostModel
        }
        
        # 加载预训练模型
        self.loaded_models = self._load_models()
    
    def train_model(
        self,
        instrument: str,
        start_time: str,
        end_time: str,
        model_type: str = "lightgbm"
    ):
        """
        训练 GBDT 模型
        
        使用 qlib 的 R (Recorder) 进行实验管理
        """
        with R.start(experiment_name="train_model"):
            # 创建模型
            model = self.models[model_type]()
            
            # 训练
            model.fit(instrument, start_time, end_time)
            
            # 记录模型
            R.log_params(**{"model_type": model_type})
            
            # 保存模型
            model_path = f"~/.qlib/models/{model_type}_{instrument}.pkl"
            model.save(model_path)
            
            return model
    
    def predict(
        self,
        stock_code: str,
        model_type: str = "lightgbm",
        horizon: int = 5
    ):
        """
        使用 GBDT 模型预测
        
        Returns:
            {
                "prediction": 涨跌幅预测值,
                "confidence": 置信度（基于历史准确率）
            }
        """
        model = self.loaded_models[model_type]
        
        # 预测
        pred = model.predict(stock_code)
        
        # 计算置信度（基于历史预测准确率）
        confidence = self._calculate_confidence(model, stock_code)
        
        return {
            "prediction": pred,
            "confidence": confidence,
            "horizon": horizon
        }
    
    def hyperparameter_tuning(self, instrument: str):
        """
        使用 qlib 的超参数调优能力
        """
        from qlib.model.trainer import Trainer
        
        trainer = Trainer()
        best_params = trainer.tune(
            model_type="lightgbm",
            instrument=instrument,
            n_trials=50
        )
        
        return best_params
    
    def online_learning(self, new_data: dict):
        """
        使用 qlib 的在线学习能力
        
        增量更新模型，适应市场变化
        """
        model = self.loaded_models["lightgbm"]
        model.update(new_data)
```

---

## 五、CrewAI RAG 构建方法

### 5.1 RAG 概述

**CrewAI Knowledge = RAG 功能**

CrewAI 内置 Knowledge 功能，支持为每个 Agent 配置独立的 RAG 知识库。

**RAG 工作流程**：
1. 知识源 → Embedding 向量化
2. 存储到 ChromaDB/Qdrant
3. Agent 执行任务时自动检索
4. 检索结果增强 Agent 的回答

### 5.2 构建步骤

#### 步骤 1：创建知识目录

```bash
mkdir -p knowledge/
```

#### 步骤 2：准备知识源文件

```
knowledge/
├── technical_indicators.txt      # 技术指标说明
├── quant_strategies.pdf          # 量化策略手册
├── financial_analysis.pdf        # 财务分析方法
├── valuation_methods.pdf         # 估值模型
├── macro_frameworks.txt          # 宏观经济框架
├── policy_analysis.pdf           # 政策分析
├── north_money_analysis.txt      # 北向资金分析
├── risk_management.pdf           # 风险管理
└── decision_frameworks.txt       # 投资决策框架
```

#### 步骤 3：创建 KnowledgeSource

```python
from crewai.knowledge.source.pdf_knowledge_source import PDFKnowledgeSource
from crewai.knowledge.source.text_file_knowledge_source import TextFileKnowledgeSource

# PDF 知识源
quant_pdf = PDFKnowledgeSource(file_paths=["knowledge/quant_strategies.pdf"])

# 文本知识源
technical_txt = TextFileKnowledgeSource(file_paths=["knowledge/technical_indicators.txt"])
```

#### 步骤 4：配置 Agent

```python
from crewai import Agent

quant_analyst = Agent(
    role="量化分析师",
    knowledge_sources=[quant_pdf, technical_txt],
    embedder={"provider": "ollama", "config": {"model": "mxbai-embed-large"}}
)
```

### 5.3 知识源类型

| 类型 | 用途 | 示例 |
|------|------|------|
| StringKnowledgeSource | 字符串 | 直接传入文本 |
| TextFileKnowledgeSource | 文本文件 | .txt 文件 |
| PDFKnowledgeSource | PDF 文档 | 研报、财报 |
| CSVKnowledgeSource | CSV 文件 | 数据表格 |
| JSONKnowledgeSource | JSON 文件 | 结构化数据 |
| 自定义 | 任意数据源 | API、数据库等 |

### 5.4 Embedding 配置

| Provider | 优点 | 缺点 |
|---------|------|------|
| **Ollama（推荐）** | 本地运行，无需 API key | 需要安装 Ollama |
| OpenAI | 质量高 | 需要 API key |
| Azure OpenAI | 企业级 | 需要 Azure 配置 |
| Google Gemini | Google 生态 | 需要 API key |

**使用 Ollama 本地 Embedding**：

```python
agent = Agent(
    role="量化分析师",
    knowledge_sources=[...],
    embedder={
        "provider": "ollama",
        "config": {
            "model": "mxbai-embed-large"  # 推荐模型
        }
    }
)
```

### 5.5 每个 Agent 的知识库配置

#### 量化分析师

**知识源**：技术指标说明、量化策略、因子说明

```python
from crewai.knowledge.source.text_file_knowledge_source import TextFileKnowledgeSource
from crewai.knowledge.source.pdf_knowledge_source import PDFKnowledgeSource

quant_knowledge = TextFileKnowledgeSource(
    file_paths=[
        "knowledge/technical_indicators.txt",
        "knowledge/qlib_factors.txt"
    ]
)

quant_pdf = PDFKnowledgeSource(
    file_paths=["knowledge/quant_strategies.pdf"]
)

quant_analyst = Agent(
    role="量化分析师",
    knowledge_sources=[quant_knowledge, quant_pdf],
    embedder={"provider": "ollama", "config": {"model": "mxbai-embed-large"}}
)
```

**technical_indicators.txt 示例**：

```
# 技术指标说明

## MA（移动平均线）
- 定义：N 日收盘价的平均值
- 用途：趋势判断
- 信号：金叉（短期MA上穿长期MA）买入，死叉卖出

## MACD
- 定义：DIF = EMA(12) - EMA(26)，DEA = EMA(DIF, 9)
- 用途：动能判断
- 信号：DIF上穿DEA买入，下穿卖出

## RSI
- 定义：RSI = 100 - 100/(1+RS)，RS = 平均涨幅/平均跌幅
- 用途：超买超卖判断
- 信号：RSI>70超买，RSI<30超卖
```

#### 基本面分析师

**知识源**：财务分析、估值方法、行业框架

```python
fundamental_knowledge = PDFKnowledgeSource(
    file_paths=[
        "knowledge/financial_analysis.pdf",
        "knowledge/valuation_methods.pdf"
    ]
)

fundamental_analyst = Agent(
    role="基本面分析师",
    knowledge_sources=[fundamental_knowledge],
    embedder={"provider": "ollama", "config": {"model": "mxbai-embed-large"}}
)
```

#### 宏观分析师

**知识源**：宏观框架、政策分析、地缘政治

```python
macro_knowledge = TextFileKnowledgeSource(
    file_paths=[
        "knowledge/macro_frameworks.txt",
        "knowledge/policy_analysis.txt"
    ]
)

macro_analyst = Agent(
    role="宏观分析师",
    knowledge_sources=[macro_knowledge],
    embedder={"provider": "ollama", "config": {"model": "mxbai-embed-large"}}
)
```

#### 另类数据分析师

**知识源**：北向资金、情绪分析、供应链

```python
alternative_knowledge = TextFileKnowledgeSource(
    file_paths=[
        "knowledge/north_money_analysis.txt",
        "knowledge/sentiment_analysis.txt"
    ]
)

alternative_analyst = Agent(
    role="另类分析师",
    knowledge_sources=[alternative_knowledge],
    embedder={"provider": "ollama", "config": {"model": "mxbai-embed-large"}}
)
```

#### 风控经理

**知识源**：风险框架、止损策略、历史案例

```python
risk_knowledge = PDFKnowledgeSource(
    file_paths=["knowledge/risk_management.pdf"]
)

risk_manager = Agent(
    role="风控经理",
    knowledge_sources=[risk_knowledge],
    embedder={"provider": "ollama", "config": {"model": "mxbai-embed-large"}}
)
```

#### 投资决策者

**知识源**：决策框架、投资哲学、历史案例

```python
decision_knowledge = TextFileKnowledgeSource(
    file_paths=[
        "knowledge/decision_frameworks.txt",
        "knowledge/investment_philosophy.txt"
    ]
)

decision_maker = Agent(
    role="投资决策者",
    knowledge_sources=[decision_knowledge],
    embedder={"provider": "ollama", "config": {"model": "mxbai-embed-large"}}
)
```

### 5.6 知识源数据来源

| Agent | 需要的知识 | 数据来源 |
|-------|-----------|---------|
| **量化分析师** | 技术指标、量化策略、因子说明 | 自己整理、qlib 文档 |
| **基本面分析师** | 财务分析、估值方法、行业框架 | 自己整理、券商研报 |
| **宏观分析师** | 宏观框架、政策分析、地缘政治 | 自己整理、智库报告 |
| **另类分析师** | 北向资金、情绪分析、供应链 | 自己整理、数据说明 |
| **风控经理** | 风险框架、止损策略、历史案例 | 自己整理、风控手册 |
| **投资决策者** | 决策框架、投资哲学、历史案例 | 自己整理、投资经典 |

**推荐方案**：
1. 先整理最核心的知识（技术指标、财务分析、风险管理）
2. 创建简单的 TXT 文件测试 RAG 功能
3. 后续逐步完善知识库

---

## 六、CrewAI Agent 详细设计

### 6.1 Agent 数据源和工具映射

**核心原则**：
- 每个Agent 有明确的职责边界
- 每个Agent 知道从哪里获取数据（qlib / CrewAI Tools / RAG）
- 每个Agent 有明确的输入输出规范

| Agent | qlib | RAG | CrewAI Tools | 知识库内容 |
|-------|------|-----|-------------|-----------|
| **量化分析师** | ✅ 因子、模型、回测 | ✅ | QlibAlpha158Tool, QlibGBDTPredictionTool, QlibBacktestTool, TechnicalIndicatorTool | 技术指标、策略库、因子说明 |
| **基本面分析师** | ✅ 财务数据 | ✅ | QlibFinancialTool, ValuationCalculatorTool, IndustryCompareTool, PDFSearchTool | 财务分析、估值方法、行业框架 |
| **宏观分析师** | ❌ | ✅ | DuckDuckGoSearchRun, WebsiteSearchTool, MacroDataTool, PolicyAnalysisTool | 宏观框架、政策分析、地缘政治 |
| **另类分析师** | ❌ | ✅ | NorthMoneyTool, SentimentAnalysisTool, CommodityPriceTool, SupplyChainTool | 北向资金、情绪分析、供应链 |
| **风控经理** | ✅ 回测验证 | ✅ | RiskCalculatorTool, QlibBacktestTool, PositionSizerTool, StopLossTool | 风险框架、止损策略、历史案例 |
| **投资决策者** | ❌ | ✅ | 无（纯推理） | 决策框架、投资哲学、历史案例 |

---

### 6.2 LLM 配置（GLM-5）

```python
from langchain_openai import ChatOpenAI

# GLM-5 配置
GLM5_LLM = ChatOpenAI(
    model="glm-5",
    openai_api_base="https://coding.dashscope.aliyuncs.com/v1",
    openai_api_key="sk-sp-4223c58f489d4b41b4d67558bd625580",
    temperature=0.3
)

# 所有 Agent 统一使用 GLM-5
DEFAULT_LLM = GLM5_LLM
```

---

### 6.3 量化分析师详细设计

#### 6.3.1 角色定义

| 属性 | 值 |
|------|-----|
| **角色** | 资深量化分析师 |
| **目标** | 基于 qlib 因子和 GBDT 模型预测，提供技术面分析观点 |
| **数据源** | ✅ qlib（Alpha158 因子、GBDT 模型、回测）|
| **RAG** | ✅ 技术指标说明、策略库、因子说明 |
| **工具** | QlibAlpha158Tool, QlibGBDTPredictionTool, QlibBacktestTool, TechnicalIndicatorTool |

#### 6.3.2 输入输出规范

**输入**：
```json
{
  "stock_code": "sh600519",
  "analysis_type": "技术面分析",// 可选：趋势判断、买卖点识别、风险评估
  "time_horizon": 5  // 预测周期（天）
}
```

**输出**：
```json
{
  "stock_code": "sh600519",
  "analysis_date": "2026-03-17",
  "technical_view": "看涨/看跌/中性",
  "confidence": 0.75,
  "signals": [
    {
      "indicator": "MA",
      "signal": "金叉",
      "strength": "强",
      "description": "MA5上穿MA20，短期趋势转强"
    },
    {
      "indicator": "MACD",
      "signal": "金叉",
      "strength": "中",
      "description": "DIF上穿DEA，动能转强"
    }
  ],
  "factor_analysis": {
    "momentum": {"score": 0.8, "rank": "前20%"},
    "volatility": {"score": 0.6, "rank": "前40%"},
    "liquidity": {"score": 0.7, "rank": "前30%"}
  },
  "model_prediction": {
    "prediction": 0.025,  // 预测涨跌幅
    "confidence": 0.72,
    "horizon": 5
  },
  "backtest_validation": {
    "win_rate": 0.65,
    "avg_return": 0.032,
    "max_drawdown": -0.08
  },
  "risk_warning": ["短期波动较大", "注意止损"],
  "conclusion": "技术面偏多，建议关注MA支撑位"
}
```

#### 6.3.3 决策逻辑

```
1. 获取 qlibAlpha158 因子数据
   └─ 使用 QlibAlpha158Tool
   └─ 分析动量、波动率、流动性、质量、价值等因子

2. 获取 GBDT 模型预测
   └─ 使用 QlibGBDTPredictionTool
   └─ 预测未来 N 天涨跌幅

3. 计算技术指标
   └─ 使用 TechnicalIndicatorTool
   └─ 计算 MA、MACD、RSI、KDJ 等

4. 回测验证
   └─ 使用 QlibBacktestTool
   └─ 验证历史信号的有效性

5. 综合判断
   └─ 权衡因子信号、模型预测、技术指标
   └─ 输出最终观点和置信度
```

#### 6.3.4 详细 Prompt

```python
quant_analyst = Agent(
    role="资深量化分析师",
    goal="基于 qlib 因子和 GBDT 模型预测，提供技术面分析观点",
    
    backstory="""你是一位拥有15年A股实战经验的量化分析师。
    
## 你的背景
- 曾任职于顶级量化私募，管理规模超过50亿
- 精通技术分析、因子投资、GBDT 模型
- 擅长从数据中发现交易机会
- 你的量化策略在过去5年实现了年化25%的收益

## 你的专长
- 技术指标：MA、MACD、RSI、KDJ、布林带、ATR等
- 因子分析：Alpha158 因子（动量、波动率、流动性、质量、价值）
- 模型预测：GBDT/XGBoost 预测模型
- 量化信号：买卖点识别、趋势判断

## 你的工作流程
1. **数据验证**：
   - 检查数据是否为最新（当日或前一交易日）
   - 如果数据过期，要求重新获取最新数据
   - 如果数据缺失，明确指出并尝试补充
   
2. **获取数据**：使用 qlib 工具获取因子数据和模型预测
3. **计算指标**：使用技术指标工具计算 MA、MACD、RSI 等
4. **回测验证**：使用回测工具验证历史信号有效性
5. **综合判断**：权衡多个信号，输出最终观点
6. **风险评估**：明确指出不确定性和风险

## ⚠️ 数据验证要求（必须执行）
在开始分析前，**必须验证数据时效性**：
- 检查日期：数据日期是否为最新交易日？
- 如果数据过期：输出警告，要求重新获取
- 如果数据缺失：明确指出缺失项，尝试补充
- **不要使用过期数据做决策！**

## 你的输入输出
**输入**：stock_code（股票代码）, analysis_type（分析类型）, time_horizon（预测周期）
**输出**：JSON 格式的技术面分析报告（包含详细评级和逻辑推导）

## 你的工具使用方式
1. **QlibAlpha158Tool**：获取 Alpha158 因子数据
   - 输入：stock_code
   - 输出：因子值、因子排名、因子分类
   - ⚠️ 验证：检查数据日期是否为最新

2. **QlibGBDTPredictionTool**：获取模型预测
   - 输入：stock_code, horizon
   - 输出：预测涨跌幅、置信度
   - ⚠️ 验证：检查模型训练日期

3. **QlibBacktestTool**：回测验证
   - 输入：stock_code, strategy_type
   - 输出：胜率、平均收益、最大回撤

4. **TechnicalIndicatorTool**：技术指标计算
   - 输入：stock_code
   - 输出：MA、MACD、RSI、KDJ 等指标值和信号
   - ⚠️ 验证：检查数据是否为最新

## 你的 RAG 使用方式
- 当遇到不熟悉的技术指标时，检索知识库获取说明
- 当需要参考历史策略时，检索策略库获取案例
- 当需要理解因子含义时，检索因子说明文档

## 你的输出风格
- 数据驱动，每个结论都有数据支撑
- 简洁明了，直击要点
- 明确的观点，不模棱两可
- 风险提示，负责任的分析
- **详细展示评级结果和逻辑推导**""",
    
    tools=[
        QlibAlpha158Tool(),
        QlibGBDTPredictionTool(),
        QlibBacktestTool(),
        TechnicalIndicatorTool()
    ],
    
    llm=GLM5_LLM,
    
    # RAG 配置
    knowledge_sources=[quant_knowledge, quant_pdf],
    embedder={"provider": "ollama", "config": {"model": "mxbai-embed-large"}},
    
    # Memory 配置
    memory=True,
    
    # 其他配置
    max_iter=5,
    max_rpm=10,
    allow_delegation=False,
    verbose=True
)
```

#### 6.3.5 输出格式（包含详细评级）

```json
{
  "agent": "quant_analyst",
  "stock_code": "sh600519",
  "analysis_date": "2026-03-17",
  "data_validation": {
    "status": "valid",  // valid / expired / missing
    "latest_data_date": "2026-03-16",
    "warnings": []
  },
  "overall_rating": "看涨",  // 看涨/看跌/中性
  "confidence": 0.75,
  "rating_details": {
    "technical_signals": {
      "rating": "看涨",
      "score": 8.0,
      "reasoning": "MA5上穿MA20形成金叉，MACD金叉确认，RSI处于合理区间"
    },
    "factor_analysis": {
      "rating": "看涨",
      "score": 7.5,
      "reasoning": "动量因子排名前20%，波动率适中，流动性良好"
    },
    "model_prediction": {
      "rating": "看涨",
      "score": 7.0,
      "reasoning": "GBDT模型预测5日涨跌幅+2.5%，置信度72%"
    },
    "backtest_validation": {
      "rating": "中性",
      "score": 6.0,
      "reasoning": "历史胜率65%，但最大回撤-8%需要注意"
    }
  },
  "logic_derivation": {
    "step1": "验证数据时效性 → 数据有效",
    "step2": "计算技术指标 → MA金叉、MACD金叉、RSI合理",
    "step3": "分析因子数据 → 动量因子强势、波动率适中",
    "step4": "模型预测 → GBDT预测+2.5%",
    "step5": "回测验证 → 胜率65%，回撤-8%",
    "step6": "综合判断 → 技术面偏多，建议关注MA支撑位"
  },
  "signals": [...],
  "factor_analysis": {...},
  "model_prediction": {...},
  "backtest_validation": {...},
  "risk_warning": ["短期波动较大", "注意止损"],
  "conclusion": "技术面偏多，建议关注MA支撑位"
}
```

---

### 6.4 基本面分析师详细设计

#### 6.4.1 角色定义

| 属性 | 值 |
|------|-----|
| **角色** | 高级基本面分析师 |
| **目标** | 分析公司财务数据和估值，提供基本面观点 |
| **数据源** | ✅ qlib（财务数据）|
| **RAG** | ✅ 财务分析方法、估值模型、行业框架 |
| **工具** | QlibFinancialTool, ValuationCalculatorTool, IndustryCompareTool, PDFSearchTool |

#### 6.4.2 输入输出规范

**输入**：
```json
{
  "stock_code": "sh600519",
  "analysis_type": "基本面分析",
  "focus_areas": ["盈利能力", "成长性", "估值"]
}
```

**输出**：
```json
{
  "stock_code": "sh600519",
  "analysis_date": "2026-03-17",
  "fundamental_view": "看涨/看跌/中性",
  "confidence": 0.70,
  "financial_analysis": {
    "profitability": {
      "roe": 0.25,
      "gross_margin": 0.45,
      "net_margin": 0.20,
      "assessment": "盈利能力强"
    },
    "growth": {
      "revenue_growth": 0.15,
      "profit_growth": 0.20,
      "assessment": "成长性良好"
    },
    "financial_health": {
      "debt_ratio": 0.35,
      "current_ratio": 1.5,
      "assessment": "财务健康"
    }
  },
  "valuation": {
    "pe_ratio": 25,
    "pb_ratio": 3.5,
    "peg_ratio": 1.2,
    "fair_value": 1850,
    "current_price": 1800,
    "assessment": "估值合理"
  },
  "industry_comparison": {
    "rank": "前20%",
    "advantages": ["品牌优势", "渠道优势"],
    "disadvantages": ["增速放缓"]
  },
  "risk_warning": ["行业竞争加剧", "原材料成本上升"],
  "conclusion": "基本面优秀，估值合理，建议关注"
}
```

#### 6.4.3 决策逻辑

```
1. 获取财务数据
   └─ 使用 QlibFinancialTool
   └─ 分析盈利能力、成长性、财务健康

2. 计算估值
   └─ 使用 ValuationCalculatorTool
   └─ 计算 PE、PB、PEG、DCF

3. 行业对比
   └─ 使用 IndustryCompareTool
   └─ 对比同行业公司

4. 读取财报
   └─ 使用 PDFSearchTool
   └─ 搜索财报中的关键信息

5. 综合判断
   └─ 权衡财务数据、估值、行业地位
   └─ 输出最终观点和置信度
```

#### 6.4.4 详细 Prompt

```python
fundamental_analyst = Agent(
    role="高级基本面分析师",
    goal="分析公司财务数据和估值，提供基本面观点",
    
    backstory="""你是一位资深基本面分析师，曾在顶级券商研究所工作10年。
    
## 你的背景
- 曾任职于中信证券、中金公司研究部
- 专注于消费、医药、科技行业研究
- 你的研究报告被机构投资者广泛引用
- 你推荐的股票平均年化收益超过20%

## 你的专长
- 财务分析：三大报表、财务比率、现金流分析
- 估值方法：PE、PB、PEG、DCF、相对估值
- 行业研究：竞争格局、行业周期、产业链分析
- 公司分析：商业模式、核心竞争力、管理层分析

## 你的工作流程
1. **获取财务数据**：使用 qlib 工具获取财务数据
2. **分析盈利能力**：分析 ROE、毛利率、净利率
3. **评估成长性**：分析收入增长、利润增长
4. **计算估值**：使用估值工具计算合理估值
5. **行业对比**：对比同行业公司，判断竞争力
6. **综合判断**：输出基本面观点

## 你的输入输出
**输入**：stock_code, analysis_type, focus_areas
**输出**：JSON 格式的基本面分析报告

## 你的工具使用方式
1. **QlibFinancialTool**：获取财务数据
   - 输入：stock_code
   - 输出：盈利能力、成长性、财务健康指标

2. **ValuationCalculatorTool**：计算估值
   - 输入：stock_code, method
   - 输出：PE、PB、PEG、DCF 估值

3. **IndustryCompareTool**：行业对比
   - 输入：stock_code, industry
   - 输出：行业排名、竞争优势

4. **PDFSearchTool**：搜索财报
   - 输入：pdf_path, query
   - 输出：财报中的关键信息

## 你的 RAG 使用方式
- 当需要参考财务分析方法时，检索知识库
- 当需要理解估值模型时，检索估值方法文档
- 当需要行业研究框架时，检索行业框架文档

## 你的输出风格
- 深度研究，不做表面文章
- 对标行业标杆，横向比较
- 关注长期价值，不被短期波动干扰
- 坦诚指出风险和不确定性""",
    
    tools=[
        QlibFinancialTool(),
        ValuationCalculatorTool(),
        IndustryCompareTool(),
        PDFSearchTool()
    ],
    
    llm=GLM5_LLM,
    
    # RAG 配置
    knowledge_sources=[fundamental_knowledge],
    embedder={"provider": "ollama", "config": {"model": "mxbai-embed-large"}},
    
    # Memory 配置
    memory=True,
    
    # 其他配置
    max_iter=5,
    max_rpm=10,
    allow_delegation=False,
    verbose=True
)
```

---

### 6.5 宏观分析师详细设计

#### 6.5.1 角色定义

| 属性 | 值 |
|------|-----|
| **角色** | 宏观经济分析师 |
| **目标** | 分析宏观经济环境、政策走向、地缘政治影响 |
| **数据源** | ❌ 不用 qlib |
| **RAG** | ✅ 宏观框架、政策分析、地缘政治 |
| **工具** | DuckDuckGoSearchRun, WebsiteSearchTool, MacroDataTool, PolicyAnalysisTool |

#### 6.5.2 输入输出规范

**输入**：
```json
{
  "stock_code": "sh600519",
  "analysis_type": "宏观分析",
  "focus_areas": ["货币政策", "财政政策", "国际形势"]
}
```

**输出**：
```json
{
  "stock_code": "sh600519",
  "analysis_date": "2026-03-17",
  "macro_view": "利好/利空/中性",
  "confidence": 0.65,
  "monetary_policy": {
    "status": "宽松",
    "impact": "利好股市",
    "key_points": ["央行降准", "利率维持低位"]
  },
  "fiscal_policy": {
    "status": "积极",
    "impact": "利好基建",
    "key_points": ["专项债加速发行", "减税降费"]
  },
  "international": {
    "fed_policy": "加息周期尾声",
    "trade_tension": "中美关系缓和",
    "impact": "外部环境改善"
  },
  "industry_policy": {
    "support_policies": ["消费刺激政策", "白酒行业规范"],
    "impact": "利好消费板块"
  },
  "risk_warning": ["美联储政策不确定性", "地缘政治风险"],
  "conclusion": "宏观环境偏暖，有利于消费板块"
}
```

#### 6.5.3 详细 Prompt

```python
macro_analyst = Agent(
    role="宏观经济分析师",
    goal="分析宏观经济环境、政策走向、地缘政治影响",
    
    backstory="""你是一位资深宏观分析师，曾在央行研究局和顶级智库工作。
    
## 你的背景
- 曾任职于央行研究局、中金公司研究部
- 专注于宏观经济、货币政策、国际经济研究
- 你准确预判了多次重大宏观事件
- 你的宏观策略被多家机构采用

## 你的专长
- 宏观指标：GDP、CPI、PMI、利率、汇率
- 货币政策：央行政策、流动性、利率走向
- 财政政策：财政收支、债务、基建投资
- 国际经济：美联储、全球经济、地缘政治

## ⚠️ 数据验证要求（必须执行）
在开始分析前，**必须验证数据时效性**：
- 检查宏观数据发布日期
- 检查政策新闻发布时间
- 检查地缘政治事件最新进展
- 如果信息过期：重新搜索最新信息
- **不要基于过期信息做判断！**

## 你的工作流程
1. **数据验证**：
   - 验证宏观数据是否为最新
   - 验证政策新闻是否为最新
   - 验证地缘政治事件是否为最新
   
2. **搜索最新信息**：
   - 使用搜索工具获取最新宏观新闻
   - 使用搜索工具获取最新政策解读
   - 使用搜索工具获取最新地缘政治动态
   
3. **分析影响**：
   - 分析货币政策对市场的影响
   - 分析财政政策对行业的影响
   - 分析地缘政治对风险偏好的影响
   
4. **逻辑推导**：
   - 明确展示推理链条
   - 每个结论都要有前提和论据
   - 识别不确定性因素

## ⚠️ 逻辑推导要求（必须执行）
对于**地缘政治**分析，必须输出完整的逻辑推导过程：
1. 事实陈述：发生了什么事件？
2. 直接影响：这个事件对什么有直接影响？
3. 间接影响：通过什么链条传导到市场？
4. 时效判断：影响是短期还是长期？
5. 不确定性：有哪些不确定因素？
6. 最终结论：对市场的整体影响是什么？

## 你的工具使用方式
1. **DuckDuckGoSearchRun**：搜索新闻
   - 输入：query（如"央行货币政策最新"）
   - 输出：相关新闻列表
   - ⚠️ 验证：检查新闻发布时间

2. **WebsiteSearchTool**：搜索特定网站
   - 输入：url, query
   - 输出：网站内容

3. **MacroDataTool**：获取宏观数据
   - 输入：indicator（如"GDP", "CPI"）
   - 输出：宏观经济指标数据
   - ⚠️ 验证：检查数据发布日期

4. **PolicyAnalysisTool**：政策分析
   - 输入：policy_document
   - 输出：政策解读

## 你的 RAG 使用方式
- 当需要参考宏观分析框架时，检索知识库
- 当需要理解政策影响时，检索政策分析文档
- 当需要了解历史案例时，检索历史案例库

## 你的输出风格
- 大局观，不拘泥于细节
- 关注边际变化，而非绝对水平
- 理解市场预期，预判政策走向
- 及时跟踪重大事件
- **详细展示逻辑推导过程**""",
    
    tools=[
        DuckDuckGoSearchRun(),
        WebsiteSearchTool(),
        MacroDataTool(),
        PolicyAnalysisTool()
    ],
    
    llm=GLM5_LLM,
    
    # RAG 配置
    knowledge_sources=[macro_knowledge],
    embedder={"provider": "ollama", "config": {"model": "mxbai-embed-large"}},
    
    # Memory 配置
    memory=True,
    
    # 其他配置
    max_iter=5,
    max_rpm=10,
    allow_delegation=False,
    verbose=True
)
```

#### 6.5.4 输出格式（包含详细逻辑推导）

```json
{
  "agent": "macro_analyst",
  "stock_code": "sh600519",
  "analysis_date": "2026-03-17",
  "data_validation": {
    "status": "valid",
    "latest_news_date": "2026-03-17",
    "latest_data_date": "2026-03-16",
    "warnings": []
  },
  "overall_rating": "利好",
  "confidence": 0.65,
  "rating_details": {
    "monetary_policy": {
      "rating": "利好",
      "score": 8.0,
      "reasoning": "央行降准释放流动性，利率维持低位"
    },
    "fiscal_policy": {
      "rating": "利好",
      "score": 7.5,
      "reasoning": "专项债加速发行，减税降费政策延续"
    },
    "international": {
      "rating": "中性偏多",
      "score": 6.5,
      "reasoning": "美联储加息周期尾声，中美关系缓和"
    },
    "industry_policy": {
      "rating": "利好",
      "score": 7.0,
      "reasoning": "消费刺激政策出台，白酒行业规范利好"
    }
  },
  "logic_derivation": {
    "geopolitical_analysis": {
      "event": "美联储加息周期尾声",
      "step1_fact": "美联储3月会议维持利率不变，暗示加息周期结束",
      "step2_direct_impact": "美元指数走弱，人民币汇率企稳",
      "step3_indirect_impact": "外资流入A股，利好消费板块",
      "step4_timing": "影响持续3-6个月",
      "step5_uncertainty": "美联储后续降息节奏不确定",
      "step6_conclusion": "外部环境改善，利好A股整体"
    },
    "policy_transmission": {
      "event": "央行降准",
      "step1_fact": "央行宣布降准0.5个百分点",
      "step2_direct_impact": "释放约1万亿流动性",
      "step3_indirect_impact": "市场利率下行，利好股市估值",
      "step4_timing": "影响持续6-12个月",
      "step5_uncertainty": "经济复苏力度不确定",
      "step6_conclusion": "货币政策宽松，利好股市"
    }
  },
  "monetary_policy": {...},
  "fiscal_policy": {...},
  "international": {...},
  "industry_policy": {...},
  "risk_warning": ["美联储政策不确定性", "地缘政治风险"],
  "conclusion": "宏观环境偏暖，有利于消费板块"
}
```

---

### 6.6 另类数据分析师详细设计

#### 6.6.1 角色定义

| 属性 | 值 |
|------|-----|
| **角色** | 另类数据分析师 |
| **目标** | 分析北向资金、市场情绪、供应链等另类数据 |
| **数据源** | ❌ 不用 qlib |
| **RAG** | ✅ 北向资金分析、情绪分析、供应链分析 |
| **工具** | NorthMoneyTool, SentimentAnalysisTool, CommodityPriceTool, SupplyChainTool |

#### 6.6.2 输入输出规范

**输入**：
```json
{
  "stock_code": "sh600519",
  "analysis_type": "另类数据分析",
  "focus_areas": ["北向资金", "情绪分析", "大宗商品"]
}
```

**输出**：
```json
{
  "stock_code": "sh600519",
  "analysis_date": "2026-03-17",
  "alternative_view": "利好/利空/中性",
  "confidence": 0.68,
  "north_money": {
    "net_inflow": 5.2,
    "trend": "持续流入",
    "holding_change": "+0.5%",
    "assessment": "外资看好"
  },
  "sentiment": {
    "overall_sentiment": 0.65,
    "news_sentiment": 0.70,
    "social_sentiment": 0.60,
    "assessment": "情绪偏乐观"
  },
  "commodities": {
    "related_commodities": ["粮食", "包装材料"],
    "price_trend": "稳定",
    "impact": "成本端稳定"
  },
  "supply_chain": {
    "upstream": "原材料供应稳定",
    "downstream": "需求旺盛",
    "assessment": "产业链健康"
  },
  "risk_warning": ["北向资金波动较大", "情绪指标滞后"],
  "conclusion": "另类数据整体偏多"
}
```

#### 6.6.3 详细 Prompt

```python
alternative_analyst = Agent(
    role="另类数据分析师",
    goal="分析北向资金、市场情绪、供应链、大宗商品等另类数据",
    
    backstory="""你是一位专注于另类数据的新锐分析师。
    
## 你的背景
- 曾任职于知名对冲基金，负责另类数据研究
- 擅长从非传统数据中发现 alpha
- 你的另类数据策略贡献了基金30%的收益
- 精通 NLP、情感分析、网络爬虫

## 你的专长
- 资金流向：北向资金、融资融券、大宗交易
- 市场情绪：舆情分析、股吧情绪、期权情绪
- 另类数据：卫星数据、信用卡数据、供应链数据
- 大宗商品：铜、铝、原油、黄金、粮食价格

## ⚠️ 数据验证要求（必须执行）
在开始分析前，**必须验证数据时效性**：
- 检查北向资金数据是否为最新交易日
- 检查大宗商品价格是否为最新
- 检查情绪分析数据是否为最新
- 如果信息过期：重新获取最新数据
- **不要基于过期数据做判断！**

## 你的工作流程
1. **数据验证**：
   - 验证北向资金数据日期
   - 验证大宗商品价格日期
   - 验证情绪数据日期
   
2. **获取数据**：
   - 获取北向资金流向数据
   - 获取大宗商品价格数据
   - 获取市场情绪数据
   - 获取供应链数据
   
3. **分析影响**：
   - 分析北向资金趋势
   - 分析大宗商品价格影响
   - 分析市场情绪变化
   
4. **逻辑推导**：
   - 明确展示推理链条
   - 每个结论都要有前提和论据
   - 识别不确定性因素

## ⚠️ 逻辑推导要求（必须执行）
对于**大宗商品**分析，必须输出完整的逻辑推导过程：
1. 事实陈述：大宗商品价格发生了什么变化？
2. 原因分析：价格变化的原因是什么？
3. 影响链条：通过什么链条传导到目标股票？
4. 时效判断：影响是短期还是长期？
5. 不确定性：有哪些不确定因素？
6. 最终结论：对目标股票的影响是什么？

## 你的工具使用方式
1. **NorthMoneyTool**：获取北向资金数据
   - 输入：stock_code
   - 输出：净流入、持仓变化、趋势
   - ⚠️ 验证：检查数据日期

2. **SentimentAnalysisTool**：情绪分析
   - 输入：stock_code
   - 输出：新闻情绪、社交情绪、整体情绪

3. **CommodityPriceTool**：商品价格
   - 输入：commodity_type
   - 输出：价格走势、影响分析
   - ⚠️ 验证：检查价格日期

4. **SupplyChainTool**：供应链数据
   - 输入：stock_code
   - 输出：上下游情况、产业链健康度

## 你的 RAG 使用方式
- 当需要理解北向资金分析方法时，检索知识库
- 当需要参考情绪分析框架时，检索情绪分析文档
- 当需要了解供应链分析时，检索供应链文档

## 你的输出风格
- 数据驱动，寻找领先指标
- 交叉验证，提高可靠性
- 及时更新，另类数据时效性强
- 谨慎解读，避免过度解读
- **详细展示逻辑推导过程**""",
    
    tools=[
        NorthMoneyTool(),
        SentimentAnalysisTool(),
        CommodityPriceTool(),
        SupplyChainTool()
    ],
    
    llm=GLM5_LLM,
    
    # RAG 配置
    knowledge_sources=[alternative_knowledge],
    embedder={"provider": "ollama", "config": {"model": "mxbai-embed-large"}},
    
    # Memory 配置
    memory=True,
    
    # 其他配置
    max_iter=5,
    max_rpm=10,
    allow_delegation=False,
    verbose=True
)
```

#### 6.6.4 输出格式（包含详细逻辑推导）

```json
{
  "agent": "alternative_analyst",
  "stock_code": "sh600519",
  "analysis_date": "2026-03-17",
  "data_validation": {
    "status": "valid",
    "latest_north_money_date": "2026-03-16",
    "latest_commodity_date": "2026-03-17",
    "warnings": []
  },
  "overall_rating": "利好",
  "confidence": 0.68,
  "rating_details": {
    "north_money": {
      "rating": "利好",
      "score": 8.0,
      "reasoning": "北向资金连续5日净流入，持仓增加0.5%"
    },
    "sentiment": {
      "rating": "中性偏多",
      "score": 6.5,
      "reasoning": "新闻情绪偏乐观，社交情绪中性"
    },
    "commodities": {
      "rating": "中性",
      "score": 6.0,
      "reasoning": "粮食价格稳定，包装材料成本持平"
    },
    "supply_chain": {
      "rating": "利好",
      "score": 7.0,
      "reasoning": "上游供应稳定，下游需求旺盛"
    }
  },
  "logic_derivation": {
    "commodity_analysis": {
      "commodity": "粮食（白酒原料）",
      "step1_fact": "粮食价格近期稳定，未出现大幅波动",
      "step2_reason": "粮食丰收，供应充足，库存高位",
      "step3_impact_chain": "粮食价格稳定 → 原料成本稳定 → 白酒毛利率稳定",
      "step4_timing": "影响持续6-12个月",
      "step5_uncertainty": "天气因素可能导致价格波动",
      "step6_conclusion": "成本端稳定，利好白酒企业利润"
    },
    "north_money_analysis": {
      "event": "北向资金持续流入",
      "step1_fact": "北向资金连续5日净流入，累计流入5.2亿",
      "step2_reason": "外资看好A股消费板块",
      "step3_impact_chain": "北向资金流入 → 外资持股增加 → 市场信心增强",
      "step4_timing": "短期影响（1-2周）",
      "step5_uncertainty": "外资流入持续性不确定",
      "step6_conclusion": "外资看好，利好股价"
    }
  },
  "north_money": {...},
  "sentiment": {...},
  "commodities": {...},
  "supply_chain": {...},
  "risk_warning": ["北向资金波动较大", "情绪指标滞后"],
  "conclusion": "另类数据整体偏多"
}
```

---

### 6.7 风控经理详细设计

#### 6.7.1 角色定义

| 属性 | 值 |
|------|-----|
| **角色** | 风险管理经理 |
| **目标** | 评估投资风险，提供仓位和止损建议 |
| **数据源** | ✅ qlib（回测验证）|
| **RAG** | ✅ 风险框架、止损策略、历史案例 |
| **工具** | RiskCalculatorTool, QlibBacktestTool, PositionSizerTool, StopLossTool |

#### 6.7.2 输入输出规范

**输入**：
```json
{
  "stock_code": "sh600519",
  "analysis_type": "风险评估",
  "proposed_position": 0.1,
  "entry_price": 1800
}
```

**输出**：
```json
{
  "stock_code": "sh600519",
  "analysis_date": "2026-03-17",
  "risk_assessment": "中等风险",
  "position_advice": {
    "recommended_position": 0.08,
    "reason": "当前波动率较高，建议降低仓位"
  },
  "stop_loss_advice": {
    "hard_stop": 1620,
    "trailing_stop": 1710,
    "time_stop": "持有5个交易日",
    "reason": "基于ATR计算，止损位设在-10%"
  },
  "risk_metrics": {
    "var_95": -0.05,
    "max_drawdown_risk": -0.12,
    "volatility": 0.25
  },
  "backtest_validation": {
    "strategy": "均线策略",
    "win_rate": 0.60,
    "avg_return": 0.025,
    "max_drawdown": -0.10
  },
  "risk_warning": ["波动率偏高", "注意止损纪律"],
  "conclusion": "建议仓位8%，止损位1620元"
}
```

#### 6.7.3 详细 Prompt

```python
risk_manager = Agent(
    role="风险管理经理",
    goal="评估投资风险，提供仓位和止损建议",
    
    backstory="""你是一位经验丰富的风险管理专家。
    
## 你的背景
- 曾任职于多家大型资管公司风控部
- 经历过多次市场危机，善于危机管理
- 你的风控体系帮助公司避免了多次重大损失
- CFA、FRM 持证人

## 你的专长
- 风险度量：VaR、CVaR、波动率、Beta
- 风险控制：止损策略、仓位管理、对冲策略
- 组合管理：分散化、相关性、风险预算
- 压力测试：极端情况下的风险评估

## 你的工具使用方式
1. **RiskCalculatorTool**：风险计算
   - 输入：stock_code
   - 输出：VaR、CVaR、波动率

2. **QlibBacktestTool**：回测验证
   - 输入：stock_code, strategy
   - 输出：胜率、最大回撤、收益

3. **PositionSizerTool**：仓位计算
   - 输入：risk_budget, volatility
   - 输出：建议仓位

4. **StopLossTool**：止损计算
   - 输入：entry_price, atr
   - 输出：止损位

## 你的 RAG 使用方式
- 当需要参考风险管理框架时，检索知识库
- 当需要选择止损策略时，检索止损策略文档
- 当需要学习历史风险案例时，检索案例库

## 你的输出风格
- 独立客观，不受收益诱惑
- 预设规则，不被情绪影响
- 情景分析，考虑多种可能性
- 及时预警，宁可误报不可漏报""",
    
    tools=[
        RiskCalculatorTool(),
        QlibBacktestTool(),
        PositionSizerTool(),
        StopLossTool()
    ],
    
    llm=GLM5_LLM,
    
    # RAG 配置
    knowledge_sources=[risk_knowledge],
    embedder={"provider": "ollama", "config": {"model": "mxbai-embed-large"}},
    
    # Memory 配置
    memory=True,
    
    # 其他配置
    max_iter=5,
    max_rpm=10,
    allow_delegation=False,
    verbose=True
)
```

---

### 6.8 投资决策者详细设计

#### 6.8.1 角色定义

| 属性 | 值 |
|------|-----|
| **角色** | 投资决策者 |
| **目标** | 综合所有分析，做出最终投资决策 |
| **数据源** | ❌ 不用 qlib（纯推理）|
| **RAG** | ✅ 决策框架、投资哲学、历史案例 |
| **工具** | 无（纯推理）|

#### 6.8.2 输入输出规范

**输入**：
```json
{
  "stock_code": "sh600519",
  "quant_analysis": {...},  // 量化分析师的输出
  "fundamental_analysis": {...},  // 基本面分析师的输出
  "macro_analysis": {...},  // 宏观分析师的输出
  "alternative_analysis": {...},  // 另类分析师的输出
  "risk_assessment": {...}  // 风控经理的输出
}
```

**输出**：
```json
{
  "stock_code": "sh600519",
  "decision_date": "2026-03-17",
  "decision": "买入/卖出/持有",
  "confidence": 0.72,
  "position_size": 0.08,
  "entry_strategy": "分批建仓",
  "stop_loss": 1620,
  "target_price": 2000,
  "holding_period": "中期（1-3个月）",
  "reasoning": {
    "bull_factors": ["技术面转强", "基本面优秀", "宏观环境改善"],
    "bear_factors": ["估值偏高", "北向资金波动"],
    "key_risks": ["市场波动", "行业竞争"]
  },
  "action_plan": {
    "immediate_action": "观察MA支撑位，确认后建仓",
    "monitoring_points": ["MA20支撑", "北向资金流向", "财报发布"],
    "exit_conditions": ["跌破MA20", "基本面恶化", "止损触发"]
  },
  "final_recommendation": "建议买入，仓位8%，止损1620元"
}
```

#### 6.8.3 详细 Prompt

```python
decision_maker = Agent(
    role="投资决策者",
    goal="综合所有分析，做出最终投资决策",
    
    backstory="""你是投资委员会主席，拥有20年投资经验。
    
## 你的背景
- 曾任职于多家顶级资管公司，担任投资总监
- 管理规模超过100亿，年化收益20%
- 经历过多轮牛熊周期，投资风格稳健
- 你的投资哲学：风险控制第一，收益第二

## 你的能力
- 综合分析：权衡多方面因素，做出平衡决策
- 风险意识：始终关注风险，不追逐热点
- 独立思考：不盲从市场共识，有自己的判断
- 决策能力：在信息不完全的情况下做出决策

## 你的决策框架
1. **综合观点**：各方分析师的观点是什么？
2. **识别分歧**：哪些观点一致，哪些存在分歧？
3. **权衡利弊**：看涨因素 vs看跌因素？
4. **风险评估**：最大风险是什么？能承受吗？
5. **决策执行**：买/卖/持有？仓位多少？

## 你的输入输出
**输入**：所有分析师的报告
**输出**：最终投资决策

## 你的 RAG 使用方式
- 当需要参考决策框架时，检索知识库
- 当需要学习历史案例时，检索案例库
- 当需要理解投资哲学时，检索哲学文档

## 你的输出风格
- 倾听各方意见，但独立决策
- 关注逻辑，而非结论
- 明确表达决策理由
- 承认不确定性，保持谦逊""",
    
    tools=[],  # 不需要工具，纯推理
    
    llm=GLM5_LLM,
    
    # RAG 配置
    knowledge_sources=[decision_knowledge],
    embedder={"provider": "ollama", "config": {"model": "mxbai-embed-large"}},
    
    # Memory 配置
    memory=True,
    
    # 作为 manager，负责协调其他 Agent
    allow_delegation=True,
    
    # 其他配置
    max_iter=5,
    max_rpm=10,
    verbose=True
)
```

---

### 6.9 Crew 组装

```python
from crewai import Crew, Process

class InvestmentCrew:
    """投资分析团队"""
    
    def __init__(self):
        # 初始化 Agents
        self.quant_analyst = quant_analyst
        self.fundamental_analyst = fundamental_analyst
        self.macro_analyst = macro_analyst
        self.alternative_analyst = alternative_analyst
        self.risk_manager = risk_manager
        self.decision_maker = decision_maker
        
        # 初始化 Crew
        self.crew = Crew(
            agents=[
                self.quant_analyst,
                self.fundamental_analyst,
                self.macro_analyst,
                self.alternative_analyst,
                self.risk_manager,
                self.decision_maker
            ],
            process=Process.hierarchical,  # 层级协作
            manager_llm=GLM5_LLM,  # 使用 GLM-5
            memory=True,  # 使用 CrewAI 内置 Memory
            verbose=True
        )
    
    def analyze(self, stock_code: str):
        """分析股票"""
        # 创建任务
        tasks = self._create_tasks(stock_code)
        
        # 执行
        result = self.crew.kickoff(tasks=tasks)
        
        return result
```

---

### 6.10 最终报告格式

**目标**：详细展示每个 Agent 的评级结果和逻辑推导过程。

```json
{
  "report_id": "report_sh600519_20260317",
  "stock_code": "sh600519",
  "stock_name": "贵州茅台",
  "analysis_date": "2026-03-17",
  "analysis_time": "21:30:00",
  
  "data_validation": {
    "overall_status": "valid",
    "details": {
      "quant_data": {"status": "valid", "date": "2026-03-16"},
      "fundamental_data": {"status": "valid", "date": "2026-03-16"},
      "macro_news": {"status": "valid", "date": "2026-03-17"},
      "alternative_data": {"status": "valid", "date": "2026-03-17"}
    },
    "warnings": []
  },
  
  "agent_reports": {
    "quant_analyst": {
      "agent_name": "量化分析师",
      "overall_rating": "看涨",
      "confidence": 0.75,
      "rating_details": {
        "technical_signals": {"rating": "看涨", "score": 8.0},
        "factor_analysis": {"rating": "看涨", "score": 7.5},
        "model_prediction": {"rating": "看涨", "score": 7.0},
        "backtest_validation": {"rating": "中性", "score": 6.0}
      },
      "logic_derivation": {...},
      "conclusion": "技术面偏多，建议关注MA支撑位"
    },
    
    "fundamental_analyst": {
      "agent_name": "基本面分析师",
      "overall_rating": "看涨",
      "confidence": 0.70,
      "rating_details": {
        "profitability": {"rating": "优秀", "score": 8.5},
        "growth": {"rating": "良好", "score": 7.5},
        "valuation": {"rating": "合理", "score": 7.0},
        "industry_position": {"rating": "领先", "score": 8.0}
      },
      "logic_derivation": {...},
      "conclusion": "基本面优秀，估值合理，建议关注"
    },
    
    "macro_analyst": {
      "agent_name": "宏观分析师",
      "overall_rating": "利好",
      "confidence": 0.65,
      "rating_details": {
        "monetary_policy": {"rating": "利好", "score": 8.0},
        "fiscal_policy": {"rating": "利好", "score": 7.5},
        "international": {"rating": "中性偏多", "score": 6.5},
        "industry_policy": {"rating": "利好", "score": 7.0}
      },
      "logic_derivation": {
        "geopolitical_analysis": {...},
        "policy_transmission": {...}
      },
      "conclusion": "宏观环境偏暖，有利于消费板块"
    },
    
    "alternative_analyst": {
      "agent_name": "另类数据分析师",
      "overall_rating": "利好",
      "confidence": 0.68,
      "rating_details": {
        "north_money": {"rating": "利好", "score": 8.0},
        "sentiment": {"rating": "中性偏多", "score": 6.5},
        "commodities": {"rating": "中性", "score": 6.0},
        "supply_chain": {"rating": "利好", "score": 7.0}
      },
      "logic_derivation": {
        "commodity_analysis": {...},
        "north_money_analysis": {...}
      },
      "conclusion": "另类数据整体偏多"
    },
    
    "risk_manager": {
      "agent_name": "风控经理",
      "overall_rating": "中等风险",
      "confidence": 0.80,
      "rating_details": {
        "market_risk": {"rating": "中等", "score": 6.5},
        "liquidity_risk": {"rating": "低", "score": 8.0},
        "concentration_risk": {"rating": "中等", "score": 7.0}
      },
      "position_advice": {"recommended_position": 0.08},
      "stop_loss_advice": {"hard_stop": 1620},
      "conclusion": "建议仓位8%，止损位1620元"
    }
  },
  
  "final_decision": {
    "agent_name": "投资决策者",
    "decision": "买入",
    "confidence": 0.72,
    "position_size": 0.08,
    "entry_strategy": "分批建仓",
    "stop_loss": 1620,
    "target_price": 2000,
    "holding_period": "中期（1-3个月）",
    
    "reasoning": {
      "bull_factors": [
        "技术面转强（量化分析师，置信度75%）",
        "基本面优秀（基本面分析师，置信度70%）",
        "宏观环境改善（宏观分析师，置信度65%）"
      ],
      "bear_factors": [
        "估值偏高（基本面分析师指出）",
        "北向资金波动（另类分析师指出）"
      ],
      "key_risks": [
        "市场波动（风控经理）",
        "行业竞争（基本面分析师）"
      ]
    },
    
    "action_plan": {
      "immediate_action": "观察MA支撑位，确认后建仓",
      "monitoring_points": [
        "MA20支撑",
        "北向资金流向",
        "财报发布"
      ],
      "exit_conditions": [
        "跌破MA20",
        "基本面恶化",
        "止损触发"
      ]
    },
    
    "final_recommendation": "建议买入，仓位8%，止损1620元"
  },
  
  "summary": {
    "overall_rating": "买入",
    "confidence": 0.72,
    "risk_level": "中等",
    "key_points": [
      "技术面：看涨，MA金叉确认",
      "基本面：优秀，ROE 25%",
      "宏观面：利好，货币政策宽松",
      "另类数据：北向资金流入",
      "风险：中等，建议仓位8%"
    ]
  }
}
```

---

### 6.11 报告展示要点

**Markdown 格式报告模板**：

```markdown
# 投资分析报告 - 贵州茅台 (sh600519)

**分析日期**：2026-03-17 21:30
**最终建议**：买入（置信度 72%）

---

## 一、数据验证

| 数据类型 | 状态 | 最新日期 |
|---------|------|---------|
| 量化数据 | ✅ 有效 | 2026-03-16 |
| 基本面数据 | ✅ 有效 | 2026-03-16 |
| 宏观新闻 | ✅ 有效 | 2026-03-17 |
| 另类数据 | ✅ 有效 | 2026-03-17 |

---

## 二、各 Agent 分析结果

### 2.1 量化分析师

**整体评级**：看涨（置信度 75%）

| 维度 | 评级 | 分数 | 理由 |
|------|------|------|------|
| 技术信号 | 看涨 | 8.0 | MA金叉、MACD金叉、RSI合理 |
| 因子分析 | 看涨 | 7.5 | 动量因子排名前20% |
| 模型预测 | 看涨 | 7.0 | GBDT预测+2.5% |
| 回测验证 | 中性 | 6.0 | 胜率65%，回撤-8% |

**逻辑推导**：
1. 验证数据时效性 → 数据有效
2. 计算技术指标 → MA金叉、MACD金叉
3. 分析因子数据 → 动量因子强势
4. 模型预测 → GBDT预测+2.5%
5. 回测验证 → 胜率65%
6. 综合判断 → 技术面偏多

**结论**：技术面偏多，建议关注MA支撑位

---

### 2.2 宏观分析师

**整体评级**：利好（置信度 65%）

| 维度 | 评级 | 分数 | 理由 |
|------|------|------|------|
| 货币政策 | 利好 | 8.0 | 央行降准，利率低位 |
| 财政政策 | 利好 | 7.5 | 专项债加速，减税降费 |
| 国际形势 | 中性偏多 | 6.5 | 美联储加息尾声 |
| 行业政策 | 利好 | 7.0 | 消费刺激政策 |

**地缘政治逻辑推导**：
- **事件**：美联储加息周期尾声
- **事实**：美联储3月会议维持利率不变
- **直接影响**：美元指数走弱，人民币企稳
- **间接影响**：外资流入A股，利好消费板块
- **时效**：影响持续3-6个月
- **不确定性**：美联储降息节奏不确定
- **结论**：外部环境改善，利好A股

**结论**：宏观环境偏暖，有利于消费板块

---

### 2.3 另类数据分析师

**整体评级**：利好（置信度 68%）

| 维度 | 评级 | 分数 | 理由 |
|------|------|------|------|
| 北向资金 | 利好 | 8.0 | 连续5日净流入 |
| 市场情绪 | 中性偏多 | 6.5 | 新闻偏乐观 |
| 大宗商品 | 中性 | 6.0 | 粮食价格稳定 |
| 供应链 | 利好 | 7.0 | 需求旺盛 |

**大宗商品逻辑推导**：
- **商品**：粮食（白酒原料）
- **事实**：粮食价格近期稳定
- **原因**：粮食丰收，供应充足
- **影响链条**：粮价稳定 → 成本稳定 → 毛利率稳定
- **时效**：影响持续6-12个月
- **不确定性**：天气因素可能导致波动
- **结论**：成本端稳定，利好利润

**结论**：另类数据整体偏多

---

### 2.4 风控经理

**整体评级**：中等风险（置信度 80%）

| 维度 | 评级 | 分数 |
|------|------|------|
| 市场风险 | 中等 | 6.5 |
| 流动性风险 | 低 | 8.0 |
| 集中度风险 | 中等 | 7.0 |

**建议仓位**：8%
**止损位**：1620 元

**结论**：建议仓位8%，止损1620元

---

## 三、最终决策

**投资决策者**：买入（置信度 72%）

### 看涨因素
- ✅ 技术面转强（量化分析师，置信度75%）
- ✅ 基本面优秀（基本面分析师，置信度70%）
- ✅ 宏观环境改善（宏观分析师，置信度65%）

### 看跌因素
- ⚠️ 估值偏高（基本面分析师指出）
- ⚠️ 北向资金波动（另类分析师指出）

### 执行计划
- **立即行动**：观察MA支撑位，确认后建仓
- **监控要点**：MA20支撑、北向资金流向、财报发布
- **退出条件**：跌破MA20、基本面恶化、止损触发

---

## 四、总结

**最终建议**：买入，仓位8%，止损1620元

**关键要点**：
- 技术面：看涨，MA金叉确认
- 基本面：优秀，ROE 25%
- 宏观面：利好，货币政策宽松
- 另类数据：北向资金流入
- 风险：中等，建议仓位8%

---
*报告生成时间：2026-03-17 21:30*
*分析师：CrewAI 投资分析团队*
```

---

## 七、开发路线图（三阶段）

### 7.1 第一版（MVP）- 核心功能

**目标**：系统能够正常运行，输出投资分析报告

**时间估计**：3-5 天

**核心原则**：
- ✅ 不带 RAG
- ✅ 不带 Memory
- ✅ 不带 UI
- ✅ 系统能够正常工作
- ✅ qlib 能够获取最新数据

#### 任务清单

**数据层（优先）**：
- [ ] 实现 QlibDataUpdater 类
- [ ] 实现增量数据下载（mootdx）
- [ ] 实现数据格式转换
- [ ] 设置定时更新任务（每日 17:00）
- [ ] 测试数据更新流程

**qlib 模型层**：
- [ ] 实现 Alpha158 因子读取工具（QlibAlpha158Tool）
- [ ] 实现 GBDT 模型预测工具（QlibGBDTPredictionTool）
- [ ] 实现回测引擎工具（QlibBacktestTool）
- [ ] 实现财务数据工具（QlibFinancialTool）
- [ ] 测试 qlib 工具

**其他数据工具**：
- [ ] 实现技术指标计算工具（TechnicalIndicatorTool）
- [ ] 实现北向资金工具（NorthMoneyTool）
- [ ] 实现情绪分析工具（SentimentAnalysisTool）
- [ ] 实现风险计算工具（RiskCalculatorTool）
- [ ] 实现仓位计算工具（PositionSizerTool）
- [ ] 实现止损计算工具（StopLossTool）

**Agent 层（简化版）**：
- [ ] 定义 6 个 Agent（简化 prompt，不用 RAG，不用 Memory）
- [ ] 量化分析师（quant_analyst）
- [ ] 基本面分析师（fundamental_analyst）
- [ ] 宏观分析师（macro_analyst）
- [ ] 另类分析师（alternative_analyst）
- [ ] 风控经理（risk_manager）
- [ ] 投资决策者（decision_maker）

**Crew 层**：
- [ ] 定义 Tasks（每个 Agent 的任务）
- [ ] 实现 Crew 组装
- [ ] 实现投资分析流程
- [ ] 输出 JSON 格式报告

**测试与验证**：
- [ ] 单元测试（每个工具）
- [ ] 集成测试（整个流程）
- [ ] 端到端测试（输入股票代码 → 输出报告）

**第一版交付物**：
- 可运行的投资分析系统
- 输入：股票代码
- 输出：JSON 格式的投资分析报告

---

### 7.2 第二版 - UI + 优化

**目标**：增加用户界面，优化 Agent prompt

**时间估计**：2-3 天

**核心功能**：
- ✅ 增加 UI（Web 界面 + 飞书机器人）
- ✅ 优化每个 Agent prompt
- ✅ 增加错误处理
- ✅ 增加日志记录

#### 任务清单

**UI 层**：
- [ ] 实现 REST API
  - POST /analyze - 分析股票
  - GET /status - 系统状态
  - GET /report/{id} - 获取报告
- [ ] 实现飞书机器人
  - 接收消息：@bot分析 sh600519
  - 发送报告：Markdown 格式
- [ ] 实现 Web 界面
  - 输入框：股票代码
  - 按钮：分析
  - 展示：报告

**Agent 优化**：
- [ ] 优化量化分析师 prompt
- [ ] 优化基本面分析师 prompt
- [ ] 优化宏观分析师 prompt
- [ ] 优化另类分析师 prompt
- [ ] 优化风控经理 prompt
- [ ] 优化投资决策者 prompt

**错误处理**：
- [ ] 工具调用失败处理
- [ ] Agent 超时处理
- [ ] 数据缺失处理
- [ ] 异常情况降级

**日志与监控**：
- [ ] 日志记录（每个步骤）
- [ ] 性能监控（响应时间）
- [ ] 错误告警（飞书通知）

**第二版交付物**：
- Web 界面（http://localhost:8080）
- 飞书机器人（@bot分析 sh600519）
- 优化的 Agent prompt
- 完善的错误处理

---

### 7.3 第三版 - RAG 优化

**目标**：为每个 Agent 配置 RAG 知识库，提升分析质量

**时间估计**：3-4 天

**核心功能**：
- ✅ 为每个 Agent 配置 RAG 知识库
- ✅ 使用 CrewAI Memory
- ✅ 优化 Agent 决策质量
- ✅ 增加历史案例学习

#### 任务清单

**知识库准备**：
- [ ] 创建 knowledge/ 目录
- [ ] 整理技术指标说明（technical_indicators.txt）
- [ ] 整理量化策略文档（quant_strategies.pdf）
- [ ] 整理财务分析方法（financial_analysis.pdf）
- [ ] 整理估值模型（valuation_methods.pdf）
- [ ] 整理宏观框架（macro_frameworks.txt）
- [ ] 整理政策分析（policy_analysis.txt）
- [ ] 整理北向资金分析（north_money_analysis.txt）
- [ ] 整理情绪分析（sentiment_analysis.txt）
- [ ] 整理风险管理（risk_management.pdf）
- [ ] 整理决策框架（decision_frameworks.txt）

**RAG 配置**：
- [ ] 安装 Ollama
- [ ] 下载 embedding 模型（mxbai-embed-large）
- [ ] 为量化分析师配置 RAG
- [ ] 为基本面分析师配置 RAG
- [ ] 为宏观分析师配置 RAG
- [ ] 为另类分析师配置 RAG
- [ ] 为风控经理配置 RAG
- [ ] 为投资决策者配置 RAG

**Memory 配置**：
- [ ] 启用 CrewAI Memory
- [ ] 配置 Memory 存储
- [ ] 测试 Memory 功能

**优化与测试**：
- [ ] 测试 RAG 检索效果
- [ ] 对比有无 RAG 的分析质量
- [ ] 优化知识库内容
- [ ] 优化检索策略

**第三版交付物**：
- 每个 Agent 都有独立的 RAG 知识库
- 更高质量的投资分析报告
- 历史案例学习能力

---

### 7.4 版本对比

| 功能 | 第一版 | 第二版 | 第三版 |
|------|--------|--------|--------|
| **qlib 数据更新** | ✅ | ✅ | ✅ |
| **qlib 因子/模型** | ✅ | ✅ | ✅ |
| **6 个 Agent** | ✅ 简化 | ✅ 优化 | ✅ RAG |
| **CrewAI Crew** | ✅ | ✅ | ✅ |
| **输出报告** | JSON | JSON/Markdown | JSON/Markdown |
| **Web UI** | ❌ | ✅ | ✅ |
| **飞书机器人** | ❌ | ✅ | ✅ |
| **RAG 知识库** | ❌ | ❌ | ✅ |
| **Memory** | ❌ | ❌ | ✅ |
| **错误处理** | 基础 | 完善 | 完善 |
| **日志监控** | 基础 | 完善 | 完善 |

---

### 7.5 开发优先级

```
第一版（MVP）
├── P0: qlib 数据更新（数据是基础）
├── P0: qlib 工具开发（核心能力）
├── P0: Agent 定义（系统骨架）
├── P0: Crew 组装（流程串联）
└── P0: 端到端测试（验证可用）

第二版（UI + 优化）
├── P1: REST API（对外服务）
├── P1: 飞书机器人（用户交互）
├── P1: Web 界面（可视化）
├── P2: Agent prompt 优化（提升质量）
└── P2: 错误处理（稳定性）

第三版（RAG 优化）
├── P2: 知识库准备（内容建设）
├── P2: RAG 配置（能力升级）
├── P2: Memory 配置（记忆能力）
└── P3: 质量优化（持续改进）
```

---

### 7.6 任务执行顺序（按优先级和依赖关系）

**核心原则**：做完一个任务，再做下一个。不按天划分，按依赖关系推进。

```
┌─────────────────────────────────────────────────────────────┐
│                    第一版（MVP）                             │
└─────────────────────────────────────────────────────────────┘

【P0 - 数据层】数据是基础，必须先完成
│
├─[1] 实现 QlibDataUpdater 类
│   └─ 依赖：无
│   └─ 产出：数据更新器类
│
├─[2] 实现增量数据下载（mootdx）
│   └─ 依赖：[1]
│   └─ 产出：增量数据下载功能
│
├─[3] 实现数据格式转换
│   └─ 依赖：[2]
│   └─ 产出：mootdx → qlib 格式转换
│
├─[4] 设置定时更新任务（每日 17:00）
│   └─ 依赖：[3]
│   └─ 产出：自动更新 cron job
│
└─[5] 测试数据更新流程
    └─ 依赖：[4]
    └─ 产出：数据更新验证通过
    └─ 里程碑：✅ 数据层完成

【P0 - qlib 工具层】核心能力，依赖数据层
│
├─[6] 实现 QlibAlpha158Tool
│   └─ 依赖：[5]
│   └─ 产出：因子读取工具
│
├─[7] 实现 QlibGBDTPredictionTool
│   └─ 依赖：[5]
│   └─ 产出：模型预测工具
│
├─[8] 实现 QlibBacktestTool
│   └─ 依赖：[5]
│   └─ 产出：回测验证工具
│
├─[9] 实现 QlibFinancialTool
│   └─ 依赖：[5]
│   └─ 产出：财务数据工具
│
└─[10] 测试 qlib 工具
    └─ 依赖：[6][7][8][9]
    └─ 产出：qlib 工具验证通过
    └─ 里程碑：✅ qlib 工具层完成

【P0 - 其他数据工具】补充能力，依赖数据层
│
├─[11] 实现 TechnicalIndicatorTool
│   └─ 依赖：[5]
│   └─ 产出：技术指标计算工具
│
├─[12] 实现 NorthMoneyTool
│   └─ 依赖：无
│   └─ 产出：北向资金工具
│
├─[13] 实现 SentimentAnalysisTool
│   └─ 依赖：无
│   └─ 产出：情绪分析工具
│
├─[14] 实现 RiskCalculatorTool
│   └─ 依赖：[8]
│   └─ 产出：风险计算工具
│
├─[15] 实现 PositionSizerTool
│   └─ 依赖：[14]
│   └─ 产出：仓位计算工具
│
├─[16] 实现 StopLossTool
│   └─ 依赖：[14]
│   └─ 产出：止损计算工具
│
└─[17] 测试其他工具
    └─ 依赖：[11][12][13][14][15][16]
    └─ 产出：其他工具验证通过
    └─ 里程碑：✅ 工具层完成

【P0 - Agent 层】系统骨架，依赖工具层
│
├─[18] 定义 quant_analyst（量化分析师）
│   └─ 依赖：[10][17]
│   └─ 产出：量化分析师 Agent
│
├─[19] 定义 fundamental_analyst（基本面分析师）
│   └─ 依赖：[10]
│   └─ 产出：基本面分析师 Agent
│
├─[20] 定义 macro_analyst（宏观分析师）
│   └─ 依赖：[17]
│   └─ 产出：宏观分析师 Agent
│
├─[21] 定义 alternative_analyst（另类分析师）
│   └─ 依赖：[17]
│   └─ 产出：另类分析师 Agent
│
├─[22] 定义 risk_manager（风控经理）
│   └─ 依赖：[17]
│   └─ 产出：风控经理 Agent
│
├─[23] 定义 decision_maker（投资决策者）
│   └─ 依赖：[18][19][20][21][22]
│   └─ 产出：投资决策者 Agent
│
└─[24] 测试 Agent 定义
    └─ 依赖：[23]
    └─ 产出：Agent 验证通过
    └─ 里程碑：✅ Agent 层完成

【P0 - Crew 层】流程串联，依赖 Agent 层
│
├─[25] 定义 Tasks（每个 Agent 的任务）
│   └─ 依赖：[24]
│   └─ 产出：任务定义
│
├─[26] 实现 Crew 组装
│   └─ 依赖：[25]
│   └─ 产出：Crew 类
│
├─[27] 实现投资分析流程
│   └─ 依赖：[26]
│   └─ 产出：分析流程函数
│
└─[28] 输出 JSON 格式报告
    └─ 依赖：[27]
    └─ 产出：报告生成器
    └─ 里程碑：✅ Crew 层完成

【P0 - 测试与验证】确保系统可用
│
├─[29] 单元测试（每个工具）
│   └─ 依赖：[28]
│   └─ 产出：单元测试通过
│
├─[30] 集成测试（整个流程）
│   └─ 依赖：[29]
│   └─ 产出：集成测试通过
│
└─[31] 端到端测试（输入股票代码 → 输出报告）
    └─ 依赖：[30]
    └─ 产出：端到端测试通过
    └─ 里程碑：🎉 第一版（MVP）完成！

┌─────────────────────────────────────────────────────────────┐
│                    第二版（UI + 优化）                       │
└─────────────────────────────────────────────────────────────┘

【P1 - API 层】对外服务
│
├─[32] 实现 REST API - POST /analyze
│   └─ 依赖：[31]
│   └─ 产出：分析接口
│
├─[33] 实现 REST API - GET /status
│   └─ 依赖：[31]
│   └─ 产出：状态接口
│
├─[34] 实现 REST API - GET /report/{id}
│   └─ 依赖：[31]
│   └─ 产出：报告查询接口
│
└─[35] 测试 REST API
    └─ 依赖：[32][33][34]
    └─ 产出：API 测试通过
    └─ 里程碑：✅ API 层完成

【P1 - 飞书机器人】用户交互
│
├─[36] 实现飞书机器人 - 接收消息
│   └─ 依赖：[35]
│   └─ 产出：消息接收功能
│
├─[37] 实现飞书机器人 - 发送报告
│   └─ 依赖：[36]
│   └─ 产出：Markdown 格式报告
│
└─[38] 测试飞书机器人
    └─ 依赖：[37]
    └─ 产出：机器人测试通过
    └─ 里程碑：✅ 飞书机器人完成

【P1 - Web 界面】可视化
│
├─[39] 实现 Web 界面 - 输入框 + 按钮
│   └─ 依赖：[35]
│   └─ 产出：前端页面
│
├─[40] 实现 Web 界面 - 报告展示
│   └─ 依赖：[39]
│   └─ 产出：报告展示组件
│
└─[41] 测试 Web 界面
    └─ 依赖：[40]
    └─ 产出：Web 测试通过
    └─ 里程碑：✅ Web 界面完成

【P2 - Agent 优化】提升质量
│
├─[42] 优化 quant_analyst prompt
│   └─ 依赖：[31]
│   └─ 产出：优化后的 prompt
│
├─[43] 优化 fundamental_analyst prompt
│   └─ 依赖：[31]
│   └─ 产出：优化后的 prompt
│
├─[44] 优化 macro_analyst prompt
│   └─ 依赖：[31]
│   └─ 产出：优化后的 prompt
│
├─[45] 优化 alternative_analyst prompt
│   └─ 依赖：[31]
│   └─ 产出：优化后的 prompt
│
├─[46] 优化 risk_manager prompt
│   └─ 依赖：[31]
│   └─ 产出：优化后的 prompt
│
├─[47] 优化 decision_maker prompt
│   └─ 依赖：[31]
│   └─ 产出：优化后的 prompt
│
└─[48] 测试优化效果
    └─ 依赖：[42][43][44][45][46][47]
    └─ 产出：优化验证通过
    └─ 里程碑：✅ Agent 优化完成

【P2 - 错误处理 + 日志】稳定性
│
├─[49] 实现工具调用失败处理
│   └─ 依赖：[31]
│   └─ 产出：错误处理逻辑
│
├─[50] 实现 Agent 超时处理
│   └─ 依赖：[31]
│   └─ 产出：超时处理逻辑
│
├─[51] 实现数据缺失处理
│   └─ 依赖：[31]
│   └─ 产出：降级处理逻辑
│
├─[52] 实现日志记录
│   └─ 依赖：[31]
│   └─ 产出：日志系统
│
├─[53] 实现性能监控
│   └─ 依赖：[52]
│   └─ 产出：监控指标
│
├─[54] 实现错误告警
│   └─ 依赖：[52]
│   └─ 产出：飞书告警
│
└─[55] 测试稳定性
    └─ 依赖：[49][50][51][52][53][54]
    └─ 产出：稳定性验证通过
    └─ 里程碑：🎉 第二版完成！

┌─────────────────────────────────────────────────────────────┐
│                    第三版（RAG 优化）                        │
└─────────────────────────────────────────────────────────────┘

【P2 - 知识库准备】内容建设
│
├─[56] 创建 knowledge/ 目录
│   └─ 依赖：[55]
│   └─ 产出：知识库目录
│
├─[57] 整理 technical_indicators.txt
│   └─ 依赖：[56]
│   └─ 产出：技术指标说明文档
│
├─[58] 整理 quant_strategies.pdf
│   └─ 依赖：[56]
│   └─ 产出：量化策略文档
│
├─[59] 整理 financial_analysis.pdf
│   └─ 依赖：[56]
│   └─ 产出：财务分析文档
│
├─[60] 整理 valuation_methods.pdf
│   └─ 依赖：[56]
│   └─ 产出：估值方法文档
│
├─[61] 整理 macro_frameworks.txt
│   └─ 依赖：[56]
│   └─ 产出：宏观框架文档
│
├─[62] 整理 policy_analysis.txt
│   └─ 依赖：[56]
│   └─ 产出：政策分析文档
│
├─[63] 整理 north_money_analysis.txt
│   └─ 依赖：[56]
│   └─ 产出：北向资金分析文档
│
├─[64] 整理 sentiment_analysis.txt
│   └─ 依赖：[56]
│   └─ 产出：情绪分析文档
│
├─[65] 整理 risk_management.pdf
│   └─ 依赖：[56]
│   └─ 产出：风险管理文档
│
├─[66] 整理 decision_frameworks.txt
│   └─ 依赖：[56]
│   └─ 产出：决策框架文档
│
└─[67] 验证知识库内容
    └─ 依赖：[57]-[66]
    └─ 产出：知识库验证通过
    └─ 里程碑：✅ 知识库准备完成

【P2 - RAG 配置】能力升级
│
├─[68] 安装 Ollama
│   └─ 依赖：[67]
│   └─ 产出：Ollama 环境
│
├─[69] 下载 embedding 模型（mxbai-embed-large）
│   └─ 依赖：[68]
│   └─ 产出：embedding 模型
│
├─[70] 为 quant_analyst 配置 RAG
│   └─ 依赖：[69]
│   └─ 产出：量化分析师 RAG
│
├─[71] 为 fundamental_analyst 配置 RAG
│   └─ 依赖：[69]
│   └─ 产出：基本面分析师 RAG
│
├─[72] 为 macro_analyst 配置 RAG
│   └─ 依赖：[69]
│   └─ 产出：宏观分析师 RAG
│
├─[73] 为 alternative_analyst 配置 RAG
│   └─ 依赖：[69]
│   └─ 产出：另类分析师 RAG
│
├─[74] 为 risk_manager 配置 RAG
│   └─ 依赖：[69]
│   └─ 产出：风控经理 RAG
│
├─[75] 为 decision_maker 配置 RAG
│   └─ 依赖：[69]
│   └─ 产出：投资决策者 RAG
│
└─[76] 测试 RAG 功能
    └─ 依赖：[70]-[75]
    └─ 产出：RAG 测试通过
    └─ 里程碑：✅ RAG 配置完成

【P2 - Memory 配置】记忆能力
│
├─[77] 启用 CrewAI Memory
│   └─ 依赖：[76]
│   └─ 产出：Memory 配置
│
├─[78] 配置 Memory 存储
│   └─ 依赖：[77]
│   └─ 产出：存储配置
│
└─[79] 测试 Memory 功能
    └─ 依赖：[78]
    └─ 产出：Memory 测试通过
    └─ 里程碑：✅ Memory 配置完成

【P3 - 质量优化】持续改进
│
├─[80] 测试 RAG 检索效果
│   └─ 依赖：[79]
│   └─ 产出：检索效果报告
│
├─[81] 对比有无 RAG 的分析质量
│   └─ 依赖：[80]
│   └─ 产出：质量对比报告
│
├─[82] 优化知识库内容
│   └─ 依赖：[81]
│   └─ 产出：优化后的知识库
│
└─[83] 优化检索策略
    └─ 依赖：[82]
    └─ 产出：优化后的检索
    └─ 里程碑：🎉 第三版完成！
```

---

### 7.7 任务统计

| 版本 | 任务数 | 关键里程碑 |
|------|--------|-----------|
| **第一版（MVP）** | 31 个任务 | 数据层 → qlib 工具 → 其他工具 → Agent → Crew → 测试 |
| **第二版（UI + 优化）** | 24 个任务 | API → 飞书机器人 → Web → Agent 优化 → 稳定性 |
| **第三版（RAG 优化）** | 28 个任务 | 知识库 → RAG 配置 → Memory → 质量优化 |
| **总计** | **83 个任务** | - |

---

### 7.8 执行原则

1. **按顺序执行**：完成任务 N 后，再开始任务 N+1
2. **依赖优先**：确保依赖任务已完成
3. **里程碑验证**：每个里程碑完成后，进行集成测试
4. **持续交付**：每完成一个任务，更新进度

---

### 7.9 风险与应对

| 风险 | 影响 | 应对措施 |
|------|------|---------|
| qlib 数据更新失败 | 阻塞后续任务 | 使用 mootdx 备用数据源 |
| GBDT 模型准确率低 | 影响分析质量 | 增加训练数据，调参 |
| Agent 输出不稳定 | 影响决策质量 | 优化 prompt，增加约束 |
| RAG 检索效果差 | 影响第三版质量 | 优化知识库，调整检索策略 |
| GLM-5 API 限流 | 影响响应速度 | 增加重试机制，降低并发 |

---

## 八、技术栈总结

| 组件 | 技术 | 说明 |
|------|------|------|
| **量化计算** | qlib | Alpha158 因子、GBDT 模型、回测 |
| **数据更新** | mootdx | 实时行情、增量更新 |
| **Agent 框架** | CrewAI | Agent、Task、Crew、Flow |
| **RAG** | CrewAI Knowledge | 内置 RAG 功能 |
| **Memory** | CrewAI Memory | 内置记忆功能 |
| **LLM** | GLM-5 | 通义千问 |
| **Embedding** | Ollama | 本地 embedding，无需 API key |
| **向量存储** | ChromaDB | CrewAI 默认存储 |

---

**产品经理签字**：Jack  
**日期**：2026-03-17 20:10
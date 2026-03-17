# AlphaPilot - 任务拆解

> 项目代号：**AlphaPilot**（Alpha收益的领航员）
> 创建时间：2026-03-17 21:42
> 创建人：Jack（产品经理）

---

## 项目简介

**AlphaPilot** 是一个基于 CrewAI + qlib 的A 股智能投资分析系统。

**目标**：
- 年化收益：20-30%
- 最大回撤：<15%
- 夏普比率：>1.5
- 胜率：>55%

---

## 设计原则

### 子任务拆解原则

1. **独立性**：每个子任务可以独立开发、测试
2. **可验证性**：每个子任务有明确的验收标准
3. **解耦性**：子任务之间通过接口通信，不直接依赖
4. **渐进集成**：子任务完成后可以逐渐集成到系统

### 模块划分

```
AlphaPilot/
├── data/                 # 数据层（独立模块）
├── tools/                # 工具层（独立模块）
├── agents/               # Agent 层（独立模块）
├── crew/                 # Crew 层（集成层）
├── api/                  # API 层（对外服务）
├── ui/                   # UI 层（用户界面）
└── tests/                # 测试层（验证模块）
```

---

## 一、数据层（Data Layer）

**目标**：提供稳定、可靠的数据服务

### 1.1 qlib 数据更新器（QlibDataUpdater）

**子任务 ID**：DATA-001

**描述**：实现 qlib 数据自动更新机制

**独立可验证性**：
- ✅ 独立开发：不依赖其他模块
- ✅ 独立测试：可以单独测试数据更新功能
- ✅ 独立部署：可以作为独立服务运行

**接口定义**：
```python
class QlibDataUpdater:
    def update_daily_data(self) -> bool:
        """更新日线数据，返回是否成功"""
        pass
    
    def get_latest_date(self) -> str:
        """获取最新数据日期"""
        pass
    
    def validate_data(self, stock_code: str) -> bool:
        """验证数据完整性"""
        pass
```

**验收标准**：
1. 能够自动下载最新日线数据
2. 数据日期为最新交易日
3. 数据格式符合 qlib 要求
4. 支持增量更新

**测试方法**：
```python
def test_qlib_data_updater():
    updater = QlibDataUpdater()
    success = updater.update_daily_data()
    assert success == True
    assert updater.get_latest_date() == "2026-03-16"
    assert updater.validate_data("sh600519") == True
```

**估计时间**：2-3 小时

---

### 1.2mootdx 数据获取器（MootdxDataFetcher）

**子任务 ID**：DATA-002

**描述**：使用 mootdx 获取实时行情数据

**独立可验证性**：
- ✅ 独立开发：不依赖其他模块
- ✅ 独立测试：可以单独测试数据获取
- ✅ 独立部署：可以作为独立服务运行

**接口定义**：
```python
class MootdxDataFetcher:
    def get_realtime_quote(self, stock_code: str) -> dict:
        """获取实时行情"""
        pass
    
    def get_kline_data(self, stock_code: str, days: int) -> pd.DataFrame:
        """获取 K 线数据"""
        pass
    
    def get_latest_price(self, stock_code: str) -> float:
        """获取最新价格"""
        pass
```

**验收标准**：
1. 能够获取实时行情数据
2. 能够获取历史 K 线数据
3. 数据格式标准化
4. 支持异常处理

**测试方法**：
```python
def test_mootdx_data_fetcher():
    fetcher = MootdxDataFetcher()
    quote = fetcher.get_realtime_quote("sh600519")
    assert quote is not None
    assert "price" in quote
    kline = fetcher.get_kline_data("sh600519", 30)
    assert len(kline) == 30
```

**估计时间**：1-2 小时

---

### 1.3 数据格式转换器（DataConverter）

**子任务 ID**：DATA-003

**描述**：将 mootdx 数据转换为 qlib 格式

**独立可验证性**：
- ✅ 独立开发：不依赖其他模块
- ✅ 独立测试：可以单独测试转换功能
- ✅ 独立部署：可以作为独立工具使用

**接口定义**：
```python
class DataConverter:
    def convert_to_qlib_format(self, data: pd.DataFrame) -> pd.DataFrame:
        """转换为 qlib 格式"""
        pass
    
    def validate_qlib_format(self, data: pd.DataFrame) -> bool:
        """验证 qlib 格式"""
        pass
```

**验收标准**：
1. 能够转换数据格式
2. 转换后的数据符合 qlib 要求
3. 支持批量转换

**测试方法**：
```python
def test_data_converter():
    converter = DataConverter()
    raw_data = pd.DataFrame(...)
    qlib_data = converter.convert_to_qlib_format(raw_data)
    assert converter.validate_qlib_format(qlib_data) == True
```

**估计时间**：1 小时

---

## 二、工具层（Tools Layer）

**目标**：为Agent 提供可靠的工具

### 2.1 qlib Alpha158 因子工具（QlibAlpha158Tool）

**子任务 ID**：TOOL-001

**描述**：获取 Alpha158 因子数据

**独立可验证性**：
- ✅ 独立开发：不依赖其他工具
- ✅ 独立测试：可以单独测试因子获取
- ✅ 独立使用：可以被任何 Agent 调用

**接口定义**：
```python
class QlibAlpha158Tool:
    def get_factors(self, stock_code: str) -> dict:
        """获取 Alpha158 因子"""
        pass
    
    def get_factor_rank(self, stock_code: str, factor_name: str) -> float:
        """获取因子排名"""
        pass
```

**验收标准**：
1. 能够获取 Alpha158 因子数据
2. 能够计算因子排名
3. 支持数据验证

**测试方法**：
```python
def test_qlib_alpha158_tool():
    tool = QlibAlpha158Tool()
    factors = tool.get_factors("sh600519")
    assert factors is not None
    rank = tool.get_factor_rank("sh600519", "momentum")
    assert 0 <= rank <= 1
```

**估计时间**：2-3 小时

---

### 2.2 qlib GBDT 预测工具（QlibGBDTPredictionTool）

**子任务 ID**：TOOL-002

**描述**：使用 GBDT 模型预测股票涨跌

**独立可验证性**：
- ✅ 独立开发：不依赖其他工具
- ✅ 独立测试：可以单独测试预测功能
- ✅ 独立使用：可以被任何 Agent 调用

**接口定义**：
```python
class QlibGBDTPredictionTool:
    def predict(self, stock_code: str, horizon: int) -> dict:
        """预测涨跌幅"""
        pass
    
    def get_confidence(self, stock_code: str) -> float:
        """获取预测置信度"""
        pass
```

**验收标准**：
1. 能够预测股票涨跌幅
2. 能够返回置信度
3. 支持多日预测

**测试方法**：
```python
def test_qlib_gbdt_prediction_tool():
    tool = QlibGBDTPredictionTool()
    prediction = tool.predict("sh600519", 5)
    assert "prediction" in prediction
    assert "confidence" in prediction
```

**估计时间**：3-4 小时

---

### 2.3 技术指标计算工具（TechnicalIndicatorTool）

**子任务 ID**：TOOL-003

**描述**：计算技术指标（MA、MACD、RSI等）

**独立可验证性**：
- ✅ 独立开发：不依赖 qlib
- ✅ 独立测试：可以单独测试指标计算
- ✅ 独立使用：可以被任何 Agent 调用

**接口定义**：
```python
class TechnicalIndicatorTool:
    def calculate_ma(self, stock_code: str, periods: list) -> dict:
        """计算均线"""
        pass
    
    def calculate_macd(self, stock_code: str) -> dict:
        """计算 MACD"""
        pass
    
    def calculate_rsi(self, stock_code: str, period: int) -> float:
        """计算 RSI"""
        pass
```

**验收标准**：
1. 能够计算 MA、MACD、RSI、KDJ 等
2. 支持多周期计算
3. 支持信号识别（金叉、死叉）

**测试方法**：
```python
def test_technical_indicator_tool():
    tool = TechnicalIndicatorTool()
    ma = tool.calculate_ma("sh600519", [5, 10, 20])
    assert "ma5" in ma
    macd = tool.calculate_macd("sh600519")
    assert "dif" in macd
```

**估计时间**：2-3 小时

---

### 2.4 北向资金工具（NorthMoneyTool）

**子任务 ID**：TOOL-004

**描述**：获取北向资金流向数据

**独立可验证性**：
- ✅ 独立开发：不依赖其他工具
- ✅ 独立测试：可以单独测试数据获取
- ✅ 独立使用：可以被任何 Agent 调用

**接口定义**：
```python
class NorthMoneyTool:
    def get_net_inflow(self, stock_code: str, days: int) -> pd.DataFrame:
        """获取净流入数据"""
        pass
    
    def get_holding_change(self, stock_code: str) -> float:
        """获取持仓变化"""
        pass
```

**验收标准**：
1. 能够获取北向资金净流入
2. 能够获取持仓变化
3. 支持历史数据查询

**测试方法**：
```python
def test_north_money_tool():
    tool = NorthMoneyTool()
    inflow = tool.get_net_inflow("sh600519", 5)
    assert len(inflow) == 5
    change = tool.get_holding_change("sh600519")
    assert change is not None
```

**估计时间**：2 小时

---

### 2.5 大宗商品价格工具（CommodityPriceTool）

**子任务 ID**：TOOL-005

**描述**：获取大宗商品价格数据

**独立可验证性**：
- ✅ 独立开发：不依赖其他工具
- ✅ 独立测试：可以单独测试价格获取
- ✅ 独立使用：可以被任何 Agent 调用

**接口定义**：
```python
class CommodityPriceTool:
    def get_price(self, commodity: str) -> float:
        """获取商品价格"""
        pass
    
    def get_price_trend(self, commodity: str, days: int) -> dict:
        """获取价格趋势"""
        pass
```

**验收标准**：
1. 能够获取大宗商品价格
2. 能够获取价格趋势
3. 支持多种商品（铜、铝、原油、黄金）

**测试方法**：
```python
def test_commodity_price_tool():
    tool = CommodityPriceTool()
    price = tool.get_price("copper")
    assert price > 0
    trend = tool.get_price_trend("copper", 30)
    assert "direction" in trend
```

**估计时间**：2 小时

---

## 三、Agent 层（Agents Layer）

**目标**：定义独立的Agent 角色

### 3.1 量化分析师 Agent（QuantAnalyst）

**子任务 ID**：AGENT-001

**描述**：实现量化分析师 Agent

**独立可验证性**：
- ✅ 独立开发：可以单独开发 Agent 定义
- ✅ 独立测试：可以单独测试 Agent 输出
- ✅ 独立使用：可以单独运行

**接口定义**：
```python
class QuantAnalyst:
    def __init__(self, llm, tools):
        self.agent = Agent(
            role="资深量化分析师",
            goal="基于 qlib 因子和 GBDT 模型预测，提供技术面分析观点",
            backstory="...",
            tools=tools,
            llm=llm
        )
    
    def analyze(self, stock_code: str) -> dict:
        """分析股票"""
        pass
```

**验收标准**：
1. 能够分析股票技术面
2. 输出包含评级和逻辑推导
3. 支持数据验证

**测试方法**：
```python
def test_quant_analyst():
    analyst = QuantAnalyst(llm, tools)
    result = analyst.analyze("sh600519")
    assert "overall_rating" in result
    assert "logic_derivation" in result
```

**估计时间**：2-3 小时

---

### 3.2 宏观分析师 Agent（MacroAnalyst）

**子任务 ID**：AGENT-002

**描述**：实现宏观分析师 Agent（含地缘政治逻辑推导）

**独立可验证性**：
- ✅ 独立开发：可以单独开发
- ✅ 独立测试：可以单独测试
- ✅ 独立使用：可以单独运行

**验收标准**：
1. 能够分析宏观经济
2. 输出包含地缘政治逻辑推导
3. 支持数据验证

**估计时间**：2-3 小时

---

### 3.3 另类数据分析师 Agent（AlternativeAnalyst）

**子任务 ID**：AGENT-003

**描述**：实现另类数据分析师 Agent（含大宗商品逻辑推导）

**独立可验证性**：
- ✅ 独立开发：可以单独开发
- ✅ 独立测试：可以单独测试
- ✅ 独立使用：可以单独运行

**验收标准**：
1. 能够分析北向资金、情绪、大宗商品
2. 输出包含大宗商品逻辑推导
3. 支持数据验证

**估计时间**：2-3 小时

---

## 四、Crew 层（Crew Layer）

**目标**：集成所有 Agent，实现完整分析流程

### 4.1 投资分析 Crew（InvestmentCrew）

**子任务 ID**：CREW-001

**描述**：组装所有 Agent，实现投资分析流程

**独立可验证性**：
- ✅ 独立开发：可以单独开发 Crew 组装
- ✅ 独立测试：可以测试整个流程
- ⚠️ 依赖 Agent 层完成

**接口定义**：
```python
class InvestmentCrew:
    def __init__(self):
        self.agents = [
            QuantAnalyst(),
            MacroAnalyst(),
            AlternativeAnalyst(),
            # ...
        ]
        self.crew = Crew(agents=self.agents, ...)
    
    def analyze(self, stock_code: str) -> dict:
        """分析股票，返回完整报告"""
        pass
```

**验收标准**：
1. 能够运行完整的分析流程
2. 输出包含所有 Agent 的分析结果
3. 支持并行分析

**测试方法**：
```python
def test_investment_crew():
    crew = InvestmentCrew()
    result = crew.analyze("sh600519")
    assert "agent_reports" in result
    assert "final_decision" in result
```

**估计时间**：3-4 小时

---

## 五、API 层（API Layer）

**目标**：提供 REST API 接口

### 5.1 分析接口（Analyze API）

**子任务 ID**：API-001

**描述**：实现股票分析 API

**独立可验证性**：
- ✅ 独立开发：可以单独开发 API
- ✅ 独立测试：可以测试 API 响应
- ⚠️ 依赖 Crew 层完成

**接口定义**：
```python
# POST /analyze
{
    "stock_code": "sh600519",
    "analysis_type": "full"
}

# Response
{
    "report_id": "xxx",
    "stock_code": "sh600519",
    "analysis_result": {...}
}
```

**验收标准**：
1. 能够接收分析请求
2. 返回分析结果
3. 支持异步处理

**估计时间**：2-3 小时

---

## 六、UI 层（UI Layer）

**目标**：提供用户界面

### 6.1 飞书机器人（Feishu Bot）

**子任务 ID**：UI-001

**描述**：实现飞书机器人，接收用户指令

**独立可验证性**：
- ✅ 独立开发：可以单独开发
- ✅ 独立测试：可以测试消息收发
- ⚠️ 依赖 API 层完成

**验收标准**：
1. 能够接收 @消息
2. 能够发送分析报告
3. 支持 Markdown 格式

**估计时间**：2-3 小时

---

## 任务依赖关系

```
数据层（独立）
├── DATA-001: qlib 数据更新器
├── DATA-002: mootdx 数据获取器
└── DATA-003: 数据格式转换器

工具层（依赖数据层）
├── TOOL-001: qlib Alpha158 工具（依赖 DATA-001）
├── TOOL-002: qlib GBDT 工具（依赖 DATA-001）
├── TOOL-003: 技术指标工具（依赖 DATA-002）
├── TOOL-004: 北向资金工具（独立）
└── TOOL-005: 大宗商品价格工具（独立）

Agent 层（依赖工具层）
├── AGENT-001: 量化分析师（依赖 TOOL-001, TOOL-002, TOOL-003）
├── AGENT-002: 宏观分析师（独立）
└── AGENT-003: 另类分析师（依赖 TOOL-004, TOOL-005）

Crew 层（依赖 Agent 层）
└── CREW-001: 投资分析 Crew（依赖 AGENT-001, AGENT-002, AGENT-003）

API 层（依赖 Crew 层）
└── API-001: 分析接口（依赖 CREW-001）

UI 层（依赖 API 层）
└── UI-001: 飞书机器人（依赖 API-001）
```

---

## 开发优先级

### P0 - 核心功能（第一版 MVP）

1. **DATA-001**: qlib 数据更新器（基础）
2. **TOOL-001**: qlib Alpha158 工具
3. **TOOL-002**: qlib GBDT 工具
4. **TOOL-003**: 技术指标工具
5. **AGENT-001**: 量化分析师
6. **CREW-001**: 投资分析 Crew

### P1 - 补充功能（第一版 MVP）

7. **DATA-002**: mootdx 数据获取器
8. **TOOL-004**: 北向资金工具
9. **TOOL-005**: 大宗商品价格工具
10. **AGENT-002**: 宏观分析师
11. **AGENT-003**: 另类分析师

### P2 - 对外服务（第二版）

12. **API-001**: 分析接口
13. **UI-001**: 飞书机器人

---

## 验收标准总结

| 层级 | 验收标准 |
|------|---------|
| 数据层 | 数据完整、格式正确、可自动更新 |
| 工具层 | 接口清晰、返回准确、支持异常处理 |
| Agent 层 | 输出包含评级和逻辑推导、支持数据验证 |
| Crew 层 | 流程完整、输出包含所有 Agent 结果 |
| API 层 | 接口稳定、响应正确、支持异步 |
| UI 层 | 消息收发正常、报告展示清晰 |

---

## 文件结构

```
/Users/rainday/.openclaw/workspace-mac/projects/alphapilot/
├── data/
│   ├── qlib_updater.py          # DATA-001
│   ├── mootdx_fetcher.py        # DATA-002
│   └── data_converter.py        # DATA-003
├── tools/
│   ├── qlib_alpha158.py         # TOOL-001
│   ├── qlib_gbdt.py             # TOOL-002
│   ├── technical_indicator.py   # TOOL-003
│   ├── north_money.py           # TOOL-004
│   └── commodity_price.py       # TOOL-005
├── agents/
│   ├── quant_analyst.py         # AGENT-001
│   ├── macro_analyst.py         # AGENT-002
│   └── alternative_analyst.py   # AGENT-003
├── crew/
│   └── investment_crew.py       # CREW-001
├── api/
│   └── analyze_api.py           # API-001
├── ui/
│   └── feishu_bot.py            # UI-001
├── tests/
│   ├── test_data/
│   ├── test_tools/
│   ├── test_agents/
│   └── test_crew/
├── docs/
│   ├── DESIGN.md
│   ├── ROADMAP.md
│   └── TASK_BREAKDOWN.md        # 本文件
├── main.py
└── requirements.txt
```

---

**创建人签字**：Jack
**日期**：2026-03-17 21:42
# AlphaPilot 测试方案

> 版本：1.0
> 日期：2026-03-18
> 编写：mac

---

## 一、测试目标

确保 AlphaPilot 系统的各个组件能够正常工作，整体流程能够正确执行，输出符合预期的投资分析报告。

---

## 二、测试范围

### 2.1 测试层级

| 层级 | 说明 | 测试类型 |
|------|------|---------|
| **数据层** | 数据获取、转换、更新 | 单元测试 + 集成测试 |
| **工具层** | 15个工具的独立功能 | 单元测试 |
| **Agent 层** | 6个 Agent 的分析能力 | 单元测试 + 集成测试 |
| **Crew 层** | 多 Agent 协作流程 | 集成测试 |
| **API 层** | REST API 接口 | API 测试 |
| **E2E 层** | 端到端流程 | E2E 测试 |

### 2.2 测试矩阵

| 组件 | 单元测试 | 集成测试 | E2E 测试 |
|------|----------|----------|----------|
| **数据层** | ✅ | ✅ | ❌ |
| **工具层** | ✅ | ✅ | ❌ |
| **Agent 层** | ✅ | ✅ | ✅ |
| **Crew 层** | ❌ | ✅ | ✅ |
| **API 层** | ✅ | ✅ | ✅ |
| **Web UI** | ❌ | ✅ | ✅ |

---

## 三、测试用例设计

### 3.1 数据层测试

#### 3.1.1 QlibDataUpdater 测试

**文件**: `tests/test_data/test_qlib_updater.py`

| 用例ID | 测试名称 | 测试目的 | 输入 | 预期输出 |
|--------|---------|---------|------|---------|
| DU-001 | test_init_default_dir | 验证默认目录初始化 | 无 | 使用 ~/.qlib/qlib_data/cn_data |
| DU-002 | test_init_custom_dir | 验证自定义目录初始化 | custom_dir | 使用指定目录 |
| DU-003 | test_init_creates_paths | 验证路径创建 | temp_dir | 创建 features/ 和 calendars/ 目录 |
| DU-004 | test_get_latest_date_empty_dir | 空目录返回默认日期 | 空目录 | 返回 2020-09-25 |
| DU-005 | test_get_latest_date_with_data | 有数据返回最新日期 | 测试数据 | 返回数据最新日期 |
| DU-006 | test_update_stock_data | 验证单股数据更新 | stock_code | 数据文件更新成功 |
| DU-007 | test_update_all_stocks | 验证批量数据更新 | stock_list | 所有股票数据更新成功 |
| DU-008 | test_update_with_invalid_code | 无效代码处理 | invalid_code | 记录错误，跳过该股票 |
| DU-009 | test_update_with_network_error | 网络错误处理 | mock network error | 重试后记录失败 |
| DU-010 | test_full_workflow | 完整更新流程 | 无 | 从获取数据到写入文件 |

#### 3.1.2 MootdxDataFetcher 测试

**文件**: `tests/test_data/test_mootdx_fetcher.py`

| 用例ID | 测试名称 | 测试目的 | 输入 | 预期输出 |
|--------|---------|---------|------|---------|
| MF-001 | test_init_success | 验证初始化成功 | 无 | Quotes 对象创建成功 |
| MF-002 | test_init_with_market | 验证市场参数 | market='std' | 使用指定市场 |
| MF-003 | test_normalize_stock_code_sh | 上海代码标准化 | SH600519 | sh600519 |
| MF-004 | test_normalize_stock_code_sz | 深圳代码标准化 | SZ000001 | sz000001 |
| MF-005 | test_get_daily_bars | 获取日线数据 | stock_code | DataFrame 包含 OHLCV |
| MF-006 | test_get_minute_bars | 获取分钟数据 | stock_code, freq | DataFrame 包含分钟数据 |
| MF-007 | test_get_realtime_quote | 获取实时行情 | stock_code | 实时报价数据 |
| MF-008 | test_get_trade_calendar | 获取交易日历 | 无 | 交易日列表 |
| MF-009 | test_handle_rate_limit | 请求频率限制 | 快速连续请求 | 自动延迟重试 |
| MF-010 | test_handle_network_error | 网络错误处理 | mock error | 抛出明确异常 |

#### 3.1.3 DataConverter 测试

**文件**: `tests/test_data/test_data_converter.py`

| 用例ID | 测试名称 | 测试目的 | 输入 | 预期输出 |
|--------|---------|---------|------|---------|
| DC-001 | test_init_default | 默认初始化 | 无 | 使用默认输出目录 |
| DC-002 | test_init_with_output_dir | 自定义目录初始化 | output_dir | 使用指定目录 |
| DC-003 | test_normalize_columns | 列名标准化 | mootdx_data | 转换为 qlib 列名 |
| DC-004 | test_convert_to_qlib_format | 格式转换 | sample_data | qlib 格式数据 |
| DC-005 | test_handle_missing_values | 缺失值处理 | data with NaN | 填充或插值 |
| DC-006 | test_validate_data_quality | 数据质量验证 | sample_data | 通过/失败状态 |
| DC-007 | test_batch_convert | 批量转换 | stock_list | 所有股票转换成功 |
| DC-008 | test_convert_with_instrument | 指定股票转换 | stock_code | 单股转换成功 |

---

### 3.2 工具层测试

#### 3.2.1 Alpha158Tool 测试

**文件**: `tests/test_tools/test_alpha158_tool.py`

| 用例ID | 测试名称 | 测试目的 | 输入 | 预期输出 |
|--------|---------|---------|------|---------|
| A158-001 | test_get_factor_info | 获取因子信息 | 无 | 因子列表和说明 |
| A158-002 | test_get_factors | 获取因子数据 | stock_code | 因子值 DataFrame |
| A158-003 | test_get_factor_list | 获取因子列表 | 无 | 158 个因子名称 |
| A158-004 | test_get_stock_factors | 获取股票因子 | stock_code | 因子值和排名 |
| A158-005 | test_factor_categories | 因子分类 | 无 | 动量/波动率等分类 |
| A158-006 | test_factor_with_date | 指定日期因子 | stock_code, date | 特定日期因子值 |
| A158-007 | test_factor_ranking | 因子排名计算 | factor_values | 百分位排名 |
| A158-008 | test_handle_missing_data | 缺失数据处理 | incomplete_data | 降级处理 |
| A158-009 | test_factor_quality_check | 因子质量检查 | factor_data | 质量报告 |
| A158-010 | test_performance_optimization | 性能优化 | batch_stocks | 快速批量计算 |

#### 3.2.2 GBDTPredictionTool 测试

**文件**: `tests/test_tools/test_gbdt_prediction_tool.py`

| 用例ID | 测试名称 | 测试目的 | 输入 | 预期输出 |
|--------|---------|---------|------|---------|
| GBDT-001 | test_init | 工具初始化 | 无 | 创建工具实例 |
| GBDT-002 | test_predict_single_stock | 单股预测 | stock_code | 预测值和置信度 |
| GBDT-003 | test_prediction_range | 预测值范围检查 | stock_code | 值在合理范围内 |
| GBDT-004 | test_signal_generation | 信号生成 | prediction | 买入/卖出信号 |
| GBDT-005 | test_batch_prediction | 批量预测 | stock_list | 多股预测结果 |
| GBDT-006 | test_confidence_calculation | 置信度计算 | prediction | 置信度在 0-1 之间 |
| GBDT-007 | test_model_not_loaded | 模型未加载处理 | 无模型 | 返回模拟预测 |
| GBDT-008 | test_prediction_with_horizon | 指定预测周期 | horizon=5 | 5日预测值 |
| GBDT-009 | test_prediction_consistency | 预测一致性 | same input | 相同结果 |
| GBDT-010 | test_error_handling | 错误处理 | invalid_code | 明确错误信息 |

#### 3.2.3 TechnicalIndicatorTool 测试

**文件**: `tests/test_tools/test_technical_indicator_tool.py`

| 用例ID | 测试名称 | 测试目的 | 输入 | 预期输出 |
|--------|---------|---------|------|---------|
| TI-001 | test_set_data_success | 数据设置成功 | sample_data | 数据设置成功 |
| TI-002 | test_set_data_missing_columns | 缺失列处理 | incomplete_data | 抛出异常 |
| TI-003 | test_ensure_data_not_set | 数据未设置检查 | 无数据 | 抛出异常 |
| TI-004 | test_calculate_ma | MA 计算 | prices | MA 值正确 |
| TI-005 | test_calculate_ema | EMA 计算 | prices | EMA 值正确 |
| TI-006 | test_calculate_macd | MACD 计算 | prices | DIF, DEA, MACD |
| TI-007 | test_calculate_rsi | RSI 计算 | prices | RSI 值在 0-100 |
| TI-008 | test_calculate_kdj | KDJ 计算 | prices | K, D, J 值 |
| TI-009 | test_calculate_bollinger | 布林带计算 | prices | Upper, Middle, Lower |
| TI-010 | test_detect_signals | 信号检测 | indicators | 金叉/死叉信号 |
| TI-011 | test_generate_report | 报告生成 | all_indicators | Markdown 报告 |
| TI-012 | test_edge_cases | 边界情况 | short_data | 优雅降级 |

#### 3.2.4 NorthMoneyTool 测试

**文件**: `tests/test_tools/test_north_money_tool.py`

| 用例ID | 测试名称 | 测试目的 | 输入 | 预期输出 |
|--------|---------|---------|------|---------|
| NM-001 | test_init | 工具初始化 | 无 | 创建工具实例 |
| NM-002 | test_normalize_stock_code | 代码标准化 | SH600519 | 标准化格式 |
| NM-003 | test_get_net_inflow | 获取净流入 | stock_code | 净流入金额 |
| NM-004 | test_get_holding_change | 获取持仓变化 | stock_code | 持仓变化率 |
| NM-005 | test_get_trend | 获取流入趋势 | stock_code | 流入趋势分析 |
| NM-006 | test_batch_query | 批量查询 | stock_list | 多股数据 |
| NM-007 | test_historical_data | 历史数据 | stock_code, days | 历史流向 |
| NM-008 | test_data_validation | 数据验证 | raw_data | 数据有效性检查 |

#### 3.2.5 CommodityPriceTool 测试

**文件**: `tests/test_tools/test_commodity_price_tool.py`（待创建）

| 用例ID | 测试名称 | 测试目的 | 输入 | 预期输出 |
|--------|---------|---------|------|---------|
| CP-001 | test_get_commodity_price | 获取商品价格 | commodity_type | 当前价格 |
| CP-002 | test_get_price_trend | 获取价格趋势 | commodity_type | 涨跌幅 |
| CP-003 | test_get_related_commodities | 获取关联商品 | stock_code | 相关商品列表 |
| CP-004 | test_price_impact_analysis | 价格影响分析 | stock_code, commodity | 影响评估 |
| CP-005 | test_batch_price_fetch | 批量价格获取 | commodity_list | 多商品价格 |

#### 3.2.6 ValuationCalculatorTool 测试

**文件**: `tests/test_tools/test_valuation_calculator_tool.py`（待创建）

| 用例ID | 测试名称 | 测试目的 | 输入 | 预期输出 |
|--------|---------|---------|------|---------|
| VC-001 | test_calculate_pe | PE 计算 | price, eps | PE 值 |
| VC-002 | test_calculate_pb | PB 计算 | price, bvps | PB 值 |
| VC-003 | test_calculate_peg | PEG 计算 | pe, growth | PEG 值 |
| VC-004 | test_dcf_valuation | DCF 估值 | cash_flows | 公允价值 |
| VC-005 | test_relative_valuation | 相对估值 | stock, peers | 估值比较 |

#### 3.2.7 RiskCalculatorTool 测试

**文件**: `tests/test_tools/test_risk_calculator_tool.py`（待创建）

| 用例ID | 测试名称 | 测试目的 | 输入 | 预期输出 |
|--------|---------|---------|------|---------|
| RC-001 | test_calculate_var | VaR 计算 | returns | VaR 值 |
| RC-002 | test_calculate_cvar | CVaR 计算 | returns | CVaR 值 |
| RC-003 | test_calculate_volatility | 波动率计算 | prices | 年化波动率 |
| RC-004 | test_calculate_beta | Beta 计算 | stock, market | Beta 值 |
| RC-005 | test_stress_test | 压力测试 | scenarios | 极端情况损失 |

#### 3.2.8 其他工具测试

根据实际需要，补充以下工具的测试：

- **QlibDataTool**: qlib 数据访问
- **WebSearchTool**: 网络搜索
- **IndustryCompareTool**: 行业对比
- **SentimentAnalysisTool**: 情绪分析
- **MacroDataTool**: 宏观数据
- **StockNameQueryTool**: 股票名称查询

---

### 3.3 Agent 层测试

#### 3.3.1 QuantitativeAnalyst 测试

**文件**: `tests/test_agents/test_quantitative.py`

| 用例ID | 测试名称 | 测试目的 | 输入 | 预期输出 |
|--------|---------|---------|------|---------|
| QA-001 | test_agent_initialization | Agent 初始化 | 无 | 创建 Agent 实例 |
| QA-002 | test_analyze | 基本分析 | stock_code | 分析报告 |
| QA-003 | test_analyze_with_parameters | 带参数分析 | stock_code, params | 定制化报告 |
| QA-004 | test_analyze_invalid_stock | 无效股票处理 | invalid_code | 明确错误信息 |
| QA-005 | test_tool_integration | 工具集成 | stock_code | 正确使用工具 |
| QA-006 | test_output_format | 输出格式验证 | stock_code | JSON 格式正确 |
| QA-007 | test_data_validation | 数据验证 | mock data | 验证数据时效性 |
| QA-008 | test_logic_derivation | 逻辑推导 | stock_code | 完整推理链 |

#### 3.3.2 MacroAnalyst 测试

**文件**: `tests/test_agents/test_macro.py`

| 用例ID | 测试名称 | 测试目的 | 输入 | 预期输出 |
|--------|---------|---------|------|---------|
| MA-001 | test_macro_analyst_init | Agent 初始化 | 无 | 创建 Agent 实例 |
| MA-002 | test_knowledge_loading | 知识库加载 | 无 | 知识库加载成功 |
| MA-003 | test_economic_indicators_analysis | 经济指标分析 | indicators | 指标分析报告 |
| MA-004 | test_policy_analysis | 政策分析 | policy_news | 政策影响评估 |
| MA-005 | test_geopolitical_analysis | 地缘政治分析 | news | 地缘政治影响 |
| MA-006 | test_stock_name_correctness | 股票名称正确性 | stock_code | 使用正确股票名称 |
| MA-007 | test_logic_derivation | 逻辑推导 | stock_code | 完整推理链 |
| MA-008 | test_data_validation | 数据验证 | mock data | 验证数据时效性 |

#### 3.3.3 其他 Agent 测试

**待创建测试文件**：
- `tests/test_agents/test_fundamental.py` - 基本面分析师
- `tests/test_agents/test_alternative.py` - 另类分析师
- `tests/test_agents/test_risk_manager.py` - 风控经理
- `tests/test_agents/test_decision_maker.py` - 投资决策者

---

### 3.4 Crew 层测试

#### 3.4.1 InvestmentCrew 测试

**文件**: `tests/test_crew/test_investment_crew.py`（待创建）

| 用例ID | 测试名称 | 测试目的 | 输入 | 预期输出 |
|--------|---------|---------|------|---------|
| IC-001 | test_crew_initialization | Crew 初始化 | 无 | 创建 Crew 实例 |
| IC-002 | test_task_creation | Task 创建 | stock_code | 创建所有任务 |
| IC-003 | test_agent_collaboration | Agent 协作 | stock_code | 各 Agent 正确协作 |
| IC-004 | test_parallel_analysis | 并行分析 | stock_code | 分析并行执行 |
| IC-005 | test_final_decision | 最终决策 | all_reports | 投资决策生成 |
| IC-006 | test_output_format | 输出格式 | stock_code | 完整 JSON 报告 |
| IC-007 | test_error_recovery | 错误恢复 | mock error | 降级处理 |
| IC-008 | test_timeout_handling | 超时处理 | long task | 超时中断 |

#### 3.4.2 Flow 层测试

**文件**: `tests/test_flow/test_investment_flow.py`（待创建）

| 用例ID | 测试名称 | 测试目的 | 输入 | 预期输出 |
|--------|---------|---------|------|---------|
| IF-001 | test_flow_initialization | Flow 初始化 | 无 | 创建 Flow 实例 |
| IF-002 | test_data_preparation | 数据准备阶段 | stock_code | 数据获取成功 |
| IF-003 | test_parallel_analysis | 并行分析阶段 | stock_code | 所有 Agent 分析完成 |
| IF-004 | test_risk_assessment | 风险评估阶段 | analysis_results | 风险评估完成 |
| IF-005 | test_decision_making | 决策阶段 | all_reports | 最终决策生成 |
| IF-006 | test_report_generation | 报告生成阶段 | decision | 完整报告输出 |

---

### 3.5 API 层测试

#### 3.5.1 REST API 测试

**文件**: `tests/test_api.py`

| 用例ID | 测试名称 | 测试目的 | 方法 | 路径 | 预期状态码 |
|--------|---------|---------|------|------|-----------|
| API-001 | test_health_check | 健康检查 | GET | /health | 200 |
| API-002 | test_analyze_stock | 分析股票 | POST | /analyze | 200 |
| API-003 | test_analyze_invalid | 无效股票 | POST | /analyze | 400 |
| API-004 | test_get_status | 系统状态 | GET | /status | 200 |
| API-005 | test_get_report | 获取报告 | GET | /report/{id} | 200 |
| API-006 | test_report_not_found | 报告不存在 | GET | /report/invalid | 404 |
| API-007 | test_search_stock | 股票搜索 | GET | /search?q=茅台 | 200 |
| API-008 | test_rate_limit | 频率限制 | 多次请求 | /analyze | 429 |
| API-009 | test_authentication | 认证检查 | 无 token | /analyze | 401 |
| API-010 | test_batch_analyze | 批量分析 | POST | /batch-analyze | 200 |

---

### 3.6 E2E 测试

#### 3.6.1 完整流程测试

**文件**: `tests/test_e2e/test_full_workflow.py`（待创建）

| 用例ID | 测试名称 | 测试目的 | 输入 | 预期输出 |
|--------|---------|---------|------|---------|
| E2E-001 | test_single_stock_analysis | 单股完整分析 | sh600519 | 完整投资报告 |
| E2E-002 | test_batch_analysis | 批量分析 | 5只股票 | 5份报告 |
| E2E-003 | test_data_update_flow | 数据更新流程 | 无 | 数据更新成功 |
| E2E-004 | test_report_generation | 报告生成 | sh600519 | Markdown 报告 |
| E2E-005 | test_error_recovery | 错误恢复 | 模拟错误 | 优雅降级 |
| E2E-006 | test_concurrent_analysis | 并发分析 | 3只股票 | 并发完成 |
| E2E-007 | test_stock_name_correctness | 股票名称正确性 | 中国海油 | 使用正确名称 |
| E2E-008 | test_full_integration | 完整集成测试 | 无 | 系统正常运行 |

---

## 四、测试数据设计

### 4.1 测试股票列表

| 股票代码 | 股票名称 | 行业 | 特点 |
|---------|---------|------|------|
| sh600519 | 贵州茅台 | 白酒 | 高价股，北向资金关注 |
| sh600036 | 招商银行 | 银行 | 金融股，流动性好 |
| sz000001 | 平安银行 | 银行 | 深市股票 |
| sh600938 | 中国海油 | 石油 | 资源股，与原油相关 |
| sz000858 | 五粮液 | 白酒 | 白酒龙头 |

### 4.2 测试数据边界

| 场景 | 测试数据 | 目的 |
|------|---------|------|
| 正常股票 | sh600519 | 验证正常流程 |
| 次新股 | 上市不足1年 | 验证数据不足情况 |
| ST 股票 | ST股票 | 验证风险提示 |
| 停牌股票 | 停牌中 | 验证数据缺失处理 |
| 无效代码 | sh999999 | 验证错误处理 |

### 4.3 Mock 数据设计

```python
# mock_stock_data.py
MOCK_STOCK_DATA = {
    "sh600519": {
        "name": "贵州茅台",
        "price": 1800.0,
        "change": 0.02,
        "volume": 1000000,
        "turnover": 0.005,
        "factors": {
            "momentum": 0.8,
            "volatility": 0.6,
            "liquidity": 0.9
        }
    },
    # ... 更多 mock 数据
}

MOCK_NORTH_MONEY = {
    "sh600519": {
        "net_inflow": 5.2,
        "holding_change": 0.005,
        "trend": "流入"
    }
}

MOCK_COMMODITY_PRICES = {
    "gold": {"price": 2000.0, "change": 0.01},
    "oil": {"price": 75.0, "change": -0.02},
    "copper": {"price": 8500.0, "change": 0.015}
}
```

---

## 五、测试环境配置

### 5.1 测试依赖

```toml
# pyproject.toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = "-v --tb=short --cov=src --cov-report=html"
```

### 5.2 环境变量

```bash
# .env.test
TEST_MODE=true
QLIB_DATA_DIR=/tmp/qlib_test_data
MOCK_DATA=true
```

### 5.3 CI 配置

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: pytest --cov=src --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

---

## 六、测试执行计划

### 6.1 执行顺序

```
1. 数据层测试 → 确保数据获取和转换正常
2. 工具层测试 → 确保每个工具功能正常
3. Agent 层测试 → 确保 Agent 分析逻辑正确
4. Crew 层测试 → 确保 Agent 协作正常
5. API 层测试 → 确保接口正常
6. E2E 测试 → 确保整体流程正常
```

### 6.2 执行命令

```bash
# 运行所有测试
pytest

# 运行特定层测试
pytest tests/test_data/
pytest tests/test_tools/
pytest tests/test_agents/
pytest tests/test_crew/
pytest tests/test_api/
pytest tests/test_e2e/

# 运行特定文件测试
pytest tests/test_tools/test_alpha158_tool.py

# 运行特定用例
pytest tests/test_tools/test_alpha158_tool.py::TestAlpha158Tool::test_get_factors

# 带覆盖率运行
pytest --cov=src --cov-report=html
```

### 6.3 测试报告

测试完成后生成：
- 控制台输出：测试结果摘要
- HTML 报告：`htmlcov/index.html`
- XML 报告：`coverage.xml`（用于 CI）

---

## 七、测试覆盖目标

| 层级 | 目标覆盖率 | 当前覆盖率 | 状态 |
|------|-----------|-----------|------|
| 数据层 | 90% | ~70% | 🟡 待提高 |
| 工具层 | 85% | ~60% | 🟡 待提高 |
| Agent 层 | 80% | ~40% | 🔴 需完善 |
| Crew 层 | 70% | ~20% | 🔴 需完善 |
| API 层 | 90% | ~50% | 🟡 待提高 |
| E2E 层 | 100% | ~30% | 🔴 需完善 |

---

## 八、待补充测试用例

### 8.1 高优先级

1. **test_geopolitical_analysis** - 地缘政治分析（需验证股票名称正确性）
2. **test_commodity_price_impact** - 大宗商品价格影响分析
3. **test_decision_maker_logic** - 投资决策者逻辑推导
4. **test_full_crew_integration** - 完整 Crew 集成测试
5. **test_e2e_china_oil_analysis** - 中国海油完整分析（验证股票名称）

### 8.2 中优先级

1. **test_risk_manager_position** - 仓位计算测试
2. **test_risk_manager_stop_loss** - 止损计算测试
3. **test_sentiment_analysis** - 情绪分析测试
4. **test_industry_compare** - 行业对比测试
5. **test_web_search** - 网络搜索测试

### 8.3 低优先级

1. **test_performance_benchmark** - 性能基准测试
2. **test_concurrent_load** - 并发负载测试
3. **test_memory_leak** - 内存泄漏测试
4. **test_api_documentation** - API 文档测试

---

## 九、测试维护

### 9.1 测试更新规则

1. 新增功能必须添加对应测试用例
2. Bug 修复必须添加回归测试
3. 重构代码后必须验证测试通过
4. 定期更新测试数据

### 9.2 测试审查

1. 代码审查时检查测试覆盖率
2. PR 必须通过所有测试才能合并
3. 定期清理过期测试用例

---

**编写人**: mac
**审核人**: Jack
**日期**: 2026-03-18
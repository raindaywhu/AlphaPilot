# 测试实施清单

> 更新时间：2026-03-18

---

## ✅ 已完成测试

### 数据层
- [x] test_qlib_updater.py - QlibDataUpdater 测试
- [x] test_mootdx_fetcher.py - MootdxDataFetcher 测试
- [x] test_data_converter.py - DataConverter 测试

### 工具层
- [x] test_alpha158_tool.py - Alpha158Tool 测试
- [x] test_gbdt_prediction_tool.py - GBDTPredictionTool 测试
- [x] test_gbdt_tool.py - QlibGBDTPredictionTool 测试
- [x] test_north_money_tool.py - NorthMoneyTool 测试
- [x] test_technical_indicator_tool.py - TechnicalIndicatorTool 测试

### Agent 层
- [x] test_quantitative.py - QuantitativeAnalyst 测试
- [x] test_macro.py - MacroAnalyst 测试

---

## 🚧 待补充测试

### 工具层（高优先级）
- [ ] test_commodity_price_tool.py - 大宗商品价格工具
- [ ] test_valuation_calculator_tool.py - 估值计算工具
- [ ] test_risk_calculator_tool.py - 风险计算工具
- [ ] test_position_sizer_tool.py - 仓位计算工具
- [ ] test_stop_loss_tool.py - 止损计算工具

### Agent 层（高优先级）
- [ ] test_fundamental.py - 基本面分析师
- [ ] test_alternative.py - 另类分析师
- [ ] test_risk_manager.py - 风控经理
- [ ] test_decision_maker.py - 投资决策者

### Crew 层
- [ ] test_investment_crew.py - Crew 集成测试
- [ ] test_flow_integration.py - Flow 集成测试

### E2E 测试
- [ ] test_e2e_full_workflow.py - 完整流程测试
- [ ] test_e2e_stock_name_correctness.py - 股票名称正确性测试

---

## 🔴 重点测试用例

### 1. 股票名称正确性测试

**问题描述**: 分析中国海油时，输出显示中国石化

**测试用例**:
```python
def test_stock_name_correctness():
    """验证分析中国海油时，输出使用正确的股票名称"""
    result = crew.analyze("sh600938", "中国海油")
    assert "中国石化" not in result
    assert "中国海油" in result
```

### 2. 地缘政治分析测试

**问题描述**: 地缘政治分析未获取实际价格数据

**测试用例**:
```python
def test_geopolitical_with_real_data():
    """验证地缘政治分析获取实际价格数据"""
    result = geopolitical_agent.analyze("sh600938")
    assert "未包含具体价格" not in result
    assert "原油" in result
```

### 3. 数据时效性测试

**测试用例**:
```python
def test_data_freshness():
    """验证数据时效性"""
    data = qlib_updater.get_latest_data("sh600519")
    data_date = data.index[-1]
    assert (datetime.now() - data_date).days <= 1
```

---

## 📊 测试覆盖率目标

| 层级 | 当前 | 目标 | 差距 |
|------|------|------|------|
| 数据层 | 70% | 90% | +20% |
| 工具层 | 60% | 85% | +25% |
| Agent 层 | 40% | 80% | +40% |
| Crew 层 | 20% | 70% | +50% |
| E2E | 30% | 100% | +70% |

---

## 📅 实施计划

### 第一阶段：补充核心测试
- 时间：2天
- 目标：完成高优先级测试用例
- 覆盖率：工具层 85%，Agent 层 60%

### 第二阶段：集成测试
- 时间：1天
- 目标：完成 Crew 层测试
- 覆盖率：Crew 层 70%

### 第三阶段：E2E 测试
- 时间：1天
- 目标：完成端到端测试
- 覆盖率：E2E 100%

---

**负责人**: mac
**更新日期**: 2026-03-18
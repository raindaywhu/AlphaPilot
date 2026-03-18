# E2E Agent 输出验证测试

> 测试时间: 2026-03-19 00:41
> 目的: 验证每个 Agent 的输出格式和内容是否符合预期

---

## 测试股票: sh600519 (贵州茅台)

### 完整响应结构测试

```
POST /api/analyze
Body: {"stock_code": "sh600519"}
```

**预期顶层字段**:
| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| stock_name | string | ✅ | 股票名称，如 "贵州茅台" |
| stock_code | string | ✅ | 股票代码，如 "SH600519" |
| overall_rating | string | ✅ | 整体评级: buy/hold/sell/neutral |
| confidence | number | ✅ | 置信度: 0.0-1.0 |
| recommendation | string | ✅ | 投资建议文本 |
| quantitative | object | ✅ | 量化分析结果 |
| fundamental | object | ✅ | 基本面分析结果 |
| macro | object | ✅ | 宏观分析结果 |
| alternative | object | ✅ | 另类数据分析结果 |
| risk | object | ✅ | 风险评估结果 |
| decision_log | string | ❌ | 决策日志（可选） |
| report_path | string | ❌ | PDF报告路径（可选） |

---

## Agent 1: Quantitative (量化分析师)

### 必需字段
| 字段 | 类型 | 验证规则 |
|------|------|---------|
| agent | string | 应为 "QuantitativeAgent" 或类似 |
| stock_code | string | 股票代码 |
| analysis_date | string | 日期格式 YYYY-MM-DD |
| overall_rating | string | buy/hold/sell/neutral |
| confidence | number | 0.0-1.0，不应为 null/0 |

### 可选但应有
| 字段 | 类型 | 说明 |
|------|------|------|
| data_validation | object | 数据验证结果 |
| factor_analysis | object | 因子分析 |
| signals | array | 交易信号列表 |

### 验证点
- [ ] confidence 不为 null
- [ ] confidence > 0（不能为 0）
- [ ] overall_rating 有值
- [ ] 返回了分析数据（非空对象）

---

## Agent 2: Fundamental (基本面分析师)

### 必需字段
| 字段 | 类型 | 验证规则 |
|------|------|---------|
| agent | string | 应为 "FundamentalAgent" 或类似 |
| overall_rating | string | buy/hold/sell/neutral |
| confidence | number | 0.0-1.0，不应为 null/0 |

### 预期内容
| 字段 | 说明 |
|------|------|
| financial_health | 财务健康评估 |
| valuation | 估值分析 |
| growth | 成长性分析 |
| profitability | 盈利能力 |

### 验证点
- [ ] confidence 不为 null
- [ ] confidence > 0
- [ ] 有具体的分析内容（不只是评级）
- [ ] 返回了 PE、ROE 等财务指标

---

## Agent 3: Macro (宏观分析师)

### 必需字段
| 字段 | 类型 | 验证规则 |
|------|------|---------|
| agent | string | 应为 "MacroAgent" 或类似 |
| overall_rating | string | buy/hold/sell/neutral |
| confidence | number | 0.0-1.0，不应为 null/0 |

### 预期内容
| 字段 | 说明 |
|------|------|
| industry_trend | 行业趋势分析 |
| policy_impact | 政策影响 |
| economic_cycle | 经济周期 |

### 验证点
- [ ] confidence 不为 null
- [ ] confidence > 0
- [ ] 有宏观经济分析内容

---

## Agent 4: Alternative (另类数据分析师)

### 必需字段
| 字段 | 类型 | 验证规则 |
|------|------|---------|
| agent | string | 应为 "AlternativeAgent" 或类似 |
| overall_rating | string | buy/hold/sell/neutral |
| confidence | number | 0.0-1.0，不应为 null/0 |

### 预期内容
| 字段 | 说明 |
|------|------|
| north_money_analysis | 北向资金分析 |
| sentiment_analysis | 市场情绪 |
| commodity_analysis | 大宗商品影响 |

### 验证点
- [ ] confidence 不为 null
- [ ] confidence > 0
- [ ] north_money_analysis 存在且有内容
- [ ] 数据来源标注（akshare 等）

---

## Agent 5: Risk (风控经理)

### 必需字段
| 字段 | 类型 | 验证规则 |
|------|------|---------|
| agent | string | 应为 "RiskAgent" 或类似 |
| overall_rating | string | 可能为 risk_level |
| confidence | number | 可能没有此字段 |

### 预期内容
| 字段 | 说明 |
|------|------|
| risk_level | 风险等级: low/medium/high |
| position_suggestion | 仓位建议 |
| risk_warnings | 风险警示 |

### 验证点
- [ ] 有风险评估内容
- [ ] 有仓位建议
- [ ] 有风险警示列表

---

## 常见问题检查清单

### 问题 1: confidence 为 null 或 0
**原因**: Agent 未正确设置 confidence
**检查**: 所有 Agent 的 confidence 字段

### 问题 2: Agent 返回空对象
**原因**: Agent 执行失败或数据缺失
**检查**: 每个 Agent 对象是否有内容

### 问题 3: overall_rating 缺失
**原因**: 决策逻辑问题
**检查**: 顶层和每个 Agent 的 overall_rating

### 问题 4: 数据源错误
**原因**: qlib/akshare 数据获取失败
**检查**: quantitative.data_validation, alternative.north_money_analysis

### 问题 5: 超时无响应
**原因**: Agent 执行时间过长
**检查**: API 响应时间 < 180 秒

---

## 测试执行脚本

```python
import requests
import json

def test_e2e_agent_outputs():
    """E2E 测试：验证所有 Agent 输出"""
    
    url = "http://localhost:8000/api/analyze"
    payload = {"stock_code": "sh600519"}
    
    response = requests.post(url, json=payload, timeout=180)
    data = response.json()
    
    results = {
        "top_level": check_top_level(data),
        "quantitative": check_agent(data, "quantitative"),
        "fundamental": check_agent(data, "fundamental"),
        "macro": check_agent(data, "macro"),
        "alternative": check_agent(data, "alternative"),
        "risk": check_risk_agent(data),
    }
    
    return results

def check_top_level(data):
    """检查顶层字段"""
    required = ["stock_name", "stock_code", "overall_rating", "confidence", "recommendation"]
    missing = [f for f in required if f not in data or data[f] is None]
    
    return {
        "has_all_required": len(missing) == 0,
        "missing_fields": missing,
        "stock_name": data.get("stock_name"),
        "overall_rating": data.get("overall_rating"),
        "confidence": data.get("confidence"),
    }

def check_agent(data, agent_name):
    """检查单个 Agent"""
    agent = data.get(agent_name, {})
    
    return {
        "exists": agent_name in data,
        "has_content": len(agent) > 0,
        "confidence": agent.get("confidence"),
        "confidence_valid": agent.get("confidence") is not None and agent.get("confidence") > 0,
        "overall_rating": agent.get("overall_rating"),
        "has_analysis": any(k for k in agent.keys() if "analysis" in k.lower() or "rating" in k.lower()),
        "keys": list(agent.keys())[:10],  # 前10个字段
    }

def check_risk_agent(data):
    """检查 Risk Agent（字段可能不同）"""
    risk = data.get("risk", {})
    
    return {
        "exists": "risk" in data,
        "has_content": len(risk) > 0,
        "risk_level": risk.get("risk_level"),
        "position_suggestion": risk.get("position_suggestion"),
        "has_warnings": "risk_warnings" in risk,
        "keys": list(risk.keys())[:10],
    }

if __name__ == "__main__":
    results = test_e2e_agent_outputs()
    print(json.dumps(results, indent=2, ensure_ascii=False))
```
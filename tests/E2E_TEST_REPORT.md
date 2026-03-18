# E2E 测试报告

> 测试时间: 2026-03-19 00:52
> 测试股票: sh600519 (贵州茅台)

---

## 发现并修复的 Bug

### Bug #1: Risk Agent 返回空对象 ❌→✅

**现象**: API 返回的 `risk` 字段为空对象 `{}`

**根因分析**:
```
investment_flow.py 返回结构:
{
  "agent_results": {quantitative, fundamental, macro, alternative},
  "risk_assessment": {...}  ← risk 在顶层！
}

main.py 错误代码:
agent_results = result.get("agent_results", {})
risk = agent_results.get("risk_assessment", {})  ❌ 找不到
```

**修复**:
```python
# main.py 第 276 行
risk=result.get("risk_assessment", {}),  ✅ 从顶层获取
```

**验证结果**:
- Risk Agent 字段数: 11 ✅
- confidence: 0.5 ✅
- 包含 position_advice, risk_metrics, risk_warning ✅

---

## E2E 测试结果汇总

### 顶层字段检查

| 字段 | 预期 | 实际 | 状态 |
|------|------|------|------|
| stock_name | string | "贵州茅台" | ✅ |
| stock_code | string | "sh600519" | ✅ |
| overall_rating | string | "hold" | ✅ |
| confidence | number | 0.5 | ✅ |
| recommendation | string | 存在 | ✅ |

### Agent 检查

| Agent | 存在 | confidence | overall_rating | 状态 |
|-------|------|------------|----------------|------|
| quantitative | ✅ | 0.3 | 中性 | ✅ |
| fundamental | ✅ | 0.7 | 良好 | ✅ |
| macro | ✅ | 0.32 | 利好 | ✅ |
| alternative | ✅ | 0.65 | 中性偏多 | ✅ |
| risk | ✅ | 0.5 | - | ✅ 已修复 |

### 响应性能

- 响应时间: ~135秒
- 内存占用: ~500MB
- 状态: 正常 ✅

---

## 待继续测试

1. [ ] 多股票测试 (sz000001, sz300750)
2. [ ] 错误输入测试 (无效股票代码)
3. [ ] 边界条件测试
4. [ ] 数据验证测试 (每个 Agent 的数据完整性)

---

## 文件变更

| 文件 | 变更 |
|------|------|
| /tmp/alphapilot/src/api/main.py | 修复 risk_assessment 字段获取 |
| /tmp/alphapilot/tests/e2e_agent_tests.md | 新增 E2E 测试用例 |
| /tmp/alphapilot/tests/test_cases_v2.md | 更新测试用例达标条件 |
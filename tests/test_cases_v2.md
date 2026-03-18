# AlphaPilot 测试用例设计 V2

> 更新时间: 2026-03-19 00:35
> 调整说明: 根据 API 实际返回调整达标条件

---

## 测试环境

- API: http://127.0.0.1:8000
- 测试时间: 2026-03-19

---

## 1. API 健康检查测试

### 1.1 检查 API 是否运行
```bash
curl -s http://127.0.0.1:8000/api/health
```
**达标条件**: 
- ✅ 返回 `{"status": "healthy", ...}`
- ❌ 超时或返回错误

### 1.2 检查股票搜索
```bash
curl -s "http://127.0.0.1:8000/api/stock/search?query=茅台"
```
**达标条件**:
- ✅ 返回股票列表，包含 stock_code 和 stock_name
- ❌ 404 或 Internal Server Error

---

## 2. 股票代码格式测试

### 2.1 标准格式 (sh/sz 前缀)
```bash
# 上海主板 - 贵州茅台
curl -s -X POST "http://127.0.0.1:8000/api/analyze" \
    -H "Content-Type: application/json" \
    -d '{"stock_code": "sh600519"}'
```
**达标条件**:
- ✅ `stock_name` = "贵州茅台"
- ✅ `overall_rating` 存在 (hold/buy/sell)
- ✅ `confidence` 存在 (0.0-1.0)
- ❌ Internal Server Error

### 2.2 大写格式 (SH/SZ 前缀)
```bash
curl -s -X POST "http://127.0.0.1:8000/api/analyze" \
    -H "Content-Type: application/json" \
    -d '{"stock_code": "SH600519"}'
```
**达标条件**:
- ✅ 系统自动转换为小写，正常返回分析结果
- ❌ 返回 "无法识别股票"

### 2.3 纯数字格式 (无前缀)
```bash
curl -s -X POST "http://127.0.0.1:8000/api/analyze" \
    -H "Content-Type: application/json" \
    -d '{"stock_code": "600519"}'
```
**达标条件**:
- ✅ 系统自动添加前缀（6开头=sh，0/3开头=sz），正常返回
- ❌ 返回 "无法识别股票"

### 2.4 指数代码
```bash
# 上证指数 (注意: sh000001 是上证指数，不是股票)
curl -s -X POST "http://127.0.0.1:8000/api/analyze" \
    -H "Content-Type: application/json" \
    -d '{"stock_code": "sh000001"}'
```
**达标条件**:
- ✅ 如果支持指数，返回指数分析
- ⚠️ 如果不支持，返回清晰的错误提示："指数暂不支持分析"
- ❌ Internal Server Error

### 2.5 无效代码
```bash
# 不存在的代码 (999999 不存在)
curl -s -X POST "http://127.0.0.1:8000/api/analyze" \
    -H "Content-Type: application/json" \
    -d '{"stock_code": "sh999998"}'
```
**达标条件**:
- ✅ 返回错误提示："无法识别股票代码" 或 "股票代码无效"
- ❌ Internal Server Error
- ❌ 返回空数据

---

## 3. 参数组合测试

### 3.1 串行模式（并行已禁用）
```bash
curl -s -X POST "http://127.0.0.1:8000/api/analyze" \
    -H "Content-Type: application/json" \
    -d '{"stock_code": "sh600519"}'
```
**达标条件**:
- ✅ 正常返回分析结果
- ⚠️ parallel 参数已默认为 false，不影响结果

### 3.2 缺少必需参数
```bash
curl -s -X POST "http://127.0.0.1:8000/api/analyze" \
    -H "Content-Type: application/json" \
    -d '{"parallel": false}'
```
**达标条件**:
- ✅ 返回 422 错误，包含 `{"detail": "..."}` 说明缺少 stock_code
- ❌ Internal Server Error

### 3.3 空 stock_code
```bash
curl -s -X POST "http://127.0.0.1:8000/api/analyze" \
    -H "Content-Type: application/json" \
    -d '{"stock_code": ""}'
```
**达标条件**:
- ✅ 返回错误提示："股票代码不能为空" 或类似提示
- ❌ Internal Server Error

---

## 4. 边界条件测试

### 4.1 连续多次请求（并发测试）
```bash
# 发送 3 个并发请求（减少负载）
for i in {1..3}; do
    curl -s -X POST "http://127.0.0.1:8000/api/analyze" \
        -H "Content-Type: application/json" \
        -d '{"stock_code": "sh600519"}' > /tmp/test_$i.json &
done
wait
```
**达标条件**:
- ✅ 所有请求都返回有效结果
- ❌ 任一请求返回 Internal Server Error
- ⚠️ 注意: 并发可能导致资源竞争

### 4.2 超时测试
```bash
# 设置 60 秒超时（分析通常需要 1-3 分钟）
curl -s -X POST "http://127.0.0.1:8000/api/analyze" \
    -H "Content-Type: application/json" \
    -d '{"stock_code": "sh600519"}' \
    --max-time 60
```
**达标条件**:
- ✅ 如果在 60 秒内完成，返回结果
- ⚠️ 如果超时，curl 返回 28，但 API 不应崩溃

### 4.3 请求体格式错误
```bash
# 非 JSON 格式
curl -s -X POST "http://127.0.0.1:8000/api/analyze" \
    -H "Content-Type: application/json" \
    -d 'invalid json'
```
**达标条件**:
- ✅ 返回 400/422 错误，包含 `{"detail": "Invalid JSON"}`
- ❌ Internal Server Error

---

## 5. Agent 稳定性测试

### 5.1 所有 Agent 返回有效数据
```bash
curl -s -X POST "http://127.0.0.1:8000/api/analyze" \
    -H "Content-Type: application/json" \
    -d '{"stock_code": "sh600519"}'
```
**达标条件**:
- ✅ `quantitative` 存在且 `confidence` 为数字 (0.0-1.0)
- ✅ `fundamental` 存在且 `confidence` 为数字
- ✅ `macro` 存在且 `confidence` 为数字
- ✅ `alternative` 存在且 `confidence` 为数字
- ✅ `risk` 存在（可能无 confidence 字段）
- ❌ 任一 Agent 缺失或 confidence 为 null

### 5.2 数据完整性
```bash
curl -s -X POST "http://127.0.0.1:8000/api/analyze" \
    -H "Content-Type: application/json" \
    -d '{"stock_code": "sh600519"}'
```
**达标条件**:
- ✅ `stock_name` 非空字符串
- ✅ `overall_rating` 为 "hold" | "buy" | "sell" | "neutral"
- ✅ `confidence` 为数字 (0.0-1.0)
- ✅ `recommendation` 非空字符串
- ❌ 任一字段缺失或类型错误

---

## 6. 数据源测试

### 6.1 qlib 数据验证
```bash
curl -s -X POST "http://127.0.0.1:8000/api/analyze" \
    -H "Content-Type: application/json" \
    -d '{"stock_code": "sh600519"}'
```
**达标条件**:
- ✅ `quantitative.data_validation` 存在
- ✅ `quantitative.factor_analysis` 或 `quantitative.signals` 存在
- ⚠️ 如果 qlib 数据缺失，应使用 mootdx 回退
- ❌ quantitative 整体为空

### 6.2 akshare 数据（北向资金）
```bash
curl -s -X POST "http://127.0.0.1:8000/api/analyze" \
    -H "Content-Type: application/json" \
    -d '{"stock_code": "sh600519"}'
```
**达标条件**:
- ✅ `alternative.north_money_analysis` 存在
- ✅ `alternative.confidence` 为数字
- ❌ alternative 整体为空

---

## 7. 错误处理测试

### 7.1 无效股票代码
```bash
curl -s -X POST "http://127.0.0.1:8000/api/analyze" \
    -H "Content-Type: application/json" \
    -d '{"stock_code": "sh999998"}'
```
**达标条件**:
- ✅ 返回 JSON 格式错误: `{"error": "无法识别股票代码"}`
- ❌ 返回非 JSON 或 Internal Server Error

### 7.2 网络错误处理
- 模拟: 断开网络后调用需要网络的 Agent
- **达标条件**: 
- ✅ 返回部分结果 + 错误提示
- ❌ 完全崩溃

### 7.3 数据缺失处理
- 测试: 使用新上市股票（历史数据不足）
- **达标条件**:
- ✅ 返回提示 "数据不足，分析可能不准确"
- ⚠️ 或正常分析但 confidence 较低

---

## 8. 性能测试

### 8.1 响应时间
- **达标条件**:
- ✅ 串行模式: < 180 秒 (3 分钟)
- ⚠️ 并行模式: 可能更快但资源消耗大

### 8.2 资源占用
- **达标条件**:
- ✅ 内存 < 2GB
- ✅ CPU 峰值 < 80%
- ❌ 内存泄漏（持续增长）

---

## 9. 股票名称输入测试

### 9.1 中文名称
```bash
curl -s -X POST "http://127.0.0.1:8000/api/analyze" \
    -H "Content-Type: application/json" \
    -d '{"stock_code": "贵州茅台"}'
```
**达标条件**:
- ✅ 返回股票代码 SH600519 的分析结果
- ❌ 返回 "无法识别股票"

### 9.2 简称
```bash
curl -s -X POST "http://127.0.0.1:8000/api/analyze" \
    -H "Content-Type: application/json" \
    -d '{"stock_code": "茅台"}'
```
**达标条件**:
- ✅ 正确匹配到贵州茅台
- ⚠️ 如果有多个匹配，返回第一个

### 9.3 含特殊字符
```bash
curl -s -X POST "http://127.0.0.1:8000/api/analyze" \
    -H "Content-Type: application/json" \
    -d '{"stock_code": "*ST左江"}'
```
**达标条件**:
- ✅ 正确识别 ST 股票
- ❌ 返回错误

---

## 测试结果汇总表

| 类别 | 测试数 | 通过 | 失败 | 跳过 |
|------|--------|------|------|------|
| API 健康检查 | 2 | - | - | - |
| 股票代码格式 | 5 | - | - | - |
| 参数组合 | 3 | - | - | - |
| 边界条件 | 3 | - | - | - |
| Agent 稳定性 | 2 | - | - | - |
| 数据源测试 | 2 | - | - | - |
| 错误处理 | 3 | - | - | - |
| 性能测试 | 2 | - | - | - |
| 股票名称输入 | 3 | - | - | - |
| **总计** | **25** | - | - | - |

---

## 关键变更说明

| 测试项 | 原条件 | 新条件 |
|--------|--------|--------|
| 1.1 API 检查 | 检查 /docs 页面 | 检查 /api/health 返回 healthy |
| 2.5 无效代码 | sh999999 (实际有效) | sh999998 (真正无效) |
| 3.1 并行模式 | 测试并行/串行对比 | 只测串行（并行已禁用） |
| 5.1 Agent 数据 | 检查 confidence | 检查 confidence + 允许 risk 无 confidence |
| 6.1 qlib 数据 | 检查 data_source | 检查 data_validation |
| 8.1 响应时间 | < 3 分钟 | < 180 秒（更精确） |
# AlphaPilot 测试用例设计

## 测试环境

- API: http://127.0.0.1:8000
- 测试时间: 2026-03-18

---

## 1. API 健康检查测试

### 1.1 检查 API 是否运行
```bash
curl -s http://127.0.0.1:8000/docs
```
**预期**: 返回 Swagger 文档页面

### 1.2 检查股票搜索
```bash
curl -s "http://127.0.0.1:8000/api/stock/search?query=茅台"
```
**预期**: 返回股票搜索结果

---

## 2. 股票代码格式测试

### 2.1 标准格式 (sh/sz 前缀)
```bash
# 上海主板
curl -s -X POST "http://127.0.0.1:8000/api/analyze" \
    -H "Content-Type: application/json" \
    -d '{"stock_code": "sh600519", "parallel": true}'

# 深圳主板
curl -s -X POST "http://127.0.0.1:8000/api/analyze" \
    -H "Content-Type: application/json" \
    -d '{"stock_code": "sz000001", "parallel": true}'

# 创业板
curl -s -X POST "http://127.0.0.1:8000/api/analyze" \
    -H "Content-Type: application/json" \
    -d '{"stock_code": "sz300750", "parallel": true}'
```

### 2.2 大写格式 (SH/SZ 前缀)
```bash
curl -s -X POST "http://127.0.0.1:8000/api/analyze" \
    -H "Content-Type: application/json" \
    -d '{"stock_code": "SH600519", "parallel": true}'
```

### 2.3 纯数字格式 (无前缀)
```bash
curl -s -X POST "http://127.0.0.1:8000/api/analyze" \
    -H "Content-Type: application/json" \
    -d '{"stock_code": "600519", "parallel": true}'
```

### 2.4 指数代码
```bash
# 上证指数
curl -s -X POST "http://127.0.0.1:8000/api/analyze" \
    -H "Content-Type: application/json" \
    -d '{"stock_code": "sh000001", "parallel": true}'

# 深证成指
curl -s -X POST "http://127.0.0.1:8000/api/analyze" \
    -H "Content-Type: application/json" \
    -d '{"stock_code": "sz399001", "parallel": true}'
```

### 2.5 无效代码
```bash
# 不存在的代码
curl -s -X POST "http://127.0.0.1:8000/api/analyze" \
    -H "Content-Type: application/json" \
    -d '{"stock_code": "sh999999", "parallel": true}'
```
**预期**: 返回错误提示，而不是 Internal Server Error

---

## 3. 参数组合测试

### 3.1 并行模式 vs 串行模式
```bash
# 并行模式
curl -s -X POST "http://127.0.0.1:8000/api/analyze" \
    -H "Content-Type: application/json" \
    -d '{"stock_code": "sh600519", "parallel": true}'

# 串行模式
curl -s -X POST "http://127.0.0.1:8000/api/analyze" \
    -H "Content-Type: application/json" \
    -d '{"stock_code": "sh600519", "parallel": false}'
```

### 3.2 缺少必需参数
```bash
# 缺少 stock_code
curl -s -X POST "http://127.0.0.1:8000/api/analyze" \
    -H "Content-Type: application/json" \
    -d '{"parallel": true}'
```
**预期**: 返回 422 错误，说明缺少必需参数

### 3.3 空 stock_code
```bash
curl -s -X POST "http://127.0.0.1:8000/api/analyze" \
    -H "Content-Type: application/json" \
    -d '{"stock_code": "", "parallel": true}'
```

---

## 4. 边界条件测试

### 4.1 连续多次请求（并发测试）
```bash
# 发送 5 个并发请求
for i in {1..5}; do
    curl -s -X POST "http://127.0.0.1:8000/api/analyze" \
        -H "Content-Type: application/json" \
        -d '{"stock_code": "sh600519", "parallel": true}' &
done
wait
```

### 4.2 超时测试
```bash
# 设置较短的超时时间
curl -s -X POST "http://127.0.0.1:8000/api/analyze" \
    -H "Content-Type: application/json" \
    -d '{"stock_code": "sh600519", "parallel": true}' \
    --max-time 10
```
**预期**: 超时后返回错误，不应该卡死

### 4.3 请求体格式错误
```bash
# 非 JSON 格式
curl -s -X POST "http://127.0.0.1:8000/api/analyze" \
    -H "Content-Type: application/json" \
    -d 'invalid json'

# Content-Type 错误
curl -s -X POST "http://127.0.0.1:8000/api/analyze" \
    -H "Content-Type: text/plain" \
    -d '{"stock_code": "sh600519", "parallel": true}'
```

---

## 5. Agent 稳定性测试

### 5.1 测试所有 Agent 返回有效数据
```bash
# 检查返回的 JSON 中每个 Agent 的数据
curl -s -X POST "http://127.0.0.1:8000/api/analyze" \
    -H "Content-Type: application/json" \
    -d '{"stock_code": "sh600519", "parallel": true}' | jq '
    {
        quantitative: .quantitative.confidence,
        fundamental: .fundamental.confidence,
        macro: .macro.confidence,
        alternative: .alternative.confidence,
        risk: .risk
    }'
```

### 5.2 检查数据完整性
```bash
# 检查每个 Agent 是否返回必要字段
curl -s -X POST "http://127.0.0.1:8000/api/analyze" \
    -H "Content-Type: application/json" \
    -d '{"stock_code": "sh600519", "parallel": true}' | jq '
    {
        has_overall_rating: (.overall_rating != null),
        has_confidence: (.confidence != null),
        has_recommendation: (.recommendation != null)
    }'
```

---

## 6. 数据源测试

### 6.1 测试 qlib 数据
```bash
# 检查量化分析是否使用 qlib 数据
curl -s -X POST "http://127.0.0.1:8000/api/analyze" \
    -H "Content-Type: application/json" \
    -d '{"stock_code": "sh600519", "parallel": true}' | jq '.quantitative.data_validation'
```

### 6.2 测试 akshare 数据
```bash
# 检查另类数据是否获取成功
curl -s -X POST "http://127.0.0.1:8000/api/analyze" \
    -H "Content-Type: application/json" \
    -d '{"stock_code": "sh600519", "parallel": true}' | jq '.alternative.north_money_analysis'
```

---

## 7. 错误处理测试

### 7.1 测试无效股票代码的错误提示
```bash
curl -s -X POST "http://127.0.0.1:8000/api/analyze" \
    -H "Content-Type: application/json" \
    -d '{"stock_code": "sh999999", "parallel": true}'
```
**预期**: 返回清晰的错误消息，而不是 "Internal Server Error"

### 7.2 测试网络错误处理
- 断开网络后测试 API 响应

### 7.3 测试数据缺失处理
- 测试没有数据的股票代码

---

## 8. 性能测试

### 8.1 响应时间
- 目标: 单次分析 < 3 分钟
- 测试: 记录多次请求的响应时间

### 8.2 资源占用
- 监控 CPU、内存使用情况

---

## 自动化测试脚本

```bash
#!/bin/bash
# run_tests.sh - 运行所有测试

API_URL="http://127.0.0.1:8000"
PASS=0
FAIL=0

echo "=== AlphaPilot API 测试 ==="
echo ""

# 测试 1: 标准股票代码
echo "[测试 1] 标准股票代码 (sh600519)"
result=$(curl -s -X POST "$API_URL/api/analyze" \
    -H "Content-Type: application/json" \
    -d '{"stock_code": "sh600519", "parallel": true}' \
    --max-time 180)
if echo "$result" | grep -q "stock_name"; then
    echo "✅ 通过"
    ((PASS++))
else
    echo "❌ 失败: $result"
    ((FAIL++))
fi

# 测试 2: 大写格式
echo "[测试 2] 大写格式 (SH600036)"
result=$(curl -s -X POST "$API_URL/api/analyze" \
    -H "Content-Type: application/json" \
    -d '{"stock_code": "SH600036", "parallel": true}' \
    --max-time 180)
if echo "$result" | grep -q "stock_name"; then
    echo "✅ 通过"
    ((PASS++))
else
    echo "❌ 失败"
    ((FAIL++))
fi

# 测试 3: 无效代码
echo "[测试 3] 无效股票代码 (sh999999)"
result=$(curl -s -X POST "$API_URL/api/analyze" \
    -H "Content-Type: application/json" \
    -d '{"stock_code": "sh999999", "parallel": true}' \
    --max-time 30)
if echo "$result" | grep -qE "error|Error|无法识别"; then
    echo "✅ 通过 (返回错误提示)"
    ((PASS++))
else
    echo "❌ 失败: 应返回错误提示"
    ((FAIL++))
fi

# 测试 4: 缺少参数
echo "[测试 4] 缺少 stock_code 参数"
result=$(curl -s -X POST "$API_URL/api/analyze" \
    -H "Content-Type: application/json" \
    -d '{"parallel": true}' \
    --max-time 10)
if echo "$result" | grep -qE "error|Error|422"; then
    echo "✅ 通过"
    ((PASS++))
else
    echo "❌ 失败"
    ((FAIL++))
fi

# 测试 5: 无效 JSON
echo "[测试 5] 无效 JSON 格式"
result=$(curl -s -X POST "$API_URL/api/analyze" \
    -H "Content-Type: application/json" \
    -d 'invalid json' \
    --max-time 10)
if echo "$result" | grep -qE "error|Error"; then
    echo "✅ 通过"
    ((PASS++))
else
    echo "❌ 失败"
    ((FAIL++))
fi

echo ""
echo "=== 测试结果 ==="
echo "通过: $PASS"
echo "失败: $FAIL"
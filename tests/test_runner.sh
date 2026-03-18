#!/bin/bash
# AlphaPilot 测试执行脚本
API_URL="http://127.0.0.1:8000"
LOG_FILE="/tmp/alphapilot/tests/test_results.log"

echo "=== AlphaPilot API 测试 ===" | tee -a $LOG_FILE
echo "开始时间: $(date)" | tee -a $LOG_FILE
echo ""

PASS=0
FAIL=0

# 测试 1.1: API 健康检查
echo "[测试 1.1] API 健康检查" | tee -a $LOG_FILE
result=$(curl -s --max-time 5 "$API_URL/" 2>&1 | head -1)
if echo "$result" | grep -q "DOCTYPE"; then
    echo "✅ 通过" | tee -a $LOG_FILE
    ((PASS++))
else
    echo "❌ 失败" | tee -a $LOG_FILE
    ((FAIL++))
fi

# 测试 1.2: 股票搜索
echo "[测试 1.2] 股票搜索" | tee -a $LOG_FILE
result=$(curl -s --max-time 10 "$API_URL/api/stock/search?query=茅台" 2>&1)
if echo "$result" | grep -qE "stock_code|stock_name|600519"; then
    echo "✅ 通过" | tee -a $LOG_FILE
    ((PASS++))
else
    echo "❌ 失败: $result" | tee -a $LOG_FILE
    ((FAIL++))
fi

# 测试 3.2: 缺少必需参数
echo "[测试 3.2] 缺少 stock_code 参数" | tee -a $LOG_FILE
result=$(curl -s --max-time 10 -X POST "$API_URL/api/analyze" \
    -H "Content-Type: application/json" \
    -d '{"parallel": true}' 2>&1)
if echo "$result" | grep -qE "error|detail|422"; then
    echo "✅ 通过 (正确返回错误)" | tee -a $LOG_FILE
    ((PASS++))
else
    echo "❌ 失败: $result" | tee -a $LOG_FILE
    ((FAIL++))
fi

# 测试 3.3: 空 stock_code
echo "[测试 3.3] 空 stock_code" | tee -a $LOG_FILE
result=$(curl -s --max-time 10 -X POST "$API_URL/api/analyze" \
    -H "Content-Type: application/json" \
    -d '{"stock_code": "", "parallel": true}' 2>&1)
if echo "$result" | grep -qE "error|detail"; then
    echo "✅ 通过 (正确返回错误)" | tee -a $LOG_FILE
    ((PASS++))
else
    echo "❌ 失败: $result" | tee -a $LOG_FILE
    ((FAIL++))
fi

# 测试 4.3: 请求体格式错误
echo "[测试 4.3] 无效 JSON 格式" | tee -a $LOG_FILE
result=$(curl -s --max-time 10 -X POST "$API_URL/api/analyze" \
    -H "Content-Type: application/json" \
    -d 'invalid json' 2>&1)
if echo "$result" | grep -qE "error|detail|JSON"; then
    echo "✅ 通过 (正确返回错误)" | tee -a $LOG_FILE
    ((PASS++))
else
    echo "❌ 失败: $result" | tee -a $LOG_FILE
    ((FAIL++))
fi

echo ""
echo "=== 快速测试结果 ===" | tee -a $LOG_FILE
echo "通过: $PASS" | tee -a $LOG_FILE
echo "失败: $FAIL" | tee -a $LOG_FILE

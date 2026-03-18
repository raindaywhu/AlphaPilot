# AlphaPilot REST API

## 快速开始

### 启动服务器

```bash
# 方式1: 使用 Python
python -m src.api

# 方式2: 使用 uvicorn
uvicorn src.api:app --reload --host 0.0.0.0 --port 8000
```

### 访问文档

启动服务器后，访问以下地址查看 API 文档：

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API 接口

### 1. 健康检查

```bash
GET /api/health
```

**响应示例**：
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "qlib_initialized": true,
  "crew_ready": true
}
```

### 2. 股票综合分析

```bash
POST /api/analyze
```

**请求体**：
```json
{
  "stock_code": "SH600519",
  "parallel": true,
  "time_horizon": 5
}
```

**响应示例**：
```json
{
  "stock_code": "SH600519",
  "analysis_date": "2026-03-18",
  "overall_rating": "看涨",
  "confidence": 0.75,
  "score": 0.72,
  "agent_results": {
    "quantitative": {...},
    "macro": {...},
    "alternative": {...}
  },
  "risk_warnings": [...],
  "disclaimer": "本分析报告由 AI 系统自动生成，不构成投资建议"
}
```

### 3. 量化分析

```bash
POST /api/analyze/quantitative
```

**请求体**：
```json
{
  "stock_code": "SH600519",
  "time_horizon": 5
}
```

### 4. 宏观分析

```bash
POST /api/analyze/macro
```

**请求体**：
```json
{
  "stock_code": "SH600519"
}
```

### 5. 另类分析

```bash
POST /api/analyze/alternative
```

**请求体**：
```json
{
  "stock_code": "SH600519"
}
```

## 测试

```bash
# 运行 API 测试
pytest tests/test_api.py -v

# 测试健康检查接口
curl http://localhost:8000/api/health

# 测试分析接口
curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"stock_code": "SH600519"}'
```

## 技术栈

- **FastAPI**: 现代、快速的 Web 框架
- **Uvicorn**: ASGI 服务器
- **Pydantic**: 数据验证

## 错误处理

API 返回标准的 HTTP 状态码：

- `200`: 成功
- `422`: 参数验证失败
- `500`: 服务器错误

错误响应格式：
```json
{
  "detail": "错误信息"
}
```
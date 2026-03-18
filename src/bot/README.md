# AlphaPilot Bot - 飞书机器人

飞书机器人模块，让用户通过飞书进行股票分析。

## 功能特性

### 支持的命令

| 命令 | 说明 | 示例 |
|------|------|------|
| `/analyze <股票代码>` | 综合分析 | `/analyze SH600519` |
| `/quant <股票代码>` | 量化分析 | `/quant SH600519` |
| `/macro <股票代码>` | 宏观分析 | `/macro SH600519` |
| `/alt <股票代码>` | 另类分析 | `/alt SH600519` |
| `/help` | 帮助信息 | `/help` |

### 股票代码格式

- 上海交易所：`SH` + 6位数字，如 `SH600519`
- 深圳交易所：`SZ` + 6位数字，如 `SZ000001`

> 💡 如果只输入 6 位数字，系统会默认添加 `SH` 前缀

## 快速开始

### 1. 环境准备

```bash
# 安装依赖
pip install -r requirements.txt

# 配置环境变量
export LARK_APP_ID="your_app_id"
export LARK_APP_SECRET="your_app_secret"
export LARK_ENCRYPT_KEY="your_encrypt_key"  # 可选
export LARK_VERIFICATION_TOKEN="your_token"  # 可选
export API_BASE_URL="http://localhost:8000"  # API 服务地址
```

### 2. 启动 API 服务

```bash
# 启动分析 API
cd src/api
python main.py
```

### 3. 启动机器人

```bash
# 启动 Webhook 服务
cd src/bot
python webhook.py
```

### 4. 配置飞书应用

1. 登录 [飞书开放平台](https://open.feishu.cn/)
2. 创建企业自建应用
3. 配置事件订阅：
   - URL: `https://your-domain/webhook`
   - 订阅事件：`im.message.receive_v1`
4. 启用机器人能力
5. 发布应用

## 架构设计

```
src/bot/
├── __init__.py      # 模块入口
├── bot.py           # 机器人核心实现
├── handlers.py      # 命令处理器
├── cards.py         # 消息卡片构建器
└── webhook.py       # Webhook 服务器
```

### 核心类

- **AlphaPilotBot**: 飞书机器人核心类，处理认证、消息发送、API 调用
- **CommandHandler**: 命令处理器，解析和执行各种命令
- **CardBuilder**: 消息卡片构建器，生成飞书消息卡片
- **Webhook**: FastAPI 应用，接收飞书事件回调

## API 调用流程

```
用户消息 → 飞书服务器 → Webhook → CommandHandler → AlphaPilot API → 分析结果 → 消息卡片 → 用户
```

## 消息卡片示例

### 综合分析卡片

```
┌─────────────────────────────────────┐
│ 📊 SH600519 投资分析报告              │
│ 分析日期: 2024-01-15                 │
├─────────────────────────────────────┤
│ 综合评级: 中性偏多    置信度: 65%     │
│ 得分: 0.62           耗时: 5s        │
├─────────────────────────────────────┤
│ 分析摘要                             │
│ 基于量化、宏观、另类三维分析，该股票...│
├─────────────────────────────────────┤
│ ⚠️ 风险提示                          │
│ • 市场波动风险                       │
│ • 行业周期风险                       │
└─────────────────────────────────────┘
```

## 配置说明

### 环境变量

| 变量名 | 说明 | 必填 |
|--------|------|------|
| `LARK_APP_ID` | 飞书应用 ID | ✅ |
| `LARK_APP_SECRET` | 飞书应用密钥 | ✅ |
| `LARK_ENCRYPT_KEY` | 加密密钥 | ❌ |
| `LARK_VERIFICATION_TOKEN` | 验证 Token | ❌ |
| `API_BASE_URL` | API 服务地址 | ❌ |
| `BOT_PORT` | Webhook 端口 | ❌ |

## 部署说明

### Docker 部署

```bash
# 构建镜像
docker build -t alphapilot-bot .

# 运行容器
docker run -d \
  -p 8080:8080 \
  -e LARK_APP_ID="your_app_id" \
  -e LARK_APP_SECRET="your_app_secret" \
  -e API_BASE_URL="http://api-service:8000" \
  alphapilot-bot
```

### Kubernetes 部署

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: alphapilot-bot
spec:
  replicas: 2
  selector:
    matchLabels:
      app: alphapilot-bot
  template:
    metadata:
      labels:
        app: alphapilot-bot
    spec:
      containers:
      - name: bot
        image: alphapilot-bot:latest
        ports:
        - containerPort: 8080
        env:
        - name: LARK_APP_ID
          valueFrom:
            secretKeyRef:
              name: alphapilot-secrets
              key: lark-app-id
        - name: LARK_APP_SECRET
          valueFrom:
            secretKeyRef:
              name: alphapilot-secrets
              key: lark-app-secret
```

## 测试

```bash
# 运行测试
pytest tests/test_bot.py -v

# 带覆盖率
pytest tests/test_bot.py --cov=src/bot
```

## 常见问题

### 1. 消息发送失败

检查：
- `LARK_APP_ID` 和 `LARK_APP_SECRET` 是否正确
- 应用是否有发送消息的权限
- 用户是否在机器人可用范围内

### 2. Webhook 验证失败

检查：
- Webhook URL 是否可访问
- 飞书应用是否配置了正确的验证 Token

### 3. API 调用超时

检查：
- API 服务是否正常运行
- `API_BASE_URL` 是否正确
- 网络连通性

## 更新日志

### v1.0.0 (2024-01-15)

- 初始版本
- 支持基础命令：`/analyze`, `/quant`, `/macro`, `/alt`, `/help`
- 支持消息卡片输出
- 异步处理长任务

## 许可证

MIT License
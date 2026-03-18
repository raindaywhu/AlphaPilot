# 飞书机器人命令集成修复方案

## 问题描述

飞书机器人命令（/analyze, /quant, /macro, /alt）无响应

## 根因分析

1. **OpenClaw 使用 WebSocket 模式**接收飞书消息
2. **AlphaPilot Webhook 端点**期望 HTTP POST 请求
3. **两者未连接**：OpenClaw 收到消息后不知道要调用 AlphaPilot API

## 解决方案

### 方案 A：在 OpenClaw 中添加命令 Hook（推荐）

在 OpenClaw 的消息处理流程中添加命令识别：

```python
# 在 OpenClaw 的消息处理中添加
def process_message(message: str) -> str:
    # 检查是否是 AlphaPilot 命令
    if message.startswith(('/analyze', '/quant', '/macro', '/alt', '/help')):
        # 调用 AlphaPilot API
        return call_alphapilot_api(message)

    # 正常对话处理
    return normal_conversation(message)
```

### 方案 B：切换到 Webhook 模式

修改 OpenClaw 配置，将飞书连接模式从 WebSocket 改为 Webhook：

```json
{
  "channels": {
    "feishu": {
      "connectionMode": "webhook",  // 改为 webhook
      "webhookPath": "/webhook"
    }
  }
}
```

**注意**：需要公网 IP 或内网穿透工具

### 方案 C：独立部署飞书机器人

将 AlphaPilot Bot 作为独立服务部署，使用单独的飞书应用。

## 推荐方案

**方案 A**：在 OpenClaw 中添加命令 Hook

原因：
- 不需要修改 OpenClaw 核心配置
- 不需要公网 IP
- 可以复用现有的 WebSocket 连接

## 实施步骤

1. 在 OpenClaw 的 hooks 配置中添加命令处理 hook
2. 创建 `command_hook.py` 处理 AlphaPilot 命令
3. 将命令路由到 AlphaPilot API（http://localhost:8000/api/...）

## 文件变更

需要创建/修改的文件：

1. `~/.openclaw/openclaw.json` - 添加 hook 配置
2. `~/.openclaw/workspace-mac/hooks/alphapilot_command.py` - 命令处理 hook

## 验收标准

1. 用户发送 `/analyze 600519` 能够触发股票分析
2. 用户发送 `/help` 能够返回帮助信息
3. 非命令消息正常对话
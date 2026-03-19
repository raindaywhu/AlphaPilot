# AlphaPilot 开发规范

## 🔐 敏感信息管理

### ❌ 禁止事项

1. **禁止在代码中硬编码 API Key**
   ```python
   # ❌ 错误
   api_key = "sk-xxxxx"
   
   # ✅ 正确
   api_key = os.environ.get("API_KEY")
   ```

2. **禁止提交 .env 文件**
   - 使用 `.env.example` 作为模板
   - 实际的 `.env` 文件在本地创建

3. **禁止在日志中打印敏感信息**

### ✅ 正确做法

1. **使用环境变量**
   ```python
   from src.config import Config
   
   api_key = Config.GLM_API_KEY
   ```

2. **使用统一配置模块**
   - 所有配置在 `src/config.py` 中统一管理
   - 通过 `.env` 文件加载

3. **Pre-commit 检查**
   - 提交前自动检测敏感信息
   - 发现问题会阻止提交

## 📝 代码规范

### 导入顺序
1. 标准库
2. 第三方库
3. 本地模块

### 类型注解
```python
def analyze(stock_code: str) -> Dict[str, Any]:
    ...
```

### 日志规范
```python
logger.info("分析完成")  # ✅
logger.info(f"Key: {api_key}")  # ❌ 禁止打印敏感信息
```

## 🧪 测试规范

- 测试文件放在 `tests/` 目录
- 使用 pytest 运行测试
- 测试覆盖率目标：80%+

## 📦 提交规范

```
<type>(<scope>): <subject>

type: feat|fix|docs|style|refactor|test|chore
```

示例：
- `feat(agent): 添加量化分析师`
- `fix(api): 修复股票代码验证`
- `docs(readme): 更新安装说明`
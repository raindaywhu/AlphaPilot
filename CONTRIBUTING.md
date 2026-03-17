# 贡献指南

## 快速开始

### 1. 阅读设计文档

**必读文档**（按顺序）：

| 文档 | 说明 | 路径 |
|------|------|------|
| README.md | 项目概述 | `/README.md` |
| DESIGN.md | 系统设计 | `/docs/DESIGN.md` |
| TASK_BREAKDOWN.md | 任务分解 | `/docs/TASK_BREAKDOWN.md` |
| PROGRESS.md | 当前进度 | `/PROGRESS.md` |

### 2. 克隆仓库

```bash
# 使用 SSH（推荐）
git clone git@github.com-mac:raindaywhu/AlphaPilot.git

# 或使用 HTTPS
git clone https://github.com/raindaywhu/AlphaPilot.git
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

---

## 项目结构

```
AlphaPilot/
├── README.md                   # 项目概述
├── CONTRIBUTING.md             # 本文件
├── PROGRESS.md                 # 当前进度
├── requirements.txt            # Python 依赖
│
├── docs/                       # 文档
│   ├── DESIGN.md               # 系统设计
│   └── TASK_BREAKDOWN.md       # 任务分解
│
├── src/                        # 源代码
│   ├── data/                   # 数据层
│   │   ├── __init__.py
│   │   ├── qlib_updater.py     # DATA-001
│   │   ├── mootdx_fetcher.py   # DATA-002
│   │   └── data_converter.py   # DATA-003
│   │
│   ├── tools/                  # 工具层
│   │   ├── __init__.py
│   │   ├── alpha158_tool.py    # TOOL-001
│   │   ├── gbdt_tool.py        # TOOL-002
│   │   ├── technical_tool.py   # TOOL-003
│   │   ├── north_money_tool.py # TOOL-004
│   │   └── commodity_tool.py   # TOOL-005
│   │
│   ├── agents/                 # Agent 层
│   │   ├── __init__.py
│   │   ├── quantitative.py     # AGENT-001
│   │   ├── macro.py            # AGENT-002
│   │   └── alternative.py      # AGENT-003
│   │
│   └── crew/                   # Crew 层
│       ├── __init__.py
│       └── investment_crew.py  # CREW-001
│
├── tests/                      # 测试
│   ├── __init__.py
│   ├── test_data/
│   ├── test_tools/
│   ├── test_agents/
│   └── test_crew/
│
├── scripts/                    # 脚本
│   └── run_tests.sh
│
└── examples/                   # 示例
    └── basic_usage.py
```

---

## 开发流程

### 1. 认领任务

1. 在 GitHub Issues 中找到要做的任务
2. 在 Issue 中评论："我来处理这个任务"
3. 将 Issue 分配给自己

### 2. 创建分支

```bash
# 分支命名规范：<type>/<issue-id>-<short-desc>
# 例如：feature/DATA-001-qlib-updater

git checkout -b feature/DATA-001-qlib-updater
```

**分支类型**：

| 类型 | 说明 |
|------|------|
| `feature/` | 新功能 |
| `fix/` | Bug 修复 |
| `refactor/` | 重构 |
| `docs/` | 文档更新 |

### 3. 编写代码

**编码规范**：

- 使用 Python 3.10+
- 使用 type hints
- 遵循 PEP 8
- 每个函数添加 docstring

**示例**：

```python
def get_realtime_quote(self, stock_code: str) -> dict:
    """
    获取实时行情
    
    Args:
        stock_code: 股票代码（如 000001）
        
    Returns:
        dict: 实时行情数据
        
    Raises:
        ValueError: 股票代码格式错误
    """
    pass
```

### 4. 编写测试

每个模块都需要对应的测试文件：

```python
# tests/test_data/test_mootdx_fetcher.py

def test_get_realtime_quote():
    fetcher = MootdxDataFetcher()
    quote = fetcher.get_realtime_quote("000001")
    
    assert "price" in quote
    assert "open" in quote
    assert "high" in quote
    assert "low" in quote
    assert "volume" in quote
```

### 5. 运行测试

```bash
# 运行所有测试
pytest tests/

# 运行特定测试
pytest tests/test_data/test_mootdx_fetcher.py

# 运行并显示覆盖率
pytest --cov=src tests/
```

### 6. 提交代码

**Commit 规范**：

```
<type>(<scope>): <subject>

<body>

<footer>
```

**类型**：

| 类型 | 说明 |
|------|------|
| `feat` | 新功能 |
| `fix` | Bug 修复 |
| `docs` | 文档更新 |
| `test` | 测试 |
| `refactor` | 重构 |

**示例**：

```
feat(data): 实现 qlib 数据更新器

- 实现update_daily_data 方法
- 实现 get_latest_date 方法
- 添加数据验证功能

Closes #1
```

### 7. 推送并创建 PR

```bash
git push origin feature/DATA-001-qlib-updater
```

然后在 GitHub 上创建 Pull Request。

---

## 验收标准

每个任务完成后，需要满足：

- [ ] 代码符合编码规范
- [ ] 测试通过
- [ ] 测试覆盖率 > 80%
- [ ] 更新 PROGRESS.md
- [ ] 在 Issue 中添加完成说明

---

## 问题反馈

遇到问题时：

1. 在 Issue 中添加评论，描述问题
2. 等待 PM（Jack）决策
3. 记录决策理由
4. 继续执行

---

## 联系方式

- **PM**: Jack
- **开发者**: mac
- **讨论区**: https://github.com/raindaywhu/AlphaPilot/discussions
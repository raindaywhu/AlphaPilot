# AlphaPilot

>Alpha收益的领航员

---

## 项目简介

**AlphaPilot** 是一个基于 CrewAI + qlib 的 A 股智能投资分析系统。

## 项目目标

| 指标 | 目标值 |
|------|--------|
| 年化收益 | 20-30% |
| 最大回撤 | <15% |
| 夏普比率 | >1.5 |
| 胜率 | >55% |

---

## 技术栈

- **量化计算**：qlib（Alpha158/Alpha360 因子、GBDT/XGBoost 模型、回测引擎）
- **决策推理**：CrewAI（6 Agents 协作、Memory、Knowledge/RAG、Flow）
- **LLM**：GLM-5
- **数据源**：mootdx（实时数据）、qlib（历史数据）

---

## 项目结构

```
AlphaPilot/
├── data/                 # 数据层
├── tools/                # 工具层
├── agents/               # Agent 层
├── crew/                 # Crew 层
├── api/                  # API 层
├── ui/                   # UI 层
├── docs/                 # 文档
│   ├── DESIGN.md         # 设计文档
│   └── TASK_BREAKDOWN.md # 任务拆解
├── main.py
└── requirements.txt
```

---

## Agent 架构

| Agent | 职责 | 工具 |
|-------|------|------|
| 量化分析师 | 技术面分析、因子分析、模型预测 | qlib 工具、技术指标工具 |
| 基本面分析师 | 财务分析、估值分析、行业对比 | 财务工具、估值工具 |
| 宏观分析师 | 宏观经济、货币政策、地缘政治 | 搜索工具、宏观数据工具 |
| 另类分析师 | 北向资金、市场情绪、大宗商品 | 北向资金工具、商品价格工具 |
| 风控经理 | 风险评估、仓位建议、止损策略 | 风险计算工具、回测工具 |
| 投资决策者 | 综合决策、最终建议 | 无（纯推理）|

---

## 开发进度

详见：[TASK_BREAKDOWN.md](docs/TASK_BREAKDOWN.md)

---

## 快速开始

```bash
# 克隆仓库
git clone git@github.com-jack:raindaywhu/AlphaPilot.git

# 安装依赖
pip install -r requirements.txt

# 运行
python main.py
```

---

## 许可证

MIT License

---

**创建人**：Jack
**创建时间**：2026-03-17
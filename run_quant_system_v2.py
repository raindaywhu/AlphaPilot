#!/usr/bin/env python3
"""
A股量化交易Agent系统 v2.0 - 修复版
==================================
修复 LLM 配置，使用 CrewAI LLM 类
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path

# 配置
from crewai import Agent, Task, Crew, Process, LLM

# 创建 LLM
llm = LLM(
    model="glm-5",
    api_key="YOUR_GLM_API_KEY",
    base_url="https://coding.dashscope.aliyuncs.com/v1",
    temperature=0.7
)

# 知识库
KNOWLEDGE_DIR = Path("/Users/rainday/.openclaw/workspace-mac/knowledge")
KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)

# ============================================
# Agent 0: 主控Agent
# ============================================
master_agent = Agent(
    role="主控调度Agent",
    goal="""理解用户意图，拆解复杂任务，协调各子Agent工作，汇总结果并生成最终报告""",
    backstory="""你是整个量化交易系统的"大脑"和"指挥官"。

你的核心能力：
1. 自然语言理解：精准解析用户的策略意图
2. 任务规划：将宏观目标分解为可执行的子任务
3. 工作流编排：管理任务依赖关系和执行顺序
4. 异常处理：处理失败、超时等异常情况
5. 结果汇总：整合各Agent输出，生成连贯报告

你的工作原则：
- 确保每个任务都有明确的输入和输出
- 监控任务执行状态，及时调整策略
- 在关键节点进行质量检查
- 保持系统的稳定性和可追溯性""",
    llm=llm,
    verbose=True,
    allow_delegation=True
)

# ============================================
# Agent 1: 数据采集Agent
# ============================================
data_agent = Agent(
    role="数据采集与清洗Agent",
    goal="获取高质量、实时最新的市场数据，为上层应用提供可靠的数据基础",
    backstory="""你是系统的"后勤部长"，负责数据的采集、清洗和存储。

⚠️ 核心原则：**必须获取最新数据，拒绝使用过期数据！**

核心职责：
1. 实时数据接入：行情、财务、另类数据
2. 数据清洗：缺失值处理、异常值剔除、复权处理
3. 特征工程：计算技术指标、财务指标
4. 数据存储：时间序列数据库管理
5. 数据质量监控：完整性、一致性、时效性校验

🚨 数据时效性要求：
- 行情数据：必须是当日最新或最近交易日收盘数据
- 每次查询前必须确认数据时间戳
- 如果数据超过3个交易日未更新，必须重新获取
- 明确标注数据日期，如"2026-03-15 收盘价：46.90元"

数据源优先级：
- 实时数据源：mootdx、新浪财经API（优先）
- 开源：Tushare、Akshare、Baostock
- 专业：Wind、同花顺iFinD（按需）""",
    llm=llm,
    verbose=True,
    allow_delegation=False
)

# ============================================
# Agent 2: 地缘政治分析Agent
# ============================================
geopolitical_agent = Agent(
    role="地缘政治分析师",
    goal="追踪全球地缘政治最新动态，评估对市场的实时影响，建立知识库",
    backstory="""你是资深地缘政治分析师，拥有20年国际关系研究经验。

⚠️ 核心原则：**必须获取最新资讯，拒绝使用过期分析！**

🚨🚨🚨 【绝对禁止】股票名称混淆错误！
- 分析哪只股票，就只能讨论这只股票
- 禁止使用其他股票作为示例或替代
- 每个结论都必须标注正确的股票名称
- 如果不确定股票名称，必须明确标注"待确认"

核心职责：
1. 实时信息收集：地缘政治、关税、战争相关最新资讯
2. 影响评估：直接/间接/连锁反应分析
3. 时间维度：短期冲击/中期调整/长期趋势
4. 市场映射：股票/债券/商品/外汇影响
5. 知识库建设：事件记录、分析结论、市场影响

🚨 时效性要求：
- 必须搜索最近24-72小时的最新资讯
- 标注信息来源和时间，如"据路透社 2026-03-16 报道"
- 区分"已确认事件"和"市场传闻"
- 识别信息更新时间，避免使用过期分析

分析框架：
- 风险等级：低/中/高/极高
- 影响方向：利好/利空/中性
- 持续时间：短期/中期/长期
- 置信度：高/中/低
- 信息时间：最新更新时间""",
    llm=llm,
    verbose=True,
    allow_delegation=False
)

# ============================================
# Agent 3: 因子研究Agent
# ============================================
factor_agent = Agent(
    role="因子研究与生成Agent",
    goal="基于最新数据挖掘有效Alpha因子，建立因子库",
    backstory="""你是系统的"创意引擎"，专注于因子挖掘和验证。

⚠️ 核心原则：**基于最新数据分析，拒绝使用过期数据！**

核心职责：
1. 因子生成：量价因子、财务因子、另类因子
2. 因子检验：IC/IR分析、分层回测
3. 因子库管理：存储、版本控制、元数据管理
4. 自然语言因子：将投资逻辑转化为可计算因子
5. 因子组合：多因子合成、权重优化

因子类型：
- 技术类：动量、反转、波动率、流动性
- 财务类：估值、盈利、成长、杠杆
- 另类类：舆情、供应链、招聘、卫星图像
- 地缘政治类：风险指数、事件驱动""",
    llm=llm,
    verbose=True,
    allow_delegation=False
)

# ============================================
# Agent 4: 策略开发Agent
# ============================================
strategy_agent = Agent(
    role="策略开发Agent",
    goal="将投资思想转化为可执行的交易策略，输出完整策略代码",
    backstory="""你是系统的"工程师"，负责策略设计和代码实现。

核心职责：
1. 策略设计：入场条件、出场条件、仓位管理
2. 代码生成：符合Qlib/Backtrader框架的Python代码
3. 参数配置：回测时间、基准、交易成本
4. 逻辑验证：未来函数检查、逻辑完整性
5. 文档编写：策略说明、参数说明

策略类型：
- 趋势跟踪：均线、突破、动量
- 均值回归：反转、配对交易
- 事件驱动：财报、公告、舆情
- 多因子：因子选股、组合优化""",
    llm=llm,
    verbose=True,
    allow_delegation=False
)

# ============================================
# Agent 5: 回测验证Agent
# ============================================
backtest_agent = Agent(
    role="回测验证Agent",
    goal="在历史数据上验证策略有效性，生成详细绩效报告",
    backstory="""你是系统的"质量检验员"，负责策略验证和性能评估。

核心职责：
1. 回测执行：运行策略代码
2. 绩效计算：年化收益、夏普比率、最大回撤
3. 风险分析：波动率、下行风险、VaR
4. 归因分析：收益来源分解
5. 稳健性检验：参数敏感性、滚动窗口回测

回测陷阱规避：
- 未来函数检查
- 幸存者偏差处理
- 过拟合检测
- 交易成本考虑""",
    llm=llm,
    verbose=True,
    allow_delegation=False
)

# ============================================
# Agent 6: 风险管理Agent
# ============================================
risk_agent = Agent(
    role="风险管理Agent",
    goal="识别、度量、控制投资风险，确保组合安全",
    backstory="""你是系统的"安全官"，负责全流程风险管控。

核心职责：
1. 事前风控：策略风险评估、风险预算
2. 事中风控：仓位控制、止损止盈、敞口管理
3. 合规检查：交易规则、监管要求
4. 压力测试：极端场景模拟
5. 预警机制：风险阈值监控

风险类型：
- 市场风险：波动率、回撤、相关性
- 流动性风险：成交量、冲击成本
- 地缘政治风险：事件风险、黑天鹅
- 操作风险：系统故障、人为错误""",
    llm=llm,
    verbose=True,
    allow_delegation=False
)

# ============================================
# Agent 7: 交易时机Agent
# ============================================
timing_agent = Agent(
    role="交易时机分析师",
    goal="综合地缘政治和技术面，基于最新数据给出精准的入场时机和交易计划",
    backstory="""你是专业的交易时机分析师，擅长把握入场和出场时机。

⚠️ 核心原则：**必须使用最新实时数据，拒绝基于过期数据做决策！**

核心理念：
**地缘政治决定大方向，技术面决定入场点**

🚨 数据时效性要求：
- 股价：必须是最新收盘价或实时价格
- 技术指标：基于最新K线计算
- 支撑压力位：基于最新走势更新
- 地缘政治：使用最近24-72小时资讯

决策矩阵：
| 地缘风险 | 技术信号 | 决策 |
|---------|---------|------|
| 低      | 强      | 重仓 |
| 中      | 强      | 标准仓 |
| 高      | 强      | 观察仓 |
| 极高    | 强      | 观望 |""",
    llm=llm,
    verbose=True,
    allow_delegation=False
)

# ============================================
# Agent 8: 综合报告Agent
# ============================================
report_agent = Agent(
    role="首席综合分析师",
    goal="整合所有分析结果，输出完整的投资决策报告，确保数据时效性",
    backstory="""你是首席投资分析师，负责整合和呈现最终报告。

⚠️ 核心原则：**报告必须明确标注数据时间，拒绝模糊表述！**

🚨🚨🚨 【绝对禁止】股票名称混淆错误！
- 分析哪只股票，就只能讨论这只股票
- 禁止使用其他股票作为示例或替代
- 每个结论都必须标注正确的股票名称
- 如果不确定股票名称，必须明确标注"待确认"

核心职责：
1. 信息整合：汇总各Agent分析结果
2. 逻辑串联：确保报告逻辑连贯
3. 决策建议：给出明确投资建议
4. 风险提示：强调关键风险点
5. 执行计划：详细的操作步骤

报告结构：
1. 执行摘要（核心结论 + 数据截止时间）
2. 地缘政治分析（资讯日期）
3. 技术面分析（最新价格日期）
4. 因子分析（财务数据日期）
5. 策略回测
6. 风险评估
7. 交易计划（基于最新数据）
8. 监控指标""",
    llm=llm,
    verbose=True,
    allow_delegation=True
)


# ============================================
# 完整工作流
# ============================================
def analyze_stock_full(stock_code: str, stock_name: str = "", current_price: float = None):
    """完整的股票分析流程"""
    
    price_info = f"\n当前价格：{current_price}元" if current_price else ""
    
    # ===== 阶段1：数据准备 =====
    data_task = Task(
        description=f"""
⚠️ 重要：必须获取最新数据！

获取股票 {stock_code} ({stock_name}) 的基础数据：
{price_info}

🚨 数据时效性要求：
- 行情数据：必须是最近交易日收盘数据
- 明确标注数据日期："数据日期：YYYY-MM-DD"

1. 行情数据：
   - 最近60日日K线
   - 均线系统（MA5, MA10, MA20, MA60）
   - 技术指标（MACD, RSI, KDJ, BOLL）

2. 财务数据：
   - 最新季报关键指标
   - 同比/环比变化

3. 市场数据：
   - 所属行业
   - 行业近期表现
   - 资金流向

输出格式要求：
- 数据质量报告
- 关键数据摘要
- ⚠️ 必须包含：数据日期
""",
        expected_output="完整的数据准备报告",
        agent=data_agent
    )
    
    # ===== 阶段2：地缘政治分析 =====
    geopolitical_task = Task(
        description=f"""
🚨🚨🚨 【绝对禁止】股票名称混淆错误！
目标股票：{stock_code} - {stock_name}
- 只能分析这只股票！禁止提及其他股票！
- 所有输出必须使用正确的股票名称：{stock_name}
- 如果在输出中提到其他股票名称，视为严重错误！

⚠️ 重要：必须获取最新地缘政治资讯！

分析 {stock_code} ({stock_name}) 相关的地缘政治因素：

🚨 时效性要求：
- 搜索最近 24-72 小时的最新资讯
- 每条信息必须标注来源和日期

一、宏观地缘政治评估
1. 当前全球地缘政治风险等级（低/中/高/极高）
2. 主要风险源识别
3. 近期关键事件
4. 趋势判断

二、行业/公司特定影响（针对 {stock_name}）
1. 该行业对地缘政治的敏感度
2. {stock_name} 业务涉及的风险点
3. 供应链安全评估
4. 潜在的黑天鹅事件

三、时机窗口判断
1. 当前是否为良好买入窗口
2. 最佳买入窗口期预测
3. 需要回避的时段

⚠️ 必须标注：分析日期 + 资讯来源日期
⚠️ 确认：报告中所有股票名称必须是"{stock_name}"，代码必须是"{stock_code}"
""",
        expected_output=f"{stock_name}({stock_code})地缘政治分析报告",
        agent=geopolitical_agent
    )
    
    # ===== 阶段3：因子分析 =====
    factor_task = Task(
        description=f"""
分析 {stock_code} ({stock_name}) 的因子表现：

1. 价值因子：PE、PB、PS、PEG
2. 成长因子：营收增速、利润增速
3. 质量因子：ROE、ROA
4. 动量因子：近期涨跌幅
5. 情绪因子：资金流向
6. 地缘政治因子：风险指数

输出：因子综合评分（0-100）+ 各因子详细分析
""",
        expected_output="因子分析报告",
        agent=factor_agent
    )
    
    # ===== 阶段4：策略设计 =====
    strategy_task = Task(
        description=f"""
基于分析结果，设计交易策略：

1. 策略类型选择
2. 入场条件：技术信号 + 地缘政治条件
3. 出场条件：止盈逻辑 + 止损逻辑
4. 仓位管理：基础仓位 + 风险调整

输出：策略设计文档
""",
        expected_output="策略设计文档",
        agent=strategy_agent
    )
    
    # ===== 阶段5：回测验证 =====
    backtest_task = Task(
        description=f"""
对策略进行回测验证：

1. 回测设置：时间范围、初始资金、交易成本
2. 绩效计算：年化收益、夏普比率、最大回撤
3. 风险分析：波动率、回撤分析
4. 稳健性检验：参数敏感性

输出：回测绩效报告
""",
        expected_output="回测绩效报告",
        agent=backtest_agent
    )
    
    # ===== 阶段6：风险评估 =====
    risk_task = Task(
        description=f"""
评估投资风险：

一、市场风险
二、地缘政治风险
三、流动性风险
四、操作风险

输出：风险评估报告 + 风控规则
""",
        expected_output="风险评估报告",
        agent=risk_agent
    )
    
    # ===== 阶段7：交易时机 =====
    timing_task = Task(
        description=f"""
🚨🚨🚨 【绝对禁止】股票名称混淆错误！
目标股票：{stock_code} - {stock_name}
- 只能分析这只股票！禁止提及其他股票！
- 所有输出必须使用正确的股票名称：{stock_name}
- 如果在输出中提到其他股票名称，视为严重错误！

⚠️ 重要：必须基于最新数据制定交易计划！

制定 {stock_name}({stock_code}) 的交易计划：
{price_info}

第一步：地缘政治时机窗口（针对 {stock_name}）
- 风险等级
- 窗口期
- 关键监控事件

第二步：技术入场点（针对 {stock_code}）
- 当前价格
- 强支撑位
- 入场信号
- 信号强度

第三步：综合决策
- 地缘风险
- 技术信号
- 综合判断

第四步：具体计划
| 优先级 | 价位 | 条件 | 仓位 |
|-------|------|------|------|

第五步：止损止盈（针对 {stock_name}）
- 止损位
- 目标价

第六步：地缘政治风控
- 风险升级应对
- 黑天鹅紧急止损

⚠️ 必须在报告开头标注数据截止时间！
⚠️ 确认：报告中所有股票名称必须是"{stock_name}"，代码必须是"{stock_code}"
""",
        expected_output=f"{stock_name}({stock_code})交易计划",
        agent=timing_agent
    )
    
    # ===== 阶段8：综合报告 =====
    final_task = Task(
        description=f"""
🚨🚨🚨 【绝对禁止】股票名称混淆错误！
目标股票：{stock_code} - {stock_name}
- 只能分析这只股票！禁止提及其他股票！
- 所有输出必须使用正确的股票名称：{stock_name}
- 如果在输出中提到其他股票名称，视为严重错误！

整合所有分析，输出完整投资报告：

━━━━ 执行摘要 ━━━━
- 目标股票：{stock_code} ({stock_name})
- 投资评级
- 置信度
- 地缘政治风险
- 时机窗口

━━━━ 一、地缘政治分析（{stock_name}）━━━━

━━━━ 二、因子分析（{stock_name}）━━━━

━━━━ 三、策略回测 ━━━━

━━━━ 四、风险评估 ━━━━

━━━━ 五、交易计划（{stock_name}）━━━━

━━━━ 六、监控与跟踪 ━━━━

报告生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

⚠️ 最终确认：报告标题必须是"{stock_name}({stock_code})投资分析报告"
""",
        expected_output=f"{stock_name}({stock_code})投资分析报告",
        agent=report_agent
    )
    
    # 创建团队
    agents = [
        master_agent, data_agent, geopolitical_agent, factor_agent,
        strategy_agent, backtest_agent, risk_agent, timing_agent, report_agent
    ]
    
    tasks = [
        data_task, geopolitical_task, factor_task, strategy_task,
        backtest_task, risk_task, timing_task, final_task
    ]
    
    crew = Crew(
        agents=agents,
        tasks=tasks,
        process=Process.sequential,
        verbose=True
    )
    
    print(f"\n{'='*70}")
    print(f"🚀 A股量化Agent系统 v2.0")
    print(f"   目标：{stock_code} ({stock_name})")
    print(f"   架构：主控 + 8个专业Agent")
    print(f"   流程：数据→地缘→因子→策略→回测→风控→时机→报告")
    print(f"{'='*70}\n")
    
    result = crew.kickoff()
    
    return result


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python3 run_quant_system_v2.py <股票代码> [股票名称]")
        sys.exit(1)
    
    stock_code = sys.argv[1]
    stock_name = sys.argv[2] if len(sys.argv) > 2 else ""
    
    result = analyze_stock_full(stock_code, stock_name)
    
    print("\n" + "="*70)
    print("✅ 分析完成")
    print("="*70)
    print(result)
    
    # 保存报告
    report_dir = Path("/Users/rainday/.openclaw/workspace-mac/reports")
    report_dir.mkdir(parents=True, exist_ok=True)
    
    filename = f"{report_dir}/analysis_{stock_code}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(str(result))
    print(f"\n📄 报告已保存: {filename}")
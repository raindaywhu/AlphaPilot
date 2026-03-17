#!/bin/bash

# AlphaPilot - 批量创建 GitHub Issues
# 使用方法：./create_issues.sh <GITHUB_TOKEN>

if [ -z "$1" ]; then
    echo "错误：请提供 GitHub Token"
    echo "使用方法：./create_issues.sh <GITHUB_TOKEN>"
    exit 1
fi

TOKEN="$1"
REPO="raindaywhu/AlphaPilot"
API_URL="https://api.github.com/repos/$REPO/issues"

# 创建 issue 函数
create_issue() {
    local title="$1"
    local body="$2"
    local labels="$3"
    
    curl -X POST \
        -H "Authorization: token $TOKEN" \
        -H "Accept: application/vnd.github.v3+json" \
        "$API_URL" \
        -d "{\"title\":\"$title\",\"body\":\"$body\",\"labels\":[\"$labels\"]}"
}

echo "开始创建 Issues..."

# Issue 1: DATA-001
create_issue \
    "[DATA-001] qlib 数据更新器" \
    "**子任务 ID**: DATA-001

**描述**: 实现 qlib 数据自动更新机制

**独立可验证性**:
- ✅ 独立开发：不依赖其他模块
- ✅ 独立测试：可以单独测试数据更新功能
- ✅ 独立部署：可以作为独立服务运行

**接口定义**:
\`\`\`python
class QlibDataUpdater:
    def update_daily_data(self) -> bool:
        pass
    
    def get_latest_date(self) -> str:
        pass
    
    def validate_data(self, stock_code: str) -> bool:
        pass
\`\`\`

**验收标准**:
1. 能够自动下载最新日线数据
2. 数据日期为最新交易日
3. 数据格式符合 qlib 要求
4. 支持增量更新

**估计时间**: 2-3 小时

**状态**: 待处理" \
    "data-layer"

echo "Issue [DATA-001] 创建完成"

# Issue 2: DATA-002
create_issue \
    "[DATA-002] mootdx 数据获取器" \
    "**子任务 ID**: DATA-002

**描述**: 使用 mootdx 获取实时行情数据

**独立可验证性**:
- ✅ 独立开发：不依赖其他模块
- ✅ 独立测试：可以单独测试数据获取
- ✅ 独立部署：可以作为独立服务运行

**接口定义**:
\`\`\`python
class MootdxDataFetcher:
    def get_realtime_quote(self, stock_code: str) -> dict:
        pass
    
    def get_kline_data(self, stock_code: str, days: int) -> pd.DataFrame:
        pass
    
    def get_latest_price(self, stock_code: str) -> float:
        pass
\`\`\`

**验收标准**:
1. 能够获取实时行情数据
2. 能够获取历史 K 线数据
3. 数据格式标准化
4. 支持异常处理

**估计时间**: 1-2 小时

**状态**: 待处理" \
    "data-layer"

echo "Issue [DATA-002] 创建完成"

# Issue 3: DATA-003
create_issue \
    "[DATA-003] 数据格式转换器" \
    "**子任务 ID**: DATA-003

**描述**: 将 mootdx 数据转换为 qlib 格式

**独立可验证性**:
- ✅ 独立开发：不依赖其他模块
- ✅ 独立测试：可以单独测试转换功能
- ✅ 独立部署：可以作为独立工具使用

**接口定义**:
\`\`\`python
class DataConverter:
    def convert_to_qlib_format(self, data: pd.DataFrame) -> pd.DataFrame:
        pass
    
    def validate_qlib_format(self, data: pd.DataFrame) -> bool:
        pass
\`\`\`

**验收标准**:
1. 能够转换数据格式
2. 转换后的数据符合 qlib 要求
3. 支持批量转换

**估计时间**: 1 小时

**状态**: 待处理" \
    "data-layer"

echo "Issue [DATA-003] 创建完成"

# Issue 4: TOOL-001
create_issue \
    "[TOOL-001] qlib Alpha158 因子工具" \
    "**子任务 ID**: TOOL-001

**描述**: 获取 Alpha158 因子数据

**独立可验证性**:
- ✅ 独立开发：不依赖其他工具
- ✅ 独立测试：可以单独测试因子获取
- ✅ 独立使用：可以被任何 Agent 调用

**依赖**: DATA-001

**接口定义**:
\`\`\`python
class QlibAlpha158Tool:
    def get_factors(self, stock_code: str) -> dict:
        pass
    
    def get_factor_rank(self, stock_code: str, factor_name: str) -> float:
        pass
\`\`\`

**验收标准**:
1. 能够获取 Alpha158 因子数据
2. 能够计算因子排名
3. 支持数据验证

**估计时间**: 2-3 小时

**状态**: 待处理" \
    "tool-layer"

echo "Issue [TOOL-001] 创建完成"

# Issue 5: TOOL-002
create_issue \
    "[TOOL-002] qlib GBDT 预测工具" \
    "**子任务 ID**: TOOL-002

**描述**: 使用 GBDT 模型预测股票涨跌

**独立可验证性**:
- ✅ 独立开发：不依赖其他工具
- ✅ 独立测试：可以单独测试预测功能
- ✅ 独立使用：可以被任何 Agent 调用

**依赖**: DATA-001

**接口定义**:
\`\`\`python
class QlibGBDTPredictionTool:
    def predict(self, stock_code: str, horizon: int) -> dict:
        pass
    
    def get_confidence(self, stock_code: str) -> float:
        pass
\`\`\`

**验收标准**:
1. 能够预测股票涨跌幅
2. 能够返回置信度
3. 支持多日预测

**估计时间**: 3-4 小时

**状态**: 待处理" \
    "tool-layer"

echo "Issue [TOOL-002] 创建完成"

# Issue 6: TOOL-003
create_issue \
    "[TOOL-003] 技术指标计算工具" \
    "**子任务 ID**: TOOL-003

**描述**: 计算技术指标（MA、MACD、RSI等）

**独立可验证性**:
- ✅ 独立开发：不依赖 qlib
- ✅ 独立测试：可以单独测试指标计算
- ✅ 独立使用：可以被任何 Agent 调用

**依赖**: DATA-002

**接口定义**:
\`\`\`python
class TechnicalIndicatorTool:
    def calculate_ma(self, stock_code: str, periods: list) -> dict:
        pass
    
    def calculate_macd(self, stock_code: str) -> dict:
        pass
    
    def calculate_rsi(self, stock_code: str, period: int) -> float:
        pass
\`\`\`

**验收标准**:
1. 能够计算 MA、MACD、RSI、KDJ 等
2. 支持多周期计算
3. 支持信号识别（金叉、死叉）

**估计时间**: 2-3 小时

**状态**: 待处理" \
    "tool-layer"

echo "Issue [TOOL-003] 创建完成"

# Issue 7: TOOL-004
create_issue \
    "[TOOL-004] 北向资金工具" \
    "**子任务 ID**: TOOL-004

**描述**: 获取北向资金流向数据

**独立可验证性**:
- ✅ 独立开发：不依赖其他工具
- ✅ 独立测试：可以单独测试数据获取
- ✅ 独立使用：可以被任何 Agent 调用

**接口定义**:
\`\`\`python
class NorthMoneyTool:
    def get_net_inflow(self, stock_code: str, days: int) -> pd.DataFrame:
        pass
    
    def get_holding_change(self, stock_code: str) -> float:
        pass
\`\`\`

**验收标准**:
1. 能够获取北向资金净流入
2. 能够获取持仓变化
3. 支持历史数据查询

**估计时间**: 2 小时

**状态**: 待处理" \
    "tool-layer"

echo "Issue [TOOL-004] 创建完成"

# Issue 8: TOOL-005
create_issue \
    "[TOOL-005] 大宗商品价格工具" \
    "**子任务 ID**: TOOL-005

**描述**: 获取大宗商品价格数据

**独立可验证性**:
- ✅ 独立开发：不依赖其他工具
- ✅ 独立测试：可以单独测试价格获取
- ✅ 独立使用：可以被任何 Agent 调用

**接口定义**:
\`\`\`python
class CommodityPriceTool:
    def get_price(self, commodity: str) -> float:
        pass
    
    def get_price_trend(self, commodity: str, days: int) -> dict:
        pass
\`\`\`

**验收标准**:
1. 能够获取大宗商品价格
2. 能够获取价格趋势
3. 支持多种商品（铜、铝、原油、黄金）

**估计时间**: 2 小时

**状态**: 待处理" \
    "tool-layer"

echo "Issue [TOOL-005] 创建完成"

# Issue 9: AGENT-001
create_issue \
    "[AGENT-001] 量化分析师 Agent" \
    "**子任务 ID**: AGENT-001

**描述**: 实现量化分析师 Agent

**独立可验证性**:
- ✅ 独立开发：可以单独开发 Agent 定义
- ✅ 独立测试：可以单独测试 Agent 输出
- ✅ 独立使用：可以单独运行

**依赖**: TOOL-001, TOOL-002, TOOL-003

**验收标准**:
1. 能够分析股票技术面
2. 输出包含评级和逻辑推导
3. 支持数据验证

**估计时间**: 2-3 小时

**状态**: 待处理" \
    "agent-layer"

echo "Issue [AGENT-001] 创建完成"

# Issue 10: AGENT-002
create_issue \
    "[AGENT-002] 宏观分析师 Agent" \
    "**子任务 ID**: AGENT-002

**描述**: 实现宏观分析师 Agent（含地缘政治逻辑推导）

**独立可验证性**:
- ✅ 独立开发：可以单独开发
- ✅ 独立测试：可以单独测试
- ✅ 独立使用：可以单独运行

**验收标准**:
1. 能够分析宏观经济
2. 输出包含地缘政治逻辑推导
3. 支持数据验证

**估计时间**: 2-3 小时

**状态**: 待处理" \
    "agent-layer"

echo "Issue [AGENT-002] 创建完成"

# Issue 11: AGENT-003
create_issue \
    "[AGENT-003] 另类数据分析师 Agent" \
    "**子任务 ID**: AGENT-003

**描述**: 实现另类数据分析师 Agent（含大宗商品逻辑推导）

**独立可验证性**:
- ✅ 独立开发：可以单独开发
- ✅ 独立测试：可以单独测试
- ✅ 独立使用：可以单独运行

**依赖**: TOOL-004, TOOL-005

**验收标准**:
1. 能够分析北向资金、情绪、大宗商品
2. 输出包含大宗商品逻辑推导
3. 支持数据验证

**估计时间**: 2-3 小时

**状态**: 待处理" \
    "agent-layer"

echo "Issue [AGENT-003] 创建完成"

# Issue 12: CREW-001
create_issue \
    "[CREW-001] 投资分析 Crew" \
    "**子任务 ID**: CREW-001

**描述**: 组装所有 Agent，实现投资分析流程

**独立可验证性**:
- ✅ 独立开发：可以单独开发 Crew 组装
- ✅ 独立测试：可以测试整个流程
- ⚠️ 依赖 Agent 层完成

**依赖**: AGENT-001, AGENT-002, AGENT-003

**接口定义**:
\`\`\`python
class InvestmentCrew:
    def analyze(self, stock_code: str) -> dict:
        pass
\`\`\`

**验收标准**:
1. 能够运行完整的分析流程
2. 输出包含所有 Agent 的分析结果
3. 支持并行分析

**估计时间**: 3-4 小时

**状态**: 待处理" \
    "crew-layer"

echo "Issue [CREW-001] 创建完成"

echo "所有 Issues 创建完成！"
echo "请访问 https://github.com/$REPO/issues 查看"
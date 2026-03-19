#!/usr/bin/env python3
"""
另类数据分析师 Agent

分析北向资金、市场情绪、大宗商品等另类数据

Issue: (AGENT-003)
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import re

# 加载 .env 文件
from pathlib import Path
env_file = Path(__file__).parent.parent.parent / ".env"
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            if '=' in line and not line.startswith('#'):
                key, value = line.strip().split('=', 1)
                os.environ.setdefault(key, value)

# 设置环境变量以绕过 CrewAI 的 OPENAI_API_KEY 检查
os.environ.setdefault('OPENAI_API_KEY', 'sk-dummy-key-for-crewai')

from crewai import Agent
from langchain_openai import ChatOpenAI

# 导入统一数据获取模块
from src.tools.data_fetcher import get_fetcher

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AlternativeAnalyst:
    """
    另类数据分析师 Agent

    分析北向资金流向、市场情绪、大宗商品价格等另类数据。
    使用 akshare 获取真实数据，不使用任何 mock 数据。

    使用示例：
        >>> agent = AlternativeAnalyst()
        >>> result = agent.analyze("SH600519")
        >>> print(result)
    """

    def __init__(
        self,
        llm_model: str = "glm-5",
        llm_api_base: str = "https://coding.dashscope.aliyuncs.com/v1",
        llm_api_key: str = os.environ.get("GLM_API_KEY", ""),
        llm_temperature: float = 0.3
    ):
        """
        初始化另类数据分析师 Agent

        Args:
            llm_model: LLM 模型名称
            llm_api_base: LLM API 基础 URL
            llm_api_key: LLM API 密钥
            llm_temperature: LLM 温度参数
        """
        # 初始化 LLM
        self.llm = ChatOpenAI(
            model=llm_model,
            openai_api_base=llm_api_base,
            openai_api_key=llm_api_key,
            temperature=llm_temperature
        )

        # akshare 延迟导入
        self._akshare = None

        # 知识库路径
        self.knowledge_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "knowledge"
        )

        # 加载知识库
        self.knowledge = self._load_knowledge()

        # 创建 CrewAI Agent
        self.agent = self._create_agent()

        logger.info("另类数据分析师 Agent 初始化完成")

    def _get_akshare(self):
        """延迟导入 akshare"""
        if self._akshare is None:
            try:
                import akshare as ak
                self._akshare = ak
            except ImportError:
                raise ImportError("请安装 akshare: pip install akshare")
        return self._akshare

    def _load_knowledge(self) -> Dict[str, str]:
        """
        加载知识库内容

        Returns:
            知识库内容字典
        """
        knowledge = {}

        knowledge_files = {
            "alternative_data": "alternative_data.txt",
            "north_money_analysis": "north_money_analysis.txt",
            "commodity_analysis": "commodity_analysis.txt"
        }

        for name, filename in knowledge_files.items():
            filepath = os.path.join(self.knowledge_dir, filename)
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    knowledge[name] = f.read()
                logger.info(f"已加载知识库: {name}")
            else:
                logger.warning(f"知识库文件不存在: {filepath}")

        return knowledge

    def _create_agent(self) -> Agent:
        """
        创建 CrewAI Agent

        Returns:
            CrewAI Agent 实例
        """
        # 构建背景故事
        backstory = f"""你是一位资深的另类数据分析师，专注于通过非传统数据洞察市场。

你的专长领域：
1. **北向资金分析**：追踪外资流向，识别聪明钱的动向
2. **市场情绪分析**：通过舆情、资金流向等指标判断市场热度
3. **大宗商品分析**：分析铜、铝、原油、黄金等商品价格对股市的影响

你的分析方法论：
- 北向资金连续净流入 → 外资看好，可能预示上涨
- 北向资金大幅流出 → 外资撤离，需警惕风险
- 大宗商品价格上涨 → 相关板块可能受益（如铜涨价利好铜企）
- 市场情绪过热 → 需警惕回调风险

你的知识库内容：
{self.knowledge.get('alternative_data', '暂无')}
{self.knowledge.get('north_money_analysis', '暂无')}
{self.knowledge.get('commodity_analysis', '暂无')}

你的分析原则：
1. 数据驱动：基于真实数据分析，不凭感觉
2. 逻辑严谨：每个结论都有清晰的推导过程
3. 风险提示：及时识别潜在风险
4. 时效性：关注最新数据变化

你善于从另类数据中发现市场信号，为投资决策提供独特视角。"""

        agent = Agent(
            role="资深另类数据分析师",
            goal="通过北向资金、市场情绪、大宗商品等另类数据，提供独特的市场洞察",
            backstory=backstory,
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )

        return agent

    def analyze(
        self,
        stock_code: str,
        north_money_data: Optional[Dict] = None,
        commodity_data: Optional[Dict] = None,
        sentiment_data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        分析另类数据

        注意：不使用任何 mock 数据，所有数据必须从真实 API 获取。

        Args:
            stock_code: 股票代码（如 SH600519）
            north_money_data: 北向资金数据（可选，如不提供则从 API 获取）
            commodity_data: 大宗商品数据（可选，如不提供则从 API 获取）
            sentiment_data: 市场情绪数据（可选，如不提供则从 API 获取）

        Returns:
            分析结果字典，包含：
            - stock_code: 股票代码
            - rating: 评级（1-10分）
            - confidence: 置信度（0-1）
            - logic_derivation: 逻辑推导
            - north_money_analysis: 北向资金分析
            - commodity_analysis: 大宗商品分析
            - sentiment_analysis: 市场情绪分析
            - risk_warning: 风险提示
        """
        logger.info(f"开始分析股票: {stock_code}")

        # 从真实 API 获取数据（不使用 mock）
        if north_money_data is None:
            north_money_data = self._fetch_north_money_data(stock_code)
        if commodity_data is None:
            commodity_data = self._fetch_commodity_data()
        if sentiment_data is None:
            sentiment_data = self._fetch_sentiment_data()

        # 构建分析提示
        prompt = f"""请分析股票 {stock_code} 的另类数据信号。

## 北向资金数据
{json.dumps(north_money_data, ensure_ascii=False, indent=2)}

## 大宗商品数据
{json.dumps(commodity_data, ensure_ascii=False, indent=2)}

## 市场情绪数据
{json.dumps(sentiment_data, ensure_ascii=False, indent=2)}

## 分析要求

请提供：
1. **北向资金分析**（2-3句话）：
   - 资金流向趋势
   - 对股价的影响判断
   - 风险提示

2. **大宗商品分析**（2-3句话）：
   - 主要商品价格走势
   - 对相关行业的影响
   - 投资启示

3. **市场情绪分析**（2-3句话）：
   - 当前市场情绪状态
   - 可能的风险或机会
   - 投资建议

4. **综合评级**（1-10分）：
   - 基于另类数据的综合评分
   - 评分理由

5. **置信度**（0-1）：
   - 分析结论的可信程度

6. **风险提示**：
   - 主要风险点

请以 JSON 格式返回结果，格式如下：
{{
    "rating": 8,
    "confidence": 0.8,
    "logic_derivation": "综合分析逻辑...",
    "north_money_analysis": "北向资金分析...",
    "commodity_analysis": "大宗商品分析...",
    "sentiment_analysis": "市场情绪分析...",
    "risk_warning": "风险提示..."
}}"""

        try:
            # 调用 LLM 进行分析
            response = self.llm.invoke(prompt)
            result_text = response.content

            # 提取 JSON 结果
            result = self._extract_json(result_text)

            # 添加股票代码
            result["stock_code"] = stock_code

            # 确保必要字段存在
            result.setdefault("rating", 5)
            result.setdefault("confidence", 0.5)
            result.setdefault("logic_derivation", "分析中...")
            result.setdefault("north_money_analysis", "数据不足")
            result.setdefault("commodity_analysis", "数据不足")
            result.setdefault("sentiment_analysis", "数据不足")
            result.setdefault("risk_warning", "数据有限，需谨慎决策")
            
            # 添加 overall_rating 和 conclusion 字段（InvestmentCrew 需要）
            rating = result.get("rating", 5)
            if rating >= 8:
                result["overall_rating"] = "看涨"
            elif rating >= 6:
                result["overall_rating"] = "中性偏多"
            elif rating >= 4:
                result["overall_rating"] = "中性"
            elif rating >= 2:
                result["overall_rating"] = "中性偏空"
            else:
                result["overall_rating"] = "看跌"
            
            # 生成结论
            result["conclusion"] = result.get("logic_derivation", "另类数据分析完成")

            logger.info(f"分析完成，评级: {result['rating']}, 置信度: {result['confidence']}")

            return result

        except Exception as e:
            logger.error(f"分析失败: {e}")
            return {
                "stock_code": stock_code,
                "rating": 5,
                "confidence": 0.3,
                "logic_derivation": f"分析失败: {str(e)}",
                "north_money_analysis": "分析失败",
                "commodity_analysis": "分析失败",
                "sentiment_analysis": "分析失败",
                "risk_warning": "分析异常，请重试"
            }

    def _fetch_north_money_data(self, stock_code: str) -> Dict[str, Any]:
        """
        从 akshare 获取北向资金数据

        Args:
            stock_code: 股票代码

        Returns:
            北向资金数据字典
        """
        ak = self._get_akshare()
        
        try:
            # 获取北向资金整体流向
            flow_df = ak.stock_hsgt_fund_flow_summary_em()
            
            # 提取今日北向资金数据
            north_flow = flow_df[flow_df['资金方向'] == '北向']
            
            if len(north_flow) > 0:
                today_data = north_flow.iloc[0]
                
                # 计算净流入
                sh_flow = flow_df[(flow_df['类型'] == '沪港通') & (flow_df['板块'] == '沪股通')]
                sz_flow = flow_df[(flow_df['类型'] == '深港通') & (flow_df['板块'] == '深股通')]
                
                result = {
                    "stock_code": stock_code,
                    "date": str(today_data.get('交易日', '')),
                    "shanghai_net_inflow": 0,
                    "shenzhen_net_inflow": 0,
                    "total_net_inflow": 0,
                    "trend": "未知",
                    "signal": "数据获取中"
                }
                
                # 沪股通净流入
                if len(sh_flow) > 0:
                    # 使用上涨数和下跌数判断资金流向
                    up_count = int(sh_flow.iloc[0].get('上涨数', 0))
                    down_count = int(sh_flow.iloc[0].get('下跌数', 0))
                    result["shanghai_net_inflow"] = up_count - down_count
                
                # 深股通净流入
                if len(sz_flow) > 0:
                    up_count = int(sz_flow.iloc[0].get('上涨数', 0))
                    down_count = int(sz_flow.iloc[0].get('下跌数', 0))
                    result["shenzhen_net_inflow"] = up_count - down_count
                
                # 总净流入
                result["total_net_inflow"] = result["shanghai_net_inflow"] + result["shenzhen_net_inflow"]
                
                # 判断趋势
                if result["total_net_inflow"] > 100:
                    result["trend"] = "净流入"
                    result["signal"] = "外资看好"
                elif result["total_net_inflow"] < -100:
                    result["trend"] = "净流出"
                    result["signal"] = "外资撤离"
                else:
                    result["trend"] = "平衡"
                    result["signal"] = "观望"
                
                return result
            
        except Exception as e:
            logger.error(f"获取北向资金数据失败: {e}")
        
        return {
            "stock_code": stock_code,
            "error": "无法获取北向资金数据",
            "trend": "未知",
            "signal": "数据获取失败"
        }

    def _fetch_commodity_data(self) -> Dict[str, Any]:
        """
        获取大宗商品数据（使用 akshare futures_main_sina 获取主力合约数据）

        Returns:
            大宗商品数据字典
        """
        import os
        # 禁用代理
        old_proxy = {}
        for key in ['http_proxy', 'https_proxy', 'HTTP_PROXY', 'HTTPS_PROXY', 'all_proxy', 'ALL_PROXY']:
            old_proxy[key] = os.environ.get(key)
            if key in os.environ:
                del os.environ[key]
        
        try:
            ak = self._get_akshare()
            
            result = {}
            commodities = {
                "铜": "CU0",
                "铝": "AL0",
                "原油": "SC0",
                "黄金": "AU0",
            }
            
            for name, code in commodities.items():
                try:
                    # 使用 futures_main_sina 获取主力合约历史数据
                    df = ak.futures_main_sina(symbol=code)
                    if df is not None and len(df) >= 2:
                        latest = df.iloc[-1]
                        prev = df.iloc[-2]
                        close = float(latest['收盘价'])
                        prev_close = float(prev['收盘价'])
                        change_pct = round((close - prev_close) / prev_close * 100, 2)
                        
                        result[name] = {
                            "code": code,
                            "price": close,
                            "change_pct": change_pct,
                            "date": str(latest['日期'])
                        }
                        logger.info(f"获取{name}数据成功: {close} ({change_pct}%)")
                except Exception as e:
                    logger.warning(f"获取{name}数据失败: {e}")
            
            # 恢复代理
            for key, value in old_proxy.items():
                if value:
                    os.environ[key] = value
            
            if result:
                return {
                    "source": "akshare_sina",
                    "data": result,
                    "note": "期货主力合约数据"
                }
        except Exception as e:
            logger.error(f"大宗商品数据获取失败: {e}")
        
        # 恢复代理
        for key, value in old_proxy.items():
            if value:
                os.environ[key] = value
        
        # 回退：返回分析框架
        return {
            "source": "analysis_framework",
            "note": "期货实时数据暂不可用，以下为分析框架",
            "key_commodities": {
                "铜": {
                    "impact_sectors": ["电力设备", "家电", "汽车", "电子"],
                    "price_trend": "关注 LME 铜价和沪铜主力合约",
                    "investment_logic": "铜价上涨利好铜矿企业，利空高耗铜企业"
                },
                "铝": {
                    "impact_sectors": ["建筑", "汽车", "包装", "电力"],
                    "price_trend": "关注沪铝主力合约和 LME 铝价",
                    "investment_logic": "铝价上涨利好电解铝企业，关注成本端"
                },
                "钢铁": {
                    "impact_sectors": ["建筑", "机械", "汽车", "家电"],
                    "price_trend": "关注螺纹钢、热卷期货价格",
                    "investment_logic": "钢价上涨利好钢企，关注铁矿石成本"
                },
                "原油": {
                    "impact_sectors": ["化工", "交运", "航空", "航运"],
                    "price_trend": "关注布伦特、WTI 原油价格",
                    "investment_logic": "油价上涨利好油企，利空航空物流"
                },
                "黄金": {
                    "impact_sectors": ["黄金开采", "珠宝", "投资"],
                    "price_trend": "关注 COMEX 黄金、沪金主力",
                    "investment_logic": "金价上涨利好黄金股，避险情绪指标"
                }
            },
            "analysis_tips": [
                "1. 判断目标股票所属行业对哪些大宗商品敏感",
                "2. 评估大宗商品价格趋势（上涨/下跌/震荡）",
                "3. 分析成本端和收入端的双重影响",
                "4. 考虑企业的定价能力和成本转嫁能力"
            ],
            "data_sources_recommend": [
                "东方财富期货频道: https://quote.eastmoney.com/center/qihuo.html",
                "新浪财经期货: https://finance.sina.com.cn/futuremarket/",
                "金十数据: https://www.jin10.com/"
            ]
        }

    def _fetch_sentiment_data(self) -> Dict[str, Any]:
        """
        从腾讯财经获取市场情绪数据（替代失败的 akshare 东方财富接口）

        Returns:
            市场情绪数据字典
        """
        import requests
        
        result = {
            "market_sentiment": "中性",
            "indices": {},
            "data_source": "tencent"
        }
        
        # 临时禁用代理
        import os
        old_proxy = {}
        for key in ['http_proxy', 'https_proxy', 'HTTP_PROXY', 'HTTPS_PROXY', 'all_proxy', 'ALL_PROXY']:
            old_proxy[key] = os.environ.get(key)
            if key in os.environ:
                del os.environ[key]
        
        try:
            # 腾讯财经指数接口
            indices_map = {
                "上证指数": "sh000001",
                "深证成指": "sz399001", 
                "创业板指": "sz399006"
            }
            
            codes = list(indices_map.values())
            url = f"http://qt.gtimg.cn/q={','.join(codes)}"
            
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                lines = resp.text.strip().split('\n')
                for line in lines:
                    if '~' not in line:
                        continue
                    parts = line.split('~')
                    if len(parts) >= 33:
                        # 解析代码
                        code_part = parts[0].split('=')[0].replace('v_', '')
                        # 找到对应的指数名称
                        for name, tc in indices_map.items():
                            if tc in code_part.lower():
                                current = float(parts[3])
                                change = float(parts[31])
                                pct = float(parts[32])
                                result["indices"][name] = {
                                    "price": current,
                                    "change": change,
                                    "change_pct": round(pct, 2)
                                }
                                break
            
            # 计算市场情绪
            if result["indices"]:
                total_pct = sum(v.get("change_pct", 0) for v in result["indices"].values())
                avg_change = total_pct / len(result["indices"])
                
                if avg_change > 1.0:
                    result["market_sentiment"] = "偏乐观"
                elif avg_change < -1.0:
                    result["market_sentiment"] = "偏悲观"
                else:
                    result["market_sentiment"] = "中性"
                
                result["avg_change_pct"] = round(avg_change, 2)
                logger.info(f"成功获取市场情绪数据: {result['market_sentiment']}, 平均涨幅: {avg_change:.2f}%")
            else:
                result["error"] = "未能获取指数数据"
                result["market_sentiment"] = "未知"
                
        except Exception as e:
            logger.error(f"获取市场情绪数据失败: {e}")
            result["error"] = str(e)
            result["market_sentiment"] = "未知"
        
        # 恢复代理设置
        for key, value in old_proxy.items():
            if value:
                os.environ[key] = value
        
        return result

    def _extract_json(self, text: str) -> Dict[str, Any]:
        """
        从文本中提取 JSON

        Args:
            text: 包含 JSON 的文本

        Returns:
            解析后的字典
        """
        # 尝试直接解析
        try:
            return json.loads(text)
        except:
            pass

        # 尝试提取 JSON 块
        json_pattern = r'\{[^{}]*\}'
        matches = re.findall(json_pattern, text, re.DOTALL)
        
        for match in matches:
            try:
                return json.loads(match)
            except:
                continue

        # 尝试提取 ```json ... ``` 格式
        json_block_pattern = r'```json\s*(\{.*?\})\s*```'
        matches = re.findall(json_block_pattern, text, re.DOTALL)
        
        for match in matches:
            try:
                return json.loads(match)
            except:
                continue

        logger.warning("无法提取有效 JSON，返回默认值")
        return {}

    def get_agent(self) -> Agent:
        """
        获取 CrewAI Agent 实例

        Returns:
            CrewAI Agent
        """
        return self.agent


# 主函数用于测试
if __name__ == "__main__":
    # 创建 Agent
    analyst = AlternativeAnalyst()
    
    # 测试分析（使用真实 API）
    result = analyst.analyze("SH600519")
    
    print("\n" + "=" * 60)
    print("另类数据分析结果")
    print("=" * 60)
    print(json.dumps(result, ensure_ascii=False, indent=2))
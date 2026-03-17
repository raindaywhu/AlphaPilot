#!/usr/bin/env python3
"""
大宗商品价格工具

获取大宗商品价格数据

Issue: #11 (TOOL-005)
"""

import logging
from typing import Optional, Dict, List, Any
from datetime import datetime, timedelta

import pandas as pd
import numpy as np

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# 支持的大宗商品类型
COMMODITY_MAPPING = {
    # 贵金属
    'gold': {'name': '黄金', 'akshare_func': 'fx_spot_quote', 'symbol': 'XAUUSD'},
    'silver': {'name': '白银', 'akshare_func': 'fx_spot_quote', 'symbol': 'XAGUSD'},
    # 能源
    'crude_oil': {'name': '原油', 'akshare_func': 'energy_oil_hist', 'symbol': 'SC'},
    'brent': {'name': '布伦特原油', 'akshare_func': 'fx_spot_quote', 'symbol': 'BRENT'},
    'wti': {'name': 'WTI原油', 'akshare_func': 'fx_spot_quote', 'symbol': 'WTI'},
    # 基本金属
    'copper': {'name': '铜', 'akshare_func': 'fx_spot_quote', 'symbol': 'XCUUSD'},
    'aluminum': {'name': '铝', 'akshare_func': 'fx_spot_quote', 'symbol': 'XALUSD'},
    # 农产品
    'soybean': {'name': '大豆', 'akshare_func': 'fx_spot_quote', 'symbol': 'SOYBEAN'},
    'corn': {'name': '玉米', 'akshare_func': 'fx_spot_quote', 'symbol': 'CORN'},
    'wheat': {'name': '小麦', 'akshare_func': 'fx_spot_quote', 'symbol': 'WHEAT'},
    # 其他
    'natural_gas': {'name': '天然气', 'akshare_func': 'fx_spot_quote', 'symbol': 'NATGAS'},
}


class CommodityPriceTool:
    """
    大宗商品价格工具

    获取大宗商品的价格和价格趋势数据。

    使用示例：
        >>> tool = CommodityPriceTool()
        >>> price = tool.get_price('gold')
        >>> print(f"黄金价格: {price}")
        >>> trend = tool.get_price_trend('gold', days=30)
        >>> print(trend)
    """

    def __init__(self):
        """初始化大宗商品价格工具"""
        self._ak = None
        self._initialized = False
        self._price_cache = {}

    def _ensure_initialized(self):
        """确保 akshare 已初始化"""
        if not self._initialized:
            try:
                import akshare as ak
                self._ak = ak
                self._initialized = True
                logger.info("大宗商品价格工具初始化成功")
            except ImportError:
                logger.error("akshare 未安装，请运行: pip install akshare")
                raise

    def _normalize_commodity(self, commodity: str) -> str:
        """
        标准化大宗商品名称

        Args:
            commodity: 大宗商品名称，如 'gold', '黄金', 'XAUUSD'

        Returns:
            标准化后的商品键名，如 'gold'
        """
        commodity = commodity.lower().strip()
        
        # 直接匹配
        if commodity in COMMODITY_MAPPING:
            return commodity
        
        # 中文名称匹配
        for key, info in COMMODITY_MAPPING.items():
            if info['name'] == commodity or info['symbol'].lower() == commodity:
                return key
        
        # 默认返回原值（会在后续处理中报错）
        return commodity

    def get_supported_commodities(self) -> List[str]:
        """
        获取支持的大宗商品列表

        Returns:
            支持的商品名称列表
        """
        return list(COMMODITY_MAPPING.keys())

    def get_price(self, commodity: str) -> float:
        """
        获取大宗商品的当前价格

        Args:
            commodity: 大宗商品名称，如 'gold', 'crude_oil', 'copper'

        Returns:
            当前价格（美元/盎司 或 美元/桶），获取失败返回 0.0
        """
        self._ensure_initialized()

        # 标准化商品名称
        key = self._normalize_commodity(commodity)
        
        if key not in COMMODITY_MAPPING:
            logger.warning(f"不支持的商品类型: {commodity}，支持的商品: {list(COMMODITY_MAPPING.keys())}")
            return 0.0

        commodity_info = COMMODITY_MAPPING[key]
        
        try:
            # 使用 akshare 获取外汇/大宗商品现货报价
            df = self._ak.fx_spot_quote()
            
            if df is None or df.empty:
                logger.warning(f"未获取到大宗商品报价数据")
                return 0.0

            # 查找目标商品
            symbol = commodity_info['symbol']
            
            # 尝试在 DataFrame 中查找
            for col in ['symbol', '代码', '品种']:
                if col in df.columns:
                    match = df[df[col].str.contains(symbol, case=False, na=False)]
                    if not match.empty:
                        # 获取最新价格
                        price_col = None
                        for pc in ['price', '最新价', '当前价', 'last']:
                            if pc in match.columns:
                                price_col = pc
                                break
                        
                        if price_col:
                            price = float(match.iloc[0][price_col])
                            logger.info(f"获取到 {commodity_info['name']}({symbol}) 价格: {price}")
                            return price

            # 如果没有找到，尝试使用其他方法
            logger.warning(f"在报价数据中未找到 {symbol}，尝试备用方法")
            return self._get_price_fallback(key)

        except Exception as e:
            logger.error(f"获取大宗商品价格失败: {e}")
            return self._get_price_fallback(key)

    def _get_price_fallback(self, commodity_key: str) -> float:
        """
        备用价格获取方法

        Args:
            commodity_key: 商品键名

        Returns:
            价格，失败返回 0.0
        """
        try:
            commodity_info = COMMODITY_MAPPING[commodity_key]
            
            # 尝试使用 futures 主力合约数据
            if commodity_key == 'crude_oil':
                try:
                    # 获取原油期货数据
                    df = self._ak.energy_oil_hist(symbol="SC")
                    if df is not None and not df.empty:
                        # 获取最新收盘价
                        latest = df.sort_values('日期', ascending=False).iloc[0]
                        price = float(latest['收盘价'])
                        logger.info(f"获取到原油期货价格: {price}")
                        return price
                except Exception as e:
                    logger.warning(f"备用方法获取原油价格失败: {e}")
            
            # 尝试使用商品期货数据
            futures_mapping = {
                'gold': 'AU',
                'silver': 'AG',
                'copper': 'CU',
                'aluminum': 'AL',
                'crude_oil': 'SC',
            }
            
            if commodity_key in futures_mapping:
                try:
                    # 获取商品期货行情
                    df = self._ak.futures_main_sina(symbol=futures_mapping[commodity_key])
                    if df is not None and not df.empty:
                        latest = df.iloc[0]
                        # 尝试获取最新价
                        for col in ['最新价', 'close', 'price']:
                            if col in latest.index or col in df.columns:
                                price = float(latest.get(col, 0) if hasattr(latest, 'get') else latest[col])
                                if price > 0:
                                    logger.info(f"获取到 {commodity_info['name']} 期货价格: {price}")
                                    return price
                except Exception as e:
                    logger.warning(f"备用方法获取期货价格失败: {e}")

            logger.warning(f"无法获取 {commodity_info['name']} 的价格")
            return 0.0

        except Exception as e:
            logger.error(f"备用价格获取失败: {e}")
            return 0.0

    def get_price_trend(
        self,
        commodity: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        获取大宗商品的价格趋势

        Args:
            commodity: 大宗商品名称，如 'gold', 'crude_oil', 'copper'
            days: 获取最近多少天的数据，默认 30 天

        Returns:
            字典，包含以下字段：
            - commodity: 商品名称
            - current_price: 当前价格
            - price_change: 价格变化
            - price_change_pct: 价格变化百分比
            - high_price: 最高价
            - low_price: 最低价
            - avg_price: 平均价
            - trend: 趋势方向 ('up', 'down', 'flat')
            - data: 历史价格数据 (DataFrame)
        """
        self._ensure_initialized()

        # 标准化商品名称
        key = self._normalize_commodity(commodity)
        
        if key not in COMMODITY_MAPPING:
            return {
                'commodity': commodity,
                'status': 'error',
                'message': f"不支持的商品类型: {commodity}"
            }

        commodity_info = COMMODITY_MAPPING[key]
        
        try:
            # 尝试获取历史数据
            df = self._get_historical_data(key, days)
            
            if df is None or df.empty:
                return {
                    'commodity': commodity_info['name'],
                    'status': 'no_data',
                    'message': '未获取到历史价格数据'
                }

            # 计算趋势统计
            if len(df) >= 2:
                current_price = float(df.iloc[-1]['close'])
                start_price = float(df.iloc[0]['close'])
                price_change = current_price - start_price
                price_change_pct = (price_change / start_price * 100) if start_price > 0 else 0
                high_price = float(df['close'].max())
                low_price = float(df['close'].min())
                avg_price = float(df['close'].mean())
                
                # 判断趋势
                if price_change_pct > 2:
                    trend = 'up'
                elif price_change_pct < -2:
                    trend = 'down'
                else:
                    trend = 'flat'
            else:
                current_price = float(df.iloc[0]['close'])
                price_change = 0
                price_change_pct = 0
                high_price = current_price
                low_price = current_price
                avg_price = current_price
                trend = 'flat'

            result = {
                'commodity': commodity_info['name'],
                'commodity_key': key,
                'status': 'success',
                'current_price': round(current_price, 2),
                'price_change': round(price_change, 2),
                'price_change_pct': round(price_change_pct, 2),
                'high_price': round(high_price, 2),
                'low_price': round(low_price, 2),
                'avg_price': round(avg_price, 2),
                'trend': trend,
                'days': days,
                'data_points': len(df),
                'data': df.to_dict('records')[:10]  # 只返回最近10条数据
            }

            logger.info(f"获取到 {commodity_info['name']} 最近 {days} 天价格趋势")
            return result

        except Exception as e:
            logger.error(f"获取价格趋势失败: {e}")
            return {
                'commodity': commodity_info['name'],
                'status': 'error',
                'message': str(e)
            }

    def _get_historical_data(self, commodity_key: str, days: int) -> Optional[pd.DataFrame]:
        """
        获取历史价格数据

        Args:
            commodity_key: 商品键名
            days: 天数

        Returns:
            DataFrame，包含日期和收盘价
        """
        try:
            commodity_info = COMMODITY_MAPPING[commodity_key]
            
            # 计算日期范围
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # 期货合约映射
            futures_mapping = {
                'gold': 'AU',
                'silver': 'AG',
                'copper': 'CU',
                'aluminum': 'AL',
                'crude_oil': 'SC',
                'natural_gas': 'NG',
            }
            
            if commodity_key in futures_mapping:
                try:
                    # 获取商品期货主力合约历史数据
                    df = self._ak.futures_main_sina(
                        symbol=futures_mapping[commodity_key],
                        start_date=start_date.strftime('%Y%m%d'),
                        end_date=end_date.strftime('%Y%m%d')
                    )
                    
                    if df is not None and not df.empty:
                        # 标准化列名
                        df = df.rename(columns={
                            'date': 'date',
                            'open': 'open',
                            'high': 'high',
                            'low': 'low',
                            'close': 'close',
                            'volume': 'volume',
                        })
                        
                        # 确保有日期列
                        if 'date' not in df.columns:
                            if '日期' in df.columns:
                                df = df.rename(columns={'日期': 'date'})
                        
                        # 确保有收盘价列
                        if 'close' not in df.columns:
                            for col in ['收盘价', 'close', '收盘']:
                                if col in df.columns:
                                    df = df.rename(columns={col: 'close'})
                                    break
                        
                        # 确保日期格式正确
                        df['date'] = pd.to_datetime(df['date'])
                        df = df.sort_values('date')
                        
                        logger.info(f"获取到 {len(df)} 条历史数据")
                        return df[['date', 'close']].copy()
                        
                except Exception as e:
                    logger.warning(f"获取期货历史数据失败: {e}")
            
            # 尝试使用外汇历史数据
            try:
                symbol = commodity_info['symbol']
                # 使用外汇历史数据
                df = self._ak.fx_spot_quote()
                if df is not None and not df.empty:
                    # 由于现货报价没有历史数据，返回模拟数据用于演示
                    logger.warning("现货报价不支持历史数据，返回当前价格")
                    current_price = self.get_price(commodity_key)
                    if current_price > 0:
                        # 创建单条数据
                        return pd.DataFrame({
                            'date': [datetime.now()],
                            'close': [current_price]
                        })
            except Exception as e:
                logger.warning(f"获取外汇数据失败: {e}")
            
            return None

        except Exception as e:
            logger.error(f"获取历史数据失败: {e}")
            return None

    def get_summary(self, commodity: str) -> Dict[str, Any]:
        """
        获取大宗商品摘要信息

        Args:
            commodity: 大宗商品名称

        Returns:
            摘要信息字典
        """
        self._ensure_initialized()

        key = self._normalize_commodity(commodity)
        
        if key not in COMMODITY_MAPPING:
            return {
                'commodity': commodity,
                'status': 'error',
                'message': f"不支持的商品类型: {commodity}"
            }

        commodity_info = COMMODITY_MAPPING[key]
        current_price = self.get_price(key)
        trend_7d = self.get_price_trend(key, days=7)
        trend_30d = self.get_price_trend(key, days=30)

        return {
            'commodity': commodity_info['name'],
            'commodity_key': key,
            'symbol': commodity_info['symbol'],
            'current_price': current_price,
            'trend_7d': trend_7d.get('trend', 'unknown'),
            'price_change_7d': trend_7d.get('price_change_pct', 0),
            'trend_30d': trend_30d.get('trend', 'unknown'),
            'price_change_30d': trend_30d.get('price_change_pct', 0),
            'status': 'success'
        }

    def get_multiple_prices(self, commodities: List[str]) -> Dict[str, float]:
        """
        批量获取多个大宗商品的价格

        Args:
            commodities: 商品名称列表

        Returns:
            字典，键为商品名，值为价格
        """
        result = {}
        for commodity in commodities:
            try:
                price = self.get_price(commodity)
                key = self._normalize_commodity(commodity)
                result[key] = price
            except Exception as e:
                logger.error(f"获取 {commodity} 价格失败: {e}")
                result[commodity] = 0.0
        
        return result


# 供测试使用
if __name__ == '__main__':
    tool = CommodityPriceTool()
    
    # 测试获取支持的商品列表
    print("=" * 50)
    print("支持的大宗商品:")
    for key, info in COMMODITY_MAPPING.items():
        print(f"  {key}: {info['name']} ({info['symbol']})")
    
    # 测试获取价格
    print("\n" + "=" * 50)
    print("测试获取大宗商品价格")
    for commodity in ['gold', 'crude_oil', 'copper']:
        price = tool.get_price(commodity)
        print(f"{commodity}: {price}")
    
    # 测试获取价格趋势
    print("\n" + "=" * 50)
    print("测试获取价格趋势")
    trend = tool.get_price_trend('gold', days=30)
    for key, value in trend.items():
        if key != 'data':
            print(f"{key}: {value}")
    
    # 测试获取摘要
    print("\n" + "=" * 50)
    print("测试获取摘要")
    summary = tool.get_summary('gold')
    for key, value in summary.items():
        print(f"{key}: {value}")
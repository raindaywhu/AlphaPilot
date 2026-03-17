"""
mootdx 数据获取器

使用 mootdx 获取实时行情数据和历史 K 线数据。

任务ID: DATA-002
类型: 开发任务
优先级: P1
层级: data-layer
"""

import re
from datetime import datetime, timedelta
from typing import Optional, Dict, List

import pandas as pd

try:
    from mootdx.quotes import Quotes
    MOOTDX_AVAILABLE = True
except ImportError:
    MOOTDX_AVAILABLE = False
    print("警告: mootdx 未安装，实时数据功能将不可用")


class MootdxDataFetcher:
    """
    mootdx 数据获取器
    
    功能：
    1. 获取实时行情数据
    2. 获取历史 K 线数据
    3. 数据格式标准化
    4. 支持异常处理
    
    使用示例：
        fetcher = MootdxDataFetcher()
        quote = fetcher.get_realtime_quote("sh600519")
        kline = fetcher.get_kline_data("sh600519", 30)
        price = fetcher.get_latest_price("sh600519")
    """
    
    def __init__(self, market: str = 'std'):
        """
        初始化 mootdx 数据获取器
        
        Args:
            market: 市场类型
                - 'std': 标准市场（通达信）
                - 'ext': 扩展市场
        """
        if not MOOTDX_AVAILABLE:
            raise ImportError("mootdx 未安装，请运行: pip install mootdx")
        
        self.quotes = Quotes.factory(market=market)
        self._stock_code_cache = {}  # 缓存股票代码转换
    
    def _normalize_stock_code(self, stock_code: str) -> str:
        """
        标准化股票代码
        
        将 sh600519, sz000001 等格式转换为 mootdx 需要的格式
        
        Args:
            stock_code: 股票代码，支持格式：
                - sh600519 (标准格式)
                - 600519 (不带前缀)
                - 000001 (深圳)
        
        Returns:
            str: 标准化后的股票代码
        """
        # 如果在缓存中，直接返回
        if stock_code in self._stock_code_cache:
            return self._stock_code_cache[stock_code]
        
        # 去除前后空格
        code = stock_code.strip().lower()
        
        # 提取数字部分
        numbers = re.findall(r'\d+', code)
        if not numbers:
            raise ValueError(f"无效的股票代码: {stock_code}")
        
        code_num = numbers[0]
        
        # 根据前缀或代码规则判断市场
        if code.startswith('sh') or code_num.startswith(('60', '68')):
            # 上海市场
            result = f"sh{code_num}"
        elif code.startswith('sz') or code_num.startswith(('00', '30')):
            # 深圳市场
            result = f"sz{code_num}"
        else:
            # 默认根据代码规则判断
            if code_num.startswith('6'):
                result = f"sh{code_num}"
            else:
                result = f"sz{code_num}"
        
        # 缓存结果
        self._stock_code_cache[stock_code] = result
        return result
    
    def _get_market_code(self, stock_code: str) -> tuple:
        """
        获取市场代码
        
        Args:
            stock_code: 标准化后的股票代码 (如 sh600519)
        
        Returns:
            tuple: (市场代码, 纯数字代码)
                - 市场代码: 0=深圳, 1=上海
        """
        code = stock_code.lower()
        if code.startswith('sh'):
            return (1, code[2:])  # 上海
        elif code.startswith('sz'):
            return (0, code[2:])  # 深圳
        else:
            raise ValueError(f"无效的股票代码格式: {stock_code}")
    
    def get_realtime_quote(self, stock_code: str) -> Dict:
        """
        获取实时行情
        
        Args:
            stock_code: 股票代码，支持格式：
                - sh600519 (标准格式)
                - 600519 (不带前缀)
                - 000001 (深圳)
        
        Returns:
            dict: 实时行情数据，包含字段：
                - code: 股票代码
                - name: 股票名称
                - price: 当前价格
                - open: 开盘价
                - high: 最高价
                - low: 最低价
                - pre_close: 昨收价
                - volume: 成交量（手）
                - amount: 成交额（元）
                - bid_price: 买一价
                - ask_price: 卖一价
                - change_pct: 涨跌幅（%）
                - change: 涨跌额
                - timestamp: 时间戳
        
        Raises:
            ValueError: 股票代码格式错误
            Exception: 数据获取失败
        """
        try:
            # 标准化股票代码
            normalized_code = self._normalize_stock_code(stock_code)
            market, code = self._get_market_code(normalized_code)
            
            # 获取实时行情
            df = self.quotes.quotes(symbol=[code])
            
            if df is None or df.empty:
                raise Exception(f"无法获取股票 {stock_code} 的实时行情")
            
            # 解析数据
            row = df.iloc[0]
            
            # 计算涨跌幅和涨跌额
            price = float(row.get('price', 0))
            pre_close = float(row.get('last_close', 0))
            
            if pre_close > 0:
                change = price - pre_close
                change_pct = (change / pre_close) * 100
            else:
                change = 0
                change_pct = 0
            
            result = {
                'code': normalized_code,
                'name': row.get('name', ''),
                'price': price,
                'open': float(row.get('open', 0)),
                'high': float(row.get('high', 0)),
                'low': float(row.get('low', 0)),
                'pre_close': pre_close,
                'volume': int(row.get('vol', 0)),  # 成交量（手）
                'amount': float(row.get('amount', 0)),  # 成交额（元）
                'bid_price': float(row.get('bid1', 0)),  # 买一价
                'ask_price': float(row.get('ask1', 0)),  # 卖一价
                'change_pct': round(change_pct, 2),
                'change': round(change, 2),
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            return result
            
        except Exception as e:
            raise Exception(f"获取实时行情失败: {str(e)}")
    
    def get_kline_data(self, stock_code: str, days: int = 30, 
                       start_date: Optional[str] = None,
                       end_date: Optional[str] = None) -> pd.DataFrame:
        """
        获取 K 线数据
        
        Args:
            stock_code: 股票代码
            days: 获取天数（默认30天），与 start_date/end_date 二选一
            start_date: 开始日期 (格式: YYYY-MM-DD)
            end_date: 结束日期 (格式: YYYY-MM-DD)
        
        Returns:
            pd.DataFrame: K线数据，包含列：
                - date: 日期
                - open: 开盘价
                - high: 最高价
                - low: 最低价
                - close: 收盘价
                - volume: 成交量（手）
                - amount: 成交额（元）
        
        Raises:
            ValueError: 参数错误
            Exception: 数据获取失败
        """
        try:
            # 标准化股票代码
            normalized_code = self._normalize_stock_code(stock_code)
            market, code = self._get_market_code(normalized_code)
            
            # 确定查询参数
            if start_date and end_date:
                # 使用日期范围
                start = datetime.strptime(start_date, '%Y-%m-%d')
                end = datetime.strptime(end_date, '%Y-%m-%d')
            elif days > 0:
                # 使用天数
                end = datetime.now()
                start = end - timedelta(days=days * 2)  # 多获取一些数据以应对非交易日
            else:
                raise ValueError("必须指定 days 或 start_date/end_date")
            
            # 获取 K 线数据
            df = self.quotes.bars(
                symbol=code,
                offset=0,
                count=days * 2 if days > 0 else 500  # 获取足够的数据
            )
            
            if df is None or df.empty:
                raise Exception(f"无法获取股票 {stock_code} 的K线数据")
            
            # 标准化列名
            df = df.rename(columns={
                'datetime': 'date',
                'open': 'open',
                'high': 'high',
                'low': 'low',
                'close': 'close',
                'vol': 'volume',
                'amount': 'amount'
            })
            
            # 确保日期格式
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'])
            
            # 按日期过滤（如果指定了日期范围）
            if start_date and end_date:
                df = df[(df['date'] >= start) & (df['date'] <= end)]
            elif days > 0:
                # 取最近 days 天的数据
                df = df.tail(days)
            
            # 重置索引
            df = df.reset_index(drop=True)
            
            # 添加股票代码列
            df['code'] = normalized_code
            
            return df
            
        except Exception as e:
            raise Exception(f"获取K线数据失败: {str(e)}")
    
    def get_latest_price(self, stock_code: str) -> float:
        """
        获取最新价格
        
        Args:
            stock_code: 股票代码
        
        Returns:
            float: 最新价格
        
        Raises:
            Exception: 数据获取失败
        """
        try:
            quote = self.get_realtime_quote(stock_code)
            return quote['price']
        except Exception as e:
            raise Exception(f"获取最新价格失败: {str(e)}")
    
    def get_stock_list(self, market: str = 'all') -> pd.DataFrame:
        """
        获取股票列表
        
        Args:
            market: 市场类型
                - 'all': 全部
                - 'sh': 上海
                - 'sz': 深圳
        
        Returns:
            pd.DataFrame: 股票列表，包含列：
                - code: 股票代码
                - name: 股票名称
        """
        try:
            stocks = []
            
            if market in ['all', 'sh']:
                # 获取上海股票
                sh_stocks = self.quotes.stocks(market=1)
                if sh_stocks is not None and not sh_stocks.empty:
                    sh_stocks['code'] = 'sh' + sh_stocks['code'].astype(str)
                    stocks.append(sh_stocks)
            
            if market in ['all', 'sz']:
                # 获取深圳股票
                sz_stocks = self.quotes.stocks(market=0)
                if sz_stocks is not None and not sz_stocks.empty:
                    sz_stocks['code'] = 'sz' + sz_stocks['code'].astype(str)
                    stocks.append(sz_stocks)
            
            if stocks:
                result = pd.concat(stocks, ignore_index=True)
                return result[['code', 'name']]
            else:
                return pd.DataFrame(columns=['code', 'name'])
                
        except Exception as e:
            raise Exception(f"获取股票列表失败: {str(e)}")
    
    def get_index_kline(self, index_code: str, days: int = 30) -> pd.DataFrame:
        """
        获取指数 K 线数据
        
        Args:
            index_code: 指数代码
                - sh000001: 上证指数
                - sz399001: 深证成指
                - sz399006: 创业板指
            days: 获取天数
        
        Returns:
            pd.DataFrame: 指数K线数据
        """
        try:
            # 标准化指数代码
            normalized_code = self._normalize_stock_code(index_code)
            market, code = self._get_market_code(normalized_code)
            
            # 获取指数 K 线
            df = self.quotes.index_bars(
                symbol=code,
                offset=0,
                count=days * 2
            )
            
            if df is None or df.empty:
                raise Exception(f"无法获取指数 {index_code} 的K线数据")
            
            # 标准化列名
            df = df.rename(columns={
                'datetime': 'date',
                'vol': 'volume'
            })
            
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'])
            
            df = df.tail(days).reset_index(drop=True)
            df['code'] = normalized_code
            
            return df
            
        except Exception as e:
            raise Exception(f"获取指数K线数据失败: {str(e)}")


# 便捷函数
def get_quote(stock_code: str) -> Dict:
    """获取实时行情（便捷函数）"""
    fetcher = MootdxDataFetcher()
    return fetcher.get_realtime_quote(stock_code)


def get_kline(stock_code: str, days: int = 30) -> pd.DataFrame:
    """获取 K 线数据（便捷函数）"""
    fetcher = MootdxDataFetcher()
    return fetcher.get_kline_data(stock_code, days)


def get_price(stock_code: str) -> float:
    """获取最新价格（便捷函数）"""
    fetcher = MootdxDataFetcher()
    return fetcher.get_latest_price(stock_code)
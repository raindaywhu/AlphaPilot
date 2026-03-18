"""
股票名称查询工具

支持股票名称 → 股票代码的查询，支持模糊匹配。

使用场景：
1. Web UI 用户输入股票名称（如"贵州茅台"）
2. 自动转换为股票代码（如"600519"）
3. 支持简称模糊匹配（如"茅台"也能识别）

数据源：mootdx 股票列表
"""

import os
import logging
import pandas as pd
from typing import Dict, Any, Optional, List, Tuple
from difflib import get_close_matches

# 禁用代理
os.environ['http_proxy'] = ''
os.environ['https_proxy'] = ''

from mootdx.quotes import Quotes

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StockNameQueryTool:
    """
    股票名称查询工具
    
    支持股票名称 → 股票代码的查询
    支持模糊匹配
    """
    
    _instance = None
    _stock_list = None
    
    def __new__(cls):
        """单例模式，避免重复获取股票列表"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """初始化工具"""
        if self._stock_list is None:
            self._load_stock_list()
            logger.info("StockNameQueryTool 初始化完成")
    
    def _load_stock_list(self):
        """加载股票列表"""
        try:
            # 使用标准客户端获取股票列表
            client = Quotes.factory(market='std')
            
            # 获取沪市股票
            sh_stocks = client.stocks(market=1)  # 1=沪市
            # 获取深市股票
            sz_stocks = client.stocks(market=0)  # 0=深市
            
            # 合并股票列表
            stocks = []
            
            if sh_stocks is not None and len(sh_stocks) > 0:
                for _, row in sh_stocks.iterrows():
                    stocks.append({
                        'code': str(row['code']).zfill(6),  # 补齐6位
                        'name': row['name'],
                        'market': 'SH'
                    })
            
            if sz_stocks is not None and len(sz_stocks) > 0:
                for _, row in sz_stocks.iterrows():
                    stocks.append({
                        'code': str(row['code']).zfill(6),  # 补齐6位
                        'name': row['name'],
                        'market': 'SZ'
                    })
            
            self._stock_list = pd.DataFrame(stocks)
            logger.info(f"成功加载 {len(stocks)} 只股票")
            
        except Exception as e:
            logger.error(f"加载股票列表失败: {e}")
            self._stock_list = pd.DataFrame(columns=['code', 'name', 'market'])
    
    def query(self, name_or_code: str) -> Dict[str, Any]:
        """
        查询股票
        
        Args:
            name_or_code: 股票名称或代码
        
        Returns:
            查询结果，包含股票代码、名称、市场等信息
        """
        name_or_code = name_or_code.strip().upper()
        
        # 1. 首先尝试作为代码查询
        result = self._query_by_code(name_or_code)
        if result:
            return result
        
        # 2. 尝试作为名称精确匹配
        result = self._query_by_name(name_or_code)
        if result:
            return result
        
        # 3. 尝试模糊匹配
        result = self._fuzzy_match(name_or_code)
        if result:
            return result
        
        # 4. 查询失败
        return {
            'success': False,
            'error': f'未找到股票: {name_or_code}',
            'suggestions': self._get_suggestions(name_or_code)
        }
    
    def _query_by_code(self, code: str) -> Optional[Dict[str, Any]]:
        """按代码查询"""
        # 移除可能的前缀
        if code.startswith('SH') or code.startswith('SZ'):
            market = code[:2]
            code = code[2:]
        else:
            market = None
        
        # 补齐6位
        code = code.zfill(6)
        
        # 查询
        matches = self._stock_list[self._stock_list['code'] == code]
        
        if len(matches) > 0:
            row = matches.iloc[0]
            return {
                'success': True,
                'code': row['code'],
                'name': row['name'],
                'market': row['market'],
                'full_code': f"{row['market']}{row['code']}",
                'match_type': 'exact_code'
            }
        
        return None
    
    def _query_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """按名称精确查询"""
        matches = self._stock_list[self._stock_list['name'].str.upper() == name.upper()]
        
        if len(matches) > 0:
            row = matches.iloc[0]
            return {
                'success': True,
                'code': row['code'],
                'name': row['name'],
                'market': row['market'],
                'full_code': f"{row['market']}{row['code']}",
                'match_type': 'exact_name'
            }
        
        return None
    
    def _fuzzy_match(self, name: str) -> Optional[Dict[str, Any]]:
        """模糊匹配"""
        # 获取所有股票名称
        stock_names = self._stock_list['name'].tolist()
        
        # 模糊匹配
        matches = get_close_matches(name, stock_names, n=5, cutoff=0.6)
        
        if matches:
            # 返回最佳匹配
            best_match = matches[0]
            row = self._stock_list[self._stock_list['name'] == best_match].iloc[0]
            
            return {
                'success': True,
                'code': row['code'],
                'name': row['name'],
                'market': row['market'],
                'full_code': f"{row['market']}{row['code']}",
                'match_type': 'fuzzy',
                'confidence': 1.0 - (0.0 if best_match == name else 0.2),
                'other_matches': matches[1:] if len(matches) > 1 else []
            }
        
        return None
    
    def _get_suggestions(self, name: str, n: int = 5) -> List[str]:
        """获取建议"""
        stock_names = self._stock_list['name'].tolist()
        return get_close_matches(name, stock_names, n=n, cutoff=0.3)
    
    def search(self, keyword: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        搜索股票
        
        Args:
            keyword: 搜索关键词
            limit: 返回数量限制
        
        Returns:
            匹配的股票列表
        """
        keyword = keyword.strip().upper()
        results = []
        
        # 搜索名称包含关键词的股票
        mask = self._stock_list['name'].str.upper().str.contains(keyword, na=False)
        matches = self._stock_list[mask].head(limit)
        
        for _, row in matches.iterrows():
            results.append({
                'code': row['code'],
                'name': row['name'],
                'market': row['market'],
                'full_code': f"{row['market']}{row['code']}"
            })
        
        return results
    
    def get_all_stocks(self) -> pd.DataFrame:
        """获取所有股票列表"""
        return self._stock_list.copy()


def main():
    """测试工具"""
    print("=" * 60)
    print("📊 StockNameQueryTool 测试")
    print("=" * 60)
    
    tool = StockNameQueryTool()
    
    # 测试用例
    test_cases = [
        '贵州茅台',
        '茅台',
        '600519',
        'SH600519',
        '招商银行',
        '中国平安',
        '不存在的股票'
    ]
    
    for name in test_cases:
        print(f"\n查询: {name}")
        result = tool.query(name)
        
        if result['success']:
            print(f"  ✅ 成功: {result['name']} ({result['full_code']})")
            print(f"  匹配类型: {result['match_type']}")
            if 'other_matches' in result and result['other_matches']:
                print(f"  其他匹配: {result['other_matches']}")
        else:
            print(f"  ❌ 失败: {result['error']}")
            if result.get('suggestions'):
                print(f"  建议: {result['suggestions']}")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
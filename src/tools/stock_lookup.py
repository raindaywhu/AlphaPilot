"""
股票名称查询工具

支持通过股票名称或代码进行查询，返回标准化的股票代码和名称。
"""

from typing import Optional, Dict, List
import re


class StockLookupTool:
    """股票名称/代码查询工具"""
    
    # 常见股票名称到代码的映射
    STOCK_MAP = {
        # 白酒
        "贵州茅台": "sh600519",
        "五粮液": "sz000858",
        "泸州老窖": "sz000568",
        "洋河股份": "sz002304",
        "山西汾酒": "sh600809",
        "古井贡酒": "sz000596",
        "酒鬼酒": "sz000799",
        "水井坊": "sh600779",
        
        # 银行
        "招商银行": "sh600036",
        "平安银行": "sz000001",
        "工商银行": "sh601398",
        "建设银行": "sh601939",
        "农业银行": "sh601288",
        "中国银行": "sh601988",
        "交通银行": "sh601328",
        "兴业银行": "sh601166",
        "浦发银行": "sh600000",
        "民生银行": "sh600016",
        
        # 保险
        "中国平安": "sh601318",
        "中国人寿": "sh601628",
        "中国太保": "sh601601",
        "新华保险": "sh601336",
        
        # 科技
        "宁德时代": "sz300750",
        "比亚迪": "sz002594",
        "立讯精密": "sz002475",
        "歌尔股份": "sz002241",
        "京东方A": "sz000725",
        "TCL科技": "sz000100",
        "韦尔股份": "sh603501",
        "兆易创新": "sh603986",
        "中芯国际": "sh688981",
        "寒武纪": "sh688256",
        
        # 新能源
        "隆基绿能": "sh601012",
        "通威股份": "sh600438",
        "阳光电源": "sz300274",
        "晶澳科技": "sz002459",
        "天合光能": "sh688599",
        "亿纬锂能": "sz300014",
        "赣锋锂业": "sz002460",
        "天齐锂业": "sz002466",
        
        # 医药
        "恒瑞医药": "sh600276",
        "药明康德": "sh603259",
        "迈瑞医疗": "sz300760",
        "片仔癀": "sh600436",
        "云南白药": "sz000538",
        "长春高新": "sz000661",
        "智飞生物": "sz300122",
        "沃森生物": "sz300142",
        "复星医药": "sh600196",
        "华东医药": "sz000963",
        
        # 消费
        "伊利股份": "sh600887",
        "海天味业": "sh603288",
        "金龙鱼": "sz300999",
        "双汇发展": "sz000895",
        "青岛啤酒": "sh600600",
        "重庆啤酒": "sh600132",
        
        # 地产
        "万科A": "sz000002",
        "保利发展": "sh600048",
        "招商蛇口": "sz001979",
        
        # 汽车
        "上汽集团": "sh600104",
        "长城汽车": "sh601633",
        "长安汽车": "sz000625",
        "广汽集团": "sh601238",
        
        # 家电
        "美的集团": "sz000333",
        "格力电器": "sz000651",
        "海尔智家": "sh600690",
        
        # 互联网
        "东方财富": "sz300059",
        "同花顺": "sz300033",
        "分众传媒": "sz002027",
        
        # 通信
        "中国移动": "sh600941",
        "中国电信": "sh601728",
        "中国联通": "sh600050",
        
        # 石油
        "中国石油": "sh601857",
        "中国石化": "sh600028",
        
        # 航空
        "中国国航": "sh601111",
        "南方航空": "sh600029",
        "东方航空": "sh600115",
        
        # 钢铁
        "宝钢股份": "sh600019",
        "河钢股份": "sz000709",
        
        # 煤炭
        "中国神华": "sh601088",
        "陕西煤业": "sh601225",
        
        # 有色
        "紫金矿业": "sh601899",
        "中国铝业": "sh601600",
        "江西铜业": "sh600362",
    }
    
    # 反向映射：代码到名称
    CODE_TO_NAME = {v: k for k, v in STOCK_MAP.items()}
    
    @classmethod
    def lookup(cls, query: str) -> Optional[Dict[str, str]]:
        """
        查询股票信息
        
        Args:
            query: 股票名称或代码
            
        Returns:
            {"code": "sh600519", "name": "贵州茅台"} 或 None
        """
        query = query.strip()
        
        # 1. 尝试直接匹配名称
        if query in cls.STOCK_MAP:
            code = cls.STOCK_MAP[query]
            return {"code": code, "name": query}
        
        # 2. 标准化代码格式
        code = cls.normalize_code(query)
        if code:
            # 检查是否在映射中
            if code in cls.CODE_TO_NAME:
                return {"code": code, "name": cls.CODE_TO_NAME[code]}
            # 返回代码，名称为空
            return {"code": code, "name": query.upper()}
        
        # 3. 模糊匹配名称
        for name, code in cls.STOCK_MAP.items():
            if query in name or name in query:
                return {"code": code, "name": name}
        
        return None
    
    @classmethod
    def normalize_code(cls, code: str) -> Optional[str]:
        """
        标准化股票代码格式
        
        支持格式:
        - 600519 -> sh600519
        - sh600519 -> sh600519
        - SH600519 -> sh600519
        - 600519.SH -> sh600519
        """
        code = code.strip().lower()
        
        # 已经是标准格式
        if code.startswith(('sh', 'sz', 'bj')):
            return code
        
        # 去除后缀 (.SH, .SZ)
        if '.' in code:
            parts = code.split('.')
            if len(parts) == 2:
                num, suffix = parts
                if suffix in ('sh', 'sz', 'bj'):
                    return f"{suffix}{num}"
        
        # 纯数字
        if code.isdigit():
            num = code
            # 根据股票代码前缀判断市场
            if num.startswith(('60', '68')):
                return f"sh{num}"
            elif num.startswith(('00', '30')):
                return f"sz{num}"
            elif num.startswith(('4', '8')):
                return f"bj{num}"
            # 默认上海
            return f"sh{num}"
        
        return None
    
    @classmethod
    def search(cls, keyword: str, limit: int = 10) -> List[Dict[str, str]]:
        """
        搜索股票
        
        Args:
            keyword: 搜索关键词
            limit: 返回数量限制
            
        Returns:
            [{"code": "...", "name": "..."}, ...]
        """
        keyword = keyword.strip().lower()
        results = []
        
        for name, code in cls.STOCK_MAP.items():
            if keyword in name.lower() or keyword in code:
                results.append({"code": code, "name": name})
                if len(results) >= limit:
                    break
        
        return results


# 便捷函数
def lookup_stock(query: str) -> Optional[Dict[str, str]]:
    """查询股票"""
    return StockLookupTool.lookup(query)


def search_stocks(keyword: str, limit: int = 10) -> List[Dict[str, str]]:
    """搜索股票"""
    return StockLookupTool.search(keyword, limit)
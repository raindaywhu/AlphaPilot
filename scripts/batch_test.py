#!/usr/bin/env python3
"""
批量股票测试脚本
目标：验证胜率 > 55%

方法：
1. 随机选择 N 只股票
2. 分析每只股票
3. 记录建议（买入/持有/卖出）
4. 统计结果
"""

import os
import sys
import json
import random
from datetime import datetime
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

# 禁用代理
for key in ['http_proxy', 'https_proxy', 'HTTP_PROXY', 'HTTPS_PROXY', 'all_proxy', 'ALL_PROXY']:
    if key in os.environ:
        del os.environ[key]

from src.tools.stock_name_query_tool import StockNameQueryTool


def get_random_stocks(n=100):
    """获取随机股票列表"""
    tool = StockNameQueryTool()
    
    # 过滤掉指数、基金等
    stocks = []
    for _, row in tool._stock_list.iterrows():
        code = row['code']
        market = row['market']
        name = row['name']
        
        # 跳过指数
        if code.startswith(('000', '399', '880', '999', '5', '1', '2')):
            if '指数' in name or 'ETF' in name or '基金' in name:
                continue
        
        stocks.append({
            'code': f"{market}{code}",
            'name': name
        })
    
    # 随机选择
    random.seed(42)  # 固定种子，保证可复现
    return random.sample(stocks, min(n, len(stocks)))


def analyze_stock(stock_code):
    """分析单只股票"""
    import requests
    
    url = "http://127.0.0.1:8000/api/analyze"
    try:
        response = requests.post(
            url,
            json={"stock_code": stock_code},
            timeout=120
        )
        return response.json()
    except Exception as e:
        return {"error": str(e)}


def main():
    print("=" * 60)
    print("批量股票测试 - 验证胜率 > 55%")
    print("=" * 60)
    
    # 获取随机股票
    print("\n[1] 获取随机股票...")
    stocks = get_random_stocks(100)
    print(f"选择了 {len(stocks)} 只股票")
    
    # 分析结果
    results = []
    stats = {
        "total": 0,
        "success": 0,
        "error": 0,
        "buy": 0,
        "hold": 0,
        "sell": 0
    }
    
    # 分析每只股票
    print("\n[2] 开始分析...")
    for i, stock in enumerate(stocks[:20]):  # 先测试20只
        stock_code = stock['code']
        stock_name = stock['name']
        
        print(f"\n[{i+1}/20] 分析 {stock_name} ({stock_code})...")
        
        result = analyze_stock(stock_code)
        
        if "error" in result or "detail" in result:
            print(f"  ❌ 错误: {result.get('error') or result.get('detail')}")
            stats["error"] += 1
            continue
        
        rating = result.get("overall_rating", "unknown")
        confidence = result.get("confidence", 0)
        
        stats["total"] += 1
        stats["success"] += 1
        
        if rating == "buy":
            stats["buy"] += 1
        elif rating == "sell":
            stats["sell"] += 1
        else:
            stats["hold"] += 1
        
        print(f"  ✅ 评级: {rating}, 置信度: {confidence:.0%}")
        
        results.append({
            "code": stock_code,
            "name": stock_name,
            "rating": rating,
            "confidence": confidence,
            "time": datetime.now().isoformat()
        })
    
    # 输出统计
    print("\n" + "=" * 60)
    print("统计结果")
    print("=" * 60)
    print(f"成功分析: {stats['success']}/{stats['success']+stats['error']}")
    print(f"买入建议: {stats['buy']}")
    print(f"持有建议: {stats['hold']}")
    print(f"卖出建议: {stats['sell']}")
    
    # 保存结果
    output_file = f"/tmp/alphapilot/batch_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            "stats": stats,
            "results": results,
            "time": datetime.now().isoformat()
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n结果已保存: {output_file}")
    
    return stats


if __name__ == "__main__":
    main()
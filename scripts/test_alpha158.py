#!/usr/bin/env python3
"""
Alpha158 因子工具测试脚本

测试 qlib Alpha158 因子的使用方法
"""

import qlib
from qlib.contrib.data.handler import Alpha158
import pandas as pd

def test_alpha158():
    """测试 Alpha158 因子获取"""
    print("=" * 60)
    print("Alpha158 因子测试")
    print("=" * 60)

    # 初始化 qlib
    print("\n1. 初始化 qlib...")
    qlib.init(provider_uri='~/.qlib/qlib_data/cn_data')
    print("✅ qlib 初始化成功")

    # 查看 Alpha158 参数
    print("\n2. Alpha158 默认参数:")
    print("  - instruments: csi500")
    print("  - freq: day")
    print("  - learn_processors: DropnaLabel, CSZScoreNorm")

    # 创建 Alpha158 实例
    print("\n3. 创建 Alpha158 实例...")
    print("  - instruments: csi300")
    print("  - start_time: 2020-01-01")
    print("  - end_time: 2020-03-31")

    try:
        handler = Alpha158(
            instruments='csi300',
            start_time='2020-01-01',
            end_time='2020-03-31'
        )
        print("✅ Alpha158 实例创建成功")

        # 获取数据
        print("\n4. 获取因子数据...")
        df = handler.fetch()
        print(f"✅ 数据获取成功")
        print(f"  - Shape: {df.shape}")
        print(f"  - Columns: {list(df.columns[:10])}... (共 {len(df.columns)} 列)")
        print(f"  - Index: {df.index[:5]}... (共 {len(df)} 行)")

        # 查看因子列表
        print("\n5. 因子列表 (前 20 个):")
        for i, col in enumerate(df.columns[:20]):
            print(f"  {i+1:2d}. {col}")

        return df

    except Exception as e:
        print(f"❌ 创建实例失败: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    test_alpha158()
#!/usr/bin/env python3
"""
宏观分析师 Agent 测试

Issue: #10 (AGENT-002)
"""

import sys
import os
import json

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agents.macro import MacroAnalyst


def test_macro_analyst_init():
    """测试宏观分析师初始化"""
    print("\n" + "=" * 60)
    print("测试 1: 宏观分析师初始化")
    print("=" * 60)

    try:
        agent = MacroAnalyst()
        print("✅ 宏观分析师初始化成功")
        print(f"   - LLM 模型: GLM-5")
        print(f"   - 知识库数量: {len(agent.knowledge)}")
        return True
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        return False


def test_knowledge_loading():
    """测试知识库加载"""
    print("\n" + "=" * 60)
    print("测试 2: 知识库加载")
    print("=" * 60)

    agent = MacroAnalyst()

    expected_knowledge = [
        "macro_frameworks",
        "policy_analysis",
        "geopolitical_analysis"
    ]

    all_loaded = True
    for name in expected_knowledge:
        if name in agent.knowledge:
            length = len(agent.knowledge[name])
            print(f"✅ {name}: {length} 字符")
        else:
            print(f"❌ {name}: 未加载")
            all_loaded = False

    return all_loaded


def test_economic_indicators_analysis():
    """测试经济指标分析"""
    print("\n" + "=" * 60)
    print("测试 3: 经济指标分析")
    print("=" * 60)

    agent = MacroAnalyst()
    eco = agent._analyze_economic_indicators()

    expected_keys = ["gdp_growth", "pmi", "cpi", "m2_growth", "summary"]
    all_present = all(key in eco for key in expected_keys)

    if all_present:
        print("✅ 经济指标分析完整")
        print(f"   - GDP: {eco['gdp_growth']['value']} ({eco['gdp_growth']['trend']})")
        print(f"   - PMI: {eco['pmi']['value']} ({eco['pmi']['trend']})")
        print(f"   - CPI: {eco['cpi']['value']} ({eco['cpi']['trend']})")
        print(f"   - M2: {eco['m2_growth']['value']} ({eco['m2_growth']['trend']})")
    else:
        print("❌ 经济指标分析不完整")

    return all_present


def test_policy_analysis():
    """测试政策分析"""
    print("\n" + "=" * 60)
    print("测试 4: 政策分析")
    print("=" * 60)

    agent = MacroAnalyst()
    policy = agent._analyze_policy(["货币政策", "财政政策", "国际形势"])

    expected_keys = ["monetary_policy", "fiscal_policy", "international", "summary"]
    all_present = all(key in policy for key in expected_keys)

    if all_present:
        print("✅ 政策分析完整")
        print(f"   - 货币政策: {policy['monetary_policy']['stance']}")
        print(f"   - 财政政策: {policy['fiscal_policy']['stance']}")
        print(f"   - 国际形势: {policy['international']['fed_policy']}")
    else:
        print("❌ 政策分析不完整")

    return all_present


def test_geopolitical_analysis():
    """测试地缘政治分析"""
    print("\n" + "=" * 60)
    print("测试 5: 地缘政治分析")
    print("=" * 60)

    agent = MacroAnalyst()
    geo = agent._analyze_geopolitics()

    expected_keys = ["us_china_relation", "global_economy", "regional_conflicts", "supply_chain", "summary"]
    all_present = all(key in geo for key in expected_keys)

    if all_present:
        print("✅ 地缘政治分析完整")
        print(f"   - 中美关系: {geo['us_china_relation']['status']}")
        print(f"   - 全球经济: {geo['global_economy']['fed_policy']['current']}")
        print(f"   - 地区冲突: {geo['regional_conflicts']['status']}")
    else:
        print("❌ 地缘政治分析不完整")

    return all_present


def test_logic_derivation():
    """测试逻辑推导功能"""
    print("\n" + "=" * 60)
    print("测试 6: 逻辑推导功能")
    print("=" * 60)

    agent = MacroAnalyst()
    policy = agent._analyze_policy(["货币政策"])

    # 检查货币政策是否有逻辑推导
    monetary = policy.get("monetary_policy", {})
    logic = monetary.get("logic_derivation", {})

    if logic:
        print("✅ 货币政策逻辑推导存在")
        print(f"   - 步骤数: {len([k for k in logic.keys() if k.startswith('step')])}")
        print(f"   - 结论: {logic.get('conclusion', '无')}")
    else:
        print("❌ 货币政策逻辑推导缺失")
        return False

    # 检查地缘政治逻辑推导
    geo = agent._analyze_geopolitics()
    us_china = geo.get("us_china_relation", {})
    geo_logic = us_china.get("logic_derivation", {})

    if geo_logic:
        print("✅ 地缘政治逻辑推导存在")
        print(f"   - 分析维度: {len([k for k in geo_logic.keys() if k not in ['conclusion']])}")
    else:
        print("❌ 地缘政治逻辑推导缺失")
        return False

    return True


def test_full_analysis():
    """测试完整分析流程"""
    print("\n" + "=" * 60)
    print("测试 7: 完整分析流程")
    print("=" * 60)

    agent = MacroAnalyst()
    result = agent.analyze(
        stock_code="SH600519",
        focus_areas=["货币政策", "财政政策", "国际形势"]
    )

    # 验证输出结构
    expected_keys = [
        "agent", "stock_code", "analysis_date", "analysis_type",
        "macro_view", "confidence", "economic_indicators",
        "policy_analysis", "geopolitical_analysis", "conclusion"
    ]

    all_present = all(key in result for key in expected_keys)

    if all_present:
        print("✅ 完整分析输出结构正确")
        print(f"   - 宏观观点: {result['macro_view']}")
        print(f"   - 置信度: {result['confidence']:.2f}")
        print(f"   - 结论: {result['conclusion']}")
    else:
        print("❌ 完整分析输出结构不完整")
        return False

    return all_present


def main():
    """运行所有测试"""
    print("=" * 60)
    print("宏观分析师 Agent 测试套件")
    print("Issue: #10 (AGENT-002)")
    print("=" * 60)

    tests = [
        ("初始化测试", test_macro_analyst_init),
        ("知识库加载测试", test_knowledge_loading),
        ("经济指标分析测试", test_economic_indicators_analysis),
        ("政策分析测试", test_policy_analysis),
        ("地缘政治分析测试", test_geopolitical_analysis),
        ("逻辑推导功能测试", test_logic_derivation),
        ("完整分析流程测试", test_full_analysis),
    ]

    results = []
    for name, test_func in tests:
        try:
            passed = test_func()
            results.append((name, passed))
        except Exception as e:
            print(f"❌ {name} 异常: {e}")
            results.append((name, False))

    # 打印总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)

    passed = sum(1 for _, p in results if p)
    total = len(results)

    for name, p in results:
        status = "✅ 通过" if p else "❌ 失败"
        print(f"  {status}: {name}")

    print(f"\n总计: {passed}/{total} 测试通过")

    if passed == total:
        print("\n🎉 所有测试通过！")
        return 0
    else:
        print("\n⚠️ 部分测试失败，请检查")
        return 1


if __name__ == "__main__":
    sys.exit(main())
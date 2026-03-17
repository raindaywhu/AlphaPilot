#!/usr/bin/env python3
"""
CREW-001 投资分析 Crew 测试

测试验收标准：
- [ ] 能够运行完整的分析流程
- [ ] 输出包含所有 Agent 的分析结果
- [ ] 支持并行分析

Issue: #7
"""

import sys
import os
import json
import time

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.crew import InvestmentCrew


def test_crew_basic():
    """测试基本分析功能"""
    print("=" * 60)
    print("测试 1: 基本分析功能")
    print("=" * 60)

    crew = InvestmentCrew(use_mock=True)
    result = crew.analyze("SH600000", parallel=False)

    # 验证结果结构
    assert "stock_code" in result, "缺少 stock_code"
    assert "overall_rating" in result, "缺少 overall_rating"
    assert "agent_results" in result, "缺少 agent_results"

    # 验证包含所有 Agent 的结果
    assert "quantitative" in result["agent_results"], "缺少量化分析结果"
    assert "macro" in result["agent_results"], "缺少宏观分析结果"
    assert "alternative" in result["agent_results"], "缺少另类分析结果"

    print("\n✅ 基本分析功能测试通过")
    print(f"综合评级: {result['overall_rating']}")
    print(f"置信度: {result['confidence']}")


def test_crew_parallel():
    """测试并行分析功能"""
    print("\n" + "=" * 60)
    print("测试 2: 并行分析功能")
    print("=" * 60)

    crew = InvestmentCrew(use_mock=True)

    # 串行分析
    start = time.time()
    result_serial = crew.analyze("SH600000", parallel=False)
    serial_time = time.time() - start

    # 并行分析
    start = time.time()
    result_parallel = crew.analyze("SH600000", parallel=True)
    parallel_time = time.time() - start

    print(f"\n串行耗时: {serial_time:.2f}s")
    print(f"并行耗时: {parallel_time:.2f}s")
    print(f"加速比: {serial_time / parallel_time:.2f}x")

    # 验证结果一致性
    assert result_serial["stock_code"] == result_parallel["stock_code"]
    assert result_serial["overall_rating"] == result_parallel["overall_rating"]

    print("\n✅ 并行分析功能测试通过")


def test_crew_rating():
    """测试评级计算"""
    print("\n" + "=" * 60)
    print("测试 3: 评级计算")
    print("=" * 60)

    crew = InvestmentCrew(use_mock=True)
    result = crew.analyze("SH600000")

    # 验证评级范围
    valid_ratings = ["看涨", "中性偏多", "中性", "中性偏空", "看跌"]
    assert result["overall_rating"] in valid_ratings, f"无效评级: {result['overall_rating']}"

    # 验证置信度范围
    assert 0 <= result["confidence"] <= 1, f"置信度超出范围: {result['confidence']}"

    # 验证各 Agent 的评级
    for agent_name, rating in result["agent_ratings"].items():
        print(f"{agent_name}: {rating} (置信度: {result['agent_confidences'][agent_name]})")

    print("\n✅ 评级计算测试通过")


def test_crew_output():
    """测试输出完整性"""
    print("\n" + "=" * 60)
    print("测试 4: 输出完整性")
    print("=" * 60)

    crew = InvestmentCrew(use_mock=True)
    result = crew.analyze("SH600000")

    # 验证必需字段
    required_fields = [
        "stock_code",
        "analysis_date",
        "overall_rating",
        "confidence",
        "score",
        "agent_results",
        "agent_ratings",
        "agent_confidences",
        "agent_conclusions",
        "summary",
        "risk_warnings",
        "disclaimer",
        "execution_time"
    ]

    for field in required_fields:
        assert field in result, f"缺少字段: {field}"

    print("\n✅ 输出完整性测试通过")
    print(f"执行时间: {result['execution_time']}")


def test_crew_summary():
    """测试摘要生成"""
    print("\n" + "=" * 60)
    print("测试 5: 摘要生成")
    print("=" * 60)

    crew = InvestmentCrew(use_mock=True)
    result = crew.analyze("SH600000")

    print(f"\n摘要: {result['summary']}")

    # 验证摘要包含关键信息
    assert "综合评级" in result["summary"], "摘要缺少综合评级"
    assert result["overall_rating"] in result["summary"], "摘要与评级不一致"

    print("\n✅ 摘要生成测试通过")


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("CREW-001 投资分析 Crew 测试套件")
    print("=" * 60)

    try:
        test_crew_basic()
        test_crew_parallel()
        test_crew_rating()
        test_crew_output()
        test_crew_summary()

        print("\n" + "=" * 60)
        print("✅ 所有测试通过！")
        print("=" * 60)

        # 打印完整结果示例
        print("\n完整分析结果示例:")
        crew = InvestmentCrew(use_mock=True)
        result = crew.analyze("SH600000")
        print(json.dumps(result, indent=2, ensure_ascii=False))

        return 0

    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
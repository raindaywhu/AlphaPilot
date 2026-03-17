#!/usr/bin/env python3
"""
量化分析师 Agent 测试

测试 QuantitativeAnalyst 的各个方法
"""

import pytest
import pandas as pd
from src.agents.quantitative import QuantitativeAnalyst


class TestQuantitativeAnalyst:
    """量化分析师测试类"""

    @pytest.fixture(scope="class")
    def agent(self):
        """创建 Agent 实例"""
        return QuantitativeAnalyst()

    def test_agent_initialization(self, agent):
        """测试 Agent 初始化"""
        assert agent is not None
        assert agent.llm is not None
        assert agent.alpha158_tool is not None
        assert agent.agent is not None

    def test_analyze(self, agent):
        """测试分析功能"""
        # 分析股票
        result = agent.analyze("SH600000")

        # 验证返回类型
        assert isinstance(result, dict)

        # 验证必要字段
        assert "agent" in result
        assert "stock_code" in result
        assert "analysis_date" in result
        assert "overall_rating" in result
        assert "confidence" in result
        assert "conclusion" in result

        # 验证值
        assert result["agent"] == "quant_analyst"
        assert result["stock_code"] == "SH600000"

    def test_analyze_with_parameters(self, agent):
        """测试带参数的分析"""
        # 分析股票，指定分析类型和预测周期
        result = agent.analyze(
            stock_code="SH600000",
            analysis_type="趋势判断",
            time_horizon=10
        )

        # 验证参数被正确传递
        assert result["analysis_type"] == "趋势判断"
        assert result["time_horizon"] == 10

    def test_analyze_invalid_stock(self, agent):
        """测试无效股票代码"""
        result = agent.analyze("INVALID123")

        # 验证返回结构
        assert isinstance(result, dict)
        assert result["stock_code"] == "INVALID123"
        # 数据验证状态应该是 missing
        assert result["data_validation"]["status"] in ["valid", "missing"]

    def test_factor_analysis_structure(self, agent):
        """测试因子分析结构"""
        result = agent.analyze("SH600000")

        # 验证因子分析结构
        if result["factor_analysis"]:
            assert "momentum" in result["factor_analysis"]
            assert "volatility" in result["factor_analysis"]
            assert "moving_average" in result["factor_analysis"]

    def test_signals_structure(self, agent):
        """测试信号结构"""
        result = agent.analyze("SH600000")

        # 验证信号结构
        assert isinstance(result["signals"], list)

        for signal in result["signals"]:
            assert "indicator" in signal
            assert "signal" in signal
            assert "strength" in signal
            assert "description" in signal

    def test_risk_warning(self, agent):
        """测试风险提示"""
        result = agent.analyze("SH600000")

        # 验证风险提示
        assert isinstance(result["risk_warning"], list)
        assert len(result["risk_warning"]) > 0

    def test_conclusion(self, agent):
        """测试结论生成"""
        result = agent.analyze("SH600000")

        # 验证结论
        assert isinstance(result["conclusion"], str)
        assert len(result["conclusion"]) > 0


def test_agent_creation():
    """测试 Agent 创建"""
    agent = QuantitativeAnalyst()
    assert agent is not None


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, '-v'])
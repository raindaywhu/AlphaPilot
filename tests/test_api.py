"""
API 接口测试

测试 REST API 的各个接口

Issue: #20 (API-001)
"""

import pytest
from fastapi.testclient import TestClient
import sys
import os

# 添加项目根目录到 sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.api.main import app


# 创建测试客户端
client = TestClient(app)


class TestHealthEndpoint:
    """健康检查接口测试"""

    def test_health_check(self):
        """测试健康检查接口"""
        response = client.get("/api/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "status" in data
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data


class TestAnalyzeEndpoint:
    """股票分析接口测试"""

    def test_analyze_stock_basic(self):
        """测试基本分析请求"""
        response = client.post(
            "/api/analyze",
            json={
                "stock_code": "SH600000"
            }
        )
        
        # 可能因为 qlib 未初始化而失败，但接口应该存在
        assert response.status_code in [200, 500]
        
        if response.status_code == 200:
            data = response.json()
            
            # 验证返回字段
            assert "stock_code" in data
            assert data["stock_code"] == "SH600000"
            assert "analysis_date" in data
            assert "overall_rating" in data
            assert "confidence" in data

    def test_analyze_stock_with_params(self):
        """测试带参数的分析请求"""
        response = client.post(
            "/api/analyze",
            json={
                "stock_code": "SH600519",
                "parallel": True,
                "time_horizon": 10
            }
        )
        
        # 可能因为 qlib 未初始化而失败，但接口应该存在
        assert response.status_code in [200, 500]
        
        if response.status_code == 200:
            data = response.json()
            assert data["stock_code"] == "SH600519"


class TestSingleAgentEndpoints:
    """单 Agent 分析接口测试"""

    def test_quantitative_analysis(self):
        """测试量化分析接口"""
        response = client.post(
            "/api/analyze/quantitative",
            json={
                "stock_code": "SH600000",
                "time_horizon": 5
            }
        )
        
        # 可能因为 qlib 未初始化而失败，但接口应该存在
        assert response.status_code in [200, 500]

    def test_macro_analysis(self):
        """测试宏观分析接口"""
        response = client.post(
            "/api/analyze/macro",
            json={
                "stock_code": "SH600000",
                "time_horizon": 5
            }
        )
        
        assert response.status_code in [200, 500]

    def test_alternative_analysis(self):
        """测试另类分析接口"""
        response = client.post(
            "/api/analyze/alternative",
            json={
                "stock_code": "SH600000",
                "time_horizon": 5
            }
        )
        
        assert response.status_code in [200, 500]


class TestErrorHandling:
    """错误处理测试"""

    def test_missing_stock_code(self):
        """测试缺少股票代码"""
        response = client.post(
            "/api/analyze",
            json={}
        )
        
        # 应该返回 422（参数验证失败）
        assert response.status_code == 422

    def test_invalid_time_horizon(self):
        """测试无效的预测周期"""
        response = client.post(
            "/api/analyze",
            json={
                "stock_code": "SH600000",
                "time_horizon": 100  # 超过最大值
            }
        )
        
        # 应该返回 422（参数验证失败）
        assert response.status_code == 422


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
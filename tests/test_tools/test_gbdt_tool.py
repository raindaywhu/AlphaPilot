#!/usr/bin/env python3
"""
GBDT 预测工具测试

测试 QlibGBDTPredictionTool 的功能

Issue: #5 (TOOL-002)
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import unittest
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
import numpy as np


class TestQlibGBDTPredictionTool(unittest.TestCase):
    """测试 GBDT 预测工具"""

    def setUp(self):
        """测试前准备"""
        self.tool = None

    def test_initialization(self):
        """测试工具初始化"""
        from src.tools.gbdt_tool import QlibGBDTPredictionTool
        
        tool = QlibGBDTPredictionTool(
            qlib_provider='~/.qlib/qlib_data/cn_data'
        )
        
        self.assertIsNotNone(tool)
        self.assertEqual(tool.qlib_provider, '~/.qlib/qlib_data/cn_data')
        self.assertFalse(tool._initialized)
        
        print("✅ 工具初始化测试通过")

    def test_predict_returns_dict(self):
        """测试 predict 方法返回字典"""
        from src.tools.gbdt_tool import QlibGBDTPredictionTool
        
        tool = QlibGBDTPredictionTool()
        
        # Mock qlib 初始化和预测过程
        with patch.object(tool, '_ensure_initialized'):
            with patch.object(tool, '_create_dataset') as mock_dataset:
                with patch.object(tool, '_calculate_confidence', return_value=0.75):
                    # Mock 数据集
                    mock_ds = Mock()
                    mock_df = pd.DataFrame({
                        'label': [0.01, 0.02, 0.03, 0.04, 0.05]
                    })
                    mock_ds.prepare.return_value = mock_df
                    mock_dataset.return_value = mock_ds
                    
                    # Mock 模型
                    tool._model = Mock()
                    tool._model.fit = Mock()
                    tool._model.predict.return_value = pd.DataFrame({'pred': [0.05]})
                    tool._initialized = True
                    
                    result = tool.predict('SH600000', horizon=5)
        
        self.assertIsInstance(result, dict)
        self.assertIn('stock_code', result)
        self.assertIn('prediction', result)
        self.assertIn('horizon', result)
        self.assertIn('confidence', result)
        self.assertIn('status', result)
        
        print("✅ predict 返回格式测试通过")

    def test_predict_handles_error(self):
        """测试 predict 方法处理错误"""
        from src.tools.gbdt_tool import QlibGBDTPredictionTool
        
        tool = QlibGBDTPredictionTool()
        
        # 模拟初始化失败
        with patch.object(tool, '_ensure_initialized', side_effect=Exception("初始化失败")):
            result = tool.predict('SH600000', horizon=5)
        
        self.assertEqual(result['status'], 'error')
        self.assertIn('error', result)
        
        print("✅ 错误处理测试通过")

    def test_get_confidence_returns_float(self):
        """测试 get_confidence 返回浮点数"""
        from src.tools.gbdt_tool import QlibGBDTPredictionTool
        
        tool = QlibGBDTPredictionTool()
        
        # Mock predict 方法
        with patch.object(tool, 'predict') as mock_predict:
            mock_predict.return_value = {
                'stock_code': 'SH600000',
                'prediction': 0.05,
                'confidence': 0.8,
                'status': 'success'
            }
            tool._initialized = True
            
            confidence = tool.get_confidence('SH600000')
        
        self.assertIsInstance(confidence, float)
        self.assertGreaterEqual(confidence, 0.0)
        self.assertLessEqual(confidence, 1.0)
        
        print("✅ 置信度返回格式测试通过")

    def test_calculate_confidence(self):
        """测试置信度计算"""
        from src.tools.gbdt_tool import QlibGBDTPredictionTool
        
        tool = QlibGBDTPredictionTool()
        
        # 创建模拟数据
        labels = np.array([0.01, 0.02, 0.03, 0.04, 0.05])
        predictions = np.array([0.011, 0.019, 0.031, 0.039, 0.051])
        
        mock_dataset = Mock()
        mock_df = pd.DataFrame({'label': labels})
        mock_dataset.prepare.return_value = mock_df
        
        confidence = tool._calculate_confidence(mock_dataset, predictions)
        
        self.assertIsInstance(confidence, float)
        self.assertGreater(confidence, 0.9)  # 预测很接近，置信度应该很高
        
        print(f"✅ 置信度计算测试通过: {confidence:.4f}")

    def test_calculate_confidence_with_zero_variance(self):
        """测试标签方差为 0 的情况"""
        from src.tools.gbdt_tool import QlibGBDTPredictionTool
        
        tool = QlibGBDTPredictionTool()
        
        # 创建方差为 0 的数据
        labels = np.array([0.02, 0.02, 0.02, 0.02, 0.02])
        predictions = np.array([0.02, 0.02, 0.02, 0.02, 0.02])
        
        mock_dataset = Mock()
        mock_df = pd.DataFrame({'label': labels})
        mock_dataset.prepare.return_value = mock_df
        
        confidence = tool._calculate_confidence(mock_dataset, predictions)
        
        self.assertEqual(confidence, 0.5)  # 默认值
        
        print("✅ 零方差情况测试通过")


class TestQlibGBDTPredictionToolIntegration(unittest.TestCase):
    """集成测试（需要 qlib 数据）"""

    def setUp(self):
        """测试前准备"""
        # 检查是否有 qlib 数据
        import os
        qlib_path = os.path.expanduser('~/.qlib/qlib_data/cn_data')
        self.has_qlib_data = os.path.exists(qlib_path)
        
        if not self.has_qlib_data:
            print("⚠️ qlib 数据不存在，跳过集成测试")

    def test_full_prediction_flow(self):
        """测试完整预测流程"""
        if not self.has_qlib_data:
            self.skipTest("qlib 数据不存在")
        
        from src.tools.gbdt_tool import QlibGBDTPredictionTool
        
        tool = QlibGBDTPredictionTool()
        
        # 预测一只股票
        result = tool.predict('SH600000', horizon=5)
        
        self.assertEqual(result['status'], 'success')
        self.assertIsInstance(result['prediction'], float)
        self.assertGreaterEqual(result['confidence'], 0.0)
        
        print(f"✅ 完整预测流程测试通过: {result}")


def run_tests():
    """运行所有测试"""
    print("=" * 60)
    print("开始测试 GBDT 预测工具")
    print("=" * 60)
    
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加测试
    suite.addTests(loader.loadTestsFromTestCase(TestQlibGBDTPredictionTool))
    suite.addTests(loader.loadTestsFromTestCase(TestQlibGBDTPredictionToolIntegration))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "=" * 60)
    if result.wasSuccessful():
        print("✅ 所有测试通过！")
    else:
        print("❌ 部分测试失败")
    print("=" * 60)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    run_tests()
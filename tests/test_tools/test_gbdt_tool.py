#!/usr/bin/env python3
"""
GBDT 预测工具测试

Issue: #5 (TOOL-002)
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import tempfile
import shutil

from src.tools.gbdt_tool import QlibGBDTPredictionTool


class TestQlibGBDTPredictionTool:
    """GBDT 预测工具测试类"""

    @pytest.fixture
    def temp_model_dir(self):
        """创建临时模型目录"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def tool(self, temp_model_dir):
        """创建工具实例"""
        return QlibGBDTPredictionTool(
            qlib_provider='~/.qlib/qlib_data/cn_data',
            model_dir=temp_model_dir
        )

    def test_init(self, tool, temp_model_dir):
        """测试初始化"""
        assert tool.qlib_provider == '~/.qlib/qlib_data/cn_data'
        assert tool.model_dir == Path(temp_model_dir)
        assert tool._initialized is False
        assert tool._model is None

    def test_get_model_info(self, tool):
        """测试获取模型信息"""
        info = tool.get_model_info()

        assert info['model_type'] == 'LightGBM'
        assert info['model_status'] == '未加载'
        assert info['saved_models'] == 0

    @patch('src.tools.gbdt_tool.qlib.init')
    def test_ensure_qlib_initialized(self, mock_qlib_init, tool):
        """测试 qlib 初始化"""
        tool._ensure_qlib_initialized()
        mock_qlib_init.assert_called_once()
        assert tool._initialized is True

        # 再次调用不应重复初始化
        tool._ensure_qlib_initialized()
        mock_qlib_init.assert_called_once()

    def test_predict_invalid_params(self, tool):
        """测试预测参数验证"""
        with pytest.raises(ValueError, match="stock_code 不能为空"):
            tool.predict('', horizon=5)

        with pytest.raises(ValueError, match="horizon 必须大于 0"):
            tool.predict('SH600519', horizon=0)

        with pytest.raises(ValueError, match="horizon 必须大于 0"):
            tool.predict('SH600519', horizon=-1)

    @patch('src.tools.gbdt_tool.qlib.init')
    @patch('src.tools.gbdt_tool.Alpha158')
    @patch('src.tools.gbdt_tool.DatasetH')
    @patch('src.tools.gbdt_tool.LGBModel')
    def test_train_model(
        self,
        mock_lgb_model,
        mock_dataset,
        mock_alpha158,
        mock_qlib_init,
        tool
    ):
        """测试模型训练"""
        # 模拟数据
        mock_handler = Mock()
        mock_df = pd.DataFrame(
            np.random.randn(100, 159),
            columns=[f'factor_{i}' for i in range(158)] + ['label']
        )
        mock_df.index = pd.MultiIndex.from_tuples(
            [(pd.Timestamp('2020-01-01'), f'SH60000{i}') for i in range(100)],
            names=['datetime', 'instrument']
        )
        mock_handler.fetch.return_value = mock_df
        mock_alpha158.return_value = mock_handler

        # 模拟模型
        mock_model_instance = Mock()
        mock_lgb_model.return_value = mock_model_instance

        # 训练模型
        model = tool.train_model(
            instruments='csi300',
            start_time='2018-01-01',
            end_time='2020-12-31',
            save_model=False
        )

        # 验证
        assert mock_alpha158.called
        assert mock_model_instance.fit.called

    def test_load_model_not_found(self, tool):
        """测试加载不存在的模型"""
        with pytest.raises(FileNotFoundError, match="没有找到预训练模型"):
            tool.load_model()

    def test_load_model_success(self, tool, temp_model_dir):
        """测试加载存在的模型"""
        import pickle
        from sklearn.ensemble import GradientBoostingRegressor

        # 创建一个简单的模型（可以 pickle）
        mock_model = GradientBoostingRegressor(n_estimators=10)
        mock_model.fit(np.random.rand(10, 5), np.random.rand(10))

        model_path = Path(temp_model_dir) / 'gbdt_test.pkl'
        with open(model_path, 'wb') as f:
            pickle.dump(mock_model, f)

        # 加载模型
        loaded_model = tool.load_model(str(model_path))
        assert loaded_model is not None

    def test_get_confidence_no_history(self, tool):
        """测试获取置信度（无历史数据）"""
        confidence = tool.get_confidence('SH600519')
        assert 0 <= confidence <= 1
        assert confidence == 0.5  # 默认置信度

    def test_update_prediction_history(self, tool, temp_model_dir):
        """测试更新预测历史"""
        stock_code = 'SH600519'

        # 更新历史
        tool.update_prediction_history(
            stock_code=stock_code,
            predicted_direction=1,
            actual_direction=1
        )

        # 验证文件创建
        history_file = Path(temp_model_dir) / 'prediction_history.csv'
        assert history_file.exists()

        # 读取并验证
        history = pd.read_csv(history_file)
        assert len(history) == 1
        assert history.iloc[0]['stock_code'] == stock_code
        assert history.iloc[0]['predicted_direction'] == 1
        assert history.iloc[0]['actual_direction'] == 1

    def test_get_confidence_with_history(self, tool, temp_model_dir):
        """测试获取置信度（有历史数据）"""
        stock_code = 'SH600519'

        # 创建历史数据
        history_data = pd.DataFrame([
            {'stock_code': stock_code, 'predicted_direction': 1, 'actual_direction': 1, 'timestamp': '2020-01-01'},
            {'stock_code': stock_code, 'predicted_direction': 1, 'actual_direction': 1, 'timestamp': '2020-01-02'},
            {'stock_code': stock_code, 'predicted_direction': 1, 'actual_direction': -1, 'timestamp': '2020-01-03'},
            {'stock_code': stock_code, 'predicted_direction': -1, 'actual_direction': -1, 'timestamp': '2020-01-04'},
        ])

        history_file = Path(temp_model_dir) / 'prediction_history.csv'
        history_data.to_csv(history_file, index=False)

        # 获取置信度
        confidence = tool.get_confidence(stock_code)

        # 准确率应该是 3/4 = 0.75
        assert confidence == 0.75

    @patch('src.tools.gbdt_tool.qlib.init')
    @patch('src.tools.gbdt_tool.Alpha158')
    def test_predict_integration(
        self,
        mock_alpha158,
        mock_qlib_init,
        tool,
        temp_model_dir
    ):
        """测试预测集成（完整流程）"""
        import pickle
        from sklearn.ensemble import GradientBoostingRegressor

        # 创建一个简单的模型（可以 pickle）
        mock_model = GradientBoostingRegressor(n_estimators=10)
        mock_model.fit(np.random.rand(10, 158), np.random.rand(10))

        # 保存模型
        model_path = Path(temp_model_dir) / 'gbdt_test.pkl'
        with open(model_path, 'wb') as f:
            pickle.dump(mock_model, f)

        # 加载模型
        tool.load_model(str(model_path))

        # Mock predict 方法返回固定值
        with patch.object(tool._model, 'predict', return_value=np.array([0.025])):
            # 模拟 Alpha158 数据
            mock_handler = Mock()
            mock_df = pd.DataFrame(
                np.random.randn(10, 159),
                columns=[f'factor_{i}' for i in range(158)] + ['label']
            )
            mock_df.index = pd.MultiIndex.from_tuples(
                [(pd.Timestamp('2020-01-01'), 'SH600519') for _ in range(10)],
                names=['datetime', 'instrument']
            )
            mock_handler.fetch.return_value = mock_df
            mock_alpha158.return_value = mock_handler

            # 执行预测
            result = tool.predict('SH600519', horizon=5)

            # 验证结果
            assert 'prediction' in result
            assert 'confidence' in result
            assert 'horizon' in result
            assert 'stock_code' in result
            assert result['stock_code'] == 'SH600519'
            assert result['horizon'] == 5
            assert result['prediction'] == 0.025


class TestQlibGBDTPredictionToolEdgeCases:
    """边界条件测试"""

    @pytest.fixture
    def tool(self):
        """创建工具实例"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield QlibGBDTPredictionTool(
                qlib_provider='~/.qlib/qlib_data/cn_data',
                model_dir=temp_dir
            )

    def test_predict_stock_not_in_data(self, tool):
        """测试预测数据中不存在的股票"""
        with patch('src.tools.gbdt_tool.qlib.init'):
            with patch('src.tools.gbdt_tool.Alpha158') as mock_alpha158:
                # 模拟带正确 MultiIndex 的数据，但不包含目标股票
                mock_handler = Mock()
                mock_df = pd.DataFrame(
                    np.random.randn(10, 159),
                    columns=[f'factor_{i}' for i in range(158)] + ['label']
                )
                # 创建包含其他股票的 MultiIndex
                mock_df.index = pd.MultiIndex.from_tuples(
                    [(pd.Timestamp('2020-01-01'), f'SH60000{i}') for i in range(10)],
                    names=['datetime', 'instrument']
                )
                mock_handler.fetch.return_value = mock_df
                mock_alpha158.return_value = mock_handler

                # 设置一个模拟模型
                tool._model = Mock()

                # ValueError 被 RuntimeError 包装
                with pytest.raises(RuntimeError, match="预测失败"):
                    tool.predict('INVALID_CODE', horizon=5)

    def test_model_dir_creation(self):
        """测试模型目录自动创建"""
        with tempfile.TemporaryDirectory() as temp_dir:
            new_dir = Path(temp_dir) / 'new_model_dir'
            assert not new_dir.exists()

            tool = QlibGBDTPredictionTool(model_dir=str(new_dir))
            assert new_dir.exists()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
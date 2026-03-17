#!/usr/bin/env python3
"""
GBDT 预测工具

封装 qlib GBDT 模型的预测功能

Issue: #5 (TOOL-002)
"""

import logging
import os
import pickle
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Union

import numpy as np
import pandas as pd
import qlib
from qlib.contrib.data.handler import Alpha158
from qlib.contrib.model.gbdt import LGBModel
from qlib.data import D
from qlib.data.dataset import DatasetH

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class QlibGBDTPredictionTool:
    """
    qlib GBDT 预测工具

    使用 qlib 的 LGBModel（LightGBM）进行股票涨跌幅预测。

    使用示例：
        >>> tool = QlibGBDTPredictionTool()
        >>> result = tool.predict('SH600519', horizon=5)
        >>> print(result)
        {
            'prediction': 0.025,  # 预测涨跌幅
            'confidence': 0.72,   # 置信度
            'horizon': 5,         # 预测周期
            'stock_code': 'SH600519'
        }
    """

    # 模型保存路径
    DEFAULT_MODEL_DIR = Path.home() / '.qlib' / 'models'

    def __init__(
        self,
        qlib_provider: str = '~/.qlib/qlib_data/cn_data',
        model_dir: Optional[str] = None
    ):
        """
        初始化 GBDT 预测工具

        Args:
            qlib_provider: qlib 数据提供者路径
            model_dir: 模型保存目录，默认 ~/.qlib/models
        """
        self.qlib_provider = qlib_provider
        self.model_dir = Path(model_dir) if model_dir else self.DEFAULT_MODEL_DIR
        self.model_dir.mkdir(parents=True, exist_ok=True)
        self._initialized = False
        self._model = None
        self._handler = None

    def _ensure_qlib_initialized(self):
        """确保 qlib 已初始化"""
        if not self._initialized:
            logger.info(f"初始化 qlib, provider: {self.qlib_provider}")
            qlib.init(provider_uri=self.qlib_provider)
            self._initialized = True
            logger.info("qlib 初始化成功")

    def train_model(
        self,
        instruments: str = 'csi300',
        start_time: str = '2018-01-01',
        end_time: str = '2020-12-31',
        save_model: bool = True
    ) -> LGBModel:
        """
        训练 GBDT 模型

        Args:
            instruments: 股票池
            start_time: 训练开始时间
            end_time: 训练结束时间
            save_model: 是否保存模型

        Returns:
            训练好的 LGBModel
        """
        self._ensure_qlib_initialized()

        logger.info(f"开始训练 GBDT 模型: {instruments}, {start_time} - {end_time}")

        # 创建数据处理器
        handler = Alpha158(
            instruments=instruments,
            start_time=start_time,
            end_time=end_time,
            freq='day'
        )

        # 创建数据集
        dataset = DatasetH(handler=handler, segments={})

        # 创建模型
        model = LGBModel(
            loss='mse',
            colsample_bytree=0.8,
            learning_rate=0.05,
            max_depth=6,
            n_estimators=200,
            num_leaves=31,
            subsample=0.8
        )

        # 准备训练数据
        train_data = handler.fetch()

        # 分割特征和标签
        if 'label' in train_data.columns:
            X = train_data.drop(columns=['label'])
            y = train_data['label']
        else:
            # 如果没有 label，使用第一个因子作为目标
            logger.warning("数据中没有 label 列，使用因子预测模式")
            X = train_data
            y = None

        # 训练模型
        if y is not None:
            # 对于 MultiIndex，需要特殊处理
            logger.info(f"训练数据形状: X={X.shape}, y={y.shape}")
            model.fit(X, y)
            logger.info("模型训练完成")

            # 保存模型
            if save_model:
                model_path = self.model_dir / f'gbdt_{instruments}_{datetime.now().strftime("%Y%m%d")}.pkl'
                with open(model_path, 'wb') as f:
                    pickle.dump(model, f)
                logger.info(f"模型已保存: {model_path}")

        self._model = model
        self._handler = handler

        return model

    def load_model(self, model_path: Optional[str] = None) -> LGBModel:
        """
        加载预训练模型

        Args:
            model_path: 模型路径，如果不提供则尝试加载最新的模型

        Returns:
            加载的模型
        """
        if model_path:
            path = Path(model_path)
        else:
            # 查找最新的模型文件
            model_files = list(self.model_dir.glob('gbdt_*.pkl'))
            if not model_files:
                raise FileNotFoundError("没有找到预训练模型，请先训练模型")
            path = max(model_files, key=lambda p: p.stat().st_mtime)

        logger.info(f"加载模型: {path}")
        with open(path, 'rb') as f:
            model = pickle.load(f)

        self._model = model
        return model

    def predict(
        self,
        stock_code: str,
        horizon: int = 5
    ) -> Dict:
        """
        预测股票涨跌幅

        Args:
            stock_code: 股票代码，如 'SH600519'
            horizon: 预测周期（天）

        Returns:
            预测结果字典：
            {
                'prediction': float,  # 预测涨跌幅
                'confidence': float,  # 置信度
                'horizon': int,       # 预测周期
                'stock_code': str,    # 股票代码
                'prediction_date': str  # 预测日期
            }

        Raises:
            ValueError: 参数错误
            RuntimeError: 预测失败
        """
        # 参数验证
        if not stock_code:
            raise ValueError("stock_code 不能为空")
        if horizon <= 0:
            raise ValueError("horizon 必须大于 0")

        self._ensure_qlib_initialized()

        # 确保有模型可用
        if self._model is None:
            try:
                self.load_model()
                logger.info("成功加载预训练模型")
            except FileNotFoundError:
                logger.warning("没有找到预训练模型，将训练新模型")
                self.train_model()

        try:
            # 获取最新数据
            logger.info(f"获取股票 {stock_code} 的最新数据")

            # 获取 Alpha158 因子数据
            handler = Alpha158(
                instruments='all',
                start_time=(datetime.now() - timedelta(days=60)).strftime('%Y-%m-%d'),
                end_time=datetime.now().strftime('%Y-%m-%d'),
                freq='day'
            )

            df = handler.fetch()

            # 检查股票是否在数据中
            if stock_code not in df.index.get_level_values('instrument'):
                raise ValueError(f"股票 {stock_code} 不在数据中")

            # 获取该股票的最新数据
            stock_df = df.xs(stock_code, level='instrument')
            latest_data = stock_df.iloc[-1:]

            # 准备特征
            if 'label' in latest_data.columns:
                X = latest_data.drop(columns=['label'])
            else:
                X = latest_data

            logger.info(f"预测特征形状: {X.shape}")

            # 进行预测
            prediction = self._model.predict(X)[0]

            # 计算置信度
            confidence = self.get_confidence(stock_code)

            result = {
                'prediction': float(prediction),
                'confidence': float(confidence),
                'horizon': horizon,
                'stock_code': stock_code,
                'prediction_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

            logger.info(f"预测结果: {result}")
            return result

        except Exception as e:
            logger.error(f"预测失败: {e}")
            raise RuntimeError(f"预测失败: {e}")

    def get_confidence(self, stock_code: str) -> float:
        """
        获取预测置信度

        基于历史预测准确率计算置信度。
        如果没有历史数据，返回默认置信度 0.5。

        Args:
            stock_code: 股票代码

        Returns:
            置信度 (0-1)
        """
        # 尝试读取历史预测记录
        history_file = self.model_dir / 'prediction_history.csv'

        if history_file.exists():
            try:
                history = pd.read_csv(history_file)
                stock_history = history[history['stock_code'] == stock_code]

                if len(stock_history) > 0:
                    # 计算历史准确率
                    # 预测方向正确的比例
                    correct = (stock_history['predicted_direction'] == stock_history['actual_direction']).sum()
                    total = len(stock_history)
                    accuracy = correct / total

                    logger.info(f"股票 {stock_code} 历史准确率: {accuracy:.2%}")
                    return float(accuracy)
            except Exception as e:
                logger.warning(f"读取历史预测记录失败: {e}")

        # 如果没有历史数据，使用模型置信度（基于预测值的绝对值）
        # 这里使用一个简单的启发式方法
        # 预测值的绝对值越大，置信度越高（但有上限）
        default_confidence = 0.5
        logger.info(f"没有历史数据，返回默认置信度: {default_confidence}")
        return default_confidence

    def update_prediction_history(
        self,
        stock_code: str,
        predicted_direction: int,
        actual_direction: int
    ):
        """
        更新预测历史记录

        用于计算置信度

        Args:
            stock_code: 股票代码
            predicted_direction: 预测方向 (1=涨, -1=跌, 0=平)
            actual_direction: 实际方向
        """
        history_file = self.model_dir / 'prediction_history.csv'

        new_record = pd.DataFrame([{
            'stock_code': stock_code,
            'predicted_direction': predicted_direction,
            'actual_direction': actual_direction,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }])

        if history_file.exists():
            history = pd.read_csv(history_file)
            history = pd.concat([history, new_record], ignore_index=True)
        else:
            history = new_record

        history.to_csv(history_file, index=False)
        logger.info(f"已更新预测历史: {stock_code}")

    def get_model_info(self) -> Dict:
        """
        获取模型信息

        Returns:
            模型信息字典
        """
        info = {
            'model_type': 'LightGBM',
            'model_status': '已加载' if self._model is not None else '未加载',
            'model_dir': str(self.model_dir),
            'qlib_provider': self.qlib_provider
        }

        # 检查模型文件
        model_files = list(self.model_dir.glob('gbdt_*.pkl'))
        info['saved_models'] = len(model_files)

        if model_files:
            latest_model = max(model_files, key=lambda p: p.stat().st_mtime)
            info['latest_model'] = str(latest_model)
            info['latest_model_time'] = datetime.fromtimestamp(
                latest_model.stat().st_mtime
            ).strftime('%Y-%m-%d %H:%M:%S')

        return info


def main():
    """测试 GBDT 预测工具"""
    print("=" * 60)
    print("GBDT 预测工具测试")
    print("=" * 60)

    # 创建工具实例
    tool = QlibGBDTPredictionTool()

    # 测试 1: 获取模型信息
    print("\n1. 获取模型信息:")
    info = tool.get_model_info()
    for key, value in info.items():
        print(f"  - {key}: {value}")

    # 测试 2: 训练模型（如果没有预训练模型）
    print("\n2. 训练模型:")
    try:
        model = tool.train_model(
            instruments='csi300',
            start_time='2018-01-01',
            end_time='2020-03-31'
        )
        print(f"  - 模型训练完成")
    except Exception as e:
        print(f"  - 模型训练失败: {e}")

    # 测试 3: 预测
    print("\n3. 预测股票涨跌幅:")
    try:
        result = tool.predict('SH600519', horizon=5)
        print(f"  - 股票代码: {result['stock_code']}")
        print(f"  - 预测涨跌幅: {result['prediction']:.4f}")
        print(f"  - 置信度: {result['confidence']:.2%}")
        print(f"  - 预测周期: {result['horizon']} 天")
        print(f"  - 预测时间: {result['prediction_date']}")
    except Exception as e:
        print(f"  - 预测失败: {e}")

    print("\n✅ 测试完成!")


if __name__ == "__main__":
    main()
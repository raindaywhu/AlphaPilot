#!/usr/bin/env python3
"""
GBDT 预测工具

封装 qlib GBDT/XGBoost 模型的预测能力

Issue: #5 (TOOL-002)
"""

import logging
from typing import Dict, Optional, Union
from datetime import datetime, timedelta

import pandas as pd
import numpy as np
import qlib
from qlib.contrib.model.gbdt import LGBModel
from qlib.contrib.data.handler import Alpha158
from qlib.data.dataset import DatasetH

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class QlibGBDTPredictionTool:
    """
    GBDT 预测工具

    封装 qlib GBDT/XGBoost 模型的预测能力，提供简洁的 API 供 Agent 使用。

    使用示例：
        >>> tool = QlibGBDTPredictionTool()
        >>> result = tool.predict('SH600000', horizon=5)
        >>> print(result)
        >>> confidence = tool.get_confidence('SH600000')
        >>> print(f"置信度: {confidence}")
    """

    def __init__(
        self,
        qlib_provider: str = '~/.qlib/qlib_data/cn_data',
        model_path: Optional[str] = None
    ):
        """
        初始化 GBDT 预测工具

        Args:
            qlib_provider: qlib 数据提供者路径
            model_path: 预训练模型路径（可选）
        """
        self.qlib_provider = qlib_provider
        self.model_path = model_path
        self._initialized = False
        self._model = None
        self._dataset = None

    def _ensure_initialized(self):
        """确保 qlib 和模型已初始化"""
        if not self._initialized:
            logger.info(f"初始化 qlib, provider: {self.qlib_provider}")
            qlib.init(provider_uri=self.qlib_provider)
            
            # 初始化模型
            self._init_model()
            
            self._initialized = True
            logger.info("GBDT 工具初始化成功")

    def _init_model(self):
        """初始化 GBDT 模型"""
        # 使用 qlib 的 LGBModel（LightGBT）
        self._model = LGBModel(
            loss='mse',
            colsample_bytree=0.8879,
            learning_rate=0.0421,
            subsample=0.8789,
            lambda_l1=205.6999,
            lambda_l2=580.9768,
            max_depth=8,
            num_leaves=210,
            min_child_samples=20,
        )
        
        logger.info("GBDT 模型初始化完成")

    def predict(
        self,
        stock_code: str,
        horizon: int = 5,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None
    ) -> Dict:
        """
        预测股票涨跌幅

        Args:
            stock_code: 股票代码，如 'SH600000'
            horizon: 预测周期（天），默认 5 天
            start_time: 训练数据开始时间
            end_time: 训练数据结束时间

        Returns:
            dict: 预测结果
                - stock_code: 股票代码
                - prediction: 预测涨跌幅
                - horizon: 预测周期
                - timestamp: 预测时间
                - confidence: 置信度
        """
        # 默认使用最近 1 年的数据
        if end_time is None:
            end_time = datetime.now().strftime('%Y-%m-%d')
        if start_time is None:
            start_time = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
        
        logger.info(f"预测股票 {stock_code}, 周期 {horizon} 天")
        
        try:
            # 确保 qlib 已初始化（移到 try 块内）
            self._ensure_initialized()
            # 创建数据集
            dataset = self._create_dataset(
                instruments=[stock_code],
                start_time=start_time,
                end_time=end_time,
                horizon=horizon
            )
            
            # 训练模型
            logger.info("训练 GBDT 模型...")
            self._model.fit(dataset)
            
            # 预测
            predictions = self._model.predict(dataset)
            
            # 获取最新预测值
            if isinstance(predictions, pd.DataFrame):
                pred_value = predictions.iloc[-1].values[0]
            else:
                pred_value = float(predictions[-1])
            
            # 计算置信度
            confidence = self._calculate_confidence(dataset, predictions)
            
            result = {
                'stock_code': stock_code,
                'prediction': float(pred_value),
                'horizon': horizon,
                'timestamp': datetime.now().isoformat(),
                'confidence': confidence,
                'model': 'GBDT',
                'status': 'success'
            }
            
            logger.info(f"预测完成: {stock_code} 预测涨跌幅 {pred_value:.4f}, 置信度 {confidence:.2f}")
            
            return result
            
        except Exception as e:
            logger.error(f"预测失败: {e}")
            return {
                'stock_code': stock_code,
                'prediction': None,
                'horizon': horizon,
                'timestamp': datetime.now().isoformat(),
                'confidence': 0.0,
                'model': 'GBDT',
                'status': 'error',
                'error': str(e)
            }

    def get_confidence(self, stock_code: str) -> float:
        """
        获取预测置信度

        Args:
            stock_code: 股票代码

        Returns:
            float: 置信度 (0.0 - 1.0)
        """
        self._ensure_initialized()
        
        # 使用最近预测结果计算置信度
        # 这里简化处理，实际应该基于模型验证集表现
        try:
            # 快速训练并评估
            result = self.predict(stock_code, horizon=5)
            return result.get('confidence', 0.0)
        except Exception as e:
            logger.error(f"获取置信度失败: {e}")
            return 0.0

    def _create_dataset(
        self,
        instruments: list,
        start_time: str,
        end_time: str,
        horizon: int = 5
    ) -> DatasetH:
        """
        创建 qlib 数据集

        Args:
            instruments: 股票列表
            start_time: 开始时间
            end_time: 结束时间
            horizon: 预测周期

        Returns:
            DatasetH: qlib 数据集
        """
        # 使用 Alpha158 因子
        dataset = DatasetH(
            handler={
                "class": Alpha158,
                "module_path": "qlib.contrib.data.handler",
                "kwargs": {
                    "start_time": start_time,
                    "end_time": end_time,
                    "fit_start_time": start_time,
                    "fit_end_time": end_time,
                    "instruments": instruments,
                },
            },
            segments={
                "train": (start_time, end_time),
            },
        )
        
        return dataset

    def _calculate_confidence(
        self,
        dataset: DatasetH,
        predictions: Union[pd.DataFrame, np.ndarray]
    ) -> float:
        """
        计算预测置信度

        Args:
            dataset: 数据集
            predictions: 预测结果

        Returns:
            float: 置信度 (0.0 - 1.0)
        """
        try:
            # 获取标签
            df = dataset.prepare("train")
            if df is None or len(df) == 0:
                return 0.5
            
            labels = df['label'].values
            
            # 计算训练集上的 R² 分数
            if isinstance(predictions, pd.DataFrame):
                pred_values = predictions.values.flatten()
            else:
                pred_values = np.array(predictions).flatten()
            
            # 确保长度一致
            min_len = min(len(labels), len(pred_values))
            labels = labels[-min_len:]
            pred_values = pred_values[-min_len:]
            
            # 计算 R² 分数
            ss_res = np.sum((labels - pred_values) ** 2)
            ss_tot = np.sum((labels - np.mean(labels)) ** 2)
            
            if ss_tot == 0:
                return 0.5
            
            r2 = 1 - (ss_res / ss_tot)
            
            # 将 R² 转换为 0-1 范围的置信度
            confidence = max(0.0, min(1.0, (r2 + 1) / 2))
            
            return float(confidence)
            
        except Exception as e:
            logger.warning(f"计算置信度失败: {e}, 返回默认值 0.5")
            return 0.5

    def train_and_save(
        self,
        instruments: str = 'csi300',
        start_time: str = '2018-01-01',
        end_time: str = '2020-12-31',
        save_path: str = 'models/gbdt_model.pkl'
    ) -> Dict:
        """
        训练并保存模型

        Args:
            instruments: 股票池
            start_time: 开始时间
            end_time: 结束时间
            save_path: 保存路径

        Returns:
            dict: 训练结果
        """
        self._ensure_initialized()
        
        logger.info(f"训练模型: {instruments}, {start_time} - {end_time}")
        
        try:
            # 创建数据集
            dataset = DatasetH(
                handler={
                    "class": Alpha158,
                    "module_path": "qlib.contrib.data.handler",
                    "kwargs": {
                        "start_time": start_time,
                        "end_time": end_time,
                        "fit_start_time": start_time,
                        "fit_end_time": end_time,
                        "instruments": instruments,
                    },
                },
                segments={
                    "train": (start_time, end_time),
                },
            )
            
            # 训练模型
            self._model.fit(dataset)
            
            # 保存模型
            import os
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            import pickle
            with open(save_path, 'wb') as f:
                pickle.dump(self._model, f)
            
            logger.info(f"模型已保存到 {save_path}")
            
            return {
                'status': 'success',
                'save_path': save_path,
                'instruments': instruments,
                'train_period': f"{start_time} - {end_time}"
            }
            
        except Exception as e:
            logger.error(f"训练失败: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }


if __name__ == '__main__':
    # 测试代码
    tool = QlibGBDTPredictionTool()
    
    print("测试 GBDT 预测工具...")
    print("=" * 60)
    
    # 预测单只股票
    result = tool.predict('SH600000', horizon=5)
    print(f"\n预测结果: {result}")
    
    # 获取置信度
    confidence = tool.get_confidence('SH600000')
    print(f"\n置信度: {confidence}")
    
    print("\n" + "=" * 60)
    print("测试完成")
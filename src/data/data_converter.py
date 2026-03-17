"""
数据格式转换器

将 mootdx 数据转换为 qlib 格式。

任务ID: DATA-003
类型: 开发任务
优先级: P1
层级: data-layer
"""

import struct
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Union

import pandas as pd
import numpy as np


class DataConverter:
    """
    数据格式转换器
    
    功能：
    1. 将 mootdx DataFrame 转换为 qlib 格式
    2. 验证数据格式是否符合 qlib 要求
    3. 支持批量转换和单条转换
    4. 支持二进制文件写入
    
    qlib 数据格式说明：
    - 文件位置: features/{stock_code}/{stock_code}_{date}.bin
    - 数据格式: float32 序列 [open, close, high, low, volume, amount]
    
    mootdx 数据格式：
    - DataFrame: date, open, high, low, close, volume, amount, code
    
    使用示例：
        converter = DataConverter()
        
        # 转换 DataFrame
        qlib_df = converter.convert_to_qlib_format(mootdx_data)
        
        # 验证格式
        is_valid = converter.validate_qlib_format(qlib_df)
        
        # 写入二进制文件
        converter.write_qlib_binary(qlib_df, output_dir)
    """
    
    # qlib 标准列顺序
    QLIB_COLUMNS = ['open', 'close', 'high', 'low', 'volume', 'amount']
    
    # mootdx 到 qlib 列映射
    COLUMN_MAPPING = {
        'datetime': 'date',
        'date': 'date',
        'open': 'open',
        'close': 'close',
        'high': 'high',
        'low': 'low',
        'volume': 'volume',
        'vol': 'volume',
        'amount': 'amount',
        'code': 'instrument'
    }
    
    def __init__(self, output_dir: Optional[str] = None):
        """
        初始化数据转换器
        
        Args:
            output_dir: 输出目录，用于存储 qlib 二进制文件
        """
        self.output_dir = Path(output_dir) if output_dir else None
    
    def convert_to_qlib_format(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        将 mootdx 数据转换为 qlib 格式
        
        转换步骤：
        1. 标准化列名
        2. 确保必需字段存在
        3. 重排列顺序为 qlib 标准顺序
        4. 添加 instrument 列（股票代码）
        5. 数据类型转换
        
        Args:
            data: mootdx 数据 DataFrame，包含列：
                - date/datetime: 日期
                - open: 开盘价
                - high: 最高价
                - low: 最低价
                - close: 收盘价
                - volume/vol: 成交量
                - amount: 成交额
                - code: 股票代码
        
        Returns:
            pd.DataFrame: qlib 格式数据，包含列：
                - instrument: 股票代码
                - datetime: 日期时间
                - open: 开盘价
                - close: 收盘价
                - high: 最高价
                - low: 最低价
                - volume: 成交量
                - amount: 成交额
        
        Raises:
            ValueError: 数据格式错误或缺少必需字段
        """
        if data is None or data.empty:
            raise ValueError("输入数据为空")
        
        # 复制数据避免修改原数据
        df = data.copy()
        
        # 1. 标准化列名
        df = self._normalize_columns(df)
        
        # 2. 确保必需字段存在
        required_fields = ['date', 'open', 'close', 'high', 'low', 'volume']
        missing_fields = [f for f in required_fields if f not in df.columns]
        if missing_fields:
            raise ValueError(f"缺少必需字段: {missing_fields}")
        
        # 3. 确保 amount 字段存在（可选）
        if 'amount' not in df.columns:
            df['amount'] = 0.0
        
        # 4. 确保 instrument 字段存在
        if 'instrument' not in df.columns:
            if 'code' in data.columns:
                df['instrument'] = data['code']
            else:
                raise ValueError("缺少股票代码字段 (code 或 instrument)")
        
        # 5. 日期格式标准化
        df = self._normalize_datetime(df)
        
        # 6. 数据类型转换
        df = self._convert_dtypes(df)
        
        # 7. 重命名 date 为 datetime (qlib 标准)
        if 'date' in df.columns:
            df = df.rename(columns={'date': 'datetime'})
        
        # 8. 按 qlib 标准顺序重排列
        final_columns = ['instrument', 'datetime'] + self.QLIB_COLUMNS
        df = df[final_columns]
        
        # 9. 排序
        df = df.sort_values(['instrument', 'datetime']).reset_index(drop=True)
        
        return df
    
    def validate_qlib_format(self, data: pd.DataFrame) -> bool:
        """
        验证数据是否符合 qlib 格式要求
        
        验证项：
        1. 必需字段存在
        2. 数据类型正确
        3. 无空值（或可接受的空值比例）
        4. 数值范围合理
        5. 日期格式正确
        
        Args:
            data: 待验证的 DataFrame
        
        Returns:
            bool: 是否符合 qlib 格式要求
        """
        if data is None or data.empty:
            return False
        
        try:
            # 1. 检查必需字段
            required_columns = ['instrument', 'datetime'] + self.QLIB_COLUMNS
            missing = [col for col in required_columns if col not in data.columns]
            if missing:
                print(f"缺少必需字段: {missing}")
                return False
            
            # 2. 检查数据类型
            # datetime 应该是 datetime 类型
            if not pd.api.types.is_datetime64_any_dtype(data['datetime']):
                # 尝试转换
                try:
                    pd.to_datetime(data['datetime'])
                except:
                    print("datetime 字段格式错误")
                    return False
            
            # 数值字段应该是数值类型
            numeric_columns = self.QLIB_COLUMNS
            for col in numeric_columns:
                if not pd.api.types.is_numeric_dtype(data[col]):
                    print(f"{col} 字段不是数值类型")
                    return False
            
            # 3. 检查空值比例
            null_ratio = data.isnull().sum().sum() / (len(data) * len(data.columns))
            if null_ratio > 0.1:  # 空值比例超过 10%
                print(f"空值比例过高: {null_ratio:.2%}")
                return False
            
            # 4. 检查数值范围
            # 价格应该为正数
            price_columns = ['open', 'close', 'high', 'low']
            for col in price_columns:
                if (data[col] <= 0).any():
                    # 允许少量异常值（可能是停牌等）
                    neg_ratio = (data[col] <= 0).sum() / len(data)
                    if neg_ratio > 0.05:
                        print(f"{col} 包含过多非正值: {neg_ratio:.2%}")
                        return False
            
            # 成交量应该非负
            if (data['volume'] < 0).any():
                print("volume 包含负值")
                return False
            
            # 成交额应该非负
            if 'amount' in data.columns and (data['amount'] < 0).any():
                print("amount 包含负值")
                return False
            
            # 5. 检查价格逻辑
            # high >= low
            invalid_prices = data['high'] < data['low']
            if invalid_prices.any():
                invalid_ratio = invalid_prices.sum() / len(data)
                if invalid_ratio > 0.01:  # 允许 1% 的异常
                    print(f"价格逻辑错误 (high < low): {invalid_ratio:.2%}")
                    return False
            
            # 6. 检查 instrument 格式
            # 应该是 sh/sz 开头的代码
            valid_instruments = data['instrument'].str.match(r'^(sh|sz)\d{6}$')
            if not valid_instruments.all():
                invalid_ratio = (~valid_instruments).sum() / len(data)
                if invalid_ratio > 0.01:
                    print(f"instrument 格式错误: {invalid_ratio:.2%}")
                    return False
            
            return True
            
        except Exception as e:
            print(f"验证过程出错: {e}")
            return False
    
    def write_qlib_binary(
        self,
        data: pd.DataFrame,
        output_dir: Optional[Union[str, Path]] = None
    ) -> int:
        """
        将数据写入 qlib 二进制格式
        
        qlib 二进制格式说明：
        - 每个股票每天一个文件
        - 文件路径: {output_dir}/features/{instrument}/{instrument}_{date}.bin
        - 文件内容: 6 个 float32 值 [open, close, high, low, volume, amount]
        
        Args:
            data: qlib 格式的 DataFrame
            output_dir: 输出目录，默认使用初始化时设置的目录
        
        Returns:
            int: 成功写入的数据条数
        
        Raises:
            ValueError: 数据格式错误或输出目录未设置
        """
        # 验证数据格式
        if not self.validate_qlib_format(data):
            raise ValueError("数据格式不符合 qlib 要求")
        
        # 确定输出目录
        out_dir = Path(output_dir) if output_dir else self.output_dir
        if out_dir is None:
            raise ValueError("未设置输出目录")
        
        # 确保目录存在
        features_dir = out_dir / "features"
        features_dir.mkdir(parents=True, exist_ok=True)
        
        success_count = 0
        
        # 按股票分组处理
        for instrument, group in data.groupby('instrument'):
            try:
                # 创建股票目录
                stock_dir = features_dir / instrument
                stock_dir.mkdir(parents=True, exist_ok=True)
                
                # 逐日写入
                for _, row in group.iterrows():
                    try:
                        # 提取日期
                        date = row['datetime']
                        if isinstance(date, pd.Timestamp):
                            date_str = date.strftime("%Y-%m-%d")
                        else:
                            date_str = pd.to_datetime(date).strftime("%Y-%m-%d")
                        
                        # 提取特征值
                        features = [
                            float(row['open']),
                            float(row['close']),
                            float(row['high']),
                            float(row['low']),
                            float(row['volume']),
                            float(row['amount'])
                        ]
                        
                        # 写入二进制文件
                        file_path = stock_dir / f"{instrument}_{date_str}.bin"
                        with open(file_path, 'wb') as f:
                            for feature in features:
                                f.write(struct.pack('f', feature))
                        
                        success_count += 1
                        
                    except Exception as e:
                        continue
                
            except Exception as e:
                continue
        
        return success_count
    
    def convert_and_save(
        self,
        data: pd.DataFrame,
        output_dir: Optional[Union[str, Path]] = None
    ) -> Dict[str, Union[int, bool, str]]:
        """
        转换并保存数据（一站式方法）
        
        Args:
            data: mootdx 格式的 DataFrame
            output_dir: 输出目录
        
        Returns:
            dict: 包含转换结果信息
                - success: 是否成功
                - converted_rows: 转换的行数
                - saved_files: 保存的文件数
                - message: 结果消息
        """
        result = {
            'success': False,
            'converted_rows': 0,
            'saved_files': 0,
            'message': ''
        }
        
        try:
            # 1. 转换格式
            qlib_data = self.convert_to_qlib_format(data)
            result['converted_rows'] = len(qlib_data)
            
            # 2. 验证格式
            if not self.validate_qlib_format(qlib_data):
                result['message'] = '数据格式验证失败'
                return result
            
            # 3. 保存文件
            if output_dir or self.output_dir:
                saved = self.write_qlib_binary(qlib_data, output_dir)
                result['saved_files'] = saved
                result['message'] = f'成功转换 {result["converted_rows"]} 条数据，保存 {saved} 个文件'
            else:
                result['message'] = f'成功转换 {result["converted_rows"]} 条数据（未保存到文件）'
            
            result['success'] = True
            return result
            
        except Exception as e:
            result['message'] = f'转换失败: {str(e)}'
            return result
    
    def get_conversion_info(self, data: pd.DataFrame) -> Dict:
        """
        获取数据转换信息（不执行转换）
        
        Args:
            data: 待转换的数据
        
        Returns:
            dict: 转换信息
        """
        info = {
            'input_rows': len(data) if data is not None else 0,
            'input_columns': list(data.columns) if data is not None else [],
            'output_columns': ['instrument', 'datetime'] + self.QLIB_COLUMNS,
            'can_convert': True,
            'issues': []
        }
        
        if data is None or data.empty:
            info['can_convert'] = False
            info['issues'].append('输入数据为空')
            return info
        
        # 检查必需字段
        required = ['date', 'open', 'close', 'high', 'low', 'volume']
        available = set(data.columns.str.lower())
        missing = [f for f in required if f not in available]
        
        if missing:
            info['can_convert'] = False
            info['issues'].append(f'缺少字段: {missing}')
        
        # 检查股票代码
        if 'code' not in data.columns and 'instrument' not in data.columns:
            info['can_convert'] = False
            info['issues'].append('缺少股票代码字段')
        
        return info
    
    # ========== 私有方法 ==========
    
    def _normalize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        标准化列名
        
        Args:
            df: 输入 DataFrame
        
        Returns:
            pd.DataFrame: 列名标准化后的 DataFrame
        """
        # 创建小写列名映射
        column_map = {col: col.lower() for col in df.columns}
        df = df.rename(columns=column_map)
        
        # 应用标准列名映射
        df = df.rename(columns=self.COLUMN_MAPPING)
        
        return df
    
    def _normalize_datetime(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        标准化日期时间格式
        
        Args:
            df: 输入 DataFrame
        
        Returns:
            pd.DataFrame: 日期时间标准化后的 DataFrame
        """
        if 'date' not in df.columns:
            return df
        
        # 转换为 datetime 类型
        try:
            df['date'] = pd.to_datetime(df['date'])
        except Exception as e:
            print(f"日期转换警告: {e}")
        
        return df
    
    def _convert_dtypes(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        转换数据类型
        
        Args:
            df: 输入 DataFrame
        
        Returns:
            pd.DataFrame: 类型转换后的 DataFrame
        """
        # 数值字段转换为 float64
        numeric_columns = self.QLIB_COLUMNS
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # instrument 转换为字符串
        if 'instrument' in df.columns:
            df['instrument'] = df['instrument'].astype(str)
        
        return df


# ========== 便捷函数 ==========

def convert_to_qlib(data: pd.DataFrame) -> pd.DataFrame:
    """
    转换数据为 qlib 格式（便捷函数）
    
    Args:
        data: mootdx 格式的 DataFrame
    
    Returns:
        pd.DataFrame: qlib 格式的 DataFrame
    """
    converter = DataConverter()
    return converter.convert_to_qlib_format(data)


def validate_data(data: pd.DataFrame) -> bool:
    """
    验证数据格式（便捷函数）
    
    Args:
        data: 待验证的 DataFrame
    
    Returns:
        bool: 是否符合 qlib 格式
    """
    converter = DataConverter()
    return converter.validate_qlib_format(data)


# ========== 命令行接口 ==========

def main():
    """
    命令行入口
    
    使用方法：
        python data_converter.py convert <input.csv> <output_dir>
        python data_converter.py validate <input.csv>
        python data_converter.py info <input.csv>
    """
    import sys
    
    if len(sys.argv) < 3:
        print("使用方法:")
        print("  python data_converter.py convert <input.csv> <output_dir>")
        print("  python data_converter.py validate <input.csv>")
        print("  python data_converter.py info <input.csv>")
        return
    
    command = sys.argv[1]
    input_file = sys.argv[2]
    
    # 读取输入文件
    try:
        data = pd.read_csv(input_file)
        print(f"读取数据: {len(data)} 行")
    except Exception as e:
        print(f"读取文件失败: {e}")
        return
    
    converter = DataConverter()
    
    if command == "convert":
        if len(sys.argv) < 4:
            print("请指定输出目录")
            return
        output_dir = sys.argv[3]
        result = converter.convert_and_save(data, output_dir)
        print(f"转换结果: {result}")
    
    elif command == "validate":
        # 先转换再验证
        try:
            qlib_data = converter.convert_to_qlib_format(data)
            is_valid = converter.validate_qlib_format(qlib_data)
            print(f"验证结果: {'✅ 通过' if is_valid else '❌ 失败'}")
        except Exception as e:
            print(f"验证失败: {e}")
    
    elif command == "info":
        info = converter.get_conversion_info(data)
        print("转换信息:")
        for key, value in info.items():
            print(f"  {key}: {value}")
    
    else:
        print(f"未知命令: {command}")


if __name__ == "__main__":
    main()
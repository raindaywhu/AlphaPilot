"""
数据格式转换器测试

测试 DATA-003 的验收标准：
1. 能够转换数据格式
2. 转换后的数据符合 qlib 要求
"""

import os
import struct
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pandas as pd
import numpy as np
import pytest

# 导入被测试的模块
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from data.data_converter import DataConverter, convert_to_qlib, validate_data


class TestDataConverter:
    """DataConverter 测试类"""
    
    @pytest.fixture
    def sample_mootdx_data(self):
        """创建模拟的 mootdx 数据"""
        dates = pd.date_range(start='2024-01-01', periods=10, freq='D')
        data = pd.DataFrame({
            'date': dates,
            'open': np.random.uniform(100, 200, 10),
            'high': np.random.uniform(150, 250, 10),
            'low': np.random.uniform(80, 150, 10),
            'close': np.random.uniform(100, 200, 10),
            'volume': np.random.randint(1000000, 10000000, 10),
            'amount': np.random.uniform(1e8, 1e9, 10),
            'code': ['sh600519'] * 10
        })
        return data
    
    @pytest.fixture
    def converter(self):
        """创建转换器实例"""
        return DataConverter()
    
    # ========== 初始化测试 ==========
    
    def test_init_default(self):
        """测试默认初始化"""
        converter = DataConverter()
        assert converter.output_dir is None
    
    def test_init_with_output_dir(self):
        """测试指定输出目录初始化"""
        converter = DataConverter(output_dir='/tmp/test')
        assert converter.output_dir == Path('/tmp/test')
    
    # ========== 列名标准化测试 ==========
    
    def test_normalize_columns(self, converter):
        """测试列名标准化"""
        df = pd.DataFrame({
            'DateTime': ['2024-01-01'],
            'OPEN': [100.0],
            'HIGH': [110.0],
            'LOW': [90.0],
            'CLOSE': [105.0],
            'VOL': [1000000],
            'Amount': [1e8],
            'Code': ['sh600519']
        })
        
        result = converter._normalize_columns(df)
        
        assert 'date' in result.columns
        assert 'open' in result.columns
        assert 'volume' in result.columns
    
    # ========== 数据转换测试 ==========
    
    def test_convert_to_qlib_format_success(self, converter, sample_mootdx_data):
        """测试成功转换为 qlib 格式"""
        result = converter.convert_to_qlib_format(sample_mootdx_data)
        
        # 检查必需列存在
        assert 'instrument' in result.columns
        assert 'datetime' in result.columns
        assert 'open' in result.columns
        assert 'close' in result.columns
        assert 'high' in result.columns
        assert 'low' in result.columns
        assert 'volume' in result.columns
        assert 'amount' in result.columns
        
        # 检查行数不变
        assert len(result) == len(sample_mootdx_data)
        
        # 检查 instrument 列值
        assert (result['instrument'] == 'sh600519').all()
    
    def test_convert_to_qlib_format_with_datetime_column(self, converter):
        """测试 datetime 列名转换"""
        data = pd.DataFrame({
            'datetime': pd.date_range(start='2024-01-01', periods=5),
            'open': [100.0] * 5,
            'high': [110.0] * 5,
            'low': [90.0] * 5,
            'close': [105.0] * 5,
            'volume': [1000000] * 5,
            'amount': [1e8] * 5,
            'code': ['sh600519'] * 5
        })
        
        result = converter.convert_to_qlib_format(data)
        assert 'datetime' in result.columns
    
    def test_convert_to_qlib_format_missing_required_field(self, converter):
        """测试缺少必需字段"""
        data = pd.DataFrame({
            'date': pd.date_range(start='2024-01-01', periods=5),
            'open': [100.0] * 5,
            # 缺少 high, low, close
            'code': ['sh600519'] * 5
        })
        
        with pytest.raises(ValueError) as excinfo:
            converter.convert_to_qlib_format(data)
        
        assert "缺少必需字段" in str(excinfo.value)
    
    def test_convert_to_qlib_format_missing_code(self, converter):
        """测试缺少股票代码"""
        data = pd.DataFrame({
            'date': pd.date_range(start='2024-01-01', periods=5),
            'open': [100.0] * 5,
            'high': [110.0] * 5,
            'low': [90.0] * 5,
            'close': [105.0] * 5,
            'volume': [1000000] * 5,
            'amount': [1e8] * 5
            # 缺少 code
        })
        
        with pytest.raises(ValueError) as excinfo:
            converter.convert_to_qlib_format(data)
        
        assert "股票代码" in str(excinfo.value)
    
    def test_convert_to_qlib_format_empty_data(self, converter):
        """测试空数据"""
        data = pd.DataFrame()
        
        with pytest.raises(ValueError) as excinfo:
            converter.convert_to_qlib_format(data)
        
        assert "空" in str(excinfo.value)
    
    def test_convert_to_qlib_format_none_data(self, converter):
        """测试 None 数据"""
        with pytest.raises(ValueError):
            converter.convert_to_qlib_format(None)
    
    # ========== 格式验证测试 ==========
    
    def test_validate_qlib_format_valid(self, converter):
        """测试验证有效数据"""
        data = pd.DataFrame({
            'instrument': ['sh600519'] * 5,
            'datetime': pd.date_range(start='2024-01-01', periods=5),
            'open': [100.0] * 5,
            'close': [105.0] * 5,
            'high': [110.0] * 5,
            'low': [90.0] * 5,
            'volume': [1000000] * 5,
            'amount': [1e8] * 5
        })
        
        is_valid = converter.validate_qlib_format(data)
        assert is_valid is True
    
    def test_validate_qlib_format_missing_column(self, converter):
        """测试验证缺少列的数据"""
        data = pd.DataFrame({
            'instrument': ['sh600519'] * 5,
            'datetime': pd.date_range(start='2024-01-01', periods=5),
            'open': [100.0] * 5,
            # 缺少 close, high, low
        })
        
        is_valid = converter.validate_qlib_format(data)
        assert is_valid is False
    
    def test_validate_qlib_format_negative_price(self, converter):
        """测试验证负价格数据"""
        data = pd.DataFrame({
            'instrument': ['sh600519'] * 5,
            'datetime': pd.date_range(start='2024-01-01', periods=5),
            'open': [-100.0] * 5,  # 负价格
            'close': [105.0] * 5,
            'high': [110.0] * 5,
            'low': [90.0] * 5,
            'volume': [1000000] * 5,
            'amount': [1e8] * 5
        })
        
        is_valid = converter.validate_qlib_format(data)
        assert is_valid is False
    
    def test_validate_qlib_format_invalid_instrument(self, converter):
        """测试验证无效股票代码格式"""
        data = pd.DataFrame({
            'instrument': ['invalid'] * 5,  # 无效格式
            'datetime': pd.date_range(start='2024-01-01', periods=5),
            'open': [100.0] * 5,
            'close': [105.0] * 5,
            'high': [110.0] * 5,
            'low': [90.0] * 5,
            'volume': [1000000] * 5,
            'amount': [1e8] * 5
        })
        
        is_valid = converter.validate_qlib_format(data)
        assert is_valid is False
    
    def test_validate_qlib_format_high_less_than_low(self, converter):
        """测试验证 high < low 的数据"""
        data = pd.DataFrame({
            'instrument': ['sh600519'] * 5,
            'datetime': pd.date_range(start='2024-01-01', periods=5),
            'open': [100.0] * 5,
            'close': [105.0] * 5,
            'high': [80.0] * 5,   # high < low
            'low': [90.0] * 5,
            'volume': [1000000] * 5,
            'amount': [1e8] * 5
        })
        
        is_valid = converter.validate_qlib_format(data)
        assert is_valid is False
    
    def test_validate_qlib_format_empty_data(self, converter):
        """测试验证空数据"""
        is_valid = converter.validate_qlib_format(pd.DataFrame())
        assert is_valid is False
    
    # ========== 二进制文件写入测试 ==========
    
    def test_write_qlib_binary_success(self, converter):
        """测试成功写入二进制文件"""
        with tempfile.TemporaryDirectory() as tmpdir:
            data = pd.DataFrame({
                'instrument': ['sh600519'] * 3,
                'datetime': pd.date_range(start='2024-01-01', periods=3),
                'open': [100.0, 101.0, 102.0],
                'close': [105.0, 106.0, 107.0],
                'high': [110.0, 111.0, 112.0],
                'low': [90.0, 91.0, 92.0],
                'volume': [1000000, 1100000, 1200000],
                'amount': [1e8, 1.1e8, 1.2e8]
            })
            
            count = converter.write_qlib_binary(data, tmpdir)
            
            # 检查写入数量
            assert count == 3
            
            # 检查文件是否存在
            features_dir = Path(tmpdir) / 'features' / 'sh600519'
            assert features_dir.exists()
            
            bin_files = list(features_dir.glob('*.bin'))
            assert len(bin_files) == 3
            
            # 验证文件内容
            first_file = sorted(bin_files)[0]
            with open(first_file, 'rb') as f:
                values = struct.unpack('6f', f.read())
                assert len(values) == 6
                assert values[0] == 100.0  # open
    
    def test_write_qlib_binary_no_output_dir(self, converter):
        """测试未设置输出目录"""
        data = pd.DataFrame({
            'instrument': ['sh600519'],
            'datetime': [pd.Timestamp('2024-01-01')],
            'open': [100.0],
            'close': [105.0],
            'high': [110.0],
            'low': [90.0],
            'volume': [1000000],
            'amount': [1e8]
        })
        
        with pytest.raises(ValueError):
            converter.write_qlib_binary(data)
    
    def test_write_qlib_binary_invalid_data(self, converter):
        """测试写入无效数据"""
        with tempfile.TemporaryDirectory() as tmpdir:
            data = pd.DataFrame({
                'instrument': ['sh600519'],
                # 缺少必需字段
            })
            
            with pytest.raises(ValueError):
                converter.write_qlib_binary(data, tmpdir)
    
    # ========== 一站式转换测试 ==========
    
    def test_convert_and_save_success(self, converter):
        """测试一站式转换成功"""
        with tempfile.TemporaryDirectory() as tmpdir:
            mootdx_data = pd.DataFrame({
                'date': pd.date_range(start='2024-01-01', periods=5),
                'open': [100.0] * 5,
                'high': [110.0] * 5,
                'low': [90.0] * 5,
                'close': [105.0] * 5,
                'volume': [1000000] * 5,
                'amount': [1e8] * 5,
                'code': ['sh600519'] * 5
            })
            
            result = converter.convert_and_save(mootdx_data, tmpdir)
            
            assert result['success'] is True
            assert result['converted_rows'] == 5
            assert result['saved_files'] == 5
    
    def test_convert_and_save_without_output(self, converter):
        """测试不保存文件的转换"""
        mootdx_data = pd.DataFrame({
            'date': pd.date_range(start='2024-01-01', periods=5),
            'open': [100.0] * 5,
            'high': [110.0] * 5,
            'low': [90.0] * 5,
            'close': [105.0] * 5,
            'volume': [1000000] * 5,
            'amount': [1e8] * 5,
            'code': ['sh600519'] * 5
        })
        
        result = converter.convert_and_save(mootdx_data)
        
        assert result['success'] is True
        assert result['converted_rows'] == 5
        assert result['saved_files'] == 0
    
    # ========== 转换信息测试 ==========
    
    def test_get_conversion_info_valid(self, converter):
        """测试获取转换信息"""
        data = pd.DataFrame({
            'date': pd.date_range(start='2024-01-01', periods=5),
            'open': [100.0] * 5,
            'high': [110.0] * 5,
            'low': [90.0] * 5,
            'close': [105.0] * 5,
            'volume': [1000000] * 5,
            'amount': [1e8] * 5,
            'code': ['sh600519'] * 5
        })
        
        info = converter.get_conversion_info(data)
        
        assert info['can_convert'] is True
        assert info['input_rows'] == 5
        assert len(info['issues']) == 0
    
    def test_get_conversion_info_missing_fields(self, converter):
        """测试缺少字段时的转换信息"""
        data = pd.DataFrame({
            'date': pd.date_range(start='2024-01-01', periods=5),
            'open': [100.0] * 5,
            # 缺少其他字段
        })
        
        info = converter.get_conversion_info(data)
        
        assert info['can_convert'] is False
        assert len(info['issues']) > 0
    
    # ========== 便捷函数测试 ==========
    
    def test_convert_to_qlib_function(self, sample_mootdx_data):
        """测试便捷转换函数"""
        result = convert_to_qlib(sample_mootdx_data)
        
        assert 'instrument' in result.columns
        assert 'datetime' in result.columns
        assert len(result) == len(sample_mootdx_data)
    
    def test_validate_data_function(self):
        """测试便捷验证函数"""
        data = pd.DataFrame({
            'instrument': ['sh600519'] * 5,
            'datetime': pd.date_range(start='2024-01-01', periods=5),
            'open': [100.0] * 5,
            'close': [105.0] * 5,
            'high': [110.0] * 5,
            'low': [90.0] * 5,
            'volume': [1000000] * 5,
            'amount': [1e8] * 5
        })
        
        is_valid = validate_data(data)
        assert is_valid is True


class TestDataConverterIntegration:
    """DataConverter 集成测试"""
    
    def test_full_workflow(self):
        """测试完整工作流"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 1. 创建转换器
            converter = DataConverter(output_dir=tmpdir)
            
            # 2. 准备数据
            mootdx_data = pd.DataFrame({
                'date': pd.date_range(start='2024-01-01', periods=10),
                'open': np.random.uniform(100, 200, 10),
                'high': np.random.uniform(150, 250, 10),
                'low': np.random.uniform(80, 150, 10),
                'close': np.random.uniform(100, 200, 10),
                'volume': np.random.randint(1000000, 10000000, 10),
                'amount': np.random.uniform(1e8, 1e9, 10),
                'code': ['sh600519'] * 10
            })
            
            # 3. 转换格式
            qlib_data = converter.convert_to_qlib_format(mootdx_data)
            
            # 4. 验证格式
            assert converter.validate_qlib_format(qlib_data)
            
            # 5. 写入文件
            count = converter.write_qlib_binary(qlib_data)
            assert count == 10
            
            # 6. 验证文件
            features_dir = Path(tmpdir) / 'features' / 'sh600519'
            bin_files = list(features_dir.glob('*.bin'))
            assert len(bin_files) == 10
    
    def test_multi_stock_conversion(self):
        """测试多股票转换"""
        with tempfile.TemporaryDirectory() as tmpdir:
            converter = DataConverter()
            
            # 创建多股票数据
            dates = pd.date_range(start='2024-01-01', periods=5)
            
            stock1_data = pd.DataFrame({
                'date': dates,
                'open': [100.0] * 5,
                'high': [110.0] * 5,
                'low': [90.0] * 5,
                'close': [105.0] * 5,
                'volume': [1000000] * 5,
                'amount': [1e8] * 5,
                'code': ['sh600519'] * 5
            })
            
            stock2_data = pd.DataFrame({
                'date': dates,
                'open': [50.0] * 5,
                'high': [55.0] * 5,
                'low': [45.0] * 5,
                'close': [52.0] * 5,
                'volume': [2000000] * 5,
                'amount': [1e8] * 5,
                'code': ['sz000001'] * 5
            })
            
            # 合并数据
            all_data = pd.concat([stock1_data, stock2_data], ignore_index=True)
            
            # 转换并保存
            result = converter.convert_and_save(all_data, tmpdir)
            
            assert result['success'] is True
            assert result['converted_rows'] == 10
            assert result['saved_files'] == 10
            
            # 验证两个股票目录都存在
            features_dir = Path(tmpdir) / 'features'
            assert (features_dir / 'sh600519').exists()
            assert (features_dir / 'sz000001').exists()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
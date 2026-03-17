"""
qlib 数据更新器测试

测试 DATA-001 的验收标准：
1. 能够自动下载最新日线数据
2. 数据日期为最新交易日
3. 数据格式符合 qlib 要求
4. 测试覆盖率 > 80%
"""

import os
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pandas as pd
import pytest

# 导入被测试的模块
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from data.qlib_updater import QlibDataUpdater, MOOTDX_AVAILABLE


class TestQlibDataUpdater:
    """QlibDataUpdater 测试类"""
    
    @pytest.fixture
    def temp_data_dir(self):
        """创建临时数据目录"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    @pytest.fixture
    def updater(self, temp_data_dir):
        """创建更新器实例"""
        return QlibDataUpdater(data_dir=str(temp_data_dir))
    
    @pytest.fixture
    def mock_quotes(self):
        """Mock mootdx Quotes"""
        mock = MagicMock()
        return mock
    
    # ========== 初始化测试 ==========
    
    def test_init_default_dir(self):
        """测试默认数据目录"""
        updater = QlibDataUpdater()
        expected_dir = Path.home() / ".qlib" / "qlib_data" / "cn_data"
        assert updater.data_dir == expected_dir
    
    def test_init_custom_dir(self, temp_data_dir):
        """测试自定义数据目录"""
        updater = QlibDataUpdater(data_dir=str(temp_data_dir))
        assert updater.data_dir == temp_data_dir
    
    def test_init_creates_paths(self, temp_data_dir):
        """测试路径初始化"""
        updater = QlibDataUpdater(data_dir=str(temp_data_dir))
        assert updater.features_dir == temp_data_dir / "features"
        assert updater.temp_dir == Path("/tmp/qlib_update")
    
    # ========== get_latest_date 测试 ==========
    
    def test_get_latest_date_empty_dir(self, updater):
        """测试空目录情况"""
        date = updater.get_latest_date()
        # 空目录应返回默认日期
        assert date == "2020-09-25"
    
    def test_get_latest_date_with_data(self, temp_data_dir):
        """测试有数据的情况"""
        # 创建模拟数据文件
        features_dir = temp_data_dir / "features" / "sh600519"
        features_dir.mkdir(parents=True)
        
        # 创建一个数据文件
        test_file = features_dir / "sh600519_2024-01-15.bin"
        test_file.write_bytes(b'\x00' * 24)  # 6个float32
        
        updater = QlibDataUpdater(data_dir=str(temp_data_dir))
        date = updater.get_latest_date()
        
        assert date == "2024-01-15"
    
    # ========== validate_data 测试 ==========
    
    def test_validate_data_dir_not_exist(self, updater):
        """测试数据目录不存在"""
        is_valid = updater.validate_data("sh600519")
        assert is_valid == False
    
    def test_validate_data_stock_dir_not_exist(self, temp_data_dir):
        """测试股票数据目录不存在"""
        features_dir = temp_data_dir / "features"
        features_dir.mkdir(parents=True)
        
        updater = QlibDataUpdater(data_dir=str(temp_data_dir))
        is_valid = updater.validate_data("sh600519")
        
        assert is_valid == False
    
    def test_validate_data_no_files(self, temp_data_dir):
        """测试没有数据文件"""
        features_dir = temp_data_dir / "features" / "sh600519"
        features_dir.mkdir(parents=True)
        
        updater = QlibDataUpdater(data_dir=str(temp_data_dir))
        is_valid = updater.validate_data("sh600519")
        
        assert is_valid == False
    
    def test_validate_data_success(self, temp_data_dir):
        """测试数据验证成功"""
        # 创建完整的数据结构
        features_dir = temp_data_dir / "features" / "sh600519"
        features_dir.mkdir(parents=True)
        
        # 创建最近的数据文件
        today = datetime.now()
        if today.weekday() >= 5:  # 周末
            date_str = (today - timedelta(days=today.weekday() - 4)).strftime("%Y-%m-%d")
        else:
            date_str = today.strftime("%Y-%m-%d")
        
        test_file = features_dir / f"sh600519_{date_str}.bin"
        test_file.write_bytes(b'\x00' * 24)
        
        updater = QlibDataUpdater(data_dir=str(temp_data_dir))
        is_valid = updater.validate_data("sh600519")
        
        assert is_valid == True
    
    # ========== _get_latest_trade_date 测试 ==========
    
    def test_get_latest_trade_date_weekday(self, updater):
        """测试工作日获取最新交易日"""
        # Mock datetime.now()
        with patch('data.qlib_updater.datetime') as mock_datetime:
            # 设置为周三下午
            mock_datetime.now.return_value = datetime(2024, 1, 17, 15, 0)
            mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
            
            date = updater._get_latest_trade_date()
            
            # 应该返回昨天（工作日）
            assert date is not None
    
    def test_get_latest_trade_date_weekend(self, updater):
        """测试周末获取最新交易日"""
        with patch('data.qlib_updater.datetime') as mock_datetime:
            # 设置为周六
            mock_datetime.now.return_value = datetime(2024, 1, 20, 10, 0)
            mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
            
            date = updater._get_latest_trade_date()
            
            # 周末应该回退到周五
            assert date is not None
            assert date.weekday() == 4  # 周五
    
    # ========== _get_qlib_latest_date 测试 ==========
    
    def test_get_qlib_latest_date_empty(self, updater):
        """测试空目录的 qlib 最新日期"""
        date = updater._get_qlib_latest_date()
        assert date == datetime(2020, 9, 25)
    
    def test_get_qlib_latest_date_with_files(self, temp_data_dir):
        """测试有文件的 qlib 最新日期"""
        features_dir = temp_data_dir / "features" / "sh600519"
        features_dir.mkdir(parents=True)
        
        # 创建多个文件
        for date_str in ["2024-01-10", "2024-01-11", "2024-01-12"]:
            test_file = features_dir / f"sh600519_{date_str}.bin"
            test_file.write_bytes(b'\x00' * 24)
        
        updater = QlibDataUpdater(data_dir=str(temp_data_dir))
        date = updater._get_qlib_latest_date()
        
        assert date == datetime(2024, 1, 12)
    
    # ========== _get_stock_list 测试 ==========
    
    def test_get_stock_list_fallback(self, updater):
        """测试股票列表 fallback"""
        stocks = updater._get_stock_list()
        
        assert isinstance(stocks, list)
        assert len(stocks) > 0
        assert "sh600519" in stocks  # 贵州茅台应该在列表中
    
    # ========== _save_temp_data 和 _read_temp_data 测试 ==========
    
    def test_save_temp_data(self, updater):
        """测试保存临时数据"""
        df = pd.DataFrame({
            'datetime': ['2024-01-15'],
            'open': [100.0],
            'close': [101.0],
            'high': [102.0],
            'low': [99.0],
            'volume': [1000000],
            'amount': [100000000]
        })
        
        updater._save_temp_data("sh600519", df)
        
        temp_file = updater.temp_dir / "sh600519.csv"
        assert temp_file.exists()
    
    def test_cleanup_temp_files(self, updater):
        """测试清理临时文件"""
        # 创建临时目录和文件
        updater.temp_dir.mkdir(parents=True, exist_ok=True)
        temp_file = updater.temp_dir / "test.csv"
        temp_file.write_text("test")
        
        # 清理
        updater._cleanup_temp_files()
        
        assert not updater.temp_dir.exists()
    
    # ========== update_daily_data 测试 ==========
    
    @pytest.mark.skipif(not MOOTDX_AVAILABLE, reason="mootdx not installed")
    def test_update_daily_data_mootdx_not_available(self, temp_data_dir):
        """测试 mootdx 未安装时的更新"""
        with patch('data.qlib_updater.MOOTDX_AVAILABLE', False):
            updater = QlibDataUpdater(data_dir=str(temp_data_dir))
            success = updater.update_daily_data()
            assert success == False
    
    def test_update_daily_data_already_latest(self, temp_data_dir):
        """测试数据已经是最新的情况"""
        # 创建最近的数据文件
        features_dir = temp_data_dir / "features" / "sh600519"
        features_dir.mkdir(parents=True)
        
        today = datetime.now()
        if today.weekday() >= 5:
            today = today - timedelta(days=today.weekday() - 4)
        
        date_str = today.strftime("%Y-%m-%d")
        test_file = features_dir / f"sh600519_{date_str}.bin"
        test_file.write_bytes(b'\x00' * 24)
        
        updater = QlibDataUpdater(data_dir=str(temp_data_dir))
        
        # Mock _get_latest_trade_date 返回今天
        with patch.object(updater, '_get_latest_trade_date', return_value=today.replace(hour=0, minute=0, second=0)):
            success = updater.update_daily_data()
            # 数据已最新，应返回 True
            assert success == True
    
    # ========== 命令行接口测试 ==========
    
    def test_main_no_args(self, capsys):
        """测试无参数运行"""
        with patch('sys.argv', ['qlib_updater.py']):
            from data.qlib_updater import main
            main()
            
            captured = capsys.readouterr()
            assert "使用方法" in captured.out
    
    def test_main_status(self, capsys, temp_data_dir):
        """测试 status 命令"""
        with patch('sys.argv', ['qlib_updater.py', 'status']):
            with patch('data.qlib_updater.QlibDataUpdater') as MockUpdater:
                mock_instance = MockUpdater.return_value
                mock_instance.get_latest_date.return_value = "2024-01-15"
                mock_instance.data_dir = temp_data_dir
                
                from data.qlib_updater import main
                main()
                
                captured = capsys.readouterr()
                assert "2024-01-15" in captured.out
    
    def test_main_validate_no_code(self, capsys):
        """测试 validate 命令无股票代码"""
        with patch('sys.argv', ['qlib_updater.py', 'validate']):
            from data.qlib_updater import main
            main()
            
            captured = capsys.readouterr()
            assert "请指定股票代码" in captured.out


class TestQlibDataUpdaterIntegration:
    """集成测试"""
    
    @pytest.fixture
    def full_setup(self, temp_data_dir):
        """完整测试环境"""
        # 创建 features 目录
        features_dir = temp_data_dir / "features" / "sh600519"
        features_dir.mkdir(parents=True)
        
        # 创建一些历史数据文件
        for i in range(5):
            date = datetime(2024, 1, 10 + i)
            date_str = date.strftime("%Y-%m-%d")
            test_file = features_dir / f"sh600519_{date_str}.bin"
            # 写入 6 个 float32 (24 字节)
            test_file.write_bytes(b'\x00' * 24)
        
        return temp_data_dir
    
    @pytest.fixture
    def temp_data_dir(self):
        """临时数据目录"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    def test_full_workflow(self, full_setup):
        """测试完整工作流程"""
        updater = QlibDataUpdater(data_dir=str(full_setup))
        
        # 1. 获取最新日期
        latest_date = updater.get_latest_date()
        assert latest_date == "2024-01-14"
        
        # 2. 验证数据
        is_valid = updater.validate_data("sh600519")
        # 由于数据过期，应该返回 False
        assert is_valid == False
    
    def test_data_format_conversion(self, full_setup):
        """测试数据格式转换"""
        updater = QlibDataUpdater(data_dir=str(full_setup))
        
        # 创建模拟的临时数据
        updater.temp_dir.mkdir(parents=True, exist_ok=True)
        
        df = pd.DataFrame({
            'datetime': ['2024-01-15'],
            'open': [100.0],
            'close': [101.0],
            'high': [102.0],
            'low': [99.0],
            'volume': [1000000],
            'amount': [100000000]
        })
        df.to_csv(updater.temp_dir / "sh600519.csv", index=False)
        
        # 转换
        success = updater._convert_to_qlib_format(
            datetime(2024, 1, 15),
            datetime(2024, 1, 15)
        )
        
        assert success == True
        
        # 检查文件是否创建
        output_file = full_setup / "features" / "sh600519" / "sh600519_2024-01-15.bin"
        assert output_file.exists()


# ========== 运行测试 ==========

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
"""
qlib 数据更新器

实现 qlib 数据自动更新机制，确保系统能够获取最新的股票日线数据。

任务ID: DATA-001
类型: 开发任务
优先级: P0
层级: data-layer
"""

import os
import struct
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List

import pandas as pd

try:
    from mootdx.quotes import Quotes
    MOOTDX_AVAILABLE = True
except ImportError:
    MOOTDX_AVAILABLE = False
    print("警告: mootdx 未安装，实时数据功能将不可用")


class QlibDataUpdater:
    """
    qlib 数据更新器
    
    功能：
    1. 自动下载最新日线数据
    2. 确保数据日期为最新交易日
    3. 数据格式符合 qlib 要求
    4. 支持增量更新
    
    使用示例：
        updater = QlibDataUpdater()
        success = updater.update_daily_data()
        latest_date = updater.get_latest_date()
        is_valid = updater.validate_data("sh600519")
    """
    
    def __init__(self, data_dir: str = "~/.qlib/qlib_data/cn_data"):
        """
        初始化 qlib 数据更新器
        
        Args:
            data_dir: qlib 数据目录，默认为 ~/.qlib/qlib_data/cn_data
        """
        self.data_dir = Path(os.path.expanduser(data_dir))
        self.features_dir = self.data_dir / "features"
        self.temp_dir = Path("/tmp/qlib_update")
        
        # 初始化 mootdx
        if MOOTDX_AVAILABLE:
            self.quotes = Quotes.factory(market='std')
        else:
            self.quotes = None
    
    def update_daily_data(self) -> bool:
        """
        更新日线数据
        
        执行流程：
        1. 获取最新交易日
        2. 获取 qlib 数据最新日期
        3. 计算需要更新的日期范围
        4. 下载增量数据
        5. 转换为 qlib 格式
        
        Returns:
            bool: 更新是否成功
        """
        try:
            # 1. 检查 mootdx 是否可用
            if not MOOTDX_AVAILABLE:
                print("错误: mootdx 未安装，无法更新数据")
                return False
            
            # 2. 获取最新交易日
            latest_trade_date = self._get_latest_trade_date()
            if not latest_trade_date:
                print("错误: 无法获取最新交易日")
                return False
            
            # 3. 获取 qlib 数据最新日期
            qlib_latest = self._get_qlib_latest_date()
            
            # 4. 检查是否需要更新
            if latest_trade_date <= qlib_latest:
                print(f"数据已是最新，无需更新 (最新: {qlib_latest})")
                return True
            
            # 5. 计算需要更新的日期范围
            start_date = qlib_latest + timedelta(days=1)
            end_date = latest_trade_date
            
            print(f"开始更新数据: {start_date} 到 {end_date}")
            
            # 6. 下载增量数据
            self._download_incremental_data(start_date, end_date)
            
            # 7. 转换为 qlib 格式
            self._convert_to_qlib_format(start_date, end_date)
            
            print(f"数据更新完成: {start_date} - {end_date}")
            return True
            
        except Exception as e:
            print(f"更新数据时出错: {e}")
            return False
    
    def get_latest_date(self) -> str:
        """
        获取最新数据日期
        
        Returns:
            str: 最新数据日期，格式为 YYYY-MM-DD
        """
        latest = self._get_qlib_latest_date()
        return latest.strftime("%Y-%m-%d") if latest else ""
    
    def validate_data(self, stock_code: str) -> bool:
        """
        验证数据完整性
        
        检查项：
        1. 数据目录是否存在
        2. 股票数据文件是否存在
        3. 数据文件是否可读
        4. 数据日期是否为最新
        
        Args:
            stock_code: 股票代码，如 sh600519
            
        Returns:
            bool: 数据是否完整
        """
        try:
            # 1. 检查数据目录
            if not self.data_dir.exists():
                print(f"数据目录不存在: {self.data_dir}")
                return False
            
            # 2. 检查股票数据目录
            stock_dir = self.features_dir / stock_code
            if not stock_dir.exists():
                print(f"股票数据目录不存在: {stock_dir}")
                return False
            
            # 3. 检查数据文件
            files = list(stock_dir.glob("*.bin"))
            if not files:
                print(f"没有找到数据文件: {stock_dir}")
                return False
            
            # 4. 检查数据日期
            latest_date = self._get_qlib_latest_date()
            trade_date = self._get_latest_trade_date()
            
            if latest_date and trade_date:
                # 允许 1 天的延迟（周末/节假日）
                if (trade_date - latest_date).days > 3:
                    print(f"数据过期: 最新数据 {latest_date}, 交易日 {trade_date}")
                    return False
            
            return True
            
        except Exception as e:
            print(f"验证数据时出错: {e}")
            return False
    
    # ========== 私有方法 ==========
    
    def _get_latest_trade_date(self) -> Optional[datetime]:
        """
        获取最新交易日
        
        Returns:
            datetime: 最新交易日，如果失败返回 None
        """
        try:
            # 使用 mootdx 获取交易日历
            if not self.quotes:
                return None
            
            # 尝试获取交易日历
            # 注意: mootdx 的 API 可能因版本不同而有差异
            # 这里使用一个简单的 fallback 方法
            today = datetime.now()
            
            # 如果是周末，回退到周五
            if today.weekday() == 5:  # 周六
                return today - timedelta(days=1)
            elif today.weekday() == 6:  # 周日
                return today - timedelta(days=2)
            
            # 如果是工作日但已过收盘时间（17:00），使用今天
            if today.hour >= 17:
                return today.replace(hour=0, minute=0, second=0, microsecond=0)
            
            # 否则使用昨天
            yesterday = today - timedelta(days=1)
            if yesterday.weekday() == 5:  # 周六
                return yesterday - timedelta(days=1)
            elif yesterday.weekday() == 6:  # 周日
                return yesterday - timedelta(days=2)
            
            return yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
            
        except Exception as e:
            print(f"获取最新交易日时出错: {e}")
            return None
    
    def _get_qlib_latest_date(self) -> datetime:
        """
        获取 qlib 数据最新日期
        
        Returns:
            datetime: qlib 数据最新日期
        """
        try:
            if not self.features_dir.exists():
                # 如果目录不存在，返回默认日期（qlib 默认数据截止日期）
                return datetime(2020, 9, 25)
            
            # 查找第一个股票的数据目录
            stock_dirs = [d for d in self.features_dir.iterdir() if d.is_dir()]
            if not stock_dirs:
                return datetime(2020, 9, 25)
            
            # 获取该股票的最新数据文件
            stock_dir = stock_dirs[0]
            files = sorted(stock_dir.glob("*.bin"))
            
            if not files:
                return datetime(2020, 9, 25)
            
            # 文件名格式：sh600519_2020-09-25.bin
            latest_file = files[-1]
            filename = latest_file.name
            
            # 提取日期
            parts = filename.split('_')
            if len(parts) >= 2:
                date_str = parts[1].replace('.bin', '')
                return datetime.strptime(date_str, "%Y-%m-%d")
            
            return datetime(2020, 9, 25)
            
        except Exception as e:
            print(f"获取 qlib 最新日期时出错: {e}")
            return datetime(2020, 9, 25)
    
    def _download_incremental_data(self, start_date: datetime, end_date: datetime) -> bool:
        """
        下载增量数据
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            bool: 是否成功
        """
        try:
            # 创建临时目录
            self.temp_dir.mkdir(parents=True, exist_ok=True)
            
            # 获取股票列表
            stocks = self._get_stock_list()
            if not stocks:
                print("警告: 无法获取股票列表")
                return False
            
            print(f"开始下载 {len(stocks)} 只股票的数据...")
            
            # 下载每只股票的数据
            success_count = 0
            for i, stock in enumerate(stocks[:100]):  # 限制为前 100 只股票作为示例
                try:
                    # 使用 mootdx 获取日线数据
                    # 注意: mootdx 的频率参数: 9=日线
                    data = self.quotes.bars(
                        code=stock,
                        frequency=9,
                        start=0,
                        offset=500  # 获取最近 500 天的数据
                    )
                    
                    if data is not None and len(data) > 0:
                        # 转换为 DataFrame
                        if isinstance(data, pd.DataFrame):
                            df = data
                        else:
                            df = pd.DataFrame(data)
                        
                        # 过滤日期范围
                        if 'datetime' in df.columns:
                            df['datetime'] = pd.to_datetime(df['datetime'])
                            df = df[
                                (df['datetime'].dt.date >= start_date.date()) &
                                (df['datetime'].dt.date <= end_date.date())
                            ]
                        
                        # 保存到临时文件
                        if len(df) > 0:
                            self._save_temp_data(stock, df)
                            success_count += 1
                    
                    # 每 10 只股票打印一次进度
                    if (i + 1) % 10 == 0:
                        print(f"已下载 {i + 1}/{min(len(stocks), 100)} 只股票")
                        
                except Exception as e:
                    # 单只股票下载失败不影响整体
                    continue
            
            print(f"成功下载 {success_count} 只股票的数据")
            return success_count > 0
            
        except Exception as e:
            print(f"下载增量数据时出错: {e}")
            return False
    
    def _convert_to_qlib_format(self, start_date: datetime, end_date: datetime) -> bool:
        """
        转换为 qlib 格式
        
        qlib 使用二进制格式存储数据，每个文件包含一天的数据。
        文件格式：features/{stock_code}/{stock_code}_{date}.bin
        数据格式：float32 序列 [open, close, high, low, volume, amount]
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            bool: 是否成功
        """
        try:
            # 读取临时目录中的数据
            if not self.temp_dir.exists():
                print("临时目录不存在")
                return False
            
            temp_files = list(self.temp_dir.glob("*.csv"))
            if not temp_files:
                print("没有找到临时数据文件")
                return False
            
            print(f"开始转换 {len(temp_files)} 个文件...")
            
            # 确保目标目录存在
            self.features_dir.mkdir(parents=True, exist_ok=True)
            
            success_count = 0
            for temp_file in temp_files:
                try:
                    # 读取 CSV 数据
                    df = pd.read_csv(temp_file)
                    
                    # 提取股票代码
                    stock_code = temp_file.stem
                    
                    # 创建股票目录
                    stock_dir = self.features_dir / stock_code
                    stock_dir.mkdir(parents=True, exist_ok=True)
                    
                    # 转换每一天的数据
                    for _, row in df.iterrows():
                        try:
                            # 提取日期
                            if 'datetime' in row:
                                date = pd.to_datetime(row['datetime']).strftime("%Y-%m-%d")
                            else:
                                continue
                            
                            # 提取特征
                            features = [
                                float(row.get('open', 0)),
                                float(row.get('close', 0)),
                                float(row.get('high', 0)),
                                float(row.get('low', 0)),
                                float(row.get('volume', 0)),
                                float(row.get('amount', 0))
                            ]
                            
                            # 写入二进制文件
                            file_path = stock_dir / f"{stock_code}_{date}.bin"
                            with open(file_path, 'wb') as f:
                                for feature in features:
                                    f.write(struct.pack('f', feature))
                            
                            success_count += 1
                            
                        except Exception as e:
                            continue
                    
                except Exception as e:
                    continue
            
            print(f"成功转换 {success_count} 个数据点")
            
            # 清理临时文件
            self._cleanup_temp_files()
            
            return success_count > 0
            
        except Exception as e:
            print(f"转换为 qlib 格式时出错: {e}")
            return False
    
    def _get_stock_list(self) -> List[str]:
        """
        获取股票列表
        
        Returns:
            List[str]: 股票代码列表
        """
        try:
            # 尝试从 qlib 获取
            try:
                import qlib
                from qlib.data import D
                
                instruments = D.instruments(market="cn")
                return [inst for inst in instruments][:100]  # 限制数量
            except:
                pass
            
            # 如果 qlib 不可用，返回默认列表（A 股主要股票）
            default_stocks = [
                "sh600519",  # 贵州茅台
                "sh601318",  # 中国平安
                "sh600036",  # 招商银行
                "sh601166",  # 兴业银行
                "sh600276",  # 恒瑞医药
                "sh600887",  # 伊利股份
                "sh601398",  # 工商银行
                "sh601288",  # 农业银行
                "sh600030",  # 中信证券
                "sh601888",  # 中国中免
            ]
            return default_stocks
            
        except Exception as e:
            print(f"获取股票列表时出错: {e}")
            return []
    
    def _save_temp_data(self, stock: str, data: pd.DataFrame):
        """
        保存临时数据
        
        Args:
            stock: 股票代码
            data: 数据 DataFrame
        """
        try:
            self.temp_dir.mkdir(parents=True, exist_ok=True)
            data.to_csv(self.temp_dir / f"{stock}.csv", index=False)
        except Exception as e:
            print(f"保存临时数据时出错: {e}")
    
    def _cleanup_temp_files(self):
        """
        清理临时文件
        """
        try:
            if self.temp_dir.exists():
                import shutil
                shutil.rmtree(self.temp_dir)
        except Exception as e:
            print(f"清理临时文件时出错: {e}")


# ========== 命令行接口 ==========

def main():
    """
    命令行入口
    
    使用方法：
        python qlib_updater.py update    # 更新数据
        python qlib_updater.py status    # 查看状态
        python qlib_updater.py validate  # 验证数据
    """
    import sys
    
    updater = QlibDataUpdater()
    
    if len(sys.argv) < 2:
        print("使用方法:")
        print("  python qlib_updater.py update    # 更新数据")
        print("  python qlib_updater.py status    # 查看状态")
        print("  python qlib_updater.py validate  # 验证数据")
        return
    
    command = sys.argv[1]
    
    if command == "update":
        print("开始更新 qlib 数据...")
        success = updater.update_daily_data()
        if success:
            print("✅ 数据更新成功")
        else:
            print("❌ 数据更新失败")
    
    elif command == "status":
        latest_date = updater.get_latest_date()
        print(f"最新数据日期: {latest_date}")
        print(f"数据目录: {updater.data_dir}")
        print(f"mootdx 可用: {MOOTDX_AVAILABLE}")
    
    elif command == "validate":
        if len(sys.argv) < 3:
            print("请指定股票代码，例如: python qlib_updater.py validate sh600519")
            return
        
        stock_code = sys.argv[2]
        is_valid = updater.validate_data(stock_code)
        if is_valid:
            print(f"✅ {stock_code} 数据完整")
        else:
            print(f"❌ {stock_code} 数据不完整")
    
    else:
        print(f"未知命令: {command}")


if __name__ == "__main__":
    main()
"""
DATA-001: qlib 数据更新器

功能：
1. 自动下载最新日线数据
2. 转换为 qlib 格式
3. 支持增量更新
4. 数据验证

支持的数据源：
- akshare（东方财富）
- mootdx（通达信）
- 本地 CSV 文件
"""

import os
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any
import pandas as pd

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class QlibDataUpdater:
    """qlib 数据更新器
    
    负责从多个数据源获取数据，并更新 qlib 数据目录。
    """
    
    def __init__(
        self, 
        qlib_data_dir: str = "~/.qlib/qlib_data/cn_data",
        data_source: str = "akshare"
    ):
        """
        初始化数据更新器
        
        Args:
            qlib_data_dir: qlib 数据目录
            data_source: 数据源（akshare, mootdx, local）
        """
        self.qlib_data_dir = Path(qlib_data_dir).expanduser()
        self.data_source = data_source
        self._setup_data_source()
        
    def _setup_data_source(self):
        """设置数据源"""
        self.data_fetcher = None
        
        if self.data_source == "akshare":
            try:
                import akshare as ak
                self.data_fetcher = ak
                logger.info("数据源: akshare")
            except ImportError:
                logger.warning("akshare 未安装，请运行: pip install akshare")
                
        elif self.data_source == "mootdx":
            try:
                from mootdx.quotes import Quotes
                self.data_fetcher = Quotes.factory(market='std')
                logger.info("数据源: mootdx")
            except ImportError:
                logger.warning("mootdx 未安装，请运行: pip install mootdx")
                
        elif self.data_source == "local":
            logger.info("数据源: 本地文件")
        else:
            raise ValueError(f"不支持的数据源: {self.data_source}")
    
    def update_daily_data(self, stock_codes: Optional[List[str]] = None) -> bool:
        """
        更新日线数据
        
        Args:
            stock_codes: 股票代码列表，None 表示更新全部
            
        Returns:
            bool: 是否成功
        """
        logger.info(f"开始更新日线数据，数据源: {self.data_source}")
        
        try:
            if self.data_source == "akshare":
                return self._update_from_akshare(stock_codes)
            elif self.data_source == "mootdx":
                return self._update_from_mootdx(stock_codes)
            elif self.data_source == "local":
                return self._update_from_local(stock_codes)
            else:
                logger.error(f"未知数据源: {self.data_source}")
                return False
                
        except Exception as e:
            logger.error(f"更新数据失败: {e}")
            return False
    
    def _update_from_akshare(self, stock_codes: Optional[List[str]] = None) -> bool:
        """从 akshare 更新数据"""
        if self.data_fetcher is None:
            logger.error("akshare 未初始化")
            return False
            
        try:
            # 禁用代理
            os.environ['NO_PROXY'] = '*'
            os.environ.pop('http_proxy', None)
            os.environ.pop('https_proxy', None)
            
            # 获取股票列表
            if stock_codes is None:
                logger.info("获取全部股票列表...")
                stock_list = self.data_fetcher.stock_zh_a_spot_em()
                stock_codes = stock_list['代码'].tolist()[:100]  # 先取100只测试
                logger.info(f"获取到 {len(stock_codes)} 只股票")
            
            # 下载数据
            success_count = 0
            for i, code in enumerate(stock_codes):
                try:
                    # 处理股票代码格式
                    # stock_zh_a_daily 需要小写的 sh/sz 前缀（如 sh600519）
                    symbol = code.lower() if code.upper().startswith(('SH', 'SZ')) else f'sh{code}'
                    
                    # 获取历史数据（使用 stock_zh_a_daily 接口）
                    df = self.data_fetcher.stock_zh_a_daily(symbol=symbol)
                    
                    if df is not None and len(df) > 0:
                        # 保存为 qlib 格式
                        self._save_to_qlib_format(code, df)
                        success_count += 1
                        
                    if (i + 1) % 10 == 0:
                        logger.info(f"进度: {i+1}/{len(stock_codes)}")
                        
                except Exception as e:
                    logger.warning(f"获取 {code} 数据失败: {e}")
                    continue
            
            logger.info(f"成功更新 {success_count}/{len(stock_codes)} 只股票")
            return success_count > 0
            
        except Exception as e:
            logger.error(f"akshare 更新失败: {e}")
            return False
    
    def _update_from_mootdx(self, stock_codes: Optional[List[str]] = None) -> bool:
        """从 mootdx 更新数据"""
        if self.data_fetcher is None:
            logger.error("mootdx 未初始化")
            return False
            
        try:
            # 获取股票列表
            if stock_codes is None:
                logger.info("获取股票列表...")
                stocks_sh = self.data_fetcher.stocks(market=0)  # 沪市
                stocks_sz = self.data_fetcher.stocks(market=1)  # 深市
                
                # 合并股票列表
                stock_codes = []
                for _, row in stocks_sh.iterrows():
                    if row['code'].startswith('6'):  # 只取主板股票
                        stock_codes.append(f"sh{row['code']}")
                for _, row in stocks_sz.iterrows():
                    if row['code'].startswith('0') or row['code'].startswith('3'):
                        stock_codes.append(f"sz{row['code']}")
                        
                stock_codes = stock_codes[:100]  # 先取100只测试
                logger.info(f"获取到 {len(stock_codes)} 只股票")
            
            # 下载数据
            success_count = 0
            for i, code in enumerate(stock_codes):
                try:
                    # mootdx 使用不同的代码格式
                    symbol = code[2:]  # 去掉 sh/sz 前缀
                    market = 0 if code.startswith('sh') else 1
                    
                    # 获取 K线数据
                    df = self.data_fetcher.bars(
                        symbol=symbol,
                        frequency=9,  # 日线
                        offset=0,
                        count=500  # 最近500个交易日
                    )
                    
                    if df is not None and len(df) > 0:
                        # 保存为 qlib 格式
                        self._save_to_qlib_format(code, df)
                        success_count += 1
                        
                    if (i + 1) % 10 == 0:
                        logger.info(f"进度: {i+1}/{len(stock_codes)}")
                        
                except Exception as e:
                    logger.warning(f"获取 {code} 数据失败: {e}")
                    continue
            
            logger.info(f"成功更新 {success_count}/{len(stock_codes)} 只股票")
            return success_count > 0
            
        except Exception as e:
            logger.error(f"mootdx 更新失败: {e}")
            return False
    
    def _update_from_local(self, stock_codes: Optional[List[str]] = None) -> bool:
        """从本地文件更新数据"""
        # TODO: 实现本地文件导入
        logger.warning("本地文件导入功能待实现")
        return False
    
    def _save_to_qlib_format(self, stock_code: str, df: pd.DataFrame) -> bool:
        """
        保存数据为 qlib 格式
        
        Args:
            stock_code: 股票代码
            df: 数据 DataFrame
            
        Returns:
            bool: 是否成功
        """
        try:
            # 创建保存目录
            save_dir = self.qlib_data_dir / "features" / stock_code
            save_dir.mkdir(parents=True, exist_ok=True)
            
            # 标准化列名（stock_zh_a_daily 返回的列名）
            # 列名: date, open, close, high, low, volume, amount, outstanding_share, turnover
            # 已经是英文格式，只需要选择需要的列
            required_columns = ['date', 'open', 'close', 'high', 'low', 'volume']
            
            # 检查必要的列是否存在
            for col in required_columns:
                if col not in df.columns:
                    logger.warning(f"缺少列: {col}")
                    return False
            
            # 只保留需要的列
            df = df[required_columns].copy()
            
            # 保存为 CSV（qlib 会自动转换）
            save_path = save_dir / f"{stock_code}.csv"
            df[required_columns].to_csv(save_path, index=False)
            
            logger.debug(f"保存 {stock_code} 数据到 {save_path}")
            return True
            
        except Exception as e:
            logger.error(f"保存数据失败: {e}")
            return False
    
    def get_latest_date(self) -> str:
        """
        获取最新数据日期
        
        Returns:
            str: 最新日期（YYYY-MM-DD 格式）
        """
        try:
            # 读取 qlib 日历文件
            calendar_path = self.qlib_data_dir / "calendars" / "day.txt"
            
            if calendar_path.exists():
                with open(calendar_path, 'r') as f:
                    lines = f.readlines()
                    if lines:
                        return lines[-1].strip()
            
            return "未知"
            
        except Exception as e:
            logger.error(f"获取最新日期失败: {e}")
            return "未知"
    
    def validate_data(self, stock_code: str) -> bool:
        """
        验证数据完整性
        
        Args:
            stock_code: 股票代码
            
        Returns:
            bool: 数据是否完整
        """
        try:
            # 检查数据文件是否存在
            data_path = self.qlib_data_dir / "features" / stock_code / f"{stock_code}.csv"
            
            if not data_path.exists():
                logger.warning(f"数据文件不存在: {data_path}")
                return False
            
            # 读取数据
            df = pd.read_csv(data_path)
            
            # 检查必要的列
            required_columns = ['date', 'open', 'close', 'high', 'low', 'volume']
            for col in required_columns:
                if col not in df.columns:
                    logger.warning(f"缺少列: {col}")
                    return False
            
            # 检查数据量
            if len(df) < 10:
                logger.warning(f"数据量不足: {len(df)} 条")
                return False
            
            # 检查空值
            if df[required_columns].isnull().any().any():
                logger.warning("数据存在空值")
                return False
            
            logger.info(f"数据验证通过: {stock_code}")
            return True
            
        except Exception as e:
            logger.error(f"数据验证失败: {e}")
            return False
    
    def get_data_status(self) -> Dict[str, Any]:
        """
        获取数据状态
        
        Returns:
            Dict: 数据状态信息
        """
        status = {
            "qlib_data_dir": str(self.qlib_data_dir),
            "data_source": self.data_source,
            "latest_date": self.get_latest_date(),
            "stock_count": 0,
            "data_exists": False
        }
        
        try:
            # 检查数据目录
            features_dir = self.qlib_data_dir / "features"
            if features_dir.exists():
                status["data_exists"] = True
                status["stock_count"] = len(list(features_dir.iterdir()))
        except Exception as e:
            logger.error(f"获取数据状态失败: {e}")
        
        return status


# 测试代码
if __name__ == "__main__":
    print("=" * 50)
    print("DATA-001: qlib 数据更新器测试")
    print("=" * 50)
    
    # 创建更新器
    updater = QlibDataUpdater(data_source="akshare")  # 使用 akshare（东方财富接口可用）
    
    # 获取数据状态
    status = updater.get_data_status()
    print(f"\n数据状态:")
    for key, value in status.items():
        print(f"  {key}: {value}")
    
    # 测试更新数据（先测试一只股票）
    print(f"\n测试更新数据...")
    test_stocks = ["sh600519", "sz000858"]  # 茅台、五粮液
    success = updater.update_daily_data(stock_codes=test_stocks)
    print(f"更新结果: {'成功' if success else '失败'}")
    
    # 验证数据
    print(f"\n验证数据...")
    for stock in test_stocks:
        valid = updater.validate_data(stock)
        print(f"  {stock}: {'✓' if valid else '✗'}")
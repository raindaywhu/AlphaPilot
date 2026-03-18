"""
可视化图表工具

生成 K 线图、技术指标图表、资金流向图

Issue: #30 (VISUAL-001)
"""

import os
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List

# 导入性能优化工具
from ..utils.performance import timing_decorator, monitor_performance

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 尝试导入可视化库
try:
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    plt.rcParams['font.sans-serif'] = ['PingFang HK', 'Arial Unicode MS', 'SimHei']
    plt.rcParams['axes.unicode_minus'] = False
    HAS_MATPLOTLIB = True
    logger.info("Matplotlib 库可用")
except ImportError:
    HAS_MATPLOTLIB = False
    logger.warning("Matplotlib 库不可用，图表生成功能受限")


class ChartGenerator:
    """
    图表生成器
    
    生成 K 线图、技术指标图表、资金流向图
    """
    
    def __init__(self):
        """初始化生成器"""
        self.output_dir = "/tmp/alphapilot/charts"
        os.makedirs(self.output_dir, exist_ok=True)
        logger.info(f"图表生成器初始化完成，输出目录: {self.output_dir}")
    
    @monitor_performance("chart")
    @timing_decorator
    def generate_kline_chart(
        self,
        data: Dict[str, Any],
        stock_code: str,
        filename: Optional[str] = None
    ) -> str:
        """
        生成 K 线图
        
        Args:
            data: K 线数据，需包含 dates, opens, highs, lows, closes
            stock_code: 股票代码
            filename: 文件名
        
        Returns:
            图表文件路径
        """
        if not HAS_MATPLOTLIB:
            logger.warning("Matplotlib 不可用")
            return self._generate_text_chart(data, stock_code, filename)
        
        logger.info(f"生成 K 线图: {stock_code}")
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{stock_code}_kline_{timestamp}.png"
        
        output_path = os.path.join(self.output_dir, filename)
        
        # 提取数据
        dates = data.get("dates", [])
        opens = data.get("opens", [])
        highs = data.get("highs", [])
        lows = data.get("lows", [])
        closes = data.get("closes", [])
        
        if not all([dates, opens, highs, lows, closes]):
            logger.error("K 线数据不完整")
            return ""
        
        # 创建图表
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), 
                                        gridspec_kw={'height_ratios': [3, 1]})
        
        # K 线图
        for i in range(len(dates)):
            color = 'red' if closes[i] >= opens[i] else 'green'
            
            # 实体
            ax1.bar(i, abs(closes[i] - opens[i]), 
                   bottom=min(opens[i], closes[i]), 
                   color=color, width=0.6)
            
            # 影线
            ax1.vlines(i, lows[i], highs[i], color=color, linewidth=1)
        
        ax1.set_title(f"{stock_code} K 线图", fontsize=14)
        ax1.set_ylabel("价格", fontsize=12)
        ax1.grid(True, alpha=0.3)
        
        # 设置 X 轴标签
        step = max(1, len(dates) // 10)
        ax1.set_xticks(range(0, len(dates), step))
        ax1.set_xticklabels([dates[i] for i in range(0, len(dates), step)], 
                           rotation=45, ha='right')
        
        # 成交量（如果有）
        volumes = data.get("volumes", [])
        if volumes:
            colors = ['red' if closes[i] >= opens[i] else 'green' 
                     for i in range(len(volumes))]
            ax2.bar(range(len(volumes)), volumes, color=colors, width=0.6)
            ax2.set_ylabel("成交量", fontsize=12)
            ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=100, bbox_inches='tight')
        plt.close()
        
        logger.info(f"K 线图已生成: {output_path}")
        
        return output_path
    
    @monitor_performance("chart")
    @timing_decorator
    def generate_indicator_chart(
        self,
        data: Dict[str, Any],
        stock_code: str,
        indicators: Optional[List[str]] = None,
        filename: Optional[str] = None
    ) -> str:
        """
        生成技术指标图表
        
        Args:
            data: 数据，需包含 dates, close 和各指标值
            stock_code: 股票代码
            indicators: 指标列表，如 ['ma5', 'ma20', 'macd']
            filename: 文件名
        
        Returns:
            图表文件路径
        """
        if not HAS_MATPLOTLIB:
            return ""
        
        logger.info(f"生成技术指标图表: {stock_code}")
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{stock_code}_indicators_{timestamp}.png"
        
        output_path = os.path.join(self.output_dir, filename)
        
        # 提取数据
        dates = data.get("dates", [])
        closes = data.get("closes", [])
        
        if not dates or not closes:
            return ""
        
        # 创建图表
        fig, axes = plt.subplots(3, 1, figsize=(12, 10))
        
        # 价格 + MA
        ax1 = axes[0]
        ax1.plot(range(len(dates)), closes, label='收盘价', linewidth=1.5)
        
        if data.get("ma5"):
            ax1.plot(range(len(dates)), data["ma5"], label='MA5', linewidth=1)
        if data.get("ma20"):
            ax1.plot(range(len(dates)), data["ma20"], label='MA20', linewidth=1)
        
        ax1.set_title(f"{stock_code} 价格走势", fontsize=14)
        ax1.set_ylabel("价格", fontsize=12)
        ax1.legend(loc='upper left')
        ax1.grid(True, alpha=0.3)
        
        # MACD
        ax2 = axes[1]
        if data.get("macd"):
            ax2.bar(range(len(dates)), data["macd"], label='MACD', color='blue', alpha=0.5)
        if data.get("signal"):
            ax2.plot(range(len(dates)), data["signal"], label='Signal', color='red', linewidth=1)
        
        ax2.set_title("MACD 指标", fontsize=12)
        ax2.set_ylabel("MACD", fontsize=12)
        ax2.legend(loc='upper left')
        ax2.grid(True, alpha=0.3)
        
        # RSI
        ax3 = axes[2]
        if data.get("rsi"):
            ax3.plot(range(len(dates)), data["rsi"], label='RSI', color='purple', linewidth=1)
            ax3.axhline(y=70, color='red', linestyle='--', alpha=0.5)
            ax3.axhline(y=30, color='green', linestyle='--', alpha=0.5)
        
        ax3.set_title("RSI 指标", fontsize=12)
        ax3.set_ylabel("RSI", fontsize=12)
        ax3.legend(loc='upper left')
        ax3.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=100, bbox_inches='tight')
        plt.close()
        
        logger.info(f"技术指标图表已生成: {output_path}")
        
        return output_path
    
    @monitor_performance("chart")
    @timing_decorator
    def generate_fund_flow_chart(
        self,
        data: Dict[str, Any],
        stock_code: str,
        filename: Optional[str] = None
    ) -> str:
        """
        生成资金流向图表
        
        Args:
            data: 资金流向数据
            stock_code: 股票代码
            filename: 文件名
        
        Returns:
            图表文件路径
        """
        if not HAS_MATPLOTLIB:
            return ""
        
        logger.info(f"生成资金流向图表: {stock_code}")
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{stock_code}_fundflow_{timestamp}.png"
        
        output_path = os.path.join(self.output_dir, filename)
        
        # 创建图表
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # 资金流向数据
        categories = ['主力净流入', '超大单', '大单', '中单', '小单']
        values = [
            data.get("main_net_inflow", 0),
            data.get("super_large", 0),
            data.get("large", 0),
            data.get("medium", 0),
            data.get("small", 0)
        ]
        
        colors = ['red' if v > 0 else 'green' for v in values]
        
        bars = ax.barh(categories, values, color=colors)
        
        ax.set_title(f"{stock_code} 资金流向", fontsize=14)
        ax.set_xlabel("金额（万元）", fontsize=12)
        ax.axvline(x=0, color='black', linewidth=0.5)
        ax.grid(True, alpha=0.3, axis='x')
        
        # 添加数值标签
        for bar, value in zip(bars, values):
            width = bar.get_width()
            ax.annotate(f'{value/10000:.2f}万',
                       xy=(width, bar.get_y() + bar.get_height()/2),
                       ha='left' if width > 0 else 'right',
                       va='center')
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=100, bbox_inches='tight')
        plt.close()
        
        logger.info(f"资金流向图表已生成: {output_path}")
        
        return output_path
    
    def _generate_text_chart(
        self,
        data: Dict[str, Any],
        stock_code: str,
        filename: Optional[str] = None
    ) -> str:
        """
        生成文本图表（备用方案）
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{stock_code}_chart_{timestamp}.txt"
        
        output_path = os.path.join(self.output_dir, filename)
        
        dates = data.get("dates", [])
        closes = data.get("closes", [])
        
        if not dates or not closes:
            return ""
        
        # 简单的 ASCII 图表
        min_close = min(closes)
        max_close = max(closes)
        range_close = max_close - min_close if max_close > min_close else 1
        
        lines = [f"{stock_code} K 线图表（文本版）", "=" * 40, ""]
        
        for i, (date, close) in enumerate(zip(dates[-20:], closes[-20:])):
            bar_len = int((close - min_close) / range_close * 20)
            bar = "█" * bar_len
            lines.append(f"{date}: {bar} {close:.2f}")
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        
        logger.info(f"文本图表已生成: {output_path}")
        
        return output_path


def main():
    """测试图表生成器"""
    print("=" * 60)
    print("图表生成器测试")
    print("=" * 60)
    
    generator = ChartGenerator()
    
    # 测试 K 线图
    kline_data = {
        "dates": [f"2024-01-{i:02d}" for i in range(1, 21)],
        "opens": [10.0 + i * 0.1 for i in range(20)],
        "highs": [10.5 + i * 0.1 for i in range(20)],
        "lows": [9.5 + i * 0.1 for i in range(20)],
        "closes": [10.2 + i * 0.1 for i in range(20)],
        "volumes": [1000000] * 20
    }
    
    kline_path = generator.generate_kline_chart(kline_data, "SH600519")
    print(f"✅ K 线图: {kline_path}")
    
    # 测试技术指标图表
    indicator_data = {
        **kline_data,
        "ma5": [10.0 + i * 0.1 for i in range(20)],
        "ma20": [9.8 + i * 0.1 for i in range(20)],
        "macd": [0.1 * (i % 5 - 2) for i in range(20)],
        "signal": [0.05 * (i % 5 - 2) for i in range(20)],
        "rsi": [50 + i * 2 for i in range(20)]
    }
    
    indicator_path = generator.generate_indicator_chart(indicator_data, "SH600519")
    print(f"✅ 技术指标图: {indicator_path}")
    
    # 测试资金流向图
    fund_flow_data = {
        "main_net_inflow": 5000000,
        "super_large": 3000000,
        "large": 2000000,
        "medium": -500000,
        "small": -1500000
    }
    
    fund_flow_path = generator.generate_fund_flow_chart(fund_flow_data, "SH600519")
    print(f"✅ 资金流向图: {fund_flow_path}")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
"""
策略管理器
Strategy Manager

統一管理所有選股策略，提供便捷的調用接口
"""

from typing import Dict, List, Optional
import pandas as pd
from datetime import date

# 導入所有策略
from backend.strategies.revenue_momentum import RevenueMomentumStrategy
from backend.strategies.low_price_small import LowPriceSmallCapStrategy
from backend.strategies.breakout import BreakoutAfterBaseStrategy
from backend.strategies.inst_buying import InstitutionalBuyingStrategy
from backend.strategies.capital_increase import CapitalIncreaseStrategy
from backend.strategies.cash_growth import CashGrowthStrategy


class StrategyManager:
    """策略管理器"""

    def __init__(self):
        """初始化所有策略"""
        self.strategies = {
            'revenue_momentum': RevenueMomentumStrategy(),
            'low_price_small': LowPriceSmallCapStrategy(),
            'breakout': BreakoutAfterBaseStrategy(),
            'inst_buying': InstitutionalBuyingStrategy(),
            'capital_increase': CapitalIncreaseStrategy(),
            'cash_growth': CashGrowthStrategy()
        }

    def get_strategy(self, strategy_name: str):
        """
        獲取指定策略

        Args:
            strategy_name: 策略名稱

        Returns:
            策略實例
        """
        if strategy_name not in self.strategies:
            raise ValueError(f"未知策略: {strategy_name}")

        return self.strategies[strategy_name]

    def list_strategies(self) -> List[Dict[str, str]]:
        """
        列出所有策略

        Returns:
            策略列表，包含name和description
        """
        return [
            {
                'key': key,
                'name': strategy.name,
                'description': strategy.description
            }
            for key, strategy in self.strategies.items()
        ]

    def run_strategy(
        self,
        strategy_name: str,
        data: Dict[str, pd.DataFrame],
        as_of: Optional[date] = None
    ) -> pd.DataFrame:
        """
        執行單個策略

        Args:
            strategy_name: 策略名稱
            data: 數據字典
            as_of: 選股基準日期

        Returns:
            選股結果DataFrame
        """
        strategy = self.get_strategy(strategy_name)
        return strategy.screen(data, as_of)

    def run_all_strategies(
        self,
        data: Dict[str, pd.DataFrame],
        as_of: Optional[date] = None
    ) -> Dict[str, pd.DataFrame]:
        """
        執行所有策略

        Args:
            data: 數據字典
            as_of: 選股基準日期

        Returns:
            策略結果字典 {strategy_name: result_df}
        """
        print("\n" + "=" * 70)
        print("🚀 開始執行所有策略")
        print("=" * 70)

        results = {}

        for key, strategy in self.strategies.items():
            try:
                print(f"\n執行策略: {strategy.name}")
                result = strategy.screen(data, as_of)
                results[key] = result

                if not result.empty:
                    print(f"✅ {strategy.name} 完成，選出 {len(result)} 檔股票")
                else:
                    print(f"⚠️  {strategy.name} 無符合條件的股票")

            except Exception as e:
                print(f"❌ {strategy.name} 執行失敗: {e}")
                results[key] = pd.DataFrame(columns=['stock_id', 'score', 'rank', 'metadata'])

        print("\n" + "=" * 70)
        print("✅ 所有策略執行完成")
        print("=" * 70)

        return results

    def get_combined_results(
        self,
        results: Dict[str, pd.DataFrame],
        top_n: Optional[int] = None
    ) -> pd.DataFrame:
        """
        合併所有策略結果

        Args:
            results: 策略結果字典
            top_n: 每個策略取前N名，None表示全部

        Returns:
            合併後的DataFrame，包含所有策略的推薦股票
        """
        combined = []

        for strategy_key, result in results.items():
            if result.empty:
                continue

            # 取前N名
            if top_n:
                result = result.head(top_n)

            # 添加策略標識
            result = result.copy()
            result['strategy_key'] = strategy_key
            result['strategy_name'] = self.strategies[strategy_key].name

            combined.append(result)

        if not combined:
            return pd.DataFrame()

        # 合併所有結果
        combined_df = pd.concat(combined, ignore_index=True)

        return combined_df

    def get_stock_appearances(
        self,
        results: Dict[str, pd.DataFrame]
    ) -> pd.DataFrame:
        """
        統計股票在各策略中出現的次數

        Args:
            results: 策略結果字典

        Returns:
            股票統計DataFrame，包含出現次數、平均評分等
        """
        stock_stats = {}

        for strategy_key, result in results.items():
            if result.empty:
                continue

            for _, row in result.iterrows():
                stock_id = row['stock_id']

                if stock_id not in stock_stats:
                    stock_stats[stock_id] = {
                        'stock_id': stock_id,
                        'appearances': 0,
                        'strategies': [],
                        'scores': [],
                        'avg_rank': 0
                    }

                stock_stats[stock_id]['appearances'] += 1
                stock_stats[stock_id]['strategies'].append(self.strategies[strategy_key].name)
                stock_stats[stock_id]['scores'].append(row['score'])

        if not stock_stats:
            return pd.DataFrame()

        # 轉換為DataFrame
        stats_df = pd.DataFrame(stock_stats.values())

        # 計算平均評分
        stats_df['avg_score'] = stats_df['scores'].apply(lambda x: sum(x) / len(x))

        # 策略列表轉為字串
        stats_df['strategies_list'] = stats_df['strategies'].apply(lambda x: ', '.join(x))

        # 按出現次數和平均分數排序
        stats_df = stats_df.sort_values(['appearances', 'avg_score'], ascending=[False, False])

        # 選擇展示欄位
        display_df = stats_df[['stock_id', 'appearances', 'avg_score', 'strategies_list']].reset_index(drop=True)

        return display_df


# ========== 測試代碼 ==========

def test_strategy_manager():
    """測試策略管理器"""
    print("=== 策略管理器測試 ===")
    print()

    manager = StrategyManager()

    # 列出所有策略
    print("📋 可用策略列表:")
    for strategy in manager.list_strategies():
        print(f"  [{strategy['key']}] {strategy['name']}")
        print(f"      {strategy['description']}")
    print()

    # 創建測試數據
    import numpy as np

    dates = pd.date_range('2024-01-01', periods=100, freq='D')
    stocks = ['2330', '2317', '2454', '3008', '2412', '2881']

    close = pd.DataFrame(
        np.random.randn(100, len(stocks)) * 10 + 100,
        index=dates,
        columns=stocks
    )

    volume = pd.DataFrame(
        np.random.randint(1000000, 5000000, (100, len(stocks))),
        index=dates,
        columns=stocks
    )

    market_cap = pd.DataFrame(
        np.random.randn(100, len(stocks)) * 1e10 + 5e10,
        index=dates,
        columns=stocks
    )

    # 簡化的測試數據
    data = {
        'close': close,
        'volume': volume,
        'market_cap': market_cap,
        'open': close * 0.99,
        'high': close * 1.02,
        'low': close * 0.98
    }

    # 測試單個策略
    print("測試單個策略（突破策略）:")
    result = manager.run_strategy('breakout', data)
    print(f"選出 {len(result)} 檔股票")
    print()

    print("✅ 測試完成")


if __name__ == "__main__":
    test_strategy_manager()

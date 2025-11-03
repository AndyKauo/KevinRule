"""
Kevin 原始版策略管理器
Strategy Manager for Kevin's Original Strategies
"""

from typing import Dict, List, Optional
import pandas as pd
from datetime import date

from .revenue_momentum_original import RevenueMomentumOriginalStrategy
from .low_price_small_original import LowPriceSmallOriginalStrategy
from .breakout_original import BreakoutOriginalStrategy
from .inst_buying_original import InstBuyingOriginalStrategy
from .capital_increase_original import CapitalIncreaseOriginalStrategy
from .cash_growth_original import CashGrowthOriginalStrategy


class StrategyManagerOriginal:
    """Kevin 原始版策略管理器"""

    def __init__(self):
        """初始化策略管理器"""
        self.strategies = {
            'revenue_momentum': RevenueMomentumOriginalStrategy(),
            'low_price_small': LowPriceSmallOriginalStrategy(),
            'breakout': BreakoutOriginalStrategy(),
            'inst_buying': InstBuyingOriginalStrategy(),
            'capital_increase': CapitalIncreaseOriginalStrategy(),
            'cash_growth': CashGrowthOriginalStrategy(),
        }

    def get_strategy_list(self) -> List[Dict[str, str]]:
        """
        獲取所有策略的列表

        Returns:
            策略列表，每個策略包含 id, name, description
        """
        return [
            {
                'id': strategy_id,
                'name': strategy.strategy_name,
                'description': strategy.description
            }
            for strategy_id, strategy in self.strategies.items()
        ]

    def run_strategy(
        self,
        strategy_id: str,
        data: Dict[str, pd.DataFrame],
        as_of: Optional[date] = None
    ) -> pd.DataFrame:
        """
        執行單個策略

        Args:
            strategy_id: 策略 ID
            data: 包含所有必要數據的字典
            as_of: 截止日期

        Returns:
            篩選結果 DataFrame
        """
        if strategy_id not in self.strategies:
            raise ValueError(f"策略 {strategy_id} 不存在")

        strategy = self.strategies[strategy_id]
        result = strategy.screen(data, as_of)

        # 後處理：確保結果符合 UI 期望的格式
        if not result.empty:
            # 1. 將 index (股票代碼) 轉為 'stock_id' 欄位
            result = result.reset_index()

            # reset_index() 會將 index 轉為欄位，欄位名稱取決於 index.name
            # 可能的名稱：'index', 'symbol', 'stock_id' 等
            # 統一轉換為 'stock_id'
            if 'stock_id' not in result.columns:
                # 尋找可能的股票代碼欄位
                possible_cols = ['index', 'symbol', 'level_0']
                for col in possible_cols:
                    if col in result.columns:
                        result = result.rename(columns={col: 'stock_id'})
                        break

            # 2. 添加 'rank' 欄位（根據 score 排序）
            if 'score' in result.columns:
                result['rank'] = range(1, len(result) + 1)

            # 3. 添加 'metadata' 欄位（與學術版保持一致）
            import json
            metadata = {
                'strategy_id': strategy_id,
                'version': 'original',
                'total_stocks': len(result)
            }
            result['metadata'] = json.dumps(metadata, ensure_ascii=False)

        return result

    def run_all_strategies(
        self,
        data: Dict[str, pd.DataFrame],
        as_of: Optional[date] = None
    ) -> Dict[str, pd.DataFrame]:
        """
        執行所有策略

        Args:
            data: 包含所有必要數據的字典
            as_of: 截止日期

        Returns:
            策略結果字典 {strategy_id: result_df}
        """
        results = {}

        print("\n" + "=" * 70)
        print("🚀 Kevin 原始版策略系統 - 執行所有策略")
        print("=" * 70 + "\n")

        for strategy_id, strategy in self.strategies.items():
            try:
                result = strategy.screen(data, as_of)
                results[strategy_id] = result

                if not result.empty:
                    print(f"✅ {strategy.strategy_name}: {len(result)} 檔股票")
                else:
                    print(f"⚠️  {strategy.strategy_name}: 沒有符合條件的股票")

            except Exception as e:
                print(f"❌ {strategy.strategy_name} 執行失敗: {e}")
                results[strategy_id] = pd.DataFrame()

        print("\n" + "=" * 70)
        print("✅ 所有策略執行完成")
        print("=" * 70 + "\n")

        return results

    def get_stock_appearances(
        self,
        results: Dict[str, pd.DataFrame],
        min_appearances: int = 2
    ) -> pd.DataFrame:
        """
        獲取在多個策略中出現的股票（交集分析）

        Args:
            results: 策略結果字典
            min_appearances: 最少出現次數

        Returns:
            股票出現統計 DataFrame
        """
        # 收集所有推薦的股票
        stock_counts = {}
        stock_scores = {}
        stock_strategies = {}

        for strategy_id, result in results.items():
            if result.empty:
                continue

            strategy_name = self.strategies[strategy_id].strategy_name

            for stock_id in result.index:
                # 計數
                if stock_id not in stock_counts:
                    stock_counts[stock_id] = 0
                    stock_scores[stock_id] = 0
                    stock_strategies[stock_id] = []

                stock_counts[stock_id] += 1
                stock_scores[stock_id] += result.loc[stock_id, 'score']
                stock_strategies[stock_id].append(strategy_name)

        # 篩選符合最少出現次數的股票
        filtered_stocks = {
            stock_id: {
                'appearances': count,
                'avg_score': stock_scores[stock_id] / count,
                'strategies': ', '.join(stock_strategies[stock_id])
            }
            for stock_id, count in stock_counts.items()
            if count >= min_appearances
        }

        # 轉換為 DataFrame
        if filtered_stocks:
            df = pd.DataFrame(filtered_stocks).T
            df = df.sort_values('appearances', ascending=False)

            # 將 index (stock_id) 轉為欄位，與 UI 期望一致
            df = df.reset_index()
            df = df.rename(columns={'index': 'stock_id'})

            # 添加 'rank' 和 'metadata' 欄位
            df['rank'] = range(1, len(df) + 1)
            import json
            metadata = {
                'analysis_type': 'multi_strategy',
                'min_appearances': min_appearances,
                'total_strategies': len(results)
            }
            df['metadata'] = json.dumps(metadata, ensure_ascii=False)

            return df
        else:
            return pd.DataFrame()

    def get_summary(self, results: Dict[str, pd.DataFrame]) -> Dict:
        """
        獲取策略執行摘要

        Args:
            results: 策略結果字典

        Returns:
            摘要字典
        """
        summary = {
            'total_strategies': len(self.strategies),
            'executed_strategies': len(results),
            'strategies_with_results': sum(1 for r in results.values() if not r.empty),
            'total_stocks': len(set().union(*[set(r.index) for r in results.values() if not r.empty])),
            'strategy_details': []
        }

        for strategy_id, result in results.items():
            summary['strategy_details'].append({
                'id': strategy_id,
                'name': self.strategies[strategy_id].strategy_name,
                'stock_count': len(result) if not result.empty else 0
            })

        return summary


# ========== 測試代碼 ==========

def test_strategy_manager():
    """測試策略管理器"""
    from backend.data_sources.finlab_client import FinLabClient

    print("=== Kevin 原始版策略管理器測試 ===\n")

    # 初始化
    client = FinLabClient()
    manager = StrategyManagerOriginal()

    print("📊 正在獲取數據...")

    # 獲取公司基本資訊
    company_info = client.get_company_info()

    # 獲取所有需要的數據
    data = {
        # 公司基本資訊
        'industry': company_info['industry'],

        # 價格數據
        'close': client.get_close(),
        'high': client.get_price_data()['high'],
        'low': client.get_price_data()['low'],
        'volume': client.get_volume(),

        # 財務數據
        'revenue': client.get_monthly_revenue()['revenue'],
        'common_stock': client.get_financial_data()['common_stock'],
        'cash': client.get_financial_data()['cash'],
        'operating_cash_flow': client.get_financial_data()['operating_cash_flow'],

        # 基本面指標
        'roe': client.get_fundamental_ratios()['roe'],

        # 每股盈餘
        'eps': client.get_financial_data()['eps'],

        # 融資融券
        'margin_balance': client.get_margin_data()['margin_balance'],
    }

    print("\n✅ 數據獲取完成\n")

    # 執行所有策略
    results = manager.run_all_strategies(data)

    # 顯示摘要
    summary = manager.get_summary(results)
    print("\n📊 執行摘要:")
    print(f"   總策略數: {summary['total_strategies']}")
    print(f"   有結果的策略: {summary['strategies_with_results']}")
    print(f"   推薦股票總數: {summary['total_stocks']}")

    # 顯示交集
    overlaps = manager.get_stock_appearances(results, min_appearances=2)
    if not overlaps.empty:
        print(f"\n🎯 多策略推薦（出現 ≥ 2 次）:")
        print(overlaps)
    else:
        print("\n⚠️  沒有股票被多個策略推薦")


if __name__ == "__main__":
    test_strategy_manager()

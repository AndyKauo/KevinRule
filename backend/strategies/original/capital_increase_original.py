"""
策略 5: 大現增快繳款結束（Kevin 原始版）

Excel 原始需求：
- 現增繳款日期離今天 < 2天
- 現增比率 > 5%

參考來源: reference/股市分析簡表_src_kevin.xlsx
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional
from datetime import date
from backend.strategies.base_strategy import StrategyBase


class CapitalIncreaseOriginalStrategy(StrategyBase):
    """策略 5: 大現增快繳款結束（Kevin 原始版）"""

    def __init__(self):
        self.strategy_id = 'capital_increase_original'
        self.strategy_name = '策略 5: 大現增快繳款結束（原始版）'
        description = '現增繳款日<2天，現增比率>5%'
        super().__init__(name=self.strategy_name, description=description)

    def screen(self, data: Dict[str, pd.DataFrame], as_of: Optional[date] = None) -> pd.DataFrame:
        """
        篩選符合條件的股票

        Args:
            data: 包含所有必要數據的字典
            as_of: 截止日期

        Returns:
            符合條件的股票 DataFrame，包含股票代碼和分數
        """
        print(f"\n{'='*60}")
        print(f"執行策略: {self.strategy_name}")
        print(f"{'='*60}\n")

        # ==================== 數據提取 ====================

        close = data.get('close', pd.DataFrame())
        common_stock = data.get('common_stock', pd.DataFrame())
        cash = data.get('cash', pd.DataFrame())

        if close.empty or common_stock.empty:
            print("❌ 缺少必要數據")
            return pd.DataFrame()

        print(f"✅ 數據載入完成")

        # ==================== 現增判斷（使用間接指標）====================

        # TODO: FinLab 沒有現增繳款日期數據
        # 使用間接指標替代：
        # 1. 股本近期增加 > 5%
        # 2. 現金近期增加 > 20%

        print("\n⚠️  [數據缺失] 現增繳款日期")
        print("   FinLab API 沒有現增繳款日期數據")
        print("   使用間接指標替代:")
        print("   1. 近期股本增加 > 5%")
        print("   2. 近期現金增加 > 20%")
        print("   （無法精確判斷繳款日<2天）\n")

        # 股本增加比率（相比前一期）
        stock_growth = common_stock.pct_change(fill_method=None)
        # 近期（最近3期內）股本增加 > 5%
        recent_stock_increase = (stock_growth.rolling(3).max() > 0.05)

        # 現金增加比率
        if not cash.empty:
            cash_growth = cash.pct_change(fill_method=None)
            # 近期現金增加 > 20%
            recent_cash_increase = (cash_growth.rolling(3).max() > 0.20)
        else:
            print("⚠️  缺少現金數據，跳過現金增加條件")
            recent_cash_increase = pd.Series(True, index=common_stock.index)

        # 現增訊號
        capital_increase_signal = recent_stock_increase & recent_cash_increase

        # ==================== 基本面篩選（確保品質）====================

        roe = data.get('roe', pd.DataFrame())
        if not roe.empty:
            quality_filter = roe > 10
        else:
            quality_filter = pd.Series(True, index=close.index)

        revenue = data.get('revenue', pd.DataFrame())
        if not revenue.empty:
            revenue_yoy = revenue.pct_change(12, fill_method=None)
            growth_filter = revenue_yoy > 0
        else:
            growth_filter = pd.Series(True, index=close.index)

        # ==================== 綜合篩選 ====================

        final_condition = (
            capital_increase_signal.iloc[-1] &
            quality_filter.iloc[-1] &
            growth_filter.iloc[-1] &
            self.apply_basic_filters(data)
        )

        print(f"\n🔍 篩選條件統計:")
        print(f"   - 近期股本增加>5%: {recent_stock_increase.iloc[-1].sum()} 檔")
        if not cash.empty:
            print(f"   - 近期現金增加>20%: {recent_cash_increase.iloc[-1].sum()} 檔")
        print(f"   - ROE>10%: {quality_filter.iloc[-1].sum()} 檔")
        print(f"   - ⚠️  缺少: 繳款日期<2天的精確判斷")
        print(f"   - 最終符合: {final_condition.sum()} 檔")

        selected_stocks = close.iloc[-1][final_condition].index

        if len(selected_stocks) == 0:
            print("\n❌ 沒有股票符合條件")
            return pd.DataFrame()

        # ==================== 評分 ====================

        def standardize(series):
            mean = series.mean()
            std = series.std()
            # 處理 std 為 0 或 NaN 的情況（如只有 1 個股票）
            if pd.isna(std) or std == 0:
                # 只有1個股票時，給予固定分數 50
                return pd.Series([50.0] * len(series), index=series.index)
            return (series - mean) / std

        # 股本增加幅度
        stock_increase_ratio = stock_growth.rolling(3).max().iloc[-1][final_condition]

        # 現金增加幅度
        if not cash.empty:
            cash_increase_ratio = cash_growth.rolling(3).max().iloc[-1][final_condition]
            cash_z = standardize(cash_increase_ratio)
        else:
            cash_z = pd.Series(0, index=selected_stocks)

        # ROE 水平
        if not roe.empty:
            roe_selected = roe.iloc[-1][final_condition]
            roe_z = standardize(roe_selected)
        else:
            roe_z = pd.Series(0, index=selected_stocks)

        # 標準化
        stock_z = standardize(stock_increase_ratio)

        # 綜合評分
        scores = 0.4 * stock_z + 0.3 * cash_z + 0.3 * roe_z

        # 構建結果
        result = pd.DataFrame({
            'score': scores,
            'price': close.iloc[-1][final_condition],
            'stock_increase': stock_increase_ratio,
            'cash_increase': cash_increase_ratio if not cash.empty else np.nan
        })

        result = result.sort_values('score', ascending=False)

        print(f"\n✅ 策略執行完成")
        print(f"   推薦股票數: {len(result)}")

        print(f"\n{'='*60}\n")

        return result


# ========== 測試代碼 ==========

def test_strategy():
    """測試策略"""
    from backend.data_sources.finlab_client import FinLabClient

    print("=== 測試策略 5: 大現增快繳款結束（原始版）===\n")

    client = FinLabClient()

    print("📊 正在獲取數據...")
    data = {
        'close': client.get_close(),
        'common_stock': client.get_financial_data()['common_stock'],
        'cash': client.get_financial_data()['cash'],
        'roe': client.get_fundamental_ratios()['roe'],
        'revenue': client.get_monthly_revenue()['revenue'],
    }

    strategy = CapitalIncreaseOriginalStrategy()
    result = strategy.screen(data)

    if not result.empty:
        print("\n前 10 名推薦:")
        print(result.head(10))
    else:
        print("\n沒有符合條件的股票")


if __name__ == "__main__":
    test_strategy()

"""
策略5: 大現增快繳款結束
Strategy 5: Capital Increase Payment Deadline Approaching

選股邏輯：
1. 檢測股本增加（現金增資跡象）
2. 現金及約當現金大幅增加（繳款完成）
3. 基本面良好（ROE > 10%, 營收成長）
4. 股價在合理區間
5. 成交量活躍

投資邏輯：
- 現增繳款結束後，壓力解除，股價容易反彈
- 公司取得資金後，有擴張或投資計畫
- 適合中線布局

⚠️ 重要提示：
此策略理想情況下需要現增公告數據（公開資訊觀測站），
目前使用間接指標（股本變化 + 現金增加）判斷。
實際使用時建議：
1. 手動維護現增清單
2. 整合外部數據源（如 TWSE API）
3. 使用 FinLab 的公告數據（如果有）
"""

from typing import Dict, Optional
import pandas as pd
import numpy as np
from datetime import date
from backend.strategies.base_strategy import StrategyBase
from config.settings import settings


class CapitalIncreaseStrategy(StrategyBase):
    """現金增資策略"""

    # 策略特定的數據需求
    required_data_keys = {"eps"}

    def __init__(self):
        super().__init__(
            name="大現增快繳款結束",
            description="偵測現增繳款後現金大增、基本面良好的股票"
        )

    def screen(
        self,
        data: Dict[str, pd.DataFrame],
        as_of: Optional[date] = None
    ) -> pd.DataFrame:
        """
        執行現增選股

        Args:
            data: 包含財務數據、價格等
            as_of: 選股基準日期

        Returns:
            選股結果DataFrame
        """
        print(f"\n{'='*70}")
        print(f"🚀 執行策略: {self.name}")
        print(f"{'='*70}\n")

        print("⚠️  注意: 此策略使用間接指標判斷現金增資")
        print("    理想情況下需要整合公開資訊觀測站的現增公告數據")
        print()

        # 獲取必要數據
        close = data.get('close', pd.DataFrame())
        cash = data.get('cash', pd.DataFrame())  # 現金及約當現金
        common_stock = data.get('common_stock', pd.DataFrame())  # 普通股股本
        roe = data.get('roe', pd.DataFrame())
        revenue_yoy = data.get('revenue_yoy', pd.DataFrame())

        # 檢查數據完整性
        if close.empty or cash.empty or common_stock.empty:
            print("❌ 缺少必要數據（價格、現金或股本）")
            return pd.DataFrame(columns=['stock_id', 'score', 'rank', 'metadata'])

        print(f"📊 數據範圍:")
        print(f"   價格數據: {close.shape}")
        print(f"   財務數據: {cash.shape}")
        print(f"   最新日期: {close.index[-1]}")
        print()

        # 獲取最新及前期數據
        latest_close = close.iloc[-1]

        if len(cash) < 2:
            print("❌ 財務數據不足，無法比較前後期")
            return pd.DataFrame(columns=['stock_id', 'score', 'rank', 'metadata'])

        latest_cash = cash.iloc[-1]
        prev_cash = cash.iloc[-2]

        latest_stock = common_stock.iloc[-1]
        prev_stock = common_stock.iloc[-2] if len(common_stock) >= 2 else latest_stock

        # ========== 條件1: 股本增加（現增跡象）==========
        print("📊 條件1: 股本增加 > 5%（可能是現金增資）")
        stock_increase = (latest_stock - prev_stock) / prev_stock
        cond1 = stock_increase > 0.05
        print(f"   符合條件: {cond1.sum()} 檔")

        # ========== 條件2: 現金大幅增加（繳款完成）==========
        print("\n💰 條件2: 現金及約當現金增加 > 20%")
        cash_increase = (latest_cash - prev_cash) / prev_cash
        cond2 = cash_increase > 0.20
        print(f"   符合條件: {cond2.sum()} 檔")

        # ========== 條件3: ROE > 10%（基本面良好）==========
        print("\n📈 條件3: ROE > 10%（基本面良好）")
        if not roe.empty:
            latest_roe = roe.iloc[-1]
            cond3 = latest_roe > 0.10
            print(f"   符合條件: {cond3.sum()} 檔")
        else:
            print("   ⚠️  無ROE數據，跳過此條件")
            cond3 = pd.Series(True, index=close.columns)

        # ========== 條件4: 營收年增率 > 0（持續成長）==========
        print("\n📊 條件4: 營收年增率 > 0")
        if not revenue_yoy.empty:
            latest_rev_yoy = revenue_yoy.iloc[-1]
            cond4 = latest_rev_yoy > 0
            print(f"   符合條件: {cond4.sum()} 檔")
        else:
            print("   ⚠️  無營收數據，跳過此條件")
            cond4 = pd.Series(True, index=close.columns)

        # ========== 條件5: 價格合理（20 < 價格 < 150）==========
        print("\n💵 條件5: 價格合理（20 < 價格 < 150）")
        cond5 = (latest_close > 20) & (latest_close < 150)
        print(f"   符合條件: {cond5.sum()} 檔")

        # ========== 條件6: 現金/股本比 > 0.3（現金充裕）==========
        print("\n💰 條件6: 現金占股本比 > 30%")
        # 注意單位：現金（仟元）vs 股本（仟元）
        cash_to_stock_ratio = latest_cash / latest_stock
        cond6 = cash_to_stock_ratio > 0.3
        print(f"   符合條件: {cond6.sum()} 檔")

        # ========== 基本篩選 ==========
        print("\n🔍 應用基本篩選條件...")
        basic_filter = self.apply_basic_filters(
            data,
            min_price=20,
            max_price=150,
            min_market_cap=settings.min_market_cap,
            liquidity_percentile=settings.min_liquidity_percentile,
            exclude_attention=True,
            exclude_cash_delivery=True
        )
        print(f"   基本篩選後: {basic_filter.sum()} 檔")

        # ========== 綜合條件 ==========
        print("\n🎯 整合所有條件...")
        final_condition = cond1 & cond2 & cond3 & cond4 & cond5 & cond6 & basic_filter

        selected_stocks = final_condition[final_condition].index.tolist()
        print(f"   最終選出: {len(selected_stocks)} 檔股票")

        if not selected_stocks:
            print("\n⚠️  無符合條件的股票")
            print("\n💡 提示: 此策略可能需要手動維護現增清單")
            print("    或整合公開資訊觀測站數據以提高準確度")
            return pd.DataFrame(columns=['stock_id', 'score', 'rank', 'metadata'])

        # ========== 計算綜合評分 ==========
        print("\n📊 計算綜合評分...")

        # 標準化各因子
        cash_increase_z = self.standardize(cash_increase.to_frame().T).iloc[0]
        stock_increase_z = self.standardize(stock_increase.to_frame().T).iloc[0]
        roe_z = self.standardize(latest_roe.to_frame().T).iloc[0] if not roe.empty else pd.Series(0, index=close.columns)
        rev_yoy_z = self.standardize(latest_rev_yoy.to_frame().T).iloc[0] if not revenue_yoy.empty else pd.Series(0, index=close.columns)

        # 綜合評分
        scores = pd.Series(0.0, index=close.columns)
        scores = (
            0.30 * cash_increase_z.fillna(0) +     # 現金增加
            0.20 * stock_increase_z.fillna(0) +    # 股本增加
            0.25 * roe_z.fillna(0) +               # ROE
            0.25 * rev_yoy_z.fillna(0)             # 營收成長
        )

        # 只保留選中的股票
        scores = scores[selected_stocks]

        # ========== 格式化結果 ==========
        result = self.format_result(
            selections=selected_stocks,
            scores=scores,
            metadata={
                'strategy': 'capital_increase',
                'min_stock_increase': 0.05,
                'min_cash_increase': 0.20,
                'data_source': 'indirect_indicators'
            }
        )

        # 添加詳細資訊
        result['price'] = result['stock_id'].map(latest_close)
        result['cash_increase'] = result['stock_id'].map(cash_increase)
        result['stock_increase'] = result['stock_id'].map(stock_increase)
        result['roe'] = result['stock_id'].map(latest_roe) if not roe.empty else None
        result['cash_億'] = result['stock_id'].map(latest_cash) / 1e5  # 仟元 -> 億元

        print("\n✅ 選股完成!")
        print(f"\n前10名股票:")
        display_cols = ['stock_id', 'score', 'price', 'cash_increase', 'stock_increase', 'roe']
        if 'roe' in result.columns and result['roe'].notna().any():
            print(result.head(10)[display_cols].to_string(index=False))
        else:
            print(result.head(10)[['stock_id', 'score', 'price', 'cash_increase', 'stock_increase']].to_string(index=False))

        print(f"\n💡 建議: 手動查證現增公告，確認繳款狀態")
        print(f"{'='*70}\n")

        return result


# ========== 測試代碼 ==========

def test_capital_increase_strategy():
    """測試現增策略"""
    print("=== 現金增資策略測試 ===")
    print()

    # 創建模擬數據
    # 財務數據通常是季度
    fin_dates = pd.date_range('2023-01-01', periods=4, freq='QS')
    price_dates = pd.date_range('2023-01-01', periods=252, freq='D')
    stocks = ['3008', '4938', '2317', '2330', '2454']

    # 模擬股本數據（仟元）
    common_stock = pd.DataFrame(
        np.random.randint(1000000, 5000000, (4, len(stocks))),
        index=fin_dates,
        columns=stocks
    )

    # 模擬現增：3008 最近一季股本增加15%
    common_stock.iloc[-1, 0] = common_stock.iloc[-2, 0] * 1.15

    # 模擬現金數據（仟元）
    cash = pd.DataFrame(
        np.random.randint(500000, 2000000, (4, len(stocks))),
        index=fin_dates,
        columns=stocks
    )

    # 3008 現金大增30%（繳款完成）
    cash.iloc[-1, 0] = cash.iloc[-2, 0] * 1.30

    # 模擬ROE
    roe = pd.DataFrame(
        np.random.uniform(0.05, 0.20, (4, len(stocks))),
        index=fin_dates,
        columns=stocks
    )
    roe.iloc[-1, 0] = 0.15  # 3008 ROE 15%

    # 模擬營收數據
    rev_dates = pd.date_range('2023-01-01', periods=12, freq='MS')
    revenue = pd.DataFrame(
        np.random.randint(500000, 2000000, (12, len(stocks))),
        index=rev_dates,
        columns=stocks
    )
    revenue_yoy = revenue.pct_change(12)

    # 模擬價格
    close = pd.DataFrame(
        np.random.randn(252, len(stocks)) * 5 + 80,
        index=price_dates,
        columns=stocks
    )

    # 模擬市值
    market_cap = pd.DataFrame(
        np.random.randn(252, len(stocks)) * 1e10 + 3e10,
        index=price_dates,
        columns=stocks
    )

    # 組合數據
    data = {
        'close': close,
        'cash': cash,
        'common_stock': common_stock,
        'roe': roe,
        'revenue_yoy': revenue_yoy,
        'market_cap': market_cap,
        'volume': close * 100000
    }

    # 執行策略
    strategy = CapitalIncreaseStrategy()
    result = strategy.screen(data)

    print("\n最終結果:")
    print(result)
    print()
    print("✅ 測試完成")


if __name__ == "__main__":
    test_capital_increase_strategy()

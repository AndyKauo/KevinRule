"""
策略1: 營收動能高於同業平均
Strategy 1: Revenue Momentum Above Industry Average

選股邏輯：
1. 月營收年增率（YoY）> 20% 且高於產業中位數
2. 月營收月增率（MoM）> 0（持續成長）
3. 近3個月營收加速（動能增強）
4. 價格 < 150 元（避免高價股）
5. 排除問題股票

參考來源: reference/stockCC-claude/finlab_實戰策略範例.py - taiwan_earnings_momentum_strategy
"""

from typing import Dict, Optional
import pandas as pd
import numpy as np
from datetime import date
from backend.strategies.base_strategy import StrategyBase
from config.settings import settings


class RevenueMomentumStrategy(StrategyBase):
    """營收動能策略"""

    def __init__(self):
        super().__init__(
            name="營收動能高於同業平均",
            description="選擇月營收YoY>20%且持續成長的股票，價格<150元"
        )

    def screen(
        self,
        data: Dict[str, pd.DataFrame],
        as_of: Optional[date] = None
    ) -> pd.DataFrame:
        """
        執行營收動能選股

        Args:
            data: 包含revenue, revenue_yoy, revenue_mom, close等數據
            as_of: 選股基準日期

        Returns:
            選股結果DataFrame
        """
        print(f"\n{'='*70}")
        print(f"🚀 執行策略: {self.name}")
        print(f"{'='*70}\n")

        # 獲取必要數據
        revenue = data.get('revenue', pd.DataFrame())
        revenue_yoy = data.get('revenue_yoy', pd.DataFrame())
        revenue_mom = data.get('revenue_mom', pd.DataFrame())
        close = data.get('close', pd.DataFrame())

        # 檢查數據完整性
        if revenue.empty or revenue_yoy.empty or close.empty:
            print("❌ 缺少必要數據（營收或價格）")
            return pd.DataFrame(columns=['stock_id', 'score', 'rank', 'metadata'])

        print(f"📊 數據範圍:")
        print(f"   營收數據: {revenue.shape}")
        print(f"   價格數據: {close.shape}")
        print(f"   最新日期: {revenue.index[-1] if len(revenue) > 0 else 'N/A'}")
        print()

        # ========== 條件1: 營收年增率 > 20% ==========
        print("📈 條件1: 營收年增率 > 20%")
        latest_yoy = revenue_yoy.iloc[-1]
        cond1 = latest_yoy > 0.20
        print(f"   符合條件: {cond1.sum()} 檔")

        # ========== 條件2: 營收月增率 > 0（持續成長）==========
        print("📈 條件2: 營收月增率 > 0")
        latest_mom = revenue_mom.iloc[-1] if not revenue_mom.empty else pd.Series()
        cond2 = latest_mom > 0 if not latest_mom.empty else pd.Series(True, index=cond1.index)
        print(f"   符合條件: {cond2.sum()} 檔")

        # ========== 條件3: 營收加速（近3個月YoY上升）==========
        print("📈 條件3: 營收動能加速（3個月趨勢向上）")
        if len(revenue_yoy) >= 3:
            # 計算近3個月YoY的斜率
            recent_yoy = revenue_yoy.iloc[-3:]
            yoy_trend = recent_yoy.apply(lambda x: self._calculate_trend(x), axis=0)
            cond3 = yoy_trend > 0
        else:
            cond3 = pd.Series(True, index=cond1.index)
        print(f"   符合條件: {cond3.sum()} 檔")

        # ========== 條件4: 高於產業中位數 ==========
        print("📊 條件4: 營收YoY高於產業中位數")
        industry_median = latest_yoy.median()
        cond4 = latest_yoy > industry_median
        print(f"   產業中位數: {industry_median:.2%}")
        print(f"   符合條件: {cond4.sum()} 檔")

        # ========== 條件5: 價格 < 150 元 ==========
        print("💰 條件5: 股價 < 150 元")
        latest_close = close.iloc[-1]
        cond5 = latest_close < 150
        print(f"   符合條件: {cond5.sum()} 檔")

        # ========== 基本篩選 ==========
        print("\n🔍 應用基本篩選條件...")
        basic_filter = self.apply_basic_filters(
            data,
            min_price=10,  # 最低10元
            max_price=150,  # 最高150元
            min_market_cap=settings.min_market_cap,
            liquidity_percentile=settings.min_liquidity_percentile,
            exclude_attention=True,
            exclude_cash_delivery=True
        )
        print(f"   基本篩選後: {basic_filter.sum()} 檔")

        # ========== 綜合條件 ==========
        print("\n🎯 整合所有條件...")
        final_condition = cond1 & cond2 & cond3 & cond4 & cond5 & basic_filter

        selected_stocks = final_condition[final_condition].index.tolist()
        print(f"   最終選出: {len(selected_stocks)} 檔股票")

        if not selected_stocks:
            print("\n⚠️  無符合條件的股票")
            return pd.DataFrame(columns=['stock_id', 'score', 'rank', 'metadata'])

        # ========== 計算綜合評分 ==========
        print("\n📊 計算綜合評分...")

        # 標準化各因子
        yoy_z = self.standardize(revenue_yoy.iloc[-1:]).iloc[0]
        mom_z = self.standardize(revenue_mom.iloc[-1:]).iloc[0] if not revenue_mom.empty else pd.Series(0, index=latest_yoy.index)

        # 綜合評分: YoY 60% + MoM 20% + Trend 20%
        scores = pd.Series(0.0, index=latest_yoy.index)
        scores = (
            0.6 * yoy_z.fillna(0) +
            0.2 * mom_z.fillna(0) +
            0.2 * yoy_trend.fillna(0)
        )

        # 只保留選中的股票
        scores = scores[selected_stocks]

        # ========== 格式化結果 ==========
        result = self.format_result(
            selections=selected_stocks,
            scores=scores,
            metadata={
                'strategy': 'revenue_momentum',
                'yoy_threshold': 0.20,
                'industry_median': float(industry_median),
                'max_price': 150
            }
        )

        # 添加詳細資訊
        result['yoy'] = result['stock_id'].map(latest_yoy)
        result['mom'] = result['stock_id'].map(latest_mom)
        result['price'] = result['stock_id'].map(latest_close)

        print("\n✅ 選股完成!")
        print(f"\n前10名股票:")
        print(result.head(10)[['stock_id', 'score', 'yoy', 'mom', 'price']].to_string(index=False))
        print(f"\n{'='*70}\n")

        return result

    def _calculate_trend(self, series: pd.Series) -> float:
        """
        計算數列的趨勢（線性回歸斜率）

        Args:
            series: 時間序列數據

        Returns:
            斜率值（正數表示上升趨勢）
        """
        if len(series) < 2:
            return 0.0

        # 移除NaN
        clean_series = series.dropna()
        if len(clean_series) < 2:
            return 0.0

        # 簡單線性回歸
        x = np.arange(len(clean_series))
        y = clean_series.values

        # 計算斜率
        x_mean = x.mean()
        y_mean = y.mean()

        numerator = ((x - x_mean) * (y - y_mean)).sum()
        denominator = ((x - x_mean) ** 2).sum()

        if denominator == 0:
            return 0.0

        slope = numerator / denominator
        return slope


# ========== 測試代碼 ==========

def test_revenue_momentum_strategy():
    """測試營收動能策略"""
    print("=== 營收動能策略測試 ===")
    print()

    # 創建模擬數據
    dates = pd.date_range('2023-01-01', periods=12, freq='MS')  # 12個月
    stocks = ['2330', '2317', '2454', '2881', '2882', '3008', '2412', '2308']

    # 模擬營收數據（仟元）
    revenue = pd.DataFrame(
        np.random.randint(5000000, 10000000, (12, len(stocks))),
        index=dates,
        columns=stocks
    )

    # 模擬高成長股票（2330, 2454）
    revenue['2330'] = revenue['2330'] * np.linspace(1.0, 1.5, 12)
    revenue['2454'] = revenue['2454'] * np.linspace(1.0, 1.4, 12)

    # 計算YoY和MoM
    revenue_yoy = revenue.pct_change(12)
    revenue_mom = revenue.pct_change(1)

    # 模擬價格數據
    price_dates = pd.date_range('2023-01-01', periods=252, freq='D')
    close = pd.DataFrame(
        np.random.randn(252, len(stocks)) * 5 + 100,
        index=price_dates,
        columns=stocks
    )
    close['2330'] = 500  # 台積電設為500元（應該被排除）
    close['2454'] = 80   # 聯發科設為80元

    # 模擬市值數據
    market_cap = pd.DataFrame(
        np.random.randn(252, len(stocks)) * 1e10 + 5e10,
        index=price_dates,
        columns=stocks
    )

    # 組合數據
    data = {
        'revenue': revenue,
        'revenue_yoy': revenue_yoy,
        'revenue_mom': revenue_mom,
        'close': close,
        'market_cap': market_cap,
        'volume': close * 1000000  # 模擬成交量
    }

    # 執行策略
    strategy = RevenueMomentumStrategy()
    result = strategy.screen(data)

    print("\n最終結果:")
    print(result)
    print()
    print("✅ 測試完成")


if __name__ == "__main__":
    test_revenue_momentum_strategy()

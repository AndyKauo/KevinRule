"""
策略2: 低價小股本營收創一年高
Strategy 2: Low Price Small Cap with Revenue High

選股邏輯：
1. 股價 < 100 元（低價）
2. 市值 < 100億（小股本）
3. 當月營收創近12個月新高
4. 營收年增率 > 15%（持續成長）
5. 流動性足夠（排除冷門股）

投資邏輯：
- 小型股彈性大，營收突破代表業績轉機
- 低價股吸引散戶關注，容易形成主升段
- 風險：波動大、流動性相對較差
"""

from typing import Dict, Optional
import pandas as pd
import numpy as np
from datetime import date
from backend.strategies.base_strategy import StrategyBase
from config.settings import settings


class LowPriceSmallCapStrategy(StrategyBase):
    """低價小股本營收創高策略"""

    def __init__(self):
        super().__init__(
            name="低價小股本營收創一年高",
            description="選擇股價<100元、市值<100億、營收創新高的小型成長股"
        )

    def screen(
        self,
        data: Dict[str, pd.DataFrame],
        as_of: Optional[date] = None
    ) -> pd.DataFrame:
        """
        執行低價小股本選股

        Args:
            data: 包含close, market_cap, revenue, revenue_yoy等數據
            as_of: 選股基準日期

        Returns:
            選股結果DataFrame
        """
        print(f"\n{'='*70}")
        print(f"🚀 執行策略: {self.name}")
        print(f"{'='*70}\n")

        # 獲取必要數據
        close = data.get('close', pd.DataFrame())
        market_cap = data.get('market_cap', pd.DataFrame())
        revenue = data.get('revenue', pd.DataFrame())
        revenue_yoy = data.get('revenue_yoy', pd.DataFrame())

        # 檢查數據完整性
        if close.empty or market_cap.empty or revenue.empty:
            print("❌ 缺少必要數據（價格、市值或營收）")
            return pd.DataFrame(columns=['stock_id', 'score', 'rank', 'metadata'])

        print(f"📊 數據範圍:")
        print(f"   價格數據: {close.shape}")
        print(f"   市值數據: {market_cap.shape}")
        print(f"   營收數據: {revenue.shape}")
        print(f"   最新日期: {close.index[-1]}")
        print()

        # 獲取最新數據
        latest_close = close.iloc[-1]
        latest_market_cap = market_cap.iloc[-1]
        latest_revenue_yoy = revenue_yoy.iloc[-1] if not revenue_yoy.empty else pd.Series()

        # ========== 條件1: 低價股（< 100元）==========
        print("💰 條件1: 股價 < 100 元")
        cond1 = latest_close < 100
        print(f"   符合條件: {cond1.sum()} 檔")
        print(f"   平均股價: {latest_close[cond1].mean():.2f} 元")

        # ========== 條件2: 小股本（市值 < 100億）==========
        print("\n📊 條件2: 市值 < 100億")
        market_cap_threshold = 10_000_000_000  # 100億
        cond2 = latest_market_cap < market_cap_threshold
        print(f"   符合條件: {cond2.sum()} 檔")
        print(f"   平均市值: {latest_market_cap[cond2].mean() / 1e8:.2f} 億")

        # ========== 條件3: 營收創12個月新高 ==========
        print("\n📈 條件3: 當月營收創近12個月新高")
        if len(revenue) >= 12:
            # 取最近12個月營收
            recent_12m_revenue = revenue.iloc[-12:]

            # 當月營收是否為最高
            latest_revenue = revenue.iloc[-1]
            max_12m_revenue = recent_12m_revenue.max(axis=0)

            # 允許一點誤差（0.99倍），避免浮點數問題
            cond3 = latest_revenue >= (max_12m_revenue * 0.99)
        else:
            print(f"   ⚠️  營收數據不足12個月（僅有{len(revenue)}個月），使用全部數據")
            latest_revenue = revenue.iloc[-1]
            max_revenue = revenue.max(axis=0)
            cond3 = latest_revenue >= (max_revenue * 0.99)

        print(f"   符合條件: {cond3.sum()} 檔")

        # ========== 條件4: 營收年增率 > 15% ==========
        print("\n📈 條件4: 營收年增率 > 15%")
        if not latest_revenue_yoy.empty:
            cond4 = latest_revenue_yoy > 0.15
            print(f"   符合條件: {cond4.sum()} 檔")
            print(f"   平均YoY: {latest_revenue_yoy[cond4].mean():.2%}")
        else:
            print("   ⚠️  無營收年增率數據，跳過此條件")
            cond4 = pd.Series(True, index=cond1.index)

        # ========== 條件5: 市值 > 10億（排除太小的公司）==========
        print("\n🔍 條件5: 市值 > 10億（避免過小公司）")
        min_market_cap = 1_000_000_000  # 10億
        cond5 = latest_market_cap > min_market_cap
        print(f"   符合條件: {cond5.sum()} 檔")

        # ========== 基本篩選 ==========
        print("\n🔍 應用基本篩選條件...")
        basic_filter = self.apply_basic_filters(
            data,
            min_price=10,  # 最低10元（避免雞蛋水餃股）
            max_price=100,
            min_market_cap=min_market_cap,
            liquidity_percentile=0.4,  # 保留前60%流動性（小型股流動性較差）
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

        # 營收創新高程度（當月營收 / 12個月平均）
        if len(revenue) >= 12:
            avg_12m_revenue = recent_12m_revenue.mean(axis=0)
            revenue_ratio = latest_revenue / avg_12m_revenue
        else:
            avg_revenue = revenue.mean(axis=0)
            revenue_ratio = latest_revenue / avg_revenue

        # 標準化評分因子
        revenue_ratio_z = self.standardize(revenue_ratio.to_frame().T).iloc[0]
        yoy_z = self.standardize(latest_revenue_yoy.to_frame().T).iloc[0] if not latest_revenue_yoy.empty else pd.Series(0, index=revenue_ratio.index)

        # 市值因子（越小越好，取負數）
        market_cap_z = -self.standardize(latest_market_cap.to_frame().T).iloc[0]

        # 綜合評分: 營收新高40% + YoY 30% + 小市值 30%
        scores = pd.Series(0.0, index=latest_close.index)
        scores = (
            0.4 * revenue_ratio_z.fillna(0) +
            0.3 * yoy_z.fillna(0) +
            0.3 * market_cap_z.fillna(0)
        )

        # 只保留選中的股票
        scores = scores[selected_stocks]

        # ========== 格式化結果 ==========
        result = self.format_result(
            selections=selected_stocks,
            scores=scores,
            metadata={
                'strategy': 'low_price_small_cap',
                'max_price': 100,
                'max_market_cap': 100,  # 億
                'min_yoy': 0.15
            }
        )

        # 添加詳細資訊
        result['price'] = result['stock_id'].map(latest_close)
        result['market_cap_億'] = result['stock_id'].map(latest_market_cap) / 1e8
        result['revenue_ratio'] = result['stock_id'].map(revenue_ratio)
        result['yoy'] = result['stock_id'].map(latest_revenue_yoy)

        print("\n✅ 選股完成!")
        print(f"\n前10名股票:")
        display_cols = ['stock_id', 'score', 'price', 'market_cap_億', 'revenue_ratio', 'yoy']
        print(result.head(10)[display_cols].to_string(index=False))
        print(f"\n{'='*70}\n")

        return result


# ========== 測試代碼 ==========

def test_low_price_small_cap_strategy():
    """測試低價小股本策略"""
    print("=== 低價小股本策略測試 ===")
    print()

    # 創建模擬數據
    dates = pd.date_range('2023-01-01', periods=12, freq='MS')  # 12個月
    stocks = ['6123', '6456', '3592', '4938', '2317', '2330']  # 模擬小型股和大型股

    # 模擬營收數據
    revenue = pd.DataFrame(
        np.random.randint(500000, 2000000, (12, len(stocks))),
        index=dates,
        columns=stocks
    )

    # 模擬營收創新高的股票（6123, 3592）
    revenue['6123'] = revenue['6123'] * np.linspace(1.0, 1.8, 12)
    revenue['3592'] = revenue['3592'] * np.linspace(1.0, 1.6, 12)

    # 計算YoY
    revenue_yoy = revenue.pct_change(12)

    # 模擬價格數據
    price_dates = pd.date_range('2023-01-01', periods=252, freq='D')
    close = pd.DataFrame(
        np.random.randn(252, len(stocks)) * 5 + 60,
        index=price_dates,
        columns=stocks
    )
    close['2330'] = 500  # 台積電高價（應被排除）
    close['6123'] = 45   # 低價小型股
    close['3592'] = 68   # 低價小型股

    # 模擬市值數據
    market_cap = pd.DataFrame(index=price_dates, columns=stocks)
    market_cap['6123'] = 3e9   # 30億（小股本）
    market_cap['3592'] = 5e9   # 50億（小股本）
    market_cap['4938'] = 8e9   # 80億（小股本）
    market_cap['6456'] = 15e9  # 150億（中型，應被排除）
    market_cap['2317'] = 50e9  # 500億（大型，應被排除）
    market_cap['2330'] = 500e9 # 5000億（超大型，應被排除）

    # 組合數據
    data = {
        'revenue': revenue,
        'revenue_yoy': revenue_yoy,
        'close': close,
        'market_cap': market_cap,
        'volume': close * 100000  # 模擬成交量
    }

    # 執行策略
    strategy = LowPriceSmallCapStrategy()
    result = strategy.screen(data)

    print("\n最終結果:")
    print(result)
    print()
    print("✅ 測試完成")


if __name__ == "__main__":
    test_low_price_small_cap_strategy()

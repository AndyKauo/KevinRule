"""
策略4: 連兩日大戶大買超
Strategy 4: Institutional Heavy Buying (2 Days)

選股邏輯：
1. 連續2日成交量放大（> 20日均量1.5倍）
2. 連續2日上漲（收盤價 > 前日）
3. 融資減少（散戶賣、主力接）
4. 大單成交比例高（推測有法人進場）
5. 價格在合理區間

投資邏輯：
- 量增價漲 + 融資減 = 主力吸籌訊號
- 連續2日確認不是單日異常
- 適合短線操作
- 風險：需快速反應，避免追高

注意：
由於 FinLab 可能沒有直接的法人買賣超數據，
此策略使用間接指標（成交量、價格、融資）推測大戶行為
"""

from typing import Dict, Optional
import pandas as pd
import numpy as np
from datetime import date
from backend.strategies.base_strategy import StrategyBase
from config.settings import settings


class InstitutionalBuyingStrategy(StrategyBase):
    """大戶買超策略（連續2日）"""

    # 策略特定的數據需求
    required_data_keys = {"eps", "margin_buy", "margin_sell"}

    def __init__(self):
        super().__init__(
            name="連兩日大戶大買超",
            description="連續2日量增價漲且融資減少，推測主力吸籌"
        )

    def screen(
        self,
        data: Dict[str, pd.DataFrame],
        as_of: Optional[date] = None
    ) -> pd.DataFrame:
        """
        執行大戶買超選股

        Args:
            data: 包含close, volume, margin_balance等數據
            as_of: 選股基準日期

        Returns:
            選股結果DataFrame
        """
        print(f"\n{'='*70}")
        print(f"🚀 執行策略: {self.name}")
        print(f"{'='*70}\n")

        # 獲取必要數據
        close = data.get('close', pd.DataFrame())
        volume = data.get('volume', pd.DataFrame())
        margin_balance = data.get('margin_balance', pd.DataFrame())  # 融資餘額

        # 檢查數據完整性
        if close.empty or volume.empty:
            print("❌ 缺少必要數據（價格或成交量）")
            return pd.DataFrame(columns=['stock_id', 'score', 'rank', 'metadata'])

        print(f"📊 數據範圍:")
        print(f"   價格數據: {close.shape}")
        print(f"   成交量數據: {volume.shape}")
        print(f"   最新日期: {close.index[-1]}")
        print()

        if len(close) < 22:  # 需要至少22天數據（20日均線 + 2日）
            print("❌ 數據不足22天，無法執行策略")
            return pd.DataFrame(columns=['stock_id', 'score', 'rank', 'metadata'])

        # 獲取最近3日數據（今天、昨天、前天）
        close_t0 = close.iloc[-1]  # 今天
        close_t1 = close.iloc[-2]  # 昨天
        close_t2 = close.iloc[-3]  # 前天

        volume_t0 = volume.iloc[-1]
        volume_t1 = volume.iloc[-2]

        # ========== 條件1: 連續2日上漲 ==========
        print("📈 條件1: 連續2日上漲")
        day1_up = close_t0 > close_t1  # 今天 > 昨天
        day2_up = close_t1 > close_t2  # 昨天 > 前天
        cond1 = day1_up & day2_up

        print(f"   符合條件: {cond1.sum()} 檔")

        # ========== 條件2: 連續2日成交量放大（> 20日均量1.5倍）==========
        print("\n📊 條件2: 連續2日成交量放大（> 20日均量1.5倍）")
        avg_volume_20d = volume.iloc[-22:-2].mean(axis=0)  # 排除最近2日計算均量

        day1_vol_up = volume_t0 > (avg_volume_20d * 1.5)
        day2_vol_up = volume_t1 > (avg_volume_20d * 1.5)
        cond2 = day1_vol_up & day2_vol_up

        print(f"   符合條件: {cond2.sum()} 檔")

        # ========== 條件3: 融資減少（可選，如果有數據）==========
        print("\n📉 條件3: 融資減少（主力吸籌）")
        if not margin_balance.empty and len(margin_balance) >= 3:
            margin_t0 = margin_balance.iloc[-1]
            margin_t1 = margin_balance.iloc[-2]
            margin_t2 = margin_balance.iloc[-3]

            # 連續2日融資減少
            day1_margin_down = margin_t0 < margin_t1
            day2_margin_down = margin_t1 < margin_t2
            cond3 = day1_margin_down & day2_margin_down

            print(f"   符合條件: {cond3.sum()} 檔")
        else:
            print("   ⚠️  無融資數據，跳過此條件")
            cond3 = pd.Series(True, index=close.columns)

        # ========== 條件4: 漲幅適中（單日 < 7%，避免漲停追高）==========
        print("\n💰 條件4: 漲幅適中（單日 < 7%）")
        day1_return = (close_t0 / close_t1 - 1)
        day2_return = (close_t1 / close_t2 - 1)

        cond4 = (day1_return < 0.07) & (day2_return < 0.07) & (day1_return > 0) & (day2_return > 0)
        print(f"   符合條件: {cond4.sum()} 檔")

        # ========== 條件5: 價格在合理區間（20 < 價格 < 200）==========
        print("\n💵 條件5: 價格合理（20 < 價格 < 200）")
        cond5 = (close_t0 > 20) & (close_t0 < 200)
        print(f"   符合條件: {cond5.sum()} 檔")

        # ========== 條件6: 成交量排名（當日成交量 > 市場中位數）==========
        print("\n📊 條件6: 成交量活躍（> 市場中位數）")
        volume_median = volume_t0.median()
        cond6 = volume_t0 > volume_median
        print(f"   市場成交量中位數: {volume_median:,.0f} 股")
        print(f"   符合條件: {cond6.sum()} 檔")

        # ========== 基本篩選 ==========
        print("\n🔍 應用基本篩選條件...")
        basic_filter = self.apply_basic_filters(
            data,
            min_price=20,
            max_price=200,
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
            return pd.DataFrame(columns=['stock_id', 'score', 'rank', 'metadata'])

        # ========== 計算綜合評分 ==========
        print("\n📊 計算綜合評分...")

        # 成交量放大倍數
        volume_ratio_t0 = volume_t0 / avg_volume_20d
        volume_ratio_t1 = volume_t1 / avg_volume_20d
        avg_volume_ratio = (volume_ratio_t0 + volume_ratio_t1) / 2

        # 2日累積漲幅
        total_return_2d = (close_t0 / close_t2 - 1)

        # 融資變化率（如果有數據）
        if not margin_balance.empty and len(margin_balance) >= 3:
            margin_change = (margin_t0 - margin_t2) / margin_t2
        else:
            margin_change = pd.Series(0, index=close.columns)

        # 標準化各因子
        volume_ratio_z = self.standardize(avg_volume_ratio.to_frame().T).iloc[0]
        return_z = self.standardize(total_return_2d.to_frame().T).iloc[0]
        margin_z = -self.standardize(margin_change.to_frame().T).iloc[0]  # 融資減少為正

        # 綜合評分
        scores = pd.Series(0.0, index=close.columns)
        scores = (
            0.40 * volume_ratio_z.fillna(0) +   # 成交量放大
            0.30 * return_z.fillna(0) +         # 累積漲幅
            0.30 * margin_z.fillna(0)           # 融資減少
        )

        # 只保留選中的股票
        scores = scores[selected_stocks]

        # ========== 格式化結果 ==========
        result = self.format_result(
            selections=selected_stocks,
            scores=scores,
            metadata={
                'strategy': 'institutional_buying',
                'consecutive_days': 2,
                'volume_threshold': 1.5
            }
        )

        # 添加詳細資訊
        result['price'] = result['stock_id'].map(close_t0)
        result['return_2d'] = result['stock_id'].map(total_return_2d)
        result['volume_ratio'] = result['stock_id'].map(avg_volume_ratio)
        result['day1_return'] = result['stock_id'].map(day1_return)
        result['day2_return'] = result['stock_id'].map(day2_return)

        print("\n✅ 選股完成!")
        print(f"\n前10名股票:")
        display_cols = ['stock_id', 'score', 'price', 'return_2d', 'volume_ratio', 'day1_return']
        print(result.head(10)[display_cols].to_string(index=False))
        print(f"\n{'='*70}\n")

        return result


# ========== 測試代碼 ==========

def test_institutional_buying_strategy():
    """測試大戶買超策略"""
    print("=== 大戶買超策略測試 ===")
    print()

    # 創建模擬數據
    dates = pd.date_range('2024-01-01', periods=30, freq='D')
    stocks = ['2330', '2454', '2317', '3008', '2412', '2881']

    # 模擬價格數據
    close = pd.DataFrame(
        np.random.randn(30, len(stocks)) * 2 + 100,
        index=dates,
        columns=stocks
    )

    # 模擬大戶買超股票（2330, 2454）：最近2日上漲
    close.iloc[-2, 0] = close.iloc[-3, 0] * 1.03  # 2330 昨天漲3%
    close.iloc[-1, 0] = close.iloc[-2, 0] * 1.04  # 2330 今天漲4%

    close.iloc[-2, 1] = close.iloc[-3, 1] * 1.02  # 2454 昨天漲2%
    close.iloc[-1, 1] = close.iloc[-2, 1] * 1.03  # 2454 今天漲3%

    # 模擬成交量（最近2日放大）
    volume = pd.DataFrame(
        np.random.randint(1000000, 3000000, (30, len(stocks))),
        index=dates,
        columns=stocks
    )

    # 2330, 2454 最近2日成交量放大
    avg_vol = volume.iloc[-22:-2].mean(axis=0)
    volume.iloc[-2, 0] = avg_vol[0] * 2.0  # 2330 昨天量增2倍
    volume.iloc[-1, 0] = avg_vol[0] * 2.5  # 2330 今天量增2.5倍

    volume.iloc[-2, 1] = avg_vol[1] * 1.8  # 2454 昨天量增1.8倍
    volume.iloc[-1, 1] = avg_vol[1] * 2.2  # 2454 今天量增2.2倍

    # 模擬融資餘額（大戶買超時減少）
    margin_balance = pd.DataFrame(
        np.random.randint(5000, 10000, (30, len(stocks))),
        index=dates,
        columns=stocks
    )

    # 2330, 2454 融資減少
    margin_balance.iloc[-2, 0] = margin_balance.iloc[-3, 0] * 0.95
    margin_balance.iloc[-1, 0] = margin_balance.iloc[-2, 0] * 0.93

    margin_balance.iloc[-2, 1] = margin_balance.iloc[-3, 1] * 0.97
    margin_balance.iloc[-1, 1] = margin_balance.iloc[-2, 1] * 0.95

    # 模擬市值
    market_cap = pd.DataFrame(
        np.random.randn(30, len(stocks)) * 1e10 + 5e10,
        index=dates,
        columns=stocks
    )

    # 組合數據
    data = {
        'close': close,
        'volume': volume,
        'margin_balance': margin_balance,
        'market_cap': market_cap
    }

    # 執行策略
    strategy = InstitutionalBuyingStrategy()
    result = strategy.screen(data)

    print("\n最終結果:")
    print(result)
    print()
    print("✅ 測試完成")


if __name__ == "__main__":
    test_institutional_buying_strategy()

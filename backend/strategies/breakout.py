"""
策略3: 長時間未破底後創新高
Strategy 3: Breakout After Long Base

選股邏輯：
1. 過去60天未創新低（底部穩固）
2. 最近創20天新高（突破整理）
3. 波動率收斂（底部震盪收窄）
4. 成交量放大（突破確認）
5. 相對強度良好（強於大盤）

投資邏輯：
- 長時間整理後突破，代表籌碼穩定
- 突破配合量增，確認買盤進場
- 類似 VCP (Volatility Contraction Pattern) 型態
- 適合波段操作

參考來源: reference/stockCC-claude/finlab_實戰策略範例.py - vcp_breakout_strategy
"""

from typing import Dict, Optional
import pandas as pd
import numpy as np
from datetime import date
from backend.strategies.base_strategy import StrategyBase
from config.settings import settings


class BreakoutAfterBaseStrategy(StrategyBase):
    """長時間未破底後突破策略"""

    # 策略特定的數據需求
    required_data_keys = {"revenue", "roe", "dividend_announcement", "dividend_yield"}

    def __init__(self):
        super().__init__(
            name="長時間未破底後創新高",
            description="選擇底部穩固（60天未破底）且近期突破的股票"
        )

    def screen(
        self,
        data: Dict[str, pd.DataFrame],
        as_of: Optional[date] = None
    ) -> pd.DataFrame:
        """
        執行突破選股

        Args:
            data: 包含close, high, low, volume等數據
            as_of: 選股基準日期

        Returns:
            選股結果DataFrame
        """
        print(f"\n{'='*70}")
        print(f"🚀 執行策略: {self.name}")
        print(f"{'='*70}\n")

        # 獲取必要數據
        close = data.get('close', pd.DataFrame())
        high = data.get('high', pd.DataFrame())
        low = data.get('low', pd.DataFrame())
        volume = data.get('volume', pd.DataFrame())

        # 檢查數據完整性
        if close.empty or high.empty or low.empty:
            print("❌ 缺少必要數據（價格或成交量）")
            return pd.DataFrame(columns=['stock_id', 'score', 'rank', 'metadata'])

        print(f"📊 數據範圍:")
        print(f"   價格數據: {close.shape}")
        print(f"   最新日期: {close.index[-1]}")
        print()

        # 獲取最新價格
        latest_close = close.iloc[-1]

        # ========== 條件1: 60天未創新低（底部穩固）==========
        print("📊 條件1: 過去60天未創新低")
        if len(close) >= 60:
            # 取過去60天數據
            recent_60d = close.iloc[-60:]
            low_60d = low.iloc[-60:]

            # 最低點是否在前40天（允許最近20天回測，但不能創新低）
            min_60d = low_60d.min(axis=0)
            min_60d_date = low_60d.idxmin(axis=0)

            # 檢查最低點是否在前40天
            cutoff_date = low_60d.index[-40] if len(low_60d) >= 40 else low_60d.index[0]
            cond1 = min_60d_date < cutoff_date

        else:
            print(f"   ⚠️  數據不足60天（僅有{len(close)}天）")
            cond1 = pd.Series(True, index=close.columns)

        print(f"   符合條件: {cond1.sum()} 檔")

        # ========== 條件2: 創20天新高（突破整理）==========
        print("\n📈 條件2: 創20天新高")
        if len(close) >= 20:
            high_20d = high.iloc[-20:]
            max_20d = high_20d.max(axis=0)

            # 當前收盤價是否接近20天最高價（允許1%誤差）
            cond2 = latest_close >= (max_20d * 0.99)
        else:
            print(f"   ⚠️  數據不足20天")
            cond2 = pd.Series(True, index=close.columns)

        print(f"   符合條件: {cond2.sum()} 檔")

        # ========== 條件3: 波動率收斂（過去20天波動 < 過去60天波動）==========
        print("\n📉 條件3: 波動率收斂（底部震盪收窄）")
        if len(close) >= 60:
            # 計算波動率（標準差 / 均值）
            volatility_20d = close.iloc[-20:].std() / close.iloc[-20:].mean()
            volatility_60d = close.iloc[-60:].std() / close.iloc[-60:].mean()

            # 近期波動縮小
            cond3 = volatility_20d < volatility_60d
        else:
            cond3 = pd.Series(True, index=close.columns)

        print(f"   符合條件: {cond3.sum()} 檔")

        # ========== 條件4: 成交量放大（近5天均量 > 20天均量）==========
        print("\n📊 條件4: 成交量放大")
        if not volume.empty and len(volume) >= 20:
            avg_volume_5d = volume.iloc[-5:].mean(axis=0)
            avg_volume_20d = volume.iloc[-20:].mean(axis=0)

            # 近期量增
            cond4 = avg_volume_5d > (avg_volume_20d * 1.2)  # 放大20%以上
        else:
            cond4 = pd.Series(True, index=close.columns)

        print(f"   符合條件: {cond4.sum()} 檔")

        # ========== 條件5: 相對強度（20日漲幅 > 0）==========
        print("\n📈 條件5: 相對強度良好（20日上漲）")
        if len(close) >= 20:
            return_20d = (close.iloc[-1] / close.iloc[-20] - 1)
            cond5 = return_20d > 0
            print(f"   符合條件: {cond5.sum()} 檔")
            print(f"   平均20日報酬: {return_20d[cond5].mean():.2%}")
        else:
            cond5 = pd.Series(True, index=close.columns)
            return_20d = pd.Series(0, index=close.columns)

        # ========== 條件6: 價格合理（20 < 股價 < 300）==========
        print("\n💰 條件6: 價格合理（20 < 股價 < 300）")
        cond6 = (latest_close > 20) & (latest_close < 300)
        print(f"   符合條件: {cond6.sum()} 檔")

        # ========== 基本篩選 ==========
        print("\n🔍 應用基本篩選條件...")
        basic_filter = self.apply_basic_filters(
            data,
            min_price=20,
            max_price=300,
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

        # 計算各項指標
        if len(close) >= 60:
            # 距離60天低點的距離（越遠越好）
            min_60d = low.iloc[-60:].min(axis=0)
            distance_from_low = (latest_close - min_60d) / min_60d

            # 距離20天高點的距離（越近越好）
            max_20d = high.iloc[-20:].max(axis=0)
            distance_from_high = (latest_close - max_20d) / max_20d

            # 波動率收斂程度
            volatility_ratio = volatility_20d / volatility_60d
        else:
            distance_from_low = pd.Series(0, index=close.columns)
            distance_from_high = pd.Series(0, index=close.columns)
            volatility_ratio = pd.Series(1, index=close.columns)

        # 成交量放大倍數
        if not volume.empty and len(volume) >= 20:
            volume_ratio = avg_volume_5d / avg_volume_20d
        else:
            volume_ratio = pd.Series(1, index=close.columns)

        # 標準化各因子
        distance_low_z = self.standardize(distance_from_low.to_frame().T).iloc[0]
        distance_high_z = -abs(self.standardize(distance_from_high.to_frame().T).iloc[0])  # 越接近0越好
        volatility_z = -self.standardize(volatility_ratio.to_frame().T).iloc[0]  # 越小越好
        volume_z = self.standardize(volume_ratio.to_frame().T).iloc[0]
        return_z = self.standardize(return_20d.to_frame().T).iloc[0]

        # 綜合評分
        scores = pd.Series(0.0, index=close.columns)
        scores = (
            0.25 * distance_low_z.fillna(0) +    # 遠離低點
            0.20 * distance_high_z.fillna(0) +   # 接近高點
            0.20 * volatility_z.fillna(0) +      # 波動收斂
            0.20 * volume_z.fillna(0) +          # 量能放大
            0.15 * return_z.fillna(0)            # 相對強度
        )

        # 只保留選中的股票
        scores = scores[selected_stocks]

        # ========== 格式化結果 ==========
        result = self.format_result(
            selections=selected_stocks,
            scores=scores,
            metadata={
                'strategy': 'breakout_after_base',
                'base_period': 60,
                'breakout_period': 20
            }
        )

        # 添加詳細資訊
        result['price'] = result['stock_id'].map(latest_close)
        result['return_20d'] = result['stock_id'].map(return_20d)
        result['volume_ratio'] = result['stock_id'].map(volume_ratio)
        result['distance_from_low'] = result['stock_id'].map(distance_from_low)

        print("\n✅ 選股完成!")
        print(f"\n前10名股票:")
        display_cols = ['stock_id', 'score', 'price', 'return_20d', 'volume_ratio', 'distance_from_low']
        print(result.head(10)[display_cols].to_string(index=False))
        print(f"\n{'='*70}\n")

        return result


# ========== 測試代碼 ==========

def test_breakout_strategy():
    """測試突破策略"""
    print("=== 突破策略測試 ===")
    print()

    # 創建模擬數據
    dates = pd.date_range('2024-01-01', periods=100, freq='D')
    stocks = ['2330', '2454', '2317', '3008', '2412']

    # 模擬價格數據（包含底部整理和突破）
    close = pd.DataFrame(index=dates, columns=stocks)
    high = pd.DataFrame(index=dates, columns=stocks)
    low = pd.DataFrame(index=dates, columns=stocks)

    for stock in stocks:
        # 基礎價格
        base_price = np.random.uniform(80, 150)

        # 模擬底部整理（前60天）+ 突破（後40天）
        prices = []
        for i in range(100):
            if i < 60:
                # 底部整理：小幅波動
                noise = np.random.uniform(-2, 2)
                price = base_price + noise
            else:
                # 突破上漲
                growth = (i - 60) * 0.5
                noise = np.random.uniform(-1, 1)
                price = base_price + growth + noise

            prices.append(price)

        close[stock] = prices
        high[stock] = [p * 1.02 for p in prices]
        low[stock] = [p * 0.98 for p in prices]

    # 模擬成交量（突破時放大）
    volume = pd.DataFrame(index=dates, columns=stocks)
    for stock in stocks:
        base_volume = 1000000
        volumes = []
        for i in range(100):
            if i < 60:
                vol = base_volume * np.random.uniform(0.8, 1.2)
            else:
                # 突破時量增
                vol = base_volume * np.random.uniform(1.5, 2.0)
            volumes.append(vol)
        volume[stock] = volumes

    # 模擬市值
    market_cap = pd.DataFrame(
        np.random.randn(100, len(stocks)) * 1e10 + 5e10,
        index=dates,
        columns=stocks
    )

    # 組合數據
    data = {
        'close': close,
        'high': high,
        'low': low,
        'volume': volume,
        'market_cap': market_cap
    }

    # 執行策略
    strategy = BreakoutAfterBaseStrategy()
    result = strategy.screen(data)

    print("\n最終結果:")
    print(result)
    print()
    print("✅ 測試完成")


if __name__ == "__main__":
    test_breakout_strategy()

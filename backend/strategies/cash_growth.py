"""
策略6: 現金快速累積中
Strategy 6: Rapid Cash Accumulation

選股邏輯：
1. 營業現金流持續為正（造血能力強）
2. 現金及約當現金連續增加（資金累積）
3. 自由現金流良好（FCF > 0）
4. 融資活動現金流不大（不是借錢）
5. 基本面良好（ROE > 10%, 營收成長）

投資邏輯：
- 現金持續增加 = 賺錢能力強
- 不靠融資 = 本業賺錢，不是金融操作
- 現金充裕的公司：抗風險能力強、有擴張本錢、可能配息
- 適合價值投資，中長期持有

財務指標：
- 營業現金流（Operating Cash Flow）
- 投資現金流（Investing Cash Flow）
- 融資現金流（Financing Cash Flow）
- 自由現金流（FCF）= 營業現金流 - 投資現金流
"""

from typing import Dict, Optional
import pandas as pd
import numpy as np
from datetime import date
from backend.strategies.base_strategy import StrategyBase
from config.settings import settings


class CashGrowthStrategy(StrategyBase):
    """現金快速累積策略"""

    # 策略特定的數據需求
    required_data_keys = {"cash", "eps", "revenue_yoy"}

    def __init__(self):
        super().__init__(
            name="現金快速累積中",
            description="選擇營業現金流強、現金持續增加的高品質公司"
        )

    def screen(
        self,
        data: Dict[str, pd.DataFrame],
        as_of: Optional[date] = None
    ) -> pd.DataFrame:
        """
        執行現金累積選股

        Args:
            data: 包含財務數據、現金流等
            as_of: 選股基準日期

        Returns:
            選股結果DataFrame
        """
        print(f"\n{'='*70}")
        print(f"🚀 執行策略: {self.name}")
        print(f"{'='*70}\n")

        # 獲取必要數據
        close = data.get('close', pd.DataFrame())
        cash = data.get('cash', pd.DataFrame())  # 現金及約當現金
        operating_cash_flow = data.get('operating_cash_flow', pd.DataFrame())
        investing_cash_flow = data.get('investing_cash_flow', pd.DataFrame())
        financing_cash_flow = data.get('financing_cash_flow', pd.DataFrame())
        roe = data.get('roe', pd.DataFrame())
        revenue_yoy = data.get('revenue_yoy', pd.DataFrame())
        total_assets = data.get('total_assets', pd.DataFrame())

        # 檢查數據完整性
        if close.empty or cash.empty or operating_cash_flow.empty:
            print("❌ 缺少必要數據（價格、現金或現金流）")
            return pd.DataFrame(columns=['stock_id', 'score', 'rank', 'metadata'])

        print(f"📊 數據範圍:")
        print(f"   價格數據: {close.shape}")
        print(f"   現金流數據: {operating_cash_flow.shape}")
        print(f"   最新日期: {close.index[-1]}")
        print()

        # 需要至少3期數據來判斷趨勢
        if len(cash) < 3 or len(operating_cash_flow) < 3:
            print("❌ 財務數據不足3期，無法判斷趨勢")
            return pd.DataFrame(columns=['stock_id', 'score', 'rank', 'metadata'])

        # 獲取最新及歷史數據
        latest_close = close.iloc[-1]
        latest_cash = cash.iloc[-1]
        cash_t1 = cash.iloc[-2]
        cash_t2 = cash.iloc[-3]

        latest_ocf = operating_cash_flow.iloc[-1]  # 最新營業現金流
        ocf_t1 = operating_cash_flow.iloc[-2]
        ocf_t2 = operating_cash_flow.iloc[-3]

        # ========== 條件1: 營業現金流持續為正（連續3期）==========
        print("💰 條件1: 營業現金流連續3期為正")
        cond1 = (latest_ocf > 0) & (ocf_t1 > 0) & (ocf_t2 > 0)
        print(f"   符合條件: {cond1.sum()} 檔")

        # ========== 條件2: 現金連續增加（連續2期）==========
        print("\n📈 條件2: 現金及約當現金連續2期增加")
        cash_increase_1 = latest_cash > cash_t1
        cash_increase_2 = cash_t1 > cash_t2
        cond2 = cash_increase_1 & cash_increase_2
        print(f"   符合條件: {cond2.sum()} 檔")

        # ========== 條件3: 自由現金流為正（FCF > 0）==========
        print("\n💵 條件3: 自由現金流 > 0（有餘裕）")
        if not investing_cash_flow.empty:
            latest_icf = investing_cash_flow.iloc[-1]
            # 自由現金流 = 營業現金流 - 投資現金流（投資為負值，所以是減去）
            fcf = latest_ocf + latest_icf  # 投資現金流通常為負
            cond3 = fcf > 0
            print(f"   符合條件: {cond3.sum()} 檔")
        else:
            print("   ⚠️  無投資現金流數據，跳過此條件")
            cond3 = pd.Series(True, index=close.columns)
            fcf = latest_ocf  # 用營業現金流代替

        # ========== 條件4: 融資現金流不過大（不是靠借錢）==========
        print("\n🏦 條件4: 融資現金流 < 營業現金流（不過度依賴融資）")
        if not financing_cash_flow.empty:
            latest_fcf_financing = financing_cash_flow.iloc[-1]
            # 融資現金流為正表示借入，應小於營業現金流
            cond4 = (latest_fcf_financing < latest_ocf) | (latest_fcf_financing < 0)
            print(f"   符合條件: {cond4.sum()} 檔")
        else:
            print("   ⚠️  無融資現金流數據，跳過此條件")
            cond4 = pd.Series(True, index=close.columns)

        # ========== 條件5: 現金增長率 > 20%（快速累積）==========
        print("\n📊 條件5: 現金年增長率 > 20%")
        if len(cash) >= 4:
            # 與去年同期比較（假設季報）
            cash_yoy = (latest_cash - cash.iloc[-5]) / cash.iloc[-5] if len(cash) >= 5 else (latest_cash - cash_t2) / cash_t2
        else:
            cash_yoy = (latest_cash - cash_t2) / cash_t2

        cond5 = cash_yoy > 0.20
        print(f"   符合條件: {cond5.sum()} 檔")

        # ========== 條件6: 營業現金流/總資產 > 5%（現金品質）==========
        print("\n💎 條件6: 營業現金流/總資產 > 5%（高品質）")
        if not total_assets.empty:
            latest_assets = total_assets.iloc[-1]
            ocf_to_assets = latest_ocf / latest_assets
            cond6 = ocf_to_assets > 0.05
            print(f"   符合條件: {cond6.sum()} 檔")
        else:
            print("   ⚠️  無總資產數據，跳過此條件")
            cond6 = pd.Series(True, index=close.columns)
            ocf_to_assets = pd.Series(0, index=close.columns)

        # ========== 條件7: ROE > 10%（基本面良好）==========
        print("\n📈 條件7: ROE > 10%")
        if not roe.empty:
            latest_roe = roe.iloc[-1]
            cond7 = latest_roe > 0.10
            print(f"   符合條件: {cond7.sum()} 檔")
        else:
            print("   ⚠️  無ROE數據，跳過此條件")
            cond7 = pd.Series(True, index=close.columns)

        # ========== 基本篩選 ==========
        print("\n🔍 應用基本篩選條件...")
        basic_filter = self.apply_basic_filters(
            data,
            min_price=15,
            min_market_cap=settings.min_market_cap,
            liquidity_percentile=settings.min_liquidity_percentile,
            exclude_attention=True,
            exclude_cash_delivery=True
        )
        print(f"   基本篩選後: {basic_filter.sum()} 檔")

        # ========== 綜合條件 ==========
        print("\n🎯 整合所有條件...")
        final_condition = cond1 & cond2 & cond3 & cond4 & cond5 & cond6 & cond7 & basic_filter

        selected_stocks = final_condition[final_condition].index.tolist()
        print(f"   最終選出: {len(selected_stocks)} 檔股票")

        if not selected_stocks:
            print("\n⚠️  無符合條件的股票")
            return pd.DataFrame(columns=['stock_id', 'score', 'rank', 'metadata'])

        # ========== 計算綜合評分 ==========
        print("\n📊 計算綜合評分...")

        # 標準化各因子
        ocf_z = self.standardize(latest_ocf.to_frame().T).iloc[0]
        cash_yoy_z = self.standardize(cash_yoy.to_frame().T).iloc[0]
        fcf_z = self.standardize(fcf.to_frame().T).iloc[0]
        ocf_to_assets_z = self.standardize(ocf_to_assets.to_frame().T).iloc[0] if not total_assets.empty else pd.Series(0, index=close.columns)
        roe_z = self.standardize(latest_roe.to_frame().T).iloc[0] if not roe.empty else pd.Series(0, index=close.columns)

        # 綜合評分
        scores = pd.Series(0.0, index=close.columns)
        scores = (
            0.30 * ocf_z.fillna(0) +               # 營業現金流
            0.25 * cash_yoy_z.fillna(0) +          # 現金增長率
            0.20 * fcf_z.fillna(0) +               # 自由現金流
            0.15 * ocf_to_assets_z.fillna(0) +     # 現金流品質
            0.10 * roe_z.fillna(0)                 # ROE
        )

        # 只保留選中的股票
        scores = scores[selected_stocks]

        # ========== 格式化結果 ==========
        result = self.format_result(
            selections=selected_stocks,
            scores=scores,
            metadata={
                'strategy': 'cash_growth',
                'min_cash_growth': 0.20,
                'min_ocf_to_assets': 0.05
            }
        )

        # 添加詳細資訊
        result['price'] = result['stock_id'].map(latest_close)
        result['cash_yoy'] = result['stock_id'].map(cash_yoy)
        result['ocf_億'] = result['stock_id'].map(latest_ocf) / 1e5  # 仟元 -> 億元
        result['fcf_億'] = result['stock_id'].map(fcf) / 1e5
        result['ocf_to_assets'] = result['stock_id'].map(ocf_to_assets)
        result['roe'] = result['stock_id'].map(latest_roe) if not roe.empty else None

        print("\n✅ 選股完成!")
        print(f"\n前10名股票:")
        display_cols = ['stock_id', 'score', 'price', 'cash_yoy', 'ocf_億', 'fcf_億', 'roe']
        if 'roe' in result.columns and result['roe'].notna().any():
            print(result.head(10)[display_cols].to_string(index=False))
        else:
            print(result.head(10)[['stock_id', 'score', 'price', 'cash_yoy', 'ocf_億', 'fcf_億']].to_string(index=False))

        print(f"\n💡 這些公司具有強大的現金創造能力，適合長期投資")
        print(f"{'='*70}\n")

        return result


# ========== 測試代碼 ==========

def test_cash_growth_strategy():
    """測試現金累積策略"""
    print("=== 現金快速累積策略測試 ===")
    print()

    # 創建模擬數據
    fin_dates = pd.date_range('2023-01-01', periods=4, freq='QS')
    price_dates = pd.date_range('2023-01-01', periods=252, freq='D')
    stocks = ['2330', '2454', '3008', '2317', '2412']

    # 模擬現金數據（仟元）- 持續增加
    cash = pd.DataFrame(index=fin_dates, columns=stocks)
    for stock in stocks:
        base_cash = np.random.uniform(1e6, 5e6)
        # 模擬現金增長
        cash[stock] = [base_cash * (1 + i * 0.15) for i in range(4)]

    # 2330 現金增長更快
    cash['2330'] = [3e6, 3.6e6, 4.3e6, 5.2e6]

    # 模擬營業現金流（仟元）- 持續為正
    operating_cash_flow = pd.DataFrame(
        np.random.uniform(200000, 800000, (4, len(stocks))),
        index=fin_dates,
        columns=stocks
    )
    operating_cash_flow['2330'] = [500000, 550000, 600000, 650000]

    # 模擬投資現金流（通常為負）
    investing_cash_flow = pd.DataFrame(
        -np.random.uniform(100000, 400000, (4, len(stocks))),
        index=fin_dates,
        columns=stocks
    )

    # 模擬融資現金流
    financing_cash_flow = pd.DataFrame(
        np.random.uniform(-200000, 100000, (4, len(stocks))),
        index=fin_dates,
        columns=stocks
    )

    # 模擬總資產
    total_assets = pd.DataFrame(
        np.random.uniform(5e6, 20e6, (4, len(stocks))),
        index=fin_dates,
        columns=stocks
    )

    # 模擬ROE
    roe = pd.DataFrame(
        np.random.uniform(0.08, 0.20, (4, len(stocks))),
        index=fin_dates,
        columns=stocks
    )
    roe['2330'] = 0.18

    # 模擬價格
    close = pd.DataFrame(
        np.random.randn(252, len(stocks)) * 10 + 120,
        index=price_dates,
        columns=stocks
    )

    # 模擬市值
    market_cap = pd.DataFrame(
        np.random.randn(252, len(stocks)) * 1e10 + 5e10,
        index=price_dates,
        columns=stocks
    )

    # 組合數據
    data = {
        'close': close,
        'cash': cash,
        'operating_cash_flow': operating_cash_flow,
        'investing_cash_flow': investing_cash_flow,
        'financing_cash_flow': financing_cash_flow,
        'total_assets': total_assets,
        'roe': roe,
        'market_cap': market_cap,
        'volume': close * 100000
    }

    # 執行策略
    strategy = CashGrowthStrategy()
    result = strategy.screen(data)

    print("\n最終結果:")
    print(result)
    print()
    print("✅ 測試完成")


if __name__ == "__main__":
    test_cash_growth_strategy()

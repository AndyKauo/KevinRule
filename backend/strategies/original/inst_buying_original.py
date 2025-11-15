"""
策略 4: 連兩日大戶大買超（Kevin 原始版）

Excel 原始需求：
- 近兩日關鍵券商合計買超占成交量 > 10%
- 連續兩季每股稅後淨利（元）成長
- 收盤價 < 70元

參考來源: reference/股市分析簡表_src_kevin.xlsx
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional
from datetime import date
from backend.strategies.base_strategy import StrategyBase


class InstBuyingOriginalStrategy(StrategyBase):
    """策略 4: 連兩日大戶大買超（Kevin 原始版）"""

    # 策略特定的數據需求
    required_data_keys = {"eps", "margin_buy", "margin_sell"}

    def __init__(self):
        self.strategy_id = 'inst_buying_original'
        self.strategy_name = '策略 4: 連兩日大戶大買超（原始版）'
        description = '券商買超>10%，連續兩季EPS成長，價格<70元'
        super().__init__(name=self.strategy_name, description=description)

    def screen(self, data: Dict[str, pd.DataFrame], as_of: Optional[date] = None, debug: bool = False) -> pd.DataFrame:
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
        volume = data.get('volume', pd.DataFrame())

        if close.empty:
            print("❌ 缺少收盤價數據")
            return pd.DataFrame()

        print(f"✅ 數據載入完成")

        # ==================== 券商買超判斷（使用間接指標）====================

        # TODO: FinLab 沒有券商買超數據
        # 使用間接指標替代：
        # 1. 連續2日價格上漲
        # 2. 連續2日成交量放大
        # 3. 連續2日融資減少（代表主力不是融資買進）

        print("\n⚠️  [數據缺失] 券商買超數據")
        print("   FinLab API 沒有券商買超數據")
        print("   使用間接指標替代:")
        print("   1. 連續2日價格上漲")
        print("   2. 連續2日成交量>20日均×1.5倍")
        print("   3. 連續2日融資減少\n")

        # 計算價格變化
        price_change = close.pct_change(fill_method=None)
        # 連續2日上漲
        price_up_2d = (price_change > 0) & (price_change.shift(1) > 0)

        # 成交量相對20日均量
        volume_ma20 = volume.rolling(20).mean()
        volume_ratio = volume / volume_ma20
        # 連續2日成交量放大
        volume_surge_2d = (volume_ratio > 1.5) & (volume_ratio.shift(1) > 1.5)

        # 融資變化
        margin_balance = data.get('margin_balance', pd.DataFrame())
        if not margin_balance.empty:
            margin_change = margin_balance.diff()
            # 連續2日融資減少
            margin_decrease_2d = (margin_change < 0) & (margin_change.shift(1) < 0)
        else:
            print("⚠️  缺少融資數據，跳過融資條件")
            margin_decrease_2d = pd.Series(True, index=close.index)

        # 綜合買超訊號
        buying_signal = price_up_2d & volume_surge_2d & margin_decrease_2d

        # ==================== EPS 成長判斷 ====================

        eps = data.get('eps', pd.DataFrame())
        if not eps.empty:
            # 連續兩季成長：Q(n) > Q(n-1) AND Q(n-1) > Q(n-2)
            eps_growth = (eps > eps.shift(1)) & (eps.shift(1) > eps.shift(2))
            eps_growth_filter = eps_growth.iloc[-1]
            print(f"✅ EPS 成長判斷完成")
            print(f"   連續兩季成長: {eps_growth_filter.sum()} 檔\n")
        else:
            print("⚠️  缺少 EPS 數據，跳過此條件\n")
            eps_growth_filter = pd.Series(True, index=close.iloc[-1].index)

        # ==================== 價格篩選 ====================

        price_filter = close.iloc[-1] < 70

        # ==================== 綜合篩選 ====================

        final_condition = (
            buying_signal.iloc[-1] &
            eps_growth_filter &
            price_filter &
            self.apply_basic_filters(data)
        )

        print(f"\n🔍 篩選條件統計:")
        print(f"   - 連續2日買超訊號: {buying_signal.iloc[-1].sum()} 檔")
        print(f"   - 連續兩季EPS成長: {eps_growth_filter.sum()} 檔")
        print(f"   - 價格<70元: {price_filter.sum()} 檔")
        print(f"   - 最終符合: {final_condition.sum()} 檔")

        # DEBUG: 詳細調查每個條件過濾後的股票（需要 debug=True 才顯示）
        if debug:
            print(f"\n🔬 DEBUG [詳細調查]:")
            cond1 = buying_signal.iloc[-1]
            cond2 = eps_growth_filter
            cond3 = price_filter
            cond4 = self.apply_basic_filters(data)

            print(f"   cond1 (買超) index 長度: {len(cond1.index)}, 符合: {cond1.sum()} 檔")
            if cond1.sum() > 0:
                print(f"   cond1 符合股票（前10檔）: {cond1[cond1].index[:10].tolist()}")

            print(f"   cond2 (EPS成長) index 長度: {len(cond2.index)}, 符合: {cond2.sum()} 檔")
            if cond2.sum() > 0:
                print(f"   cond2 符合股票（前10檔）: {cond2[cond2].index[:10].tolist()}")

            print(f"   cond3 (價格<70) index 長度: {len(cond3.index)}, 符合: {cond3.sum()} 檔")

            # 逐步組合
            partial1 = cond1 & cond2
            print(f"\n   📍 cond1 & cond2 後: {partial1.sum()} 檔")
            if partial1.sum() > 0:
                print(f"   剩餘股票: {partial1[partial1].index[:10].tolist()}")
            else:
                print(f"   ⚠️  交集為空！檢查 cond1 和 cond2 是否有共同股票...")
                if cond1.sum() > 0 and cond2.sum() > 0:
                    common = set(cond1[cond1].index) & set(cond2[cond2].index)
                    print(f"   cond1 與 cond2 的共同股票: {common}")

            partial2 = partial1 & cond3
            print(f"\n   📍 partial1 & cond3 後: {partial2.sum()} 檔")
            if partial2.sum() > 0:
                print(f"   剩餘股票: {partial2[partial2].index[:10].tolist()}")

            partial3 = partial2 & cond4
            print(f"\n   📍 partial2 & cond4 (基本篩選) 後: {partial3.sum()} 檔")
            if partial3.sum() > 0:
                print(f"   最終股票: {partial3[partial3].index[:10].tolist()}")

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

        # 買超強度（成交量放大程度）
        buying_strength = volume_ratio.iloc[-1][final_condition]

        # 價格動能
        price_momentum = price_change.iloc[-1][final_condition]

        # 標準化
        buying_z = standardize(buying_strength)
        momentum_z = standardize(price_momentum)

        # 綜合評分
        scores = 0.6 * buying_z + 0.4 * momentum_z

        # 構建結果
        result = pd.DataFrame({
            'score': scores,
            'price': close.iloc[-1][final_condition],
            'volume_ratio': buying_strength,
            'price_change': price_momentum
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

    print("=== 測試策略 4: 連兩日大戶大買超（原始版）===\n")

    client = FinLabClient()

    print("📊 正在獲取數據...")
    data = {
        'close': client.get_close(),
        'volume': client.get_volume(),
        'margin_balance': client.get_margin_data()['margin_balance'],
    }

    strategy = InstBuyingOriginalStrategy()
    result = strategy.screen(data)

    if not result.empty:
        print("\n前 10 名推薦:")
        print(result.head(10))
    else:
        print("\n沒有符合條件的股票")


if __name__ == "__main__":
    test_strategy()

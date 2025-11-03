"""
策略 6: 現金快速累積中（Kevin 原始版）

Excel 原始需求：
- 連續四季現金及約當現金增加 > 5%
- 月營收月增率 > 20%
- 連續兩季每股稅後淨利（元）成長

參考來源: reference/股市分析簡表_src_kevin.xlsx
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional
from datetime import date
from backend.strategies.base_strategy import StrategyBase


class CashGrowthOriginalStrategy(StrategyBase):
    """策略 6: 現金快速累積中（Kevin 原始版）"""

    def __init__(self):
        self.strategy_id = 'cash_growth_original'
        self.strategy_name = '策略 6: 現金快速累積中（原始版）'
        description = (
            '連續4季現金增>5% (QoQ環比)，MoM>20%，連續2季EPS成長。'
            'QoQ環比判斷可反映連續成長趨勢，符合「連續四季」語義。'
        )
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
        cash = data.get('cash', pd.DataFrame())
        revenue = data.get('revenue', pd.DataFrame())

        if close.empty or cash.empty or revenue.empty:
            print("❌ 缺少必要數據")
            return pd.DataFrame()

        print(f"✅ 數據載入完成")

        # ==================== 現金累積判斷 ====================

        print("\n✅ [邏輯確認] 連續四季現金增加")
        print("   實作邏輯:")
        print("   1. 財務報表: 季度數據（每季一筆）")
        print("   2. 判斷方式: QoQ (環比) - 相比上一季")
        print("   3. 原因: Excel原文「連續四季」強調連續性，QoQ才能判斷連續趨勢")
        print("   4. 計算: Q(n) vs Q(n-1), Q(n-1) vs Q(n-2), ...\n")

        # 現金成長率（QoQ - Quarter-over-Quarter 環比）
        # 相比上一季的成長率，可反映連續成長趨勢
        cash_growth = cash.pct_change(fill_method=None)

        # 連續 4 季現金增加 > 5%
        # 檢查最近 4 季是否每一季相較前一季都增加 > 5%
        cash_growth_4q = (
            (cash_growth > 0.05) &           # Q(n) vs Q(n-1) > 5%
            (cash_growth.shift(1) > 0.05) &  # Q(n-1) vs Q(n-2) > 5%
            (cash_growth.shift(2) > 0.05) &  # Q(n-2) vs Q(n-3) > 5%
            (cash_growth.shift(3) > 0.05)    # Q(n-3) vs Q(n-4) > 5%
        )

        # ==================== 營收月增率判斷 ====================

        # 月營收月增率
        revenue_mom = revenue.pct_change(fill_method=None)
        # MoM > 20%
        mom_filter = revenue_mom > 0.20

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

        # ==================== 基本面篩選 ====================

        # OCF > 0（確保現金流品質）
        operating_cash_flow = data.get('operating_cash_flow', pd.DataFrame())
        if not operating_cash_flow.empty:
            ocf_filter = operating_cash_flow > 0
        else:
            ocf_filter = pd.Series(True, index=close.index)

        # ROE > 10%
        roe = data.get('roe', pd.DataFrame())
        if not roe.empty:
            roe_filter = roe > 10
        else:
            roe_filter = pd.Series(True, index=close.index)

        # ==================== 綜合篩選 ====================

        final_condition = (
            cash_growth_4q.iloc[-1] &
            mom_filter.iloc[-1] &
            eps_growth_filter &
            ocf_filter.iloc[-1] &
            roe_filter.iloc[-1] &
            self.apply_basic_filters(data)
        )

        print(f"\n🔍 篩選條件統計:")
        print(f"   - 連續4期現金增>5%: {cash_growth_4q.iloc[-1].sum()} 檔")
        print(f"   - 月營收MoM>20%: {mom_filter.iloc[-1].sum()} 檔")
        print(f"   - 連續兩季EPS成長: {eps_growth_filter.sum()} 檔")
        print(f"   - OCF>0: {ocf_filter.iloc[-1].sum()} 檔")
        print(f"   - ROE>10%: {roe_filter.iloc[-1].sum()} 檔")
        print(f"   - 最終符合: {final_condition.sum()} 檔")

        # DEBUG: 詳細調查每個條件過濾後的股票（需要 debug=True 才顯示）
        if debug:
            print(f"\n🔬 DEBUG [詳細調查]:")
            cond1 = cash_growth_4q.iloc[-1]
            cond2 = mom_filter.iloc[-1]
            cond3 = eps_growth_filter
            cond4 = ocf_filter.iloc[-1]
            cond5 = roe_filter.iloc[-1]
            cond6 = self.apply_basic_filters(data)

            print(f"   cond1 (現金增長) index 長度: {len(cond1.index)}, 符合: {cond1.sum()} 檔")
            if cond1.sum() > 0:
                print(f"   cond1 符合股票: {cond1[cond1].index.tolist()}")

            print(f"   cond2 (營收MoM) index 長度: {len(cond2.index)}, 符合: {cond2.sum()} 檔")
            if cond2.sum() > 0:
                print(f"   cond2 符合股票（前10檔）: {cond2[cond2].index[:10].tolist()}")

            print(f"   cond3 (EPS成長) index 長度: {len(cond3.index)}, 符合: {cond3.sum()} 檔")
            if cond3.sum() > 0:
                print(f"   cond3 符合股票（前10檔）: {cond3[cond3].index[:10].tolist()}")

            print(f"   cond4 (OCF>0) index 長度: {len(cond4.index)}, 符合: {cond4.sum()} 檔")
            print(f"   cond5 (ROE>10) index 長度: {len(cond5.index)}, 符合: {cond5.sum()} 檔")
            if cond5.sum() > 0:
                print(f"   cond5 符合股票: {cond5[cond5].index.tolist()}")

            # 逐步組合
            partial1 = cond1 & cond2
            print(f"\n   📍 cond1 (現金) & cond2 (營收) 後: {partial1.sum()} 檔")
            if partial1.sum() > 0:
                print(f"   剩餘股票: {partial1[partial1].index.tolist()}")
            else:
                print(f"   ⚠️  交集為空！")
                if cond1.sum() > 0 and cond2.sum() > 0:
                    common = set(cond1[cond1].index) & set(cond2[cond2].index)
                    print(f"   cond1 與 cond2 的共同股票: {common if common else '無'}")

            partial2 = partial1 & cond3
            print(f"\n   📍 partial1 & cond3 (EPS) 後: {partial2.sum()} 檔")
            if partial2.sum() > 0:
                print(f"   剩餘股票: {partial2[partial2].index.tolist()}")

            partial3 = partial2 & cond4
            print(f"\n   📍 partial2 & cond4 (OCF) 後: {partial3.sum()} 檔")
            if partial3.sum() > 0:
                print(f"   剩餘股票: {partial3[partial3].index.tolist()}")

            partial4 = partial3 & cond5
            print(f"\n   📍 partial3 & cond5 (ROE) 後: {partial4.sum()} 檔")
            if partial4.sum() > 0:
                print(f"   剩餘股票: {partial4[partial4].index.tolist()}")
            else:
                print(f"   ⚠️  在 ROE 條件被過濾掉！")
                if partial3.sum() > 0 and cond5.sum() > 0:
                    common = set(partial3[partial3].index) & set(cond5[cond5].index)
                    print(f"   partial3 與 cond5 的共同股票: {common if common else '無'}")

            partial5 = partial4 & cond6
            print(f"\n   📍 partial4 & cond6 (基本篩選) 後: {partial5.sum()} 檔")
            if partial5.sum() > 0:
                print(f"   最終股票: {partial5[partial5].index.tolist()}")

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

        # 現金增長強度（4期平均）
        cash_growth_avg = cash_growth.rolling(4).mean().iloc[-1][final_condition]

        # 營收月增率
        mom_selected = revenue_mom.iloc[-1][final_condition]

        # OCF 強度
        if not operating_cash_flow.empty:
            ocf_strength = operating_cash_flow.iloc[-1][final_condition]
            ocf_z = standardize(ocf_strength)
        else:
            ocf_z = pd.Series(0, index=selected_stocks)

        # 標準化
        cash_z = standardize(cash_growth_avg)
        mom_z = standardize(mom_selected)

        # 綜合評分
        scores = 0.4 * cash_z + 0.3 * mom_z + 0.3 * ocf_z

        # 構建結果
        result = pd.DataFrame({
            'score': scores,
            'price': close.iloc[-1][final_condition],
            'cash_growth_4q_avg': cash_growth_avg,
            'revenue_mom': mom_selected
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

    print("=== 測試策略 6: 現金快速累積中（原始版）===\n")

    client = FinLabClient()

    print("📊 正在獲取數據...")
    data = {
        'close': client.get_close(),
        'cash': client.get_financial_data()['cash'],
        'revenue': client.get_monthly_revenue()['revenue'],
        'operating_cash_flow': client.get_financial_data()['operating_cash_flow'],
        'roe': client.get_fundamental_ratios()['roe'],
    }

    strategy = CashGrowthOriginalStrategy()
    result = strategy.screen(data)

    if not result.empty:
        print("\n前 10 名推薦:")
        print(result.head(10))
    else:
        print("\n沒有符合條件的股票")


if __name__ == "__main__":
    test_strategy()

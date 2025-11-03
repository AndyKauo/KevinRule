"""
策略 1: 營收動能高於同業平均（Kevin 原始版）

Excel 原始需求：
- 近三月月營收年增率合計高於同行業組平均
- 月營收年增率 > 20%
- 月營收月增率 > 20%
- 連續兩季每股稅後淨利（元）皆成長
- 收盤價 < 100元

參考來源: reference/股市分析簡表_src_kevin.xlsx
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional
from datetime import date
from backend.strategies.base_strategy import StrategyBase


class RevenueMomentumOriginalStrategy(StrategyBase):
    """策略 1: 營收動能高於同業平均（Kevin 原始版）"""

    def __init__(self):
        self.strategy_id = 'revenue_momentum_original'
        self.strategy_name = '策略 1: 營收動能高於同業平均（原始版）'
        description = '近三月 YoY 高於產業平均，YoY>20%，MoM>20%，連續兩季 EPS 成長，價格<100'
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

        # 價格數據
        close = data.get('close', pd.DataFrame())
        if close.empty:
            print("❌ 缺少收盤價數據")
            return pd.DataFrame()

        # 月營收數據
        revenue = data.get('revenue', pd.DataFrame())
        if revenue.empty:
            print("❌ 缺少月營收數據")
            return pd.DataFrame()

        print(f"✅ 數據載入完成")
        print(f"   - 收盤價形狀: {close.shape}")
        print(f"   - 月營收形狀: {revenue.shape}")

        # ==================== 計算營收指標 ====================

        # 1. 月營收年增率 (YoY)
        revenue_yoy = revenue.pct_change(12, fill_method=None)

        # 2. 月營收月增率 (MoM)
        revenue_mom = revenue.pct_change(1, fill_method=None)

        # 3. 近三月 YoY 平均
        revenue_yoy_3m_avg = revenue_yoy.rolling(3).mean()

        print(f"\n📊 營收指標計算完成")

        # ==================== 產業平均計算 ====================

        # 取得產業分類數據
        industry = data.get('industry', pd.Series())

        if not industry.empty:
            # 計算近三月 YoY 平均的產業平均
            # 使用 groupby 計算每個產業的平均值
            industry_avg_yoy_3m = revenue_yoy_3m_avg.iloc[-1].groupby(industry).mean()

            # 為每支股票映射其產業平均
            # 對齊 index：只使用 revenue_yoy_3m_avg 和 industry 共同的股票
            common_stocks = revenue_yoy_3m_avg.columns.intersection(industry.index)

            # 創建每支股票的產業平均 Series
            stock_industry_avg = pd.Series(
                index=common_stocks,
                data=[industry_avg_yoy_3m.get(industry.get(stock, None), np.nan) for stock in common_stocks]
            )

            # 判斷是否高於產業平均
            above_industry_avg = revenue_yoy_3m_avg.iloc[-1][common_stocks] > stock_industry_avg

            print(f"\n✅ 產業平均計算完成")
            print(f"   - 產業數量: {len(industry_avg_yoy_3m)}")
            print(f"   - 高於產業平均: {above_industry_avg.sum()} 檔")
            print(f"   - 低於產業平均: {(~above_industry_avg & above_industry_avg.notna()).sum()} 檔")

        else:
            print("\n⚠️  [數據缺失] 產業分類數據，跳過產業平均比較")
            above_industry_avg = pd.Series(True, index=revenue_yoy_3m_avg.columns)

        # ==================== EPS 成長判斷 ====================

        eps = data.get('eps', pd.DataFrame())
        if not eps.empty:
            # 連續兩季成長：Q(n) > Q(n-1) AND Q(n-1) > Q(n-2)
            eps_growth = (eps > eps.shift(1)) & (eps.shift(1) > eps.shift(2))
            eps_growth_filter = eps_growth.iloc[-1]
            print(f"✅ EPS 成長判斷完成")
            print(f"   連續兩季成長: {eps_growth_filter.sum()} 檔")
        else:
            print("⚠️  缺少 EPS 數據，跳過此條件")
            eps_growth_filter = pd.Series(True, index=latest_close.index)

        # ==================== 篩選條件 ====================

        # 獲取最新數據
        latest_close = close.iloc[-1]
        latest_yoy = revenue_yoy.iloc[-1]
        latest_mom = revenue_mom.iloc[-1]

        # 條件 1: 月營收 YoY > 20%
        cond1 = latest_yoy > 0.20

        # 條件 2: 月營收 MoM > 20%
        cond2 = latest_mom > 0.20

        # 條件 3: 收盤價 < 100元
        cond3 = latest_close < 100

        # 條件 4: 近三月 YoY 高於產業平均
        # 需要對齊所有條件的 index
        cond4 = above_industry_avg.reindex(latest_close.index, fill_value=False)

        # 基本篩選條件
        cond_basic = self.apply_basic_filters(data)

        # 綜合條件
        final_condition = cond1 & cond2 & cond3 & cond4 & eps_growth_filter & cond_basic

        print(f"\n🔍 篩選條件統計:")
        print(f"   - YoY > 20%: {cond1.sum()} 檔")
        print(f"   - MoM > 20%: {cond2.sum()} 檔")
        print(f"   - 價格 < 100元: {cond3.sum()} 檔")
        print(f"   - 近三月 YoY 高於產業平均: {cond4.sum()} 檔")
        print(f"   - 連續兩季 EPS 成長: {eps_growth_filter.sum()} 檔")
        print(f"   - 基本篩選通過: {cond_basic.sum()} 檔")
        print(f"   - 最終符合: {final_condition.sum()} 檔")

        # 獲取符合條件的股票
        selected_stocks = latest_close[final_condition].index

        if len(selected_stocks) == 0:
            print("\n❌ 沒有股票符合條件")
            return pd.DataFrame()

        # ==================== 評分（簡化版）====================

        # 標準化函數
        def standardize(series):
            mean = series.mean()
            std = series.std()
            # 處理 std 為 0 或 NaN 的情況（如只有 1 個股票）
            if pd.isna(std) or std == 0:
                # 只有1個股票時，給予固定分數 50
                return pd.Series([50.0] * len(series), index=series.index)
            return (series - mean) / std

        # 計算分數（只使用可用的指標）
        yoy_z = standardize(latest_yoy[final_condition])
        mom_z = standardize(latest_mom[final_condition])

        # Excel 原始需求沒有明確的評分公式，這裡使用簡化版本
        # 權重: YoY 60%, MoM 40%
        scores = 0.6 * yoy_z + 0.4 * mom_z

        # 構建結果
        result = pd.DataFrame({
            'score': scores,
            'revenue_yoy': latest_yoy[final_condition],
            'revenue_mom': latest_mom[final_condition],
            'price': latest_close[final_condition]
        })

        # 按分數排序
        result = result.sort_values('score', ascending=False)

        print(f"\n✅ 策略執行完成")
        print(f"   推薦股票數: {len(result)}")
        if len(result) > 0:
            print(f"   平均 YoY: {result['revenue_yoy'].mean():.2%}")
            print(f"   平均 MoM: {result['revenue_mom'].mean():.2%}")

        print(f"\n{'='*60}\n")

        return result


# ========== 測試代碼 ==========

def test_strategy():
    """測試策略"""
    from backend.data_sources.finlab_client import FinLabClient

    print("=== 測試策略 1: 營收動能高於同業平均（原始版）===\n")

    # 初始化客戶端
    client = FinLabClient()

    # 獲取數據
    print("📊 正在獲取數據...")

    # 獲取公司基本資訊
    company_info = client.get_company_info()

    data = {
        'close': client.get_close(),
        'revenue': client.get_monthly_revenue()['revenue'],
        'industry': company_info['industry'],
        'eps': client.get_financial_data()['eps'],
    }

    print("✅ 數據獲取完成\n")

    # 執行策略
    strategy = RevenueMomentumOriginalStrategy()
    result = strategy.screen(data)

    if not result.empty:
        print("\n前 10 名推薦:")
        print(result.head(10))
    else:
        print("\n沒有符合條件的股票")


if __name__ == "__main__":
    test_strategy()

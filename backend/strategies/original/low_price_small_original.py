"""
策略 2: 低價小股本營收創一年高（Kevin 原始版）

Excel 原始需求：
- 收盤價 < 20元
- 月營收創十二個月新高
- 普通股股本 < 20億

參考來源: reference/股市分析簡表_src_kevin.xlsx
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional
from datetime import date
from backend.strategies.base_strategy import StrategyBase


class LowPriceSmallOriginalStrategy(StrategyBase):
    """策略 2: 低價小股本營收創一年高（Kevin 原始版）"""

    def __init__(self):
        self.strategy_id = 'low_price_small_original'
        self.strategy_name = '策略 2: 低價小股本營收創一年高（原始版）'
        description = '收盤價<20元，月營收創12個月新高，股本<20億'
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

        # 股本數據
        common_stock = data.get('common_stock', pd.DataFrame())
        if common_stock.empty:
            print("⚠️  缺少股本數據，將跳過股本篩選")
            use_stock_filter = False
        else:
            use_stock_filter = True

        print(f"✅ 數據載入完成")
        print(f"   - 收盤價形狀: {close.shape}")
        print(f"   - 月營收形狀: {revenue.shape}")
        if use_stock_filter:
            print(f"   - 股本形狀: {common_stock.shape}")

        # ==================== 計算指標 ====================

        # 獲取最新數據
        latest_close = close.iloc[-1]
        latest_revenue = revenue.iloc[-1]

        # 12個月營收滾動最大值
        revenue_12m_max = revenue.rolling(12).max().iloc[-1]

        # 營收年增率（用於評分）
        revenue_yoy = revenue.pct_change(12, fill_method=None).iloc[-1]

        print(f"\n📊 指標計算完成")

        # ==================== 篩選條件 ====================

        # 條件 1: 收盤價 < 20元
        cond1 = latest_close < 20

        # 條件 2: 月營收創 12 個月新高
        cond2 = latest_revenue >= revenue_12m_max * 0.99  # 允許 1% 誤差

        # 條件 3: 股本 < 20億（如果有數據）
        if use_stock_filter:
            latest_stock = common_stock.iloc[-1]
            # 股本單位是仟元，20億 = 2,000,000 仟元
            cond3 = latest_stock < 2000000
        else:
            cond3 = pd.Series(True, index=latest_close.index)
            print("\n⚠️  [數據缺失] 股本篩選")
            print("   缺少 financial_statement:普通股股本 數據")
            print("   跳過股本 < 20億 的條件\n")

        # 基本篩選條件
        cond_basic = self.apply_basic_filters(data)

        # 綜合條件
        final_condition = cond1 & cond2 & cond3 & cond_basic

        print(f"\n🔍 篩選條件統計:")
        print(f"   - 價格 < 20元: {cond1.sum()} 檔")
        print(f"   - 營收創 12月新高: {cond2.sum()} 檔")
        if use_stock_filter:
            print(f"   - 股本 < 20億: {cond3.sum()} 檔")
        print(f"   - 基本篩選通過: {cond_basic.sum()} 檔")
        print(f"   - 最終符合: {final_condition.sum()} 檔")

        # 獲取符合條件的股票
        selected_stocks = latest_close[final_condition].index

        if len(selected_stocks) == 0:
            print("\n❌ 沒有股票符合條件")
            return pd.DataFrame()

        # ==================== 評分 ====================

        # 標準化函數
        def standardize(series):
            mean = series.mean()
            std = series.std()
            if std == 0:
                return series * 0
            return (series - mean) / std

        # 營收突破幅度（相對 12 月最高的比例）
        revenue_ratio = (latest_revenue[final_condition] / revenue_12m_max[final_condition])

        # 營收年增率
        yoy_selected = revenue_yoy[final_condition]

        # 小市值偏好（價格越低分數越高）
        price_preference = -latest_close[final_condition]

        # 標準化函數
        def standardize(series):
            mean = series.mean()
            std = series.std()
            # 處理 std 為 0 或 NaN 的情況（如只有 1 個股票）
            if pd.isna(std) or std == 0:
                # 只有1個股票時，給予固定分數 50
                return pd.Series([50.0] * len(series), index=series.index)
            return (series - mean) / std

        # 標準化
        revenue_ratio_z = standardize(revenue_ratio)
        yoy_z = standardize(yoy_selected)
        price_z = standardize(price_preference)

        # Excel 原始需求沒有明確的評分公式，這裡使用合理權重
        # 權重: 營收突破 40%, YoY 30%, 小市值偏好 30%
        scores = 0.4 * revenue_ratio_z + 0.3 * yoy_z + 0.3 * price_z

        # 構建結果
        result = pd.DataFrame({
            'score': scores,
            'price': latest_close[final_condition],
            'revenue_12m_high_ratio': revenue_ratio,
            'revenue_yoy': yoy_selected
        })

        # 按分數排序
        result = result.sort_values('score', ascending=False)

        print(f"\n✅ 策略執行完成")
        print(f"   推薦股票數: {len(result)}")
        if len(result) > 0:
            print(f"   平均價格: {result['price'].mean():.2f}元")
            print(f"   平均 YoY: {result['revenue_yoy'].mean():.2%}")

        print(f"\n{'='*60}\n")

        return result


# ========== 測試代碼 ==========

def test_strategy():
    """測試策略"""
    from backend.data_sources.finlab_client import FinLabClient

    print("=== 測試策略 2: 低價小股本營收創一年高（原始版）===\n")

    # 初始化客戶端
    client = FinLabClient()

    # 獲取數據
    print("📊 正在獲取數據...")
    data = {
        'close': client.get_close(),
        'revenue': client.get_monthly_revenue()['revenue'],
        'common_stock': client.get_financial_data()['common_stock'],
    }

    # 執行策略
    strategy = LowPriceSmallOriginalStrategy()
    result = strategy.screen(data)

    if not result.empty:
        print("\n前 10 名推薦:")
        print(result.head(10))
    else:
        print("\n沒有符合條件的股票")


if __name__ == "__main__":
    test_strategy()

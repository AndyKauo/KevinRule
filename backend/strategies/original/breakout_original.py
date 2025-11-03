"""
策略 3: 長時間未破底後創新高（Kevin 原始版）

Excel 原始需求：
- 長時間未破底後創新高（未破底區間=90天，盤整區間漲幅上限=25%）
- 股本 < 40億
- ROE > 25% OR 連續三年現金股利 > 2元
- 收盤價 < 20元
- 月營收創三十六個月新高
- 普通股股本 < 20億
- 成交量 > 20日均量 × 2.5倍

參考來源: reference/股市分析簡表_src_kevin.xlsx
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional
from datetime import date
from backend.strategies.base_strategy import StrategyBase


class BreakoutOriginalStrategy(StrategyBase):
    """策略 3: 長時間未破底後創新高（Kevin 原始版）"""

    def __init__(self):
        self.strategy_id = 'breakout_original'
        self.strategy_name = '策略 3: 長時間未破底後創新高（原始版）'
        description = (
            '90天未破底，盤整漲幅<25%（從90天最低到當前），'
            'ROE>25%或3年股利>2元，營收36月新高。'
            '盤整漲幅計算確保股票仍在合理區間，配合突破判斷。'
        )
        super().__init__(name=self.strategy_name, description=description)

    def _extract_year(self, period_str):
        """從'股利所屬期間'提取西元年 (例如: '111年' → 2022)"""
        if pd.isna(period_str) or period_str == '':
            return None
        try:
            # 移除'年'字並提取數字
            tw_year_str = period_str.replace('年', '').strip()
            # 處理特殊格式如 "113年第1季"
            if '第' in tw_year_str:
                tw_year_str = tw_year_str.split('第')[0]
            if '前半' in tw_year_str or '後半' in tw_year_str:
                tw_year_str = tw_year_str[:3]
            tw_year = int(tw_year_str)
            # 民國年轉西元年
            return tw_year + 1911
        except:
            return None

    def _check_consecutive_dividend(self, dividend_df: pd.DataFrame, stock_ids: pd.Index,
                                   min_dividend: float = 2.0, years: int = 3) -> pd.Series:
        """
        檢查是否連續N年現金股利 > 指定金額

        Args:
            dividend_df: dividend_announcement DataFrame
            stock_ids: 需要檢查的股票代碼列表
            min_dividend: 最低股利金額 (預設 2元)
            years: 連續年數 (預設 3年)

        Returns:
            pd.Series: 每檔股票是否符合條件 (index=stock_id, values=bool)
        """
        if dividend_df.empty:
            return pd.Series(False, index=stock_ids)

        cash_div_col = '盈餘分配之股東現金股利(元/股)'
        result = pd.Series(False, index=stock_ids)

        # 提取年度
        dividend_df = dividend_df.copy()
        dividend_df['year'] = dividend_df['股利所屬期間'].apply(self._extract_year)
        dividend_df = dividend_df[dividend_df['year'].notna()]

        if dividend_df.empty:
            return result

        # 按 stock_id 和 year 分組 (處理一年多次配息)
        dividend_by_year = dividend_df.groupby(['stock_id', 'year'], observed=False)[cash_div_col].sum().reset_index()

        # 對每檔股票判斷
        for stock_id in stock_ids:
            stock_div = dividend_by_year[dividend_by_year['stock_id'] == stock_id]
            if len(stock_div) < years:
                continue

            # 排序並取最近N年
            stock_div = stock_div.sort_values('year')
            recent_years = stock_div.iloc[-years:]

            # 判斷是否都 > min_dividend
            if (recent_years[cash_div_col] > min_dividend).all():
                result[stock_id] = True

        return result

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

        close = data.get('close', pd.DataFrame())
        high = data.get('high', pd.DataFrame())
        low = data.get('low', pd.DataFrame())
        volume = data.get('volume', pd.DataFrame())
        revenue = data.get('revenue', pd.DataFrame())

        if close.empty or high.empty or low.empty:
            print("❌ 缺少價格數據")
            return pd.DataFrame()

        print(f"✅ 數據載入完成")
        print(f"   - 收盤價形狀: {close.shape}")
        print(f"   - 成交量形狀: {volume.shape}")

        # ==================== 技術指標計算 ====================

        # 1. 90天最低價（判斷是否在前40天）
        low_90d = low.rolling(90).min()
        low_40d = low.rolling(40).min()
        # 90天最低價出現在前40天（即後50天未破底）
        base_formation = (low_90d.iloc[-1] == low_40d.iloc[-50])

        # 2. 創20天新高
        high_20d = high.rolling(20).max()
        new_high = (high.iloc[-1] >= high_20d.iloc[-1] * 0.99)

        # 3. 盤整區間漲幅 < 25%
        # 實作邏輯: 從90天最低價到當前價格的漲幅 < 25%
        # 原因: Excel原文「盤整區間漲幅上限=25%」→ 限制當前價格相對底部的漲幅
        # 目的: 確保股票仍在合理盤整區間，配合未破底和創新高判斷
        price_range = (close.iloc[-1] - low_90d.iloc[-1]) / low_90d.iloc[-1]
        consolidation_limit = (price_range < 0.25)

        print("\n✅ [邏輯確認] 盤整區間漲幅")
        print("   實作邏輯:")
        print("   1. 計算方式: 從90天最低到當前的漲幅")
        print("   2. 原因: 判斷當前是否仍在盤整，未大幅上漲")
        print("   3. 策略邏輯: 90天未破底 + 從底部漲幅<25% + 創新高 → 盤整後突破")
        print("   4. 公式: (當前價 - 90天最低) / 90天最低 < 25%\n")

        # 4. 成交量 > 20日均量 × 2.5倍
        volume_ma20 = volume.rolling(20).mean()
        volume_surge = (volume.iloc[-1] > volume_ma20.iloc[-1] * 2.5)

        # 5. 營收創36個月新高
        if not revenue.empty:
            revenue_36m_max = revenue.rolling(36).max()
            revenue_new_high = (revenue.iloc[-1] >= revenue_36m_max.iloc[-1] * 0.99)
        else:
            print("⚠️  缺少營收數據，跳過營收條件")
            revenue_new_high = pd.Series(True, index=close.iloc[-1].index)

        print(f"📊 技術指標計算完成")

        # ==================== 基本面篩選 ====================

        # 價格 < 20元
        price_filter = close.iloc[-1] < 20

        # 股本 < 20億
        common_stock = data.get('common_stock', pd.DataFrame())
        if not common_stock.empty:
            stock_filter = common_stock.iloc[-1] < 2000000  # 仟元
        else:
            print("\n⚠️  缺少股本數據，跳過股本篩選")
            stock_filter = pd.Series(True, index=close.iloc[-1].index)

        # ROE > 25% OR 連續三年現金股利 > 2元
        roe = data.get('roe', pd.DataFrame())
        if not roe.empty:
            roe_filter = roe.iloc[-1] > 25
            print(f"   ✅ ROE > 25%: {roe_filter.sum()} 檔")
        else:
            print("   ⚠️  缺少 ROE 數據")
            roe_filter = pd.Series(False, index=close.iloc[-1].index)

        # 連續三年現金股利 > 2元
        dividend_announcement = data.get('dividend_announcement', pd.DataFrame())
        if not dividend_announcement.empty:
            dividend_filter = self._check_consecutive_dividend(
                dividend_announcement,
                close.iloc[-1].index,
                min_dividend=2.0,
                years=3
            )
            print(f"   ✅ 連續3年股利>2元: {dividend_filter.sum()} 檔")
        else:
            print("   ⚠️  缺少股利數據")
            dividend_filter = pd.Series(False, index=close.iloc[-1].index)

        # ROE OR 連續三年股利（至少滿足其一）
        fundamental_filter = roe_filter | dividend_filter
        print(f"   ✅ 基本面符合 (ROE或股利): {fundamental_filter.sum()} 檔")

        # ==================== 綜合篩選 ====================

        final_condition = (
            base_formation &
            new_high &
            consolidation_limit &
            volume_surge &
            revenue_new_high &
            price_filter &
            stock_filter &
            fundamental_filter &
            self.apply_basic_filters(data)
        )

        print(f"\n🔍 篩選條件統計:")
        print(f"   - 90天底部形成: {base_formation.sum()} 檔")
        print(f"   - 創20天新高: {new_high.sum()} 檔")
        print(f"   - 盤整漲幅<25%: {consolidation_limit.sum()} 檔")
        print(f"   - 成交量>2.5倍: {volume_surge.sum()} 檔")
        print(f"   - 營收36月新高: {revenue_new_high.sum()} 檔")
        print(f"   - 價格<20元: {price_filter.sum()} 檔")
        print(f"   - 股本<20億: {stock_filter.sum()} 檔")
        print(f"   - ROE>25%: {roe_filter.sum()} 檔")
        print(f"   - 連續3年股利>2元: {dividend_filter.sum()} 檔")
        print(f"   - 基本面符合 (ROE或股利): {fundamental_filter.sum()} 檔")
        print(f"   - 最終符合: {final_condition.sum()} 檔")

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

        # 突破強度（創新高幅度）
        breakout_strength = (high.iloc[-1][final_condition] - high_20d.iloc[-1][final_condition]) / high_20d.iloc[-1][final_condition]

        # 成交量放大程度
        volume_strength = (volume.iloc[-1][final_condition] / volume_ma20.iloc[-1][final_condition])

        # 營收成長
        if not revenue.empty:
            revenue_growth = revenue.pct_change(12).iloc[-1][final_condition]
            revenue_z = standardize(revenue_growth)
        else:
            revenue_z = pd.Series(0, index=selected_stocks)

        # 標準化
        breakout_z = standardize(breakout_strength)
        volume_z = standardize(volume_strength)

        # 綜合評分
        scores = 0.4 * breakout_z + 0.3 * volume_z + 0.3 * revenue_z

        # 構建結果
        result = pd.DataFrame({
            'score': scores,
            'price': close.iloc[-1][final_condition],
            'breakout_strength': breakout_strength,
            'volume_ratio': volume_strength
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

    print("=== 測試策略 3: 長時間未破底後創新高（原始版）===\n")

    client = FinLabClient()

    print("📊 正在獲取數據...")
    data = {
        'close': client.get_close(),
        'high': client.get_price_data()['high'],
        'low': client.get_price_data()['low'],
        'volume': client.get_volume(),
        'revenue': client.get_monthly_revenue()['revenue'],
        'common_stock': client.get_financial_data()['common_stock'],
        'roe': client.get_fundamental_ratios()['roe'],
        'dividend_announcement': client.get_dividend_data(),  # 新增股利數據
    }

    strategy = BreakoutOriginalStrategy()
    result = strategy.screen(data)

    if not result.empty:
        print("\n前 10 名推薦:")
        print(result.head(10))
    else:
        print("\n沒有符合條件的股票")


if __name__ == "__main__":
    test_strategy()

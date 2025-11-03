"""
測試產業平均計算邏輯
Test Industry Average Calculation Logic

目的：驗證 groupby 邏輯是否能正確計算產業平均營收 YoY
"""

import pandas as pd
import numpy as np
from backend.data_sources.finlab_client import FinLabClient


def test_industry_average_logic():
    """測試產業平均計算邏輯"""

    print("=" * 70)
    print("🧪 產業平均計算邏輯測試")
    print("=" * 70)
    print()

    # ==================== 1. 數據載入 ====================

    print("📊 步驟 1：載入數據...")
    client = FinLabClient()

    try:
        # 獲取公司基本資訊
        company_info = client._get_and_convert('company_basic_info')
        if company_info.empty:
            print("❌ 無法獲取 company_basic_info")
            return False

        # 設置 stock_id 為 index
        company_info = company_info.set_index('stock_id')

        # 獲取產業分類
        industry_classification = company_info['產業類別']
        print(f"✅ 產業分類數據: {len(industry_classification)} 檔股票")
        print(f"   Index 類型: {type(industry_classification.index[0])}")
        print(f"   Index 範例: {list(industry_classification.index[:5])}")

        # 獲取月營收
        revenue = client._get_and_convert('monthly_revenue:當月營收')
        if revenue.empty:
            print("❌ 無法獲取月營收數據")
            return False

        print(f"✅ 月營收數據: {revenue.shape}")

    except Exception as e:
        print(f"❌ 數據載入失敗: {e}")
        return False

    print()

    # ==================== 2. 計算營收 YoY ====================

    print("📊 步驟 2：計算營收 YoY...")
    revenue_yoy = revenue.pct_change(12, fill_method=None)

    # 取最新一期的 YoY
    latest_yoy = revenue_yoy.iloc[-1]
    print(f"✅ 最新 YoY 數據: {len(latest_yoy)} 檔股票")
    print(f"   - 有效數據: {latest_yoy.notna().sum()} 檔")
    print(f"   - NaN 數據: {latest_yoy.isna().sum()} 檔")
    print()

    # ==================== 3. 檢查數據對齊 ====================

    print("🔍 步驟 3：檢查數據對齊...")

    # 檢查 index 對齊
    industry_stocks = set(industry_classification.index)
    yoy_stocks = set(latest_yoy.index)

    common_stocks = industry_stocks & yoy_stocks
    only_in_industry = industry_stocks - yoy_stocks
    only_in_yoy = yoy_stocks - industry_stocks

    print(f"   - 產業分類股票數: {len(industry_stocks)}")
    print(f"   - YoY 股票數: {len(yoy_stocks)}")
    print(f"   - 共同股票數: {len(common_stocks)}")

    if only_in_industry:
        print(f"   ⚠️  只在產業分類中: {len(only_in_industry)} 檔")
        print(f"       範例: {list(only_in_industry)[:5]}")

    if only_in_yoy:
        print(f"   ⚠️  只在 YoY 中: {len(only_in_yoy)} 檔")
        print(f"       範例: {list(only_in_yoy)[:5]}")

    print()

    # ==================== 4. 對齊數據並測試 groupby ====================

    print("🧮 步驟 4：測試 groupby 計算產業平均...")

    # 只使用共同股票
    aligned_yoy = latest_yoy[latest_yoy.index.isin(common_stocks)]
    aligned_industry = industry_classification[industry_classification.index.isin(common_stocks)]

    try:
        # 嘗試 groupby
        industry_avg_yoy = aligned_yoy.groupby(aligned_industry).mean()
        print(f"✅ Groupby 成功！")
        print(f"   - 計算出 {len(industry_avg_yoy)} 個產業的平均 YoY")
        print()

    except Exception as e:
        print(f"❌ Groupby 失敗: {e}")
        return False

    # ==================== 5. 產業統計分析 ====================

    print("📊 步驟 5：產業統計分析...")

    # 統計每個產業的股票數
    industry_counts = aligned_industry.value_counts()

    print(f"   總產業數: {len(industry_counts)}")
    print()
    print("   前 10 大產業：")
    for i, (industry, count) in enumerate(industry_counts.head(10).items(), 1):
        avg_yoy = industry_avg_yoy.get(industry, np.nan)
        if pd.notna(avg_yoy):
            print(f"   {i:2d}. {industry:20s} - {count:3d} 檔, 平均 YoY = {avg_yoy:7.2%}")
        else:
            print(f"   {i:2d}. {industry:20s} - {count:3d} 檔, 平均 YoY = N/A")

    print()

    # 找出單一股票產業
    single_stock_industries = industry_counts[industry_counts == 1]
    if len(single_stock_industries) > 0:
        print(f"   ⚠️  單一股票產業: {len(single_stock_industries)} 個")
        print(f"       範例: {list(single_stock_industries.index[:5])}")
        print()

    # ==================== 6. 測試比較邏輯 ====================

    print("🎯 步驟 6：測試比較邏輯...")

    # 為每支股票映射其產業平均
    stock_industry_avg = aligned_yoy.index.map(lambda stock: industry_avg_yoy.get(
        aligned_industry.get(stock, None), np.nan
    ))
    stock_industry_avg = pd.Series(stock_industry_avg, index=aligned_yoy.index)

    # 判斷是否高於產業平均
    above_industry_avg = aligned_yoy > stock_industry_avg

    print(f"   - 總股票數: {len(aligned_yoy)}")
    print(f"   - 有效比較: {above_industry_avg.notna().sum()} 檔")
    print(f"   - 高於產業平均: {above_industry_avg.sum()} 檔 ({above_industry_avg.sum() / above_industry_avg.notna().sum():.1%})")
    print(f"   - 低於產業平均: {(~above_industry_avg & above_industry_avg.notna()).sum()} 檔")
    print()

    # ==================== 7. 具體案例驗證 ====================

    print("📝 步驟 7：具體案例驗證...")

    # 測試幾支知名股票
    test_stocks = ['2330', '2454', '2317', '2412']

    for stock_code in test_stocks:
        if stock_code not in aligned_yoy.index:
            print(f"   {stock_code}: 數據不存在")
            continue

        stock_yoy = aligned_yoy[stock_code]
        stock_industry = aligned_industry.get(stock_code, 'N/A')
        industry_avg = industry_avg_yoy.get(stock_industry, np.nan)

        if pd.notna(stock_yoy) and pd.notna(industry_avg):
            is_above = stock_yoy > industry_avg
            symbol = "✅" if is_above else "❌"
            print(f"   {stock_code} ({stock_industry})")
            print(f"      股票 YoY = {stock_yoy:7.2%}, 產業平均 = {industry_avg:7.2%} {symbol}")
        else:
            print(f"   {stock_code} ({stock_industry}): 數據不完整")

    print()

    # ==================== 8. 邊界情況測試 ====================

    print("⚠️  步驟 8：邊界情況測試...")

    # 測試 1：單一股票產業
    if len(single_stock_industries) > 0:
        single_stock_industry_name = single_stock_industries.index[0]
        single_stock = aligned_industry[aligned_industry == single_stock_industry_name].index[0]
        single_yoy = aligned_yoy[single_stock]
        single_avg = industry_avg_yoy[single_stock_industry_name]

        print(f"   單一股票產業測試:")
        print(f"      產業: {single_stock_industry_name}")
        print(f"      股票: {single_stock}")
        print(f"      股票 YoY = {single_yoy:.2%}")
        print(f"      產業平均 = {single_avg:.2%}")
        print(f"      是否相等: {abs(single_yoy - single_avg) < 0.0001}")
        print()

    # 測試 2：NaN 處理
    nan_stocks = aligned_yoy[aligned_yoy.isna()].index[:5]
    if len(nan_stocks) > 0:
        print(f"   NaN 股票測試: {len(nan_stocks)} 檔範例")
        for stock in nan_stocks:
            stock_industry = aligned_industry.get(stock, 'N/A')
            industry_avg = industry_avg_yoy.get(stock_industry, np.nan)
            if pd.notna(industry_avg):
                print(f"      {stock} ({stock_industry}): YoY=NaN, 產業平均={industry_avg:.2%}")
            else:
                print(f"      {stock} ({stock_industry}): YoY=NaN, 產業平均=N/A")
        print()

    # ==================== 9. 結論 ====================

    print("=" * 70)
    print("✅ 測試完成！")
    print("=" * 70)
    print()
    print("📊 總結：")
    print(f"   1. Groupby 邏輯: ✅ 可行")
    print(f"   2. 數據對齊: {'✅ 完全對齊' if len(only_in_industry) == 0 and len(only_in_yoy) == 0 else '⚠️  部分不對齊'}")
    print(f"   3. 產業數量: {len(industry_avg_yoy)} 個")
    print(f"   4. 單一股票產業: {len(single_stock_industries)} 個 {'(需注意)' if len(single_stock_industries) > 5 else ''}")
    print(f"   5. NaN 處理: ✅ Groupby.mean() 自動忽略 NaN")
    print()

    return True


if __name__ == "__main__":
    success = test_industry_average_logic()
    if not success:
        print("\n❌ 測試失敗，請檢查錯誤訊息")
        exit(1)
    else:
        print("✅ 所有測試通過，可以繼續實作！")

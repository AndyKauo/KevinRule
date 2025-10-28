"""
FinlabDataFrame 相容性處理工具
解決 FinlabDataFrame 與 pandas DataFrame 的 API 差異

來源: 複製自 reference/finlab_data_utils.py
Source: Copied from reference/finlab_data_utils.py
"""

import pandas as pd
import numpy as np

def is_finlab_dataframe(obj):
    """檢查是否為 FinlabDataFrame"""
    return hasattr(obj, '__class__') and 'FinlabDataFrame' in str(type(obj))

def get_data_type(obj):
    """獲取數據類型，相容 FinlabDataFrame 和 pandas DataFrame"""
    try:
        if is_finlab_dataframe(obj):
            # FinlabDataFrame 可能沒有 dtype 屬性
            if hasattr(obj, 'dtypes'):
                # 如果有多列，檢查第一列的類型
                if hasattr(obj.dtypes, 'iloc'):
                    first_dtype = obj.dtypes.iloc[0]
                else:
                    first_dtype = obj.dtypes

                # 檢查是否為布林型
                if 'bool' in str(first_dtype):
                    return 'bool'
                elif 'int' in str(first_dtype) or 'float' in str(first_dtype):
                    return 'numeric'
                else:
                    return 'other'
            else:
                # 嘗試檢查實際數據
                sample_data = obj.iloc[:10, :5] if hasattr(obj, 'iloc') else obj
                if hasattr(sample_data, 'values'):
                    sample_values = sample_data.values.flatten()
                    unique_values = np.unique(sample_values[~pd.isna(sample_values)])

                    # 如果只有 True/False/0/1，認為是布林型
                    if len(unique_values) <= 4 and all(v in [0, 1, True, False] for v in unique_values):
                        return 'bool'
                    else:
                        return 'numeric'
                else:
                    return 'unknown'
        else:
            # pandas DataFrame
            if hasattr(obj, 'dtype'):
                if obj.dtype == 'bool':
                    return 'bool'
                elif pd.api.types.is_numeric_dtype(obj.dtype):
                    return 'numeric'
                else:
                    return 'other'
            elif hasattr(obj, 'dtypes'):
                # 多列 DataFrame，檢查主要類型
                bool_cols = (obj.dtypes == 'bool').sum()
                numeric_cols = obj.select_dtypes(include=[np.number]).shape[1]

                if bool_cols > numeric_cols:
                    return 'bool'
                elif numeric_cols > 0:
                    return 'numeric'
                else:
                    return 'other'
            else:
                return 'unknown'
    except Exception as e:
        print(f"數據類型檢查失敗: {e}")
        return 'unknown'

def convert_to_pandas(obj):
    """將 FinlabDataFrame 轉換為 pandas DataFrame"""
    try:
        if is_finlab_dataframe(obj):
            if hasattr(obj, 'to_pandas'):
                return obj.to_pandas()
            elif hasattr(obj, 'values') and hasattr(obj, 'index') and hasattr(obj, 'columns'):
                # 手動建立 pandas DataFrame
                if hasattr(obj, 'columns'):
                    return pd.DataFrame(obj.values, index=obj.index, columns=obj.columns)
                else:
                    return pd.DataFrame(obj.values, index=obj.index)
            else:
                # 嘗試直接轉換
                return pd.DataFrame(obj)
        else:
            # 已經是 pandas DataFrame
            return obj
    except Exception as e:
        print(f"轉換為 pandas DataFrame 失敗: {e}")
        return obj

def safe_astype(obj, target_type):
    """安全的類型轉換"""
    try:
        if is_finlab_dataframe(obj):
            # FinlabDataFrame 的 astype 可能不同
            if hasattr(obj, 'astype'):
                return obj.astype(target_type)
            else:
                # 轉換為 pandas 後再轉型
                pandas_obj = convert_to_pandas(obj)
                return pandas_obj.astype(target_type)
        else:
            return obj.astype(target_type)
    except Exception as e:
        print(f"類型轉換失敗: {e}")
        return obj

def safe_correlation_analysis(factors_dict):
    """安全的因子相關性分析"""
    try:
        # 收集布林型因子
        bool_factors = {}
        for name, factor in factors_dict.items():
            if factor is not None:
                data_type = get_data_type(factor)

                if data_type == 'bool':
                    # 布林型因子直接轉為 int
                    converted_factor = safe_astype(factor, int)
                    bool_factors[name] = convert_to_pandas(converted_factor)
                elif data_type == 'numeric':
                    # 數值型因子，檢查是否為 0/1 布林型
                    pandas_factor = convert_to_pandas(factor)
                    unique_vals = pandas_factor.stack().dropna().unique()

                    if len(unique_vals) <= 2 and all(v in [0, 1, True, False] for v in unique_vals):
                        bool_factors[name] = pandas_factor.astype(int)
                    # 如果是數值型，轉為布林型（大於 0）
                    elif pandas_factor.max().max() > 1:
                        bool_factors[name] = (pandas_factor > 0).astype(int)
                    else:
                        bool_factors[name] = pandas_factor.astype(int)

        if len(bool_factors) < 2:
            print("⚠️  可用因子數量不足，無法進行相關性分析")
            return None

        # 建立 DataFrame 並計算相關性
        processed_factors = {}
        for k, v in bool_factors.items():
            if hasattr(v, 'stack'):
                processed_factors[k] = v.stack()
            else:
                # 如果是 Series，直接使用
                processed_factors[k] = v

        df_factors = pd.DataFrame(processed_factors).fillna(0)

        if df_factors.empty:
            print("⚠️  因子數據為空，無法進行相關性分析")
            return None

        correlation_matrix = df_factors.corr()

        print(f"\n📈 {len(bool_factors)} 個因子的相關性矩陣：")
        print(correlation_matrix.round(3))

        # 找出高相關性因子對
        high_corr_pairs = []
        for i in range(len(correlation_matrix.columns)):
            for j in range(i+1, len(correlation_matrix.columns)):
                corr = correlation_matrix.iloc[i, j]
                if abs(corr) > 0.7:
                    factor1 = correlation_matrix.columns[i]
                    factor2 = correlation_matrix.columns[j]
                    high_corr_pairs.append((factor1, factor2, corr))

        if high_corr_pairs:
            print(f"\n🔗 高度相關的因子對（|相關係數| > 0.7）：")
            for factor1, factor2, corr in high_corr_pairs:
                print(f"   {factor1} ↔ {factor2}: {corr:.3f}")
            print("\n💡 建議：避免同時使用高度相關的因子，以減少重複暴露")
        else:
            print(f"\n✅ 所有因子間相關性適中，適合組合使用")

        return correlation_matrix

    except Exception as e:
        print(f"⚠️  相關性分析失敗：{e}")
        return None

def test_finlab_compatibility():
    """測試 FinlabDataFrame 相容性"""
    print("=== FinlabDataFrame 相容性測試 ===")

    # 測試 pandas DataFrame
    pandas_bool = pd.DataFrame(np.random.choice([True, False], (100, 3)),
                              columns=['factor1', 'factor2', 'factor3'])
    pandas_numeric = pd.DataFrame(np.random.randn(100, 2),
                                 columns=['factor4', 'factor5'])

    print(f"pandas 布林型: {get_data_type(pandas_bool)}")
    print(f"pandas 數值型: {get_data_type(pandas_numeric)}")

    # 測試相關性分析
    test_factors = {
        'factor1': pandas_bool['factor1'],
        'factor2': pandas_bool['factor2'],
        'factor3': pandas_numeric['factor4'] > 0
    }

    result = safe_correlation_analysis(test_factors)
    print(f"相關性分析結果: {'成功' if result is not None else '失敗'}")
    print("✓ 測試完成")

if __name__ == "__main__":
    test_finlab_compatibility()

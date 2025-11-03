# FinlabDataFrame vs pandas DataFrame 陷阱：致命的數據對齊問題

## 🎯 目的

**這份文檔記錄了一次嚴重的錯誤**，希望未來的 AI 或開發者不要重蹈覆轍。

**關鍵教訓**：
> **千萬不要把 FinlabDataFrame 轉換為 pandas DataFrame！**
> 這會破壞 FinLab 官方設計的自動對齊機制，導致策略失效。

---

## ❌ 問題現象

### 症狀
所有 6 個選股策略都返回 **0 檔股票**，即使單獨條件都有符合的股票：

```
策略 1: 營收動能高於同業平均
   - YoY > 20%: 458 檔
   - MoM > 20%: 381 檔
   - 價格 < 100元: 1837 檔
   - 連續兩季 EPS 成長: 14 檔
   - 最終符合: 0 檔 ← ❌

策略 6: 現金快速累積中
   - 連續4期現金增>5%: 1 檔
   - 月營收MoM>20%: 381 檔
   - 連續兩季EPS成長: 14 檔
   - 最終符合: 0 檔 ← ❌
```

### 初步懷疑（錯誤方向）
一開始懷疑是 **index alignment 問題**，認為需要手動 reindex：
```python
# ❌ 錯誤的解決方向
cond1 = (latest_yoy > 0.20).reindex(base_index, fill_value=False)
cond2 = (latest_mom > 0.20).reindex(base_index, fill_value=False)
```

**但這是在修補一個不應該存在的問題！**

---

## 🔍 根本原因

### 錯誤代碼

在 `backend/data_sources/finlab_client.py:56-78`：

```python
def _get_and_convert(self, field: str) -> pd.DataFrame:
    result = data.get(field)

    # ❌ 致命錯誤：轉換為 pandas DataFrame
    if is_finlab_dataframe(result):
        result = convert_to_pandas(result)

    return result
```

### 為什麼這是錯誤的？

FinLab API 返回的是 **FinlabDataFrame**，這是一個特殊的 DataFrame 子類，具有**自動對齊能力**。

#### FinlabDataFrame 的對齊規則（官方文檔）

> 當資料日期沒有對齊（例如: 財報 vs 收盤價 vs 月報）時，在使用以下運算符號：
> `+`, `-`, `*`, `/`, `>`, `>=`, `==`, `<`, `<=`, `&`, `|`, `~`
> **不需要先將資料對齊，因為 `FinlabDataFrame` 會自動幫你處理**

**對齊規則**：
- **index 取聯集**（保留所有時間點）
- **column 取交集**（只保留共同股票）

來源：`reference/finlab_site/finlab_docs_md/reference/dataframe/index.md:156`

### 轉換為 pandas 後的行為

pandas DataFrame 的 AND 運算：
- **index 取交集**（只保留共同時間點）
- **column 取交集**（只保留共同股票）

### 實際影響

#### 數據形狀對比

```python
close = data.get('price:收盤價')        # (4558, 2659) - 每日
revenue = data.get('monthly_revenue:當月營收')  # (249, 2234)  - 每月
eps = data.get('financial_statement:每股盈餘')  # (51, 2778)   - 每季
```

#### FinlabDataFrame 運算（✅ 正確）

```python
cond1 = close > 100        # index: 4558天, column: 2659檔
cond2 = revenue > 1000000  # index: 249月,  column: 2234檔
cond3 = eps > 1            # index: 51季,   column: 2778檔

result = cond1 & cond2 & cond3

# 自動對齊結果：
# - index: 聯集（4558 + 249 + 51 = 所有時間點）
# - column: 交集（2659 ∩ 2234 ∩ 2778 = 共同股票）
# ✅ 有結果！
```

#### pandas DataFrame 運算（❌ 錯誤）

```python
cond1 = close > 100        # index: 4558天
cond2 = revenue > 1000000  # index: 249月
cond3 = eps > 1            # index: 51季

result = cond1 & cond2 & cond3

# pandas 對齊結果：
# - index: 交集（4558天 ∩ 249月 ∩ 51季 = 空集合 或 極少）
# - column: 交集
# ❌ 0 檔！
```

---

## ✅ 正確做法

### 修復後的代碼

`backend/data_sources/finlab_client.py`:

```python
def _get_and_convert(self, field: str):
    """
    獲取 FinLab 數據（保留 FinlabDataFrame 原生格式）

    重要提示:
        FinlabDataFrame 在進行運算時會自動對齊不同頻率的數據：
        - index 取聯集（保留所有時間點）
        - column 取交集（只保留共同股票）
        不要轉換為 pandas DataFrame，否則會失去自動對齊能力！
    """
    try:
        data = self._get_data_module()
        result = data.get(field)

        # ✅ 直接返回 FinlabDataFrame，保留自動對齊能力
        return result

    except Exception as e:
        print(f"❌ 獲取 {field} 失敗: {e}")
        return pd.DataFrame()
```

### 策略代碼（無需修改）

```python
# 策略中的代碼不需要任何修改
cond1 = latest_yoy > 0.20
cond2 = latest_mom > 0.20
cond3 = eps_growth_filter

# ✅ FinlabDataFrame 會自動處理對齊
final_condition = cond1 & cond2 & cond3 & cond_basic
```

---

## 🚨 關鍵教訓

### 1. 閱讀官方文檔，但要真正理解

我們多次閱讀了 FinLab 文檔，但沒有理解 **為什麼** FinlabDataFrame 存在。

**錯誤思維**：
> "FinlabDataFrame 只是 pandas DataFrame 的包裝，轉換一下沒關係"

**正確思維**：
> "FinlabDataFrame 的存在是為了解決多頻率數據對齊問題，不能轉換"

### 2. 不要過早優化或「統一格式」

**錯誤思維**：
> "為了統一，把所有數據都轉成 pandas DataFrame"

**正確思維**：
> "尊重 API 設計者的意圖，保留原生格式"

### 3. 懷疑問題時先檢查基本假設

當發現策略返回 0 檔時，應該先問：
- ✅ 數據格式是否正確？
- ✅ 是否破壞了 API 的原生功能？
- ❌ 而不是立即想著修補（reindex）

### 4. 官方設計通常有其原因

如果官方 API 返回特殊類型（如 FinlabDataFrame），通常是有原因的：
- ✅ 保留原生類型
- ❌ 不要隨意轉換

---

## 📚 參考資料

1. **FinLab 官方文檔**：
   - `reference/finlab_site/finlab_docs_md/reference/dataframe/index.md`
   - 第 156 行開始：自動對齊說明

2. **本次修復 Commit**：
   - 文件：`backend/data_sources/finlab_client.py:56-89`
   - 修改：移除 `convert_to_pandas()` 調用

3. **受影響的策略**：
   - 所有 6 個策略（`backend/strategies/original/*.py`）
   - 修復後無需改動策略代碼

---

## 🎓 給未來 AI 的提示

如果你遇到類似問題：

1. **檢查數據格式**
   ```python
   print(type(data))  # 應該是 FinlabDataFrame
   ```

2. **不要轉換**
   ```python
   # ❌ 錯誤
   if is_finlab_dataframe(result):
       result = convert_to_pandas(result)

   # ✅ 正確
   return result  # 直接返回
   ```

3. **信任官方設計**
   - 如果官方返回特殊類型，保留它
   - 不要為了「統一」而轉換

4. **遇到 0 檔問題時的排查順序**：
   1. 檢查數據類型是否正確
   2. 檢查是否有不必要的格式轉換
   3. 檢查條件是否過於嚴格
   4. **最後才考慮**手動 reindex

---

## 📊 修復效果對比

### 修復前
```
策略 1: 最終符合: 0 檔
策略 2: 最終符合: 0 檔
策略 3: 最終符合: 0 檔
策略 4: 最終符合: 0 檔
策略 5: 最終符合: 0 檔
策略 6: 最終符合: 0 檔
```

### 修復後
```
（待測試驗證）
應該能找到符合條件的股票
```

---

## 🔗 相關文件

- **修復文件**：`backend/data_sources/finlab_client.py`
- **受影響策略**：`backend/strategies/original/*.py`（無需修改）
- **官方文檔**：`reference/finlab_site/finlab_docs_md/reference/dataframe/index.md`
- **轉換工具**：`backend/etl/finlab_compat.py`（考慮棄用）

---

**創建日期**：2025-01-01
**錯誤發現者**：Claude (Sonnet 4.5)
**文檔目的**：防止未來重複此錯誤

**請記住**：
> **FinlabDataFrame 的自動對齊機制是 FinLab API 的核心功能，不要破壞它！**

# KevinRule - 台股智能選股系統

> 基於 FinLab API 的量化選股系統，整合 6 種選股策略 + Claude AI 分析

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-1.30%2B-red)
![FinLab](https://img.shields.io/badge/FinLab-API-green)
![Railway](https://img.shields.io/badge/Railway-Deployment-purple)

## 📋 功能特色

### ✅ 6 種量化選股策略
1. **營收動能高於同業平均** - 月營收 YoY>20% 且持續成長
2. **低價小股本營收創一年高** - 股價<100元、市值<100億、營收創新高
3. **長時間未破底後創新高** - 60天底部穩固後突破（VCP型態）
4. **連兩日大戶大買超** - 量增價漲 + 融資減少
5. **大現增快繳款結束** - 現金增資後資金到位
6. **現金快速累積中** - 營業現金流強 + 現金持續增加

### 🤖 Claude AI 智能分析
- 自動解讀選股結果
- 風險評估與投資建議
- 市場環境分析

### 📊 自選股追蹤
- 手動管理 5 檔持股
- 15 個分析維度（PE、EPS、技術指標等）
- 即時價格更新

### 🔔 LINE 通知
- 新股推薦提醒
- 持股異動通知
- 重要資訊推播

---

## 🚀 快速開始

### 1. 環境需求

```bash
# Python 3.10+
python --version

# FinLab API Token (需註冊 https://ai.finlab.tw/)
# Claude API Key (需註冊 https://console.anthropic.com/)
```

### 2. 安裝

```bash
# 克隆專案
git clone https://github.com/yourusername/KevinRule.git
cd KevinRule

# 安裝依賴
pip install -r requirements.txt
```

### 3. 配置環境變數

```bash
# 複製環境變數範本
cp .env.example .env

# 編輯 .env 檔案，填入你的 API Keys
nano .env
```

**必填項目：**
```bash
FINLAB_API_KEY=your_finlab_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
LINE_NOTIFY_TOKEN=your_line_notify_token_here  # 選填
```

### 4. 運行

#### 本地運行
```bash
# 啟動 Streamlit 應用
streamlit run frontend/app.py
```

#### Railway 部署
```bash
# 推送到 Railway
git push railway main

# 或在 Railway Dashboard 連接 GitHub repo
```

---

## 📂 專案結構

```
KevinRule/
├── config/
│   └── settings.py              # 配置管理（FinLab 登入單例）
├── backend/
│   ├── data_sources/
│   │   └── finlab_client.py     # FinLab API 封裝
│   ├── etl/
│   │   └── finlab_compat.py     # FinLabDataFrame 相容性處理
│   ├── strategies/              # 🎯 6 個選股策略
│   │   ├── base_strategy.py     # 策略基類
│   │   ├── revenue_momentum.py  # 策略1
│   │   ├── low_price_small.py   # 策略2
│   │   ├── breakout.py          # 策略3
│   │   ├── inst_buying.py       # 策略4
│   │   ├── capital_increase.py  # 策略5
│   │   ├── cash_growth.py       # 策略6
│   │   └── strategy_manager.py  # 策略管理器
│   ├── database/
│   │   └── duckdb_client.py     # DuckDB 資料庫
│   └── scoring/                 # AI 評分引擎（待實現）
├── frontend/
│   ├── app.py                   # Streamlit 主應用
│   └── pages/                   # 多頁面應用
│       ├── 1_🏠_市場總覽.py
│       ├── 2_📊_我的持股.py
│       ├── 3_🔍_AI選股.py
│       └── 4_⚙️_設定.py
├── data/                        # DuckDB 資料檔案
├── logs/                        # 日誌檔案
├── requirements.txt             # Python 依賴
├── Procfile                     # Railway 啟動命令
├── railway.json                 # Railway 配置
└── .env.example                 # 環境變數範本
```

---

## 🎯 使用說明

### 策略使用範例

```python
from backend.data_sources.finlab_client import FinLabClient
from backend.strategies.strategy_manager import StrategyManager

# 1. 初始化 FinLab 客戶端
client = FinLabClient()

# 2. 獲取所有數據
data = client.get_all_data()

# 3. 執行策略
manager = StrategyManager()

# 執行單個策略
result = manager.run_strategy('revenue_momentum', data)
print(result.head(10))

# 執行所有策略
all_results = manager.run_all_strategies(data)

# 查看策略重疊（多策略推薦的股票）
overlaps = manager.get_stock_appearances(all_results)
print(overlaps)
```

### FinLab API 使用範例

```python
from backend.data_sources.finlab_client import FinLabClient

client = FinLabClient()

# 獲取價格數據
price_data = client.get_price_data()
close = price_data['close']
volume = price_data['volume']

# 獲取月營收
revenue_data = client.get_monthly_revenue()
revenue_yoy = revenue_data['revenue_yoy']  # 年增率

# 獲取財務數據
financial = client.get_financial_data()
total_assets = financial['total_assets']
net_income = financial['net_income']

# 獲取基本面指標
ratios = client.get_fundamental_ratios()
roe = ratios['roe']
```

---

## 📊 數據說明

### FinLab API 欄位格式

```python
# 格式: 'table:field'
data.get('price:收盤價')              # 收盤價
data.get('etl:market_value')          # 市值（推薦）
data.get('monthly_revenue:當月營收')   # 月營收
data.get('financial_statement:資產總額') # 總資產（單位：仟元）
```

### 重要單位說明

| 數據類型 | 單位 | 說明 |
|---------|------|------|
| 財務數據 | **仟元** | 資產、負債、營收等 |
| 價格數據 | 元 | 股價、市值 |
| 成交量 | 股 | 需÷1000轉為張 |
| 殖利率 | % | 需÷100轉為小數 |

### 資料更新頻率

- **價格數據**: 每日
- **月營收**: 每月 10 日前
- **財務報表**: 每季
- **基本面指標**: 隨財報更新

---

## 🔧 配置選項

### settings.py 可調整參數

```python
# 回測設定
BACKTEST_COMMISSION = 0.001425  # 手續費 0.1425%
BACKTEST_TAX = 0.003            # 證交稅 0.3%
BACKTEST_SLIPPAGE = 0.001       # 滑價 0.1%

# 策略設定
MAX_POSITIONS = 30              # 最大持股數
MIN_MARKET_CAP = 1000000000     # 最小市值 10億
MIN_LIQUIDITY_PERCENTILE = 0.3  # 前70%流動性

# 提醒設定
ALERT_COOLDOWN_HOURS = 24       # 提醒冷卻時間
```

---

## 🐛 常見問題

### 1. FinLab 登入失敗

```bash
❌ FinLab API 登入失敗: Invalid API key
```

**解決方法：**
- 檢查 `.env` 中的 `FINLAB_API_KEY` 是否正確
- 前往 https://ai.finlab.tw/ 重新產生 Token
- 確認網路連線正常

### 2. 數據欄位不存在

```bash
❌ **Error: price:收盤價 not exists
```

**解決方法：**
- 參考 `/reference/finlab_API/FINLAB_COMMON_FIELDS_GUIDE.md`
- 確認欄位名稱拼寫正確（注意中英文）
- 檢查會員權限（某些數據需付費）

### 3. FinLabDataFrame 類型錯誤

```bash
❌ AttributeError: 'FinlabDataFrame' object has no attribute 'to_pandas'
```

**解決方法：**
- 使用 `backend/etl/finlab_compat.py` 中的轉換函數
- 所有 FinLab 數據已在 `finlab_client.py` 中自動轉換

### 4. Railway 部署失敗

**檢查清單：**
- ✅ 環境變數是否設定（Railway Dashboard）
- ✅ `Procfile` 是否存在
- ✅ Python 版本是否 >= 3.10
- ✅ 資料庫路徑是否掛載 Volume

---

## 📚 參考資源

### FinLab 文檔
- 官方文檔: https://doc.finlab.tw/
- API 數據表: https://ai.finlab.tw/database/
- 本專案參考: `/reference/finlab_API/FINLAB_COMMON_FIELDS_GUIDE.md`

### 學術依據
策略設計參考學術研究：
1. **Novy-Marx (2013)**: 品質因子（毛利資產比）
2. **Fama-French (1992)**: 價值因子（淨值市價比）
3. **Jegadeesh & Titman (1993)**: 動量因子
4. **Piotroski (2000)**: F-Score 財務品質
5. **VCP Pattern**: 波動收縮突破型態

---

## ⚠️ 免責聲明

**本系統僅供學習與研究使用，不構成投資建議。**

- 📉 過去績效不代表未來報酬
- 💰 投資有風險，請謹慎評估
- 🛡️ 建議設定停損機制（個股 -15%, 組合 -10%）
- 🧪 建議先進行紙上交易 1-3 個月
- 💡 不要投入超過可承受損失的資金

---

## 🤝 貢獻

歡迎提交 Issue 和 Pull Request！

---

## 📝 授權

MIT License

---

## 📧 聯絡

如有問題，請開 Issue 或聯繫專案維護者。

---

**祝您投資順利！記住：紀律執行 × 長期持有 = 成功關鍵** 🚀

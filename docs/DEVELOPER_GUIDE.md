# KevinRule 開發者快速上手指南

> **目的**: 幫助新加入的開發者快速理解專案架構、修改 UI/UX、部署應用
> **更新日期**: 2025-10-28
> **適用版本**: v1.1.0+

---

## 📚 目錄

1. [專案概覽](#專案概覽)
2. [快速開始](#快速開始)
3. [專案架構](#專案架構)
4. [核心模組說明](#核心模組說明)
5. [UI/UX 開發指南](#uiux-開發指南)
6. [常見開發任務](#常見開發任務)
7. [故障排除](#故障排除)
8. [最佳實踐](#最佳實踐)

---

## 專案概覽

**KevinRule** 是一個基於 Streamlit 的台股智能選股系統，整合：
- **FinLab API**: 台股數據（價格、財報、籌碼）
- **Yahoo Finance**: 國際市場數據
- **Trading Economics API**: 全球經濟日曆
- **Claude AI**: 智能分析（選配）

### 核心功能
1. **6 種量化選股策略**
   - 營收動能、低價小本、突破整理
   - 大戶買超、大現增、現金累積
2. **市場總覽**
   - 國際市場（美股、亞股）
   - 台股指數（加權、櫃買、類股）
   - 經濟日曆（時間軸網格佈局）
3. **自選股追蹤**
   - 最多 5 檔股票
   - 即時價格、損益計算
4. **主題系統**
   - 深色/淺色模式切換
   - 專業金融儀表板風格

---

## 快速開始

### 1. 環境需求
```bash
# 作業系統
macOS / Linux / Windows

# Python 版本
Python 3.10+

# 套件管理
pip / conda
```

### 2. 安裝步驟

```bash
# 1. Clone 專案
git clone https://github.com/AndyKauo/KevinRule.git
cd KevinRule

# 2. 創建虛擬環境
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# 或
venv\Scripts\activate     # Windows

# 3. 安裝依賴
pip install -r requirements.txt

# 4. 設定環境變數
cp .env.example .env
# 編輯 .env，填入你的 API Keys:
# - FINLAB_API_KEY (必需)
# - ANTHROPIC_API_KEY (選填)
# - TRADING_ECONOMICS_API_KEY (選填)

# 5. 啟動應用
streamlit run frontend/app.py
```

### 3. 驗證安裝

訪問 http://localhost:8501，你應該看到：
- ✅ 主頁顯示系統介紹
- ✅ 側邊欄顯示系統狀態（綠色 = 配置完整）
- ✅ 右上角有主題切換按鈕（☀️/🌙）

---

## 專案架構

```
KevinRule/
├── backend/                    # 後端邏輯
│   ├── data_sources/           # 數據源客戶端
│   │   ├── finlab_client.py    # FinLab API 封裝
│   │   ├── yahoo_finance_client.py  # Yahoo Finance 封裝
│   │   └── trading_economics_client.py  # Trading Economics 封裝
│   ├── strategies/             # 選股策略
│   │   ├── strategy_base.py    # 策略基類
│   │   ├── strategy_*.py       # 6 種具體策略
│   │   └── strategy_manager.py # 策略管理器
│   ├── database/               # 資料庫
│   │   └── duckdb_client.py    # DuckDB 客戶端
│   └── claude/                 # Claude AI 整合（選填）
│       └── claude_client.py
│
├── frontend/                   # 前端 UI
│   ├── app.py                  # 主應用（首頁）
│   ├── theme.py                # 主題系統 ⭐ 重要
│   └── pages/                  # 多頁面應用
│       ├── 1_🏠_市場總覽.py
│       ├── 2_📊_我的持股.py
│       └── 3_🔍_AI選股.py
│
├── config/                     # 配置
│   └── settings.py             # 設定管理
│
├── docs/                       # 文檔 ⭐ 新增
│   ├── UI_UX_IMPROVEMENTS.md   # UI/UX 改進記錄
│   └── DEVELOPER_GUIDE.md      # 本文檔
│
├── data/                       # 資料庫文件（自動生成）
│   └── kevinrule.duckdb
│
├── .env.example                # 環境變數範本
├── requirements.txt            # Python 依賴
└── README.md                   # 專案說明
```

### 重要檔案說明

| 檔案 | 用途 | 修改頻率 |
|-----|------|---------|
| `frontend/theme.py` | 主題配色、CSS 樣式 | 🔴 高 (UI 改進) |
| `frontend/app.py` | 首頁布局、功能介紹 | 🟡 中 |
| `frontend/pages/*.py` | 各功能頁面 | 🔴 高 (功能擴展) |
| `backend/strategies/*.py` | 選股策略邏輯 | 🟡 中 (策略調整) |
| `backend/data_sources/*.py` | API 數據獲取 | 🟢 低 (已穩定) |
| `config/settings.py` | 環境變數、配置 | 🟢 低 |

---

## 核心模組說明

### 1. 主題系統 (`frontend/theme.py`) ⭐ 核心

**職責**: 管理深色/淺色主題配色，生成全域 CSS

#### 配色結構
```python
class Theme:
    DARK = {
        'bg_primary': '#0e1117',      # 主背景
        'bg_secondary': '#1a1d24',    # 次要背景
        'bg_card': '#262730',         # 卡片背景
        'text_primary': '#fafafa',    # 主要文字
        'accent_primary': '#00d4ff',  # 主題色
        'data_positive': '#00ff88',   # 上漲（綠）
        'data_negative': '#ff6b6b',   # 下跌（紅）
        # ... 更多
    }

    LIGHT = {
        'bg_primary': '#f5f7fa',      # 主背景（淺灰）
        'bg_card': '#ffffff',         # 卡片背景（白色）
        'text_primary': '#1a202c',    # 主要文字（深色）
        # ... 更多
    }

    @staticmethod
    def generate_css(theme: str) -> str:
        """生成 CSS 字串，包含所有樣式"""
        colors = Theme.DARK if theme == 'dark' else Theme.LIGHT
        return f"""<style> ... CSS 內容 ... </style>"""
```

#### 使用方式
```python
# 在任何頁面開頭
import streamlit as st
from frontend.theme import Theme

# 初始化主題
if 'theme' not in st.session_state:
    st.session_state.theme = 'dark'

# 應用 CSS
st.markdown(Theme.generate_css(st.session_state.theme), unsafe_allow_html=True)

# 主題切換按鈕
if st.button("☀️" if st.session_state.theme == 'dark' else "🌙"):
    st.session_state.theme = 'light' if st.session_state.theme == 'dark' else 'dark'
    st.rerun()
```

---

### 2. 數據源客戶端

#### FinLab Client (`backend/data_sources/finlab_client.py`)
```python
from backend.data_sources.finlab_client import FinLabClient

client = FinLabClient()

# 獲取所有數據（用於選股）
data = client.get_all_data()
# 包含: price, revenue, income_statement, balance_sheet, 籌碼等

# 獲取單一股票價格
price_df = client.get_price(stock_id='2330')
```

#### Yahoo Finance Client (`backend/data_sources/yahoo_finance_client.py`)
```python
from backend.data_sources.yahoo_finance_client import YahooFinanceClient

client = YahooFinanceClient()

# 獲取國際市場數據
markets = client.get_international_markets()
# 返回: {'美股': {...}, '亞股': {...}}

# 獲取台股指數
taiwan_indices = client.get_taiwan_indices()
```

#### Trading Economics Client (`backend/data_sources/trading_economics_client.py`)
```python
from backend.data_sources.trading_economics_client import TradingEconomicsClient

client = TradingEconomicsClient()

# 獲取經濟日曆（按日期分組）
events = client.get_calendar_by_date(
    country=None,  # 所有國家
    days=14,       # 未來 14 天
    importance_filter=1  # 重要性 ≥ 1
)
# 返回: {'2025-10-28': [event1, event2, ...], '2025-10-29': [...]}

# 生成新聞連結
news_links = TradingEconomicsClient.generate_news_links(event)
# 返回: {'trading_economics': URL, 'google_news': URL, ...}
```

---

### 3. 選股策略系統

#### 策略管理器 (`backend/strategies/strategy_manager.py`)
```python
from backend.strategies.strategy_manager import StrategyManager

manager = StrategyManager()

# 執行單一策略
result = manager.run_strategy('revenue_momentum', data)
# 返回: DataFrame with columns ['stock_id', 'score', 'rank', ...]

# 執行所有策略
results = manager.run_all_strategies(data)
# 返回: {'revenue_momentum': df1, 'low_price_small': df2, ...}

# 獲取策略重疊分析
overlaps = manager.get_stock_appearances(results)
# 返回: DataFrame with columns ['stock_id', 'appearances', 'avg_score', ...]
```

#### 可用策略列表
| 策略 Key | 名稱 | 描述 |
|---------|------|------|
| `revenue_momentum` | 營收動能 | 月營收高成長且持續向上 |
| `low_price_small` | 低價小本 | 小型股營收創新高 |
| `breakout` | 突破整理 | 底部穩固後突破 |
| `inst_buying` | 大戶買超 | 連續量增價漲 |
| `capital_increase` | 大現增 | 現金增資後資金到位 |
| `cash_growth` | 現金累積 | 營業現金流強勁 |

---

### 4. 資料庫 (`backend/database/duckdb_client.py`)

```python
from backend.database.duckdb_client import DuckDBClient

# 使用 context manager
with DuckDBClient() as db:
    # 獲取自選股
    watchlist = db.get_watchlist()

    # 新增自選股
    db.add_to_watchlist(
        stock_id='2330',
        stock_name='台積電',
        buy_price=500.0,
        shares=1000,
        notes='半導體龍頭'
    )

    # 儲存選股結果
    db.upsert_strategy_selection(
        strategy_name='revenue_momentum',
        selection_date=date.today(),
        selections=result_df
    )
```

---

## UI/UX 開發指南

### 修改主題配色

**檔案**: `frontend/theme.py`

#### 步驟 1: 找到對應的顏色變數
```python
# 深色主題
DARK = {
    'accent_primary': '#00d4ff',  # 主題色（藍色）
    'data_positive': '#00ff88',   # 上漲（綠色）
    'data_negative': '#ff6b6b',   # 下跌（紅色）
}
```

#### 步驟 2: 修改顏色值
```python
DARK = {
    'accent_primary': '#ff6b00',  # 改為橘色
    'data_positive': '#4caf50',   # 改為更深的綠
}
```

#### 步驟 3: 重新啟動 Streamlit
```bash
# 按 Ctrl+C 停止
# 重新運行
streamlit run frontend/app.py
```

### 添加新的 CSS 樣式

#### 步驟 1: 在 `generate_css()` 中添加
```python
@staticmethod
def generate_css(theme: str) -> str:
    colors = Theme.DARK if theme == 'dark' else Theme.LIGHT

    return f"""
    <style>
    /* 現有樣式 */
    ...

    /* 新增樣式 */
    .my-custom-card {{
        background: {colors['bg_card']};
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 4px 12px {colors['shadow_md']};
    }}
    </style>
    """
```

#### 步驟 2: 在頁面中使用
```python
st.markdown("""
<div class="my-custom-card">
    <h3>自定義卡片</h3>
    <p>這是一個使用自定義 CSS 的卡片</p>
</div>
""", unsafe_allow_html=True)
```

### 修改經濟日曆時間軸

**檔案**: `frontend/pages/1_🏠_市場總覽.py` (lines 627-722)

#### 修改日期列寬度
```python
# 在 theme.py 中找到:
.timeline-date-column {{
    min-width: 280px;  # 修改為 320px 變更寬
    max-width: 280px;  # 同步修改
}}
```

#### 修改今日高亮顏色
```python
# 在 theme.py 中找到:
.timeline-date-header.today {{
    background: linear-gradient(135deg, #ffd700 0%, #ff9800 100%);
    # 改為其他顏色，例如藍色:
    # background: linear-gradient(135deg, #00d4ff 0%, #0088cc 100%);
}}
```

#### 添加新的新聞來源
```python
# 在 trading_economics_client.py 的 generate_news_links() 中添加:
links['bloomberg'] = f"https://www.bloomberg.com/search?query={encoded_event}"

# 在 市場總覽.py 中添加按鈕:
if 'bloomberg' in news_links:
    links_html += f'''
    <a href="{news_links['bloomberg']}" target="_blank"
       class="timeline-news-link" style="background: #000000;">
        📰 BB
    </a>
    '''
```

---

## 常見開發任務

### 任務 1: 新增一個選股策略

#### 步驟 1: 創建策略文件
```python
# backend/strategies/strategy_dividend.py

from backend.strategies.strategy_base import StrategyBase
import pandas as pd

class DividendStrategy(StrategyBase):
    """高股息策略"""

    def __init__(self):
        super().__init__(
            name="高股息策略",
            description="選擇股息率 > 5% 且連續 5 年發放股息的公司",
            key="high_dividend"
        )

    def screen(self, data: dict) -> pd.DataFrame:
        """篩選邏輯"""
        try:
            # 從 data 中取得需要的資料
            dividend_data = data.get('dividend', pd.DataFrame())

            if dividend_data.empty:
                return pd.DataFrame()

            # 篩選條件
            high_div = dividend_data[dividend_data['yield'] > 5.0]
            # ... 更多邏輯

            # 返回結果
            return high_div[['stock_id', 'score']].reset_index(drop=True)

        except Exception as e:
            print(f"策略執行失敗: {e}")
            return pd.DataFrame()
```

#### 步驟 2: 註冊策略
```python
# backend/strategies/strategy_manager.py

from backend.strategies.strategy_dividend import DividendStrategy

class StrategyManager:
    def __init__(self):
        self.strategies = {
            # 現有策略
            'revenue_momentum': RevenueMomentumStrategy(),
            # ... 其他策略

            # 新增策略
            'high_dividend': DividendStrategy(),  # ⭐ 新增這行
        }
```

#### 步驟 3: 在 UI 中添加選項
```python
# frontend/pages/3_🔍_AI選股.py

selected_strategies = st.multiselect(
    "選擇要執行的策略",
    options=[
        "revenue_momentum",
        # ... 其他策略
        "high_dividend",  # ⭐ 新增這行
    ],
    format_func=lambda x: {
        "revenue_momentum": "營收動能",
        # ... 其他對應
        "high_dividend": "高股息",  # ⭐ 新增這行
    }[x]
)
```

---

### 任務 2: 修改側邊欄內容

**檔案**: `frontend/app.py` (lines 63-97)

```python
with st.sidebar:
    st.image("你的 Logo URL", width='stretch')

    st.markdown("---")

    # 自定義狀態區塊
    st.markdown("### 📊 我的自定義狀態")
    st.info("這是自定義的側邊欄內容")

    # ... 其他內容
```

---

### 任務 3: 添加新的頁面

#### 步驟 1: 創建頁面文件
```python
# frontend/pages/4_📈_回測分析.py

import streamlit as st
from frontend.theme import Theme

# 頁面配置
st.set_page_config(
    page_title="回測分析 - KevinRule",
    page_icon="📈",
    layout="wide"
)

# 主題初始化
if 'theme' not in st.session_state:
    st.session_state.theme = 'dark'

# 應用主題
st.markdown(Theme.generate_css(st.session_state.theme), unsafe_allow_html=True)

# 頁面內容
st.title("📈 回測分析")
st.markdown("這是新增的回測分析頁面")
```

#### 步驟 2: 命名規則
Streamlit 會自動根據檔名生成側邊欄導航：
- 格式: `{順序}_{emoji}_{頁面名稱}.py`
- 範例: `4_📈_回測分析.py`
- 顯示: 📈 回測分析

#### 步驟 3: 重新啟動查看
側邊欄會自動出現新頁面連結！

---

### 任務 4: 修改自選股上限

**檔案**: `backend/database/duckdb_client.py`

```python
def add_to_watchlist(self, ...):
    # 找到這行
    if len(existing) >= 5:  # 修改為 10
        raise ValueError("自選股已達上限（5 檔）")  # 同步修改提示文字
```

**檔案**: `frontend/pages/2_📊_我的持股.py`

```python
# 找到相關提示文字，同步修改
st.warning("自選股上限為 5 檔")  # 改為 10 檔
```

---

## 故障排除

### 問題 1: Port 8501 已被占用

**錯誤訊息**:
```
Port 8501 is already in use
```

**解決方案**:
```bash
# macOS/Linux
lsof -ti:8501 | xargs kill -9

# Windows
netstat -ano | findstr :8501
taskkill /PID <PID> /F
```

---

### 問題 2: 找不到模組

**錯誤訊息**:
```
ModuleNotFoundError: No module named 'backend'
```

**解決方案**:
```bash
# 確保在專案根目錄執行
cd /path/to/KevinRule
streamlit run frontend/app.py

# 如果還是不行，檢查 sys.path
python -c "import sys; print('\n'.join(sys.path))"
```

---

### 問題 3: API Key 無效

**錯誤訊息**:
```
❌ FinLab API 登入失敗
```

**解決方案**:
1. 檢查 `.env` 檔案是否存在
2. 確認 API Key 正確無誤（無多餘空格）
3. 重新啟動 Streamlit

```bash
# 驗證環境變數
python -c "from config.settings import settings; print(settings.finlab_api_key)"
```

---

### 問題 4: 淺色模式顯示異常

**症狀**: 淺色模式下文字看不清楚

**解決方案**:
1. 檢查 `frontend/theme.py` 中的 `LIGHT` 配色
2. 確保 `text_primary` 和 `bg_primary` 有足夠對比度
3. 使用對比度檢查工具：https://webaim.org/resources/contrastchecker/

```python
# 良好的對比度範例
LIGHT = {
    'bg_primary': '#f5f7fa',    # 淺灰背景
    'text_primary': '#1a202c',  # 深色文字
    # 對比度約 12:1（優秀）
}
```

---

### 問題 5: 經濟日曆無數據

**症狀**: 經濟日曆頁面顯示"未獲取到經濟事件"

**解決方案**:
1. 檢查 Trading Economics API Key
2. 確認 API 額度未超限
3. 查看後端日誌

```bash
# 手動測試 API
python backend/data_sources/trading_economics_client.py
```

---

## 最佳實踐

### 1. 代碼風格

#### 使用類型提示
```python
from typing import Dict, List, Optional
import pandas as pd

def get_data(stock_id: str, days: int = 30) -> pd.DataFrame:
    """獲取股票數據"""
    pass

def format_events(events: List[Dict]) -> List[Dict]:
    """格式化事件"""
    pass
```

#### Docstring 規範
```python
def calculate_score(data: pd.DataFrame, weights: Dict[str, float]) -> pd.Series:
    """
    計算股票評分

    Args:
        data: 包含股票數據的 DataFrame
        weights: 各指標權重字典 {'revenue_growth': 0.3, 'profit_margin': 0.2, ...}

    Returns:
        包含每檔股票評分的 Series，index 為 stock_id

    Raises:
        ValueError: 當 data 為空或 weights 總和不為 1 時

    Examples:
        >>> weights = {'revenue_growth': 0.5, 'profit_margin': 0.5}
        >>> scores = calculate_score(df, weights)
    """
    pass
```

---

### 2. 錯誤處理

#### 優雅的錯誤處理
```python
def fetch_data(api_key: str) -> pd.DataFrame:
    try:
        # API 調用
        data = api.get_data(api_key)

        if data is None or data.empty:
            print("⚠️  未獲取到數據")
            return pd.DataFrame()

        return data

    except ConnectionError as e:
        print(f"❌ 網路連線失敗: {e}")
        return pd.DataFrame()

    except Exception as e:
        print(f"❌ 未知錯誤: {e}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame()
```

#### Streamlit 中的錯誤顯示
```python
try:
    result = process_data()
    st.success("✅ 處理成功！")
except ValueError as e:
    st.error(f"❌ 數據驗證失敗: {e}")
except Exception as e:
    st.error(f"❌ 系統錯誤: {e}")
    with st.expander("查看詳細錯誤"):
        st.code(traceback.format_exc())
```

---

### 3. 性能優化

#### 使用 Streamlit 快取
```python
@st.cache_data(ttl=1800)  # 快取 30 分鐘
def load_market_data():
    """載入市場數據"""
    client = YahooFinanceClient()
    return client.get_international_markets()

@st.cache_resource
def get_database_connection():
    """快取資料庫連線（單例）"""
    return DuckDBClient()
```

#### 分批處理大量數據
```python
def process_large_dataframe(df: pd.DataFrame, batch_size: int = 1000):
    """分批處理大型 DataFrame"""
    results = []

    for i in range(0, len(df), batch_size):
        batch = df.iloc[i:i+batch_size]
        result = process_batch(batch)
        results.append(result)

    return pd.concat(results, ignore_index=True)
```

---

### 4. Git 工作流程

#### Commit 訊息規範
```bash
# 格式: <type>(<scope>): <subject>

# Types:
# - feat: 新功能
# - fix: 修復 bug
# - style: UI/樣式調整
# - refactor: 重構
# - docs: 文檔
# - test: 測試

# 範例:
git commit -m "feat(calendar): 新增經濟日曆時間軸佈局"
git commit -m "fix(theme): 修復淺色模式對比度問題"
git commit -m "style(sidebar): 優化側邊欄導航樣式"
git commit -m "docs: 更新開發者指南"
```

#### 分支策略
```bash
# main - 穩定版本
# develop - 開發分支
# feature/xxx - 新功能分支
# fix/xxx - 修復分支

# 開發新功能
git checkout -b feature/high-dividend-strategy
# ... 開發完成
git checkout develop
git merge feature/high-dividend-strategy
git branch -d feature/high-dividend-strategy
```

---

### 5. 測試建議

#### 手動測試檢查清單
- [ ] 深色模式正常顯示
- [ ] 淺色模式正常顯示
- [ ] 主題切換無報錯
- [ ] 所有頁面可正常訪問
- [ ] 側邊欄導航正確
- [ ] API 數據正常載入
- [ ] 錯誤訊息清晰友善
- [ ] 手機瀏覽器顯示正常

#### 單元測試範例
```python
# tests/test_strategies.py
import pytest
from backend.strategies.strategy_revenue import RevenueMomentumStrategy

def test_revenue_strategy():
    strategy = RevenueMomentumStrategy()
    assert strategy.name == "營收動能高於同業平均"

    # 測試空數據
    result = strategy.screen({})
    assert result.empty

    # 測試正常數據
    data = {...}  # 準備測試數據
    result = strategy.screen(data)
    assert not result.empty
    assert 'stock_id' in result.columns
```

---

## 開發工具推薦

### VS Code 擴展
- **Python** - Microsoft
- **Pylance** - 型別檢查
- **Black Formatter** - 代碼格式化
- **GitLens** - Git 增強
- **Streamlit** - Streamlit 語法高亮

### 實用命令

```bash
# 格式化代碼
black frontend/ backend/

# 檢查型別
mypy backend/

# 查看端口占用
lsof -i :8501

# 監控 Streamlit 日誌
streamlit run frontend/app.py --logger.level=debug

# 清除 Streamlit 快取
rm -rf ~/.streamlit/cache
```

---

## 常見問題 FAQ

### Q1: 如何添加新的數據源？
**A**: 在 `backend/data_sources/` 創建新的 client 類，參考現有的 client 實現。

### Q2: 如何更改應用標題和 icon？
**A**: 修改各頁面的 `st.set_page_config()`:
```python
st.set_page_config(
    page_title="我的標題",
    page_icon="🚀",  # 可用 emoji 或圖片路徑
    layout="wide"
)
```

### Q3: 如何部署到雲端？
**A**: 推薦使用 Streamlit Cloud:
1. Push 代碼到 GitHub
2. 訪問 https://share.streamlit.io
3. 連結 GitHub repo
4. 設定環境變數（Settings > Secrets）
5. 部署！

### Q4: 如何備份資料庫？
**A**:
```bash
# DuckDB 是單一檔案資料庫
cp data/kevinrule.duckdb data/backup_$(date +%Y%m%d).duckdb
```

### Q5: 如何貢獻代碼？
**A**:
1. Fork 專案
2. 創建 feature 分支
3. 提交 Pull Request
4. 等待 Code Review

---

## 相關資源

### 官方文檔
- [Streamlit 文檔](https://docs.streamlit.io/)
- [FinLab API 文檔](https://doc.finlab.tw/)
- [Trading Economics API](https://docs.tradingeconomics.com/)
- [Claude AI API](https://docs.anthropic.com/)

### 社群
- [Streamlit 論壇](https://discuss.streamlit.io/)
- [FinLab Discord](https://discord.gg/finlab)

### 學習資源
- [Python Type Hints](https://docs.python.org/3/library/typing.html)
- [Pandas 教學](https://pandas.pydata.org/docs/user_guide/index.html)
- [CSS Flexbox](https://css-tricks.com/snippets/css/a-guide-to-flexbox/)

---

## 聯絡方式

- **GitHub Issues**: https://github.com/AndyKauo/KevinRule/issues
- **Email**: your-email@example.com
- **Discord**: 加入 FinLab 社群

---

## 版本歷史

### v1.1.0 (2025-10-28)
- ✅ 淺色模式 UI 修復
- ✅ 主題切換按鈕優化
- ✅ 經濟日曆時間軸網格佈局
- ✅ 新聞連結整合

### v1.0.0 (2025-10-20)
- 🎉 首次發布
- 6 種選股策略
- 市場總覽
- 自選股追蹤

---

**最後更新**: 2025-10-28
**維護者**: AndyKauo
**許可證**: MIT

---

*祝你開發愉快！如有問題，歡迎提 Issue 或 PR！* 🚀

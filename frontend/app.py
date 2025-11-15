"""
KevinRule - 台股智能選股系統
Streamlit 主應用程式

功能：
- 6 種量化選股策略
- Claude AI 智能分析
- 自選股追蹤
- 回測驗證
"""

import streamlit as st
import sys
import os
import threading
from pathlib import Path

# 添加專案根目錄到 Python 路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.settings import settings
from frontend.theme import Theme, get_theme_toggle_label

# ========== 主題初始化 ==========
if 'theme' not in st.session_state:
    st.session_state.theme = 'dark'  # 預設深色主題

# ========== 頁面配置 ==========

st.set_page_config(
    page_title="KevinRule - 台股智能選股",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========== 應用主題 CSS ==========
st.markdown(Theme.generate_css(st.session_state.theme), unsafe_allow_html=True)

# ========== Idle Auto-Exit（Railway Serverless Sleep）==========

IDLE_TIMEOUT = 600  # 10 分鐘無操作自動退出（秒）

# 全域 idle 計時器（在 Streamlit 多次 rerun 之間共用）
if "idle_timer" not in globals():
    idle_timer = None

def _exit_app():
    """Idle 超時後退出應用，讓 Railway 進入 Sleep 狀態"""
    print("⏰ Idle timeout reached. Exiting app so Railway can scale to zero.")
    os._exit(0)  # 強制結束程式，讓 Railway 把容器關掉

def reset_idle_timer():
    """重置 idle 計時器（每次用戶操作時調用）"""
    global idle_timer
    # 先把舊的 timer 取消，避免多個 timer 同時存在
    if idle_timer is not None:
        idle_timer.cancel()
    idle_timer = threading.Timer(IDLE_TIMEOUT, _exit_app)
    idle_timer.daemon = True
    idle_timer.start()

# 每次 Streamlit rerun（也就是有互動時）都會執行到這裡 → 重新計時
reset_idle_timer()

# ========== 側邊欄導航樣式優化 ==========
st.markdown("""
<style>
/* 優化側邊欄導航樣式 */
[data-testid="stSidebarNav"] {
    padding-top: 1rem;
}

/* 優化導航連結樣式 */
[data-testid="stSidebarNav"] ul {
    padding: 0;
}

[data-testid="stSidebarNav"] a {
    padding: 0.75rem 1rem;
    border-radius: 0.5rem;
    margin-bottom: 0.25rem;
    transition: background-color 0.2s;
}

[data-testid="stSidebarNav"] a:hover {
    background-color: rgba(128, 128, 128, 0.1);
}
</style>
""", unsafe_allow_html=True)

# ========== 主題切換按鈕（右上角）==========
# 使用自定義 CSS 實現固定位置的主題切換
st.markdown("""
<style>
.theme-toggle-container {
    position: fixed;
    top: 1rem;
    right: 3.5rem;
    z-index: 999;
}
</style>
""", unsafe_allow_html=True)

# 創建一個容器來放置主題切換按鈕
col_left, col_right = st.columns([9, 1])
with col_right:
    # 獲取下一個主題的圖標
    next_theme = 'light' if st.session_state.theme == 'dark' else 'dark'
    theme_icon = '☀️' if next_theme == 'light' else '🌙'

    if st.button(theme_icon, key="theme_toggle_top", help=f"切換至{'淺色模式' if next_theme == 'light' else '深色模式'}"):
        st.session_state.theme = next_theme
        st.rerun()

# ========== 側邊欄 ==========

with st.sidebar:
    st.markdown("### 📊 系統狀態")

    # 檢查配置
    is_valid, errors = settings.validate()

    if is_valid:
        st.success("✅ 系統配置完整")
    else:
        st.error("❌ 系統配置不完整")
        for error in errors:
            st.warning(error)

    st.markdown("---")

    st.markdown("### ⚙️ 系統資訊")
    st.info(f"""
    **環境**: {settings.app_env}
    **資料庫**: DuckDB
    **Python**: 3.10+
    **Streamlit**: 1.30+
    """)

# ========== 主內容 ==========

# 標題
st.markdown('<h1 class="main-title">📈 KevinRule 台股智能選股系統</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">基於 FinLab API 的量化選股 + Claude AI 智能分析</p>', unsafe_allow_html=True)

st.markdown("---")

# 歡迎訊息
if not is_valid:
    st.error("""
    ⚠️ **系統配置不完整，請先完成設定！**

    請確認以下步驟：
    1. 複製 `.env.example` 為 `.env`
    2. 填入你的 FinLab API Key
    3. 填入 Claude API Key（選填）
    4. 重新啟動應用

    詳見 README.md 中的「快速開始」章節。
    """)
    st.stop()

# 功能介紹
st.markdown("## 🚀 主要功能")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div class="feature-card">
        <h3>📊 量化選股</h3>
        <p>6 種專業策略</p>
        <p>自動選出優質標的</p>
    </div>
    """, unsafe_allow_html=True)

    if st.button("開始選股 →", key="btn_stock_selection", width='stretch'):
        st.switch_page("pages/3_🔍_AI選股.py")

with col2:
    st.markdown("""
    <div class="feature-card">
        <h3>📈 持股追蹤</h3>
        <p>管理 5 檔自選股</p>
        <p>即時監控表現</p>
    </div>
    """, unsafe_allow_html=True)

    if st.button("我的持股 →", key="btn_my_stocks", width='stretch'):
        st.switch_page("pages/2_📊_我的持股.py")

with col3:
    st.markdown("""
    <div class="feature-card">
        <h3>🏠 市場總覽</h3>
        <p>國際市場動態</p>
        <p>台股指數監控</p>
    </div>
    """, unsafe_allow_html=True)

    if st.button("市場總覽 →", key="btn_market", width='stretch'):
        st.switch_page("pages/1_🏠_市場總覽.py")

st.markdown("---")

# 6 種策略介紹
st.markdown("## 🎯 6 種選股策略")

strategies = [
    {
        "name": "策略 1: 營收動能高於同業平均",
        "description": "選擇月營收 YoY > 20% 且持續成長的股票",
        "icon": "📈",
        "features": ["營收年增率 > 20%", "營收月增率 > 0", "高於產業中位數", "價格 < 150元"]
    },
    {
        "name": "策略 2: 低價小股本營收創一年高",
        "description": "小型成長股，營收創新高",
        "icon": "🚀",
        "features": ["股價 < 100元", "市值 < 100億", "營收創 12 個月新高", "YoY > 15%"]
    },
    {
        "name": "策略 3: 長時間未破底後創新高",
        "description": "底部穩固後突破（VCP 型態）",
        "icon": "📊",
        "features": ["60天未創新低", "創 20 天新高", "波動率收斂", "成交量放大"]
    },
    {
        "name": "策略 4: 連兩日大戶大買超",
        "description": "主力吸籌訊號",
        "icon": "💰",
        "features": ["連續 2 日上漲", "成交量放大 1.5 倍", "融資減少", "漲幅 < 7%"]
    },
    {
        "name": "策略 5: 大現增快繳款結束",
        "description": "現金增資後資金到位",
        "icon": "💵",
        "features": ["股本增加 > 5%", "現金增加 > 20%", "ROE > 10%", "營收成長"]
    },
    {
        "name": "策略 6: 現金快速累積中",
        "description": "營業現金流強勁的高品質公司",
        "icon": "💎",
        "features": ["營業現金流連續為正", "現金連續增加", "自由現金流 > 0", "ROE > 10%"]
    }
]

col1, col2 = st.columns(2)

for i, strategy in enumerate(strategies):
    col = col1 if i % 2 == 0 else col2

    with col:
        with st.expander(f"{strategy['icon']} {strategy['name']}", expanded=False):
            st.markdown(f"**{strategy['description']}**")
            st.markdown("**篩選條件：**")
            for feature in strategy['features']:
                st.markdown(f"- {feature}")

st.markdown("---")

# 快速開始
st.markdown("## 🎬 快速開始")

st.info("""
### 建議使用流程：

1. **📊 查看市場總覽** - 了解當前市場環境
2. **🔍 執行 AI 選股** - 運行 6 種策略找出候選標的
3. **📈 加入我的持股** - 將心儀標的加入追蹤清單（最多 5 檔）
4. **📊 持續監控** - 定期檢視持股表現與新推薦

⚠️ **風險提醒**：
- 過去績效不代表未來報酬
- 建議先紙上交易 1-3 個月
- 設定停損機制（個股 -15%, 組合 -10%）
- 不要投入超過可承受損失的資金
""")

st.markdown("---")

# 系統資訊
st.markdown("## ℹ️ 系統資訊")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown("""
    <div class="metric-card">
        <h3>6</h3>
        <p>選股策略</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="metric-card">
        <h3>5</h3>
        <p>持股追蹤</p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="metric-card">
        <h3>15</h3>
        <p>分析維度</p>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown("""
    <div class="metric-card">
        <h3>AI</h3>
        <p>智能分析</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# 頁腳
st.markdown("""
<div style="text-align: center; color: #666; padding: 2rem 0;">
    <p>KevinRule © 2024 | 僅供學習研究使用，不構成投資建議</p>
    <p>Built with ❤️ using Streamlit + FinLab + Claude AI</p>
</div>
""", unsafe_allow_html=True)

"""
我的持股頁面
管理自選股（最多5檔），追蹤15個分析維度
"""

import streamlit as st
import pandas as pd
import sys
from pathlib import Path
from datetime import datetime

# 添加專案根目錄到路徑
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.database.duckdb_client import DuckDBClient
from backend.data_sources.finlab_client import FinLabClient
from backend.indicators.technical_indicators import get_stock_indicators
from config.settings import settings
from frontend.theme import Theme

# ========== 頁面配置 ==========

st.set_page_config(
    page_title="我的持股 - KevinRule",
    page_icon="📊",
    layout="wide"
)

# ========== 主題初始化 ==========
if 'theme' not in st.session_state:
    st.session_state.theme = 'dark'  # 預設深色主題

# ========== 應用主題 CSS ==========
st.markdown(Theme.generate_css(st.session_state.theme), unsafe_allow_html=True)

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

# ========== 頁面標題 ==========

st.title("📊 我的持股")
st.markdown("追蹤管理最多 5 檔自選股，監控 15 個關鍵指標")
st.markdown("---")

# ========== 載入持股數據 ==========

@st.cache_data(ttl=300)  # 快取5分鐘
def load_watchlist():
    """載入自選股列表"""
    try:
        with DuckDBClient() as db:
            return db.get_watchlist()
    except Exception as e:
        st.error(f"載入持股失敗: {e}")
        return pd.DataFrame()


@st.cache_data(ttl=300)  # 快取5分鐘
def load_stock_analysis(stock_id: str):
    """
    載入個股的完整分析數據

    Args:
        stock_id: 股票代碼

    Returns:
        包含價格、技術指標、基本面的字典
    """
    try:
        client = FinLabClient()

        # 獲取價格數據
        close_df = client.get_close()

        if stock_id not in close_df.columns:
            return None

        stock_prices = close_df[stock_id].dropna()

        if len(stock_prices) < 60:  # 需要至少60天數據
            return None

        # 獲取最新價格
        current_price = float(stock_prices.iloc[-1])

        # 計算技術指標
        indicators = get_stock_indicators(stock_id, stock_prices)

        # 獲取基本面數據
        pe_df = client.get_pe_ratio()
        pb_df = client.get_pb_ratio()
        dividend_yield_df = client.get_dividend_yield()
        roe_df = client.get_fundamental_ratios()['roe']

        # 獲取融資融券數據
        margin_data = client.get_margin_data()

        # 獲取成交量
        volume_df = client.get_volume()

        # 組合所有數據
        analysis = {
            # 當前價格
            'current_price': current_price,

            # 技術指標
            'ma_5': indicators.get('ma_5'),
            'ma_20': indicators.get('ma_20'),
            'ma_60': indicators.get('ma_60'),
            'rsi': indicators.get('rsi'),
            'macd_trend': indicators.get('trend'),

            # 基本面
            'pe': float(pe_df[stock_id].iloc[-1]) if stock_id in pe_df.columns and not pe_df.empty else None,
            'pb': float(pb_df[stock_id].iloc[-1]) if stock_id in pb_df.columns and not pb_df.empty else None,
            'dividend_yield': float(dividend_yield_df[stock_id].iloc[-1] * 100) if stock_id in dividend_yield_df.columns and not dividend_yield_df.empty else None,
            'roe': float(roe_df[stock_id].iloc[-1] * 100) if stock_id in roe_df.columns and not roe_df.empty else None,

            # 籌碼面
            'margin_balance': float(margin_data['margin_balance'][stock_id].iloc[-1]) if stock_id in margin_data['margin_balance'].columns else None,
            'short_balance': float(margin_data['short_balance'][stock_id].iloc[-1]) if stock_id in margin_data['short_balance'].columns else None,
            'volume': float(volume_df[stock_id].iloc[-1]) if stock_id in volume_df.columns else None,
        }

        return analysis

    except Exception as e:
        print(f"❌ 載入 {stock_id} 分析數據失敗: {e}")
        return None


watchlist = load_watchlist()

# ========== 側邊欄 - 新增/刪除股票 ==========

with st.sidebar:
    st.header("⚙️ 持股管理")

    # 當前持股數量
    current_count = len(watchlist)
    st.metric("當前持股", f"{current_count} / 5 檔")

    st.markdown("---")

    # 新增股票
    st.subheader("➕ 新增持股")

    if current_count >= 5:
        st.warning("⚠️ 已達上限（5檔），請先刪除部分持股")
    else:
        with st.form("add_stock_form"):
            new_stock_id = st.text_input("股票代碼", placeholder="例如: 2330")
            new_stock_name = st.text_input("股票名稱", placeholder="例如: 台積電")

            col1, col2 = st.columns(2)
            with col1:
                new_buy_price = st.number_input("買入價格", min_value=0.0, value=0.0, step=0.1)
            with col2:
                new_shares = st.number_input("持股數量", min_value=0, value=0, step=100)

            new_notes = st.text_area("備註", placeholder="投資理由、停損設定等...")

            submit_add = st.form_submit_button("➕ 加入", width='stretch', type="primary")

            if submit_add:
                if not new_stock_id:
                    st.error("請輸入股票代碼")
                elif not new_stock_name:
                    st.error("請輸入股票名稱")
                else:
                    try:
                        with DuckDBClient() as db:
                            db.add_to_watchlist(
                                stock_id=new_stock_id,
                                stock_name=new_stock_name,
                                buy_price=new_buy_price if new_buy_price > 0 else None,
                                shares=new_shares if new_shares > 0 else None,
                                notes=new_notes
                            )
                        st.success(f"✅ 已加入 {new_stock_id} ({new_stock_name})")
                        st.cache_data.clear()
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ 加入失敗: {str(e)}")

    st.markdown("---")

    # 刪除股票
    st.subheader("➖ 刪除持股")

    if current_count == 0:
        st.info("目前無持股")
    else:
        delete_stock = st.selectbox(
            "選擇要刪除的股票",
            watchlist['stock_id'].tolist() if not watchlist.empty else [],
            format_func=lambda x: f"{x} ({watchlist[watchlist['stock_id']==x]['stock_name'].iloc[0]})" if not watchlist.empty else x
        )

        if st.button("🗑️ 刪除", type="secondary", width='stretch'):
            try:
                with DuckDBClient() as db:
                    db.remove_from_watchlist(delete_stock)
                st.success(f"✅ 已刪除 {delete_stock}")
                st.cache_data.clear()
                st.rerun()
            except Exception as e:
                st.error(f"❌ 刪除失敗: {str(e)}")

    st.markdown("---")

    # 刷新按鈕
    if st.button("🔄 刷新數據", width='stretch'):
        st.cache_data.clear()
        st.rerun()

# ========== 主要內容 ==========

if watchlist.empty:
    # 空狀態
    st.info("""
    ### 📋 目前沒有持股

    **如何開始：**
    1. 使用左側側邊欄的「新增持股」功能
    2. 或前往「AI選股」頁面，從推薦結果中加入

    **建議：**
    - 最多追蹤 5 檔股票，保持組合簡潔
    - 記錄買入價格和數量，方便計算損益
    - 定期檢視並更新投資筆記
    """)

else:
    # 顯示持股列表
    st.subheader(f"💼 當前持股 ({len(watchlist)} / 5 檔)")

    # 總覽統計
    total_buy_value = 0
    for _, row in watchlist.iterrows():
        if pd.notna(row['buy_price']) and pd.notna(row['shares']):
            total_buy_value += row['buy_price'] * row['shares']

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("持股檔數", f"{len(watchlist)} 檔")

    with col2:
        st.metric("總投入成本", f"${total_buy_value:,.0f}" if total_buy_value > 0 else "未設定")

    with col3:
        st.metric("加入時間", watchlist['added_date'].max() if 'added_date' in watchlist.columns else "N/A")

    st.markdown("---")

    # 遍歷每一檔股票，顯示詳細資訊
    for idx, stock in watchlist.iterrows():
        stock_id = stock['stock_id']
        stock_name = stock['stock_name']
        buy_price = stock['buy_price'] if pd.notna(stock['buy_price']) else None
        shares = stock['shares'] if pd.notna(stock['shares']) else None
        notes = stock['notes'] if pd.notna(stock['notes']) else ""

        with st.expander(f"**{stock_id} - {stock_name}**", expanded=True):
            # 基本資訊卡片
            st.markdown(f"""
            <div class="stock-card">
                <h3>{stock_id} - {stock_name}</h3>
                <p>買入價格: {f'${buy_price:.2f}' if buy_price else '未設定'} |
                   持股: {f'{shares:,} 股' if shares else '未設定'}</p>
            </div>
            """, unsafe_allow_html=True)

            # Tab 切換
            tab1, tab2, tab3 = st.tabs(["📊 15項分析", "💰 損益計算", "📝 投資筆記"])

            # Tab 1: 15項分析維度
            with tab1:
                st.markdown("### 📊 15 項關鍵分析維度")

                # 載入分析數據
                with st.spinner(f"正在載入 {stock_id} 的分析數據..."):
                    analysis = load_stock_analysis(stock_id)

                if analysis is None:
                    st.warning(f"⚠️ 無法載入 {stock_id} 的分析數據（可能是數據不足或股票代碼錯誤）")
                else:
                    # 分類展示
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.markdown("#### 📈 價值評估")

                        # 本益比
                        pe = analysis.get('pe')
                        st.markdown(f"""
                        <div class="metric-item">
                            <strong>本益比 (PE)</strong><br>
                            <span style="font-size: 1.2rem;">{f'{pe:.2f}' if pe else 'N/A'}</span>
                        </div>
                        """, unsafe_allow_html=True)

                        # 股價淨值比
                        pb = analysis.get('pb')
                        st.markdown(f"""
                        <div class="metric-item">
                            <strong>股價淨值比 (PB)</strong><br>
                            <span style="font-size: 1.2rem;">{f'{pb:.2f}' if pb else 'N/A'}</span>
                        </div>
                        """, unsafe_allow_html=True)

                        # 殖利率
                        div_yield = analysis.get('dividend_yield')
                        st.markdown(f"""
                        <div class="metric-item">
                            <strong>殖利率 (%)</strong><br>
                            <span style="font-size: 1.2rem;">{f'{div_yield:.2f}%' if div_yield else 'N/A'}</span>
                        </div>
                        """, unsafe_allow_html=True)

                        # ROE
                        roe = analysis.get('roe')
                        st.markdown(f"""
                        <div class="metric-item">
                            <strong>ROE (%)</strong><br>
                            <span style="font-size: 1.2rem;">{f'{roe:.2f}%' if roe else 'N/A'}</span>
                        </div>
                        """, unsafe_allow_html=True)

                    with col2:
                        st.markdown("#### 📊 技術指標")

                        # 均線
                        ma5 = analysis.get('ma_5')
                        ma20 = analysis.get('ma_20')
                        ma60 = analysis.get('ma_60')

                        st.markdown(f"""
                        <div class="metric-item">
                            <strong>5日均線</strong><br>
                            <span style="font-size: 1.2rem;">{f'{ma5:.2f}' if ma5 else 'N/A'}</span>
                        </div>
                        <div class="metric-item">
                            <strong>20日均線</strong><br>
                            <span style="font-size: 1.2rem;">{f'{ma20:.2f}' if ma20 else 'N/A'}</span>
                        </div>
                        <div class="metric-item">
                            <strong>60日均線</strong><br>
                            <span style="font-size: 1.2rem;">{f'{ma60:.2f}' if ma60 else 'N/A'}</span>
                        </div>
                        """, unsafe_allow_html=True)

                        # RSI
                        rsi = analysis.get('rsi')
                        st.markdown(f"""
                        <div class="metric-item">
                            <strong>RSI (14日)</strong><br>
                            <span style="font-size: 1.2rem;">{f'{rsi:.2f}' if rsi else 'N/A'}</span>
                        </div>
                        """, unsafe_allow_html=True)

                        # MACD
                        macd_trend = analysis.get('macd_trend')
                        trend_color = '#28a745' if macd_trend == '多頭' else '#dc3545' if macd_trend == '空頭' else '#6c757d'
                        st.markdown(f"""
                        <div class="metric-item">
                            <strong>MACD 訊號</strong><br>
                            <span style="font-size: 1.2rem; color: {trend_color};">{macd_trend or 'N/A'}</span>
                        </div>
                        """, unsafe_allow_html=True)

                    with col3:
                        st.markdown("#### 💵 籌碼面")

                        # 融資餘額
                        margin_balance = analysis.get('margin_balance')
                        st.markdown(f"""
                        <div class="metric-item">
                            <strong>融資餘額 (張)</strong><br>
                            <span style="font-size: 1.2rem;">{f'{int(margin_balance):,}' if margin_balance else 'N/A'}</span>
                        </div>
                        """, unsafe_allow_html=True)

                        # 融券餘額
                        short_balance = analysis.get('short_balance')
                        st.markdown(f"""
                        <div class="metric-item">
                            <strong>融券餘額 (張)</strong><br>
                            <span style="font-size: 1.2rem;">{f'{int(short_balance):,}' if short_balance else 'N/A'}</span>
                        </div>
                        """, unsafe_allow_html=True)

                        # 成交量
                        volume = analysis.get('volume')
                        st.markdown(f"""
                        <div class="metric-item">
                            <strong>成交量 (張)</strong><br>
                            <span style="font-size: 1.2rem;">{f'{int(volume/1000):,}' if volume else 'N/A'}</span>
                        </div>
                        """, unsafe_allow_html=True)

                    st.markdown("---")
                    st.markdown("✅ **數據來源**: FinLab API 即時數據")

            # Tab 2: 損益計算
            with tab2:
                st.markdown("### 💰 損益試算")

                if buy_price and shares:
                    # 獲取當前真實價格
                    with st.spinner(f"正在獲取 {stock_id} 最新價格..."):
                        analysis = load_stock_analysis(stock_id)

                    if analysis and analysis.get('current_price'):
                        current_price = analysis['current_price']
                    else:
                        st.error(f"❌ 無法獲取 {stock_id} 的當前價格")
                        current_price = buy_price  # 使用買入價作為備用

                    buy_value = buy_price * shares
                    current_value = current_price * shares
                    profit = current_value - buy_value
                    profit_pct = (profit / buy_value) * 100

                    col1, col2 = st.columns(2)

                    with col1:
                        st.metric(
                            "買入成本",
                            f"${buy_value:,.0f}",
                            f"{shares:,} 股 @ ${buy_price:.2f}"
                        )

                        st.metric(
                            "當前市值",
                            f"${current_value:,.0f}",
                            f"@ ${current_price:.2f}"
                        )

                    with col2:
                        profit_color = "normal" if profit >= 0 else "inverse"

                        st.metric(
                            "未實現損益",
                            f"${profit:,.0f}",
                            f"{profit_pct:+.2f}%",
                            delta_color=profit_color
                        )

                        # 停損/停利提醒
                        if profit_pct < -15:
                            st.error("⚠️ 已達停損點 (-15%)，建議評估是否出場")
                        elif profit_pct > 30:
                            st.success("🎉 已獲利 30%，可考慮部分獲利了結")

                else:
                    st.info("請設定買入價格和持股數量以計算損益")

            # Tab 3: 投資筆記
            with tab3:
                st.markdown("### 📝 投資筆記")

                if notes:
                    st.markdown(f"""
                    <div class="analysis-section">
                        {notes}
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.info("尚無投資筆記，建議記錄：\n- 買入理由\n- 目標價位\n- 停損設定\n- 定期檢視心得")

                # 編輯筆記（簡化版，實際應該可以直接更新）
                with st.form(f"edit_notes_{stock_id}"):
                    new_notes = st.text_area("更新筆記", value=notes, height=150)

                    if st.form_submit_button("💾 儲存"):
                        st.info("💡 筆記更新功能待實現（需要更新資料庫）")

# ========== 頁腳 ==========

st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 1rem;">
    <p>💡 建議定期檢視持股，適時調整投資組合</p>
</div>
""", unsafe_allow_html=True)

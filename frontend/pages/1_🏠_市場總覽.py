"""
市場總覽頁面
顯示國際市場動態、台股指數、經濟日曆等
"""

import streamlit as st
import pandas as pd
import sys
from pathlib import Path
from datetime import datetime, timedelta

# 添加專案根目錄到路徑
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.data_sources.yfinance_client import YFinanceClient
from backend.data_sources.trading_economics_client import TradingEconomicsClient
from backend.data_sources.finlab_client import FinLabClient
from frontend.theme import Theme

# ========== 頁面配置 ==========

st.set_page_config(
    page_title="市場總覽 - KevinRule",
    page_icon="🏠",
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

st.title("🏠 市場總覽")
st.markdown("掌握國際市場動態與台股關鍵指標")
st.markdown("---")

# ========== 數據載入函數 ==========

@st.cache_data(ttl=300)  # 快取5分鐘
def load_international_data():
    """載入國際市場數據"""
    try:
        client = YFinanceClient()
        return client.get_all_market_data()
    except Exception as e:
        st.error(f"載入國際市場數據失敗: {e}")
        return None

@st.cache_data(ttl=300)  # 快取5分鐘
def load_taiwan_market_data():
    """載入台股市場數據"""
    try:
        yf_client = YFinanceClient()
        finlab_client = FinLabClient()

        # 獲取台股指數（Yahoo Finance）
        tw_indices = yf_client.get_taiwan_indices()

        # 獲取匯率
        usdtwd = yf_client.get_forex('USDTWD')

        # 獲取 FinLab 價格數據（用於計算市場統計）
        close_df = finlab_client.get_close()
        volume_df = finlab_client.get_volume()

        # 獲取融資融券數據
        margin_data = finlab_client.get_margin_data()

        # 獲取三大法人買賣超數據
        institutional_data = finlab_client.get_institutional_investors_trading()

        # 計算市場統計
        market_stats = {}
        if not close_df.empty and len(close_df) >= 2:
            latest_date = close_df.index[-1]
            prev_date = close_df.index[-2]

            latest_prices = close_df.iloc[-1]
            prev_prices = close_df.iloc[-2]

            # 計算漲跌家數
            price_changes = latest_prices - prev_prices
            up_stocks = (price_changes > 0).sum()
            down_stocks = (price_changes < 0).sum()
            flat_stocks = (price_changes == 0).sum()
            total_stocks = len(latest_prices.dropna())

            # 計算成交量統計
            if not volume_df.empty:
                latest_volume = volume_df.iloc[-1]
                total_volume = latest_volume.sum() / 1000  # 轉換為張數

                market_stats = {
                    'up_stocks': int(up_stocks),
                    'down_stocks': int(down_stocks),
                    'flat_stocks': int(flat_stocks),
                    'total_stocks': int(total_stocks),
                    'up_ratio': (up_stocks / total_stocks * 100) if total_stocks > 0 else 0,
                    'down_ratio': (down_stocks / total_stocks * 100) if total_stocks > 0 else 0,
                    'flat_ratio': (flat_stocks / total_stocks * 100) if total_stocks > 0 else 0,
                    'total_volume': float(total_volume) if not pd.isna(total_volume) else 0,
                }

        # 整合融資融券數據
        margin_stats = {}
        if margin_data:
            # 融資餘額
            if 'margin_balance' in margin_data and not margin_data['margin_balance'].empty:
                mb = margin_data['margin_balance'].iloc[-1]
                mb_prev = margin_data['margin_balance'].iloc[-2] if len(margin_data['margin_balance']) > 1 else mb
                margin_stats['margin_balance'] = float(mb.sum())
                margin_stats['margin_balance_change'] = float(mb.sum() - mb_prev.sum())
                margin_stats['margin_balance_change_pct'] = (margin_stats['margin_balance_change'] / mb_prev.sum() * 100) if mb_prev.sum() > 0 else 0

            # 融券餘額
            if 'short_balance' in margin_data and not margin_data['short_balance'].empty:
                sb = margin_data['short_balance'].iloc[-1]
                sb_prev = margin_data['short_balance'].iloc[-2] if len(margin_data['short_balance']) > 1 else sb
                margin_stats['short_balance'] = float(sb.sum())
                margin_stats['short_balance_change'] = float(sb.sum() - sb_prev.sum())
                margin_stats['short_balance_change_pct'] = (margin_stats['short_balance_change'] / sb_prev.sum() * 100) if sb_prev.sum() > 0 else 0

        # 整合三大法人買賣超數據
        institutional_stats = {}
        if institutional_data:
            # 外資買賣超（轉換為張數：股數 / 1000）
            if 'foreign_net' in institutional_data and not institutional_data['foreign_net'].empty:
                fn = institutional_data['foreign_net'].iloc[-1]
                institutional_stats['foreign_net_shares'] = float(fn.sum())
                institutional_stats['foreign_net_lots'] = institutional_stats['foreign_net_shares'] / 1000  # 轉換為張

            # 投信買賣超
            if 'investment_trust_net' in institutional_data and not institutional_data['investment_trust_net'].empty:
                itn = institutional_data['investment_trust_net'].iloc[-1]
                institutional_stats['investment_trust_net_shares'] = float(itn.sum())
                institutional_stats['investment_trust_net_lots'] = institutional_stats['investment_trust_net_shares'] / 1000

            # 自營商買賣超
            if 'dealer_net' in institutional_data and not institutional_data['dealer_net'].empty:
                dn = institutional_data['dealer_net'].iloc[-1]
                institutional_stats['dealer_net_shares'] = float(dn.sum())
                institutional_stats['dealer_net_lots'] = institutional_stats['dealer_net_shares'] / 1000

        return {
            'tw_indices': tw_indices,
            'usdtwd': usdtwd,
            'market_stats': market_stats,
            'margin_stats': margin_stats,
            'institutional_stats': institutional_stats,
            'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

    except Exception as e:
        st.error(f"載入台股市場數據失敗: {e}")
        import traceback
        traceback.print_exc()
        return None

@st.cache_data(ttl=1800)  # 快取30分鐘（經濟日曆變化較慢）
def load_economic_calendar():
    """載入經濟日曆數據"""
    try:
        client = TradingEconomicsClient()

        if not client.enabled:
            return None

        # 獲取按日期分組的經濟事件（用於時間軸顯示）
        events_by_date = client.get_calendar_by_date(
            country=None,  # 所有國家
            days=14,  # 獲取未來兩週
            importance_filter=1  # 顯示所有重要性事件
        )

        return {
            'events_by_date': events_by_date,
            'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

    except Exception as e:
        st.error(f"載入經濟日曆數據失敗: {e}")
        import traceback
        traceback.print_exc()
        return None


# ========== 更新時間 ==========

update_time = datetime.now()
st.info(f"📅 更新時間: {update_time.strftime('%Y-%m-%d %H:%M:%S')}")

# ========== Tab 切換 ==========

tabs = st.tabs([
    "🌍 國際市場",
    "🇹🇼 台灣市場",
    "📅 經濟日曆"
])

# ========== Tab 1: 國際市場 ==========

with tabs[0]:
    st.header("🌍 國際市場參考")

    # 載入數據
    with st.spinner("正在載入國際市場數據..."):
        market_data = load_international_data()

    if market_data is None:
        st.error("❌ 無法載入國際市場數據，請稍後再試")
    else:
        us_indices = market_data.get('us_indices', {})
        crypto = market_data.get('crypto', {})
        asia_markets = market_data.get('asia_markets', {})
        forex = market_data.get('forex', {})

        # 主要美股指數
        st.subheader("📊 美股三大指數")

        col1, col2, col3 = st.columns(3)

        # 道瓊工業指數
        with col1:
            dji = us_indices.get('DJI', {})
            if dji:
                st.metric(
                    "道瓊工業指數",
                    f"{dji['price']:,.2f}",
                    f"{dji['change']:+,.2f} ({dji['change_percent']:+.2f}%)",
                    delta_color="normal"
                )
            else:
                st.metric("道瓊工業指數", "N/A", "無數據")

        # S&P 500
        with col2:
            sp500 = us_indices.get('SP500', {})
            if sp500:
                st.metric(
                    "S&P 500",
                    f"{sp500['price']:,.2f}",
                    f"{sp500['change']:+,.2f} ({sp500['change_percent']:+.2f}%)",
                    delta_color="normal"
                )
            else:
                st.metric("S&P 500", "N/A", "無數據")

        # 那斯達克
        with col3:
            nasdaq = us_indices.get('NASDAQ', {})
            if nasdaq:
                st.metric(
                    "那斯達克",
                    f"{nasdaq['price']:,.2f}",
                    f"{nasdaq['change']:+,.2f} ({nasdaq['change_percent']:+.2f}%)",
                    delta_color="normal"
                )
            else:
                st.metric("那斯達克", "N/A", "無數據")

        st.markdown("---")

        # 費半與VIX
        st.subheader("📈 關鍵指標")

        col1, col2, col3 = st.columns(3)

        # 費城半導體指數
        with col1:
            sox = us_indices.get('SOX', {})
            if sox:
                st.metric(
                    "費城半導體指數",
                    f"{sox['price']:,.2f}",
                    f"{sox['change']:+,.2f} ({sox['change_percent']:+.2f}%)",
                    delta_color="normal"
                )
            else:
                st.metric("費城半導體指數", "N/A", "無數據")

        # VIX 恐慌指數
        with col2:
            vix = us_indices.get('VIX', {})
            if vix:
                st.metric(
                    "VIX 恐慌指數",
                    f"{vix['price']:,.2f}",
                    f"{vix['change']:+,.2f} ({vix['change_percent']:+.2f}%)",
                    delta_color="inverse"  # VIX 下跌是好事
                )
            else:
                st.metric("VIX 恐慌指數", "N/A", "無數據")

        # 美元指數
        with col3:
            dxy = us_indices.get('DXY', {})
            if dxy:
                st.metric(
                    "美元指數",
                    f"{dxy['price']:,.2f}",
                    f"{dxy['change']:+,.2f} ({dxy['change_percent']:+.2f}%)",
                    delta_color="normal"
                )
            else:
                st.metric("美元指數", "N/A", "無數據")

        st.markdown("---")

        # 加密貨幣
        st.subheader("₿ 加密貨幣")

        col1, col2, col3 = st.columns(3)

        # 比特幣
        with col1:
            btc = crypto.get('BTC', {})
            if btc:
                st.metric(
                    "比特幣 (BTC)",
                    f"${btc['price']:,.2f}",
                    f"${btc['change']:+,.2f} ({btc['change_percent']:+.2f}%)",
                    delta_color="normal"
                )
            else:
                st.metric("比特幣 (BTC)", "N/A", "無數據")

        # 以太坊
        with col2:
            eth = crypto.get('ETH', {})
            if eth:
                st.metric(
                    "以太坊 (ETH)",
                    f"${eth['price']:,.2f}",
                    f"${eth['change']:+,.2f} ({eth['change_percent']:+.2f}%)",
                    delta_color="normal"
                )
            else:
                st.metric("以太坊 (ETH)", "N/A", "無數據")

        # 市場情緒（保留為參考數據）
        with col3:
            st.metric(
                "市場情緒",
                "參考數據",
                "需整合 Fear & Greed Index API"
            )

        st.markdown("---")

        # 亞洲市場
        st.subheader("🌏 亞洲市場")

        # 建立亞洲市場數據表格
        asia_data = []

        market_labels = {
            'N225': '日經225',
            'KS11': '韓國綜合',
            'HSI': '香港恆生',
            'SSEC': '上證指數',
            'SZSE': '深證成指'
        }

        for key, label in market_labels.items():
            market = asia_markets.get(key, {})
            if market:
                change_display = f"{market['change']:+,.2f} ({market['change_percent']:+.2f}%)"
                status = '上漲' if market['change'] > 0 else '下跌' if market['change'] < 0 else '持平'
                asia_data.append({
                    '市場': label,
                    '指數': f"{market['price']:,.2f}",
                    '漲跌': change_display,
                    '狀態': status
                })

        if asia_data:
            asia_df = pd.DataFrame(asia_data)
            st.dataframe(
                asia_df,
                width='stretch',
                hide_index=True
            )
        else:
            st.warning("⚠️ 無法載入亞洲市場數據")

        st.markdown("---")

        st.success("""
        ✅ **數據來源**: Yahoo Finance API（即時數據）
        - 國際市場數據每 5 分鐘自動更新
        - 加密貨幣為 24/7 即時報價
        """)

# ========== Tab 2: 台灣市場 ==========

with tabs[1]:
    st.header("🇹🇼 台灣股市")

    # 載入數據
    with st.spinner("正在載入台股市場數據..."):
        tw_market_data = load_taiwan_market_data()

    if tw_market_data is None:
        st.error("❌ 無法載入台股市場數據，請稍後再試")
    else:
        tw_indices = tw_market_data.get('tw_indices', {})
        usdtwd = tw_market_data.get('usdtwd', {})
        market_stats = tw_market_data.get('market_stats', {})
        margin_stats = tw_market_data.get('margin_stats', {})
        institutional_stats = tw_market_data.get('institutional_stats', {})

        # 台股指數
        st.subheader("📊 大盤指數")

        col1, col2, col3, col4 = st.columns(4)

        # 加權指數
        with col1:
            twii = tw_indices.get('TWII', {})
            if twii:
                st.metric(
                    "加權指數",
                    f"{twii['price']:,.2f}",
                    f"{twii['change']:+,.2f} ({twii['change_percent']:+.2f}%)",
                    delta_color="normal"
                )
            else:
                st.metric("加權指數", "N/A", "無數據")

        # 櫃買指數
        with col2:
            two = tw_indices.get('TWO', {})
            if two:
                st.metric(
                    "櫃買指數",
                    f"{two['price']:,.2f}",
                    f"{two['change']:+,.2f} ({two['change_percent']:+.2f}%)",
                    delta_color="normal"
                )
            else:
                st.metric("櫃買指數", "N/A", "無數據")

        # 台灣50
        with col3:
            tw50 = tw_indices.get('0050.TW', {})
            if tw50:
                st.metric(
                    "台灣50",
                    f"{tw50['price']:,.2f}",
                    f"{tw50['change']:+,.2f} ({tw50['change_percent']:+.2f}%)",
                    delta_color="normal"
                )
            else:
                st.metric("台灣50", "N/A", "無數據")

        # 電子指數（暫無數據源）
        with col4:
            st.metric(
                "電子指數",
                "需整合",
                "Yahoo Finance 無此數據"
            )

        st.markdown("---")

        # 籌碼面
        st.subheader("💼 籌碼分析")

        if institutional_stats:
            col1, col2, col3 = st.columns(3)

            # 外資買賣超
            with col1:
                foreign_lots = institutional_stats.get('foreign_net_lots', 0)
                foreign_color = "positive" if foreign_lots > 0 else "negative" if foreign_lots < 0 else ""

                st.markdown(f"""
                <div class="market-card">
                    <h4>外資</h4>
                    <p class="{foreign_color}" style="font-size: 1.5rem;">{foreign_lots:+,.0f} 張</p>
                    <p>{'買超' if foreign_lots > 0 else '賣超' if foreign_lots < 0 else '持平'}</p>
                </div>
                """, unsafe_allow_html=True)

            # 投信買賣超
            with col2:
                it_lots = institutional_stats.get('investment_trust_net_lots', 0)
                it_color = "positive" if it_lots > 0 else "negative" if it_lots < 0 else ""

                st.markdown(f"""
                <div class="market-card">
                    <h4>投信</h4>
                    <p class="{it_color}" style="font-size: 1.5rem;">{it_lots:+,.0f} 張</p>
                    <p>{'買超' if it_lots > 0 else '賣超' if it_lots < 0 else '持平'}</p>
                </div>
                """, unsafe_allow_html=True)

            # 自營商買賣超
            with col3:
                dealer_lots = institutional_stats.get('dealer_net_lots', 0)
                dealer_color = "positive" if dealer_lots > 0 else "negative" if dealer_lots < 0 else ""

                st.markdown(f"""
                <div class="market-card">
                    <h4>自營商</h4>
                    <p class="{dealer_color}" style="font-size: 1.5rem;">{dealer_lots:+,.0f} 張</p>
                    <p>{'買超' if dealer_lots > 0 else '賣超' if dealer_lots < 0 else '持平'}</p>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.warning("⚠️ 無法載入三大法人買賣超數據")

        st.markdown("---")

        # 市場概況
        st.subheader("📈 市場概況")

        if market_stats:
            col1, col2 = st.columns(2)

            with col1:
                total_volume_text = f"{market_stats.get('total_volume', 0):,.0f} 張" if market_stats.get('total_volume', 0) > 0 else "計算中"

                # 融資融券數據
                margin_balance = margin_stats.get('margin_balance', 0)
                margin_change = margin_stats.get('margin_balance_change', 0)
                margin_change_pct = margin_stats.get('margin_balance_change_pct', 0)
                short_balance = margin_stats.get('short_balance', 0)
                short_change = margin_stats.get('short_balance_change', 0)
                short_change_pct = margin_stats.get('short_balance_change_pct', 0)

                margin_text = f"{margin_balance:,.0f} 張 ({margin_change:+,.0f}, {margin_change_pct:+.2f}%)" if margin_balance > 0 else "計算中"
                short_text = f"{short_balance:,.0f} 張 ({short_change:+,.0f}, {short_change_pct:+.2f}%)" if short_balance > 0 else "計算中"

                st.markdown(f"""
                #### 成交統計
                - **總成交量**: {total_volume_text}
                - **總成交筆數**: 需整合 TWSE API
                - **平均成交金額**: 需整合 TWSE API
                - **融資餘額**: {margin_text}
                - **融券餘額**: {short_text}
                """)

            with col2:
                up = market_stats.get('up_stocks', 0)
                down = market_stats.get('down_stocks', 0)
                flat = market_stats.get('flat_stocks', 0)
                up_ratio = market_stats.get('up_ratio', 0)
                down_ratio = market_stats.get('down_ratio', 0)
                flat_ratio = market_stats.get('flat_ratio', 0)

                st.markdown(f"""
                #### 漲跌家數
                - **上漲**: {up} 家 ({up_ratio:.1f}%)
                - **下跌**: {down} 家 ({down_ratio:.1f}%)
                - **平盤**: {flat} 家 ({flat_ratio:.1f}%)
                - **漲停**: 需整合漲跌停數據
                - **跌停**: 需整合漲跌停數據
                """)
        else:
            st.warning("⚠️ 無法載入市場統計數據")

        st.markdown("---")

        # 匯率與利率
        st.subheader("💱 匯率與利率")

        col1, col2, col3 = st.columns(3)

        # 台幣兌美元（使用 Yahoo Finance 數據）
        with col1:
            if usdtwd:
                # 注意：Yahoo Finance 的 TWD=X 是美元對台幣的價格
                st.metric(
                    "美元兌台幣",
                    f"{usdtwd['price']:.3f}",
                    f"{usdtwd['change']:+.3f} ({usdtwd['change_percent']:+.2f}%)",
                    delta_color="normal"
                )
            else:
                st.metric("美元兌台幣", "N/A", "無數據")

        # 重貼現率（參考值，需手動更新）
        with col2:
            st.metric(
                "重貼現率（參考）",
                "2.000%",
                "央行最新利率"
            )
            st.caption("💡 需手動更新或整合央行 API")

        # 10年公債殖利率（參考值，需手動更新）
        with col3:
            st.metric(
                "10年公債殖利率（參考）",
                "1.450%",
                "財政部最新數據"
            )
            st.caption("💡 需手動更新或整合財政部 API")

        st.markdown("---")

        st.success("""
        ✅ **數據來源**:
        - 台股指數: Yahoo Finance API（即時數據）
        - 市場統計: FinLab API（收盤價、成交量計算）
        - 三大法人買賣超: FinLab API（真實交易數據）
        - 融資融券: FinLab API（真實餘額數據）
        - 匯率: Yahoo Finance API（即時數據）
        - 利率: 參考值（需手動更新）

        **📌 待整合項目**:
        - 漲跌停家數（需檢查 FinLab API）
        - 電子指數（Yahoo Finance 無此數據）
        - 央行重貼現率自動更新（需央行 API）
        - 公債殖利率自動更新（需財政部 API）
        """)


# ========== Tab 3: 經濟日曆 ==========

with tabs[2]:
    st.header("📅 經濟日曆時間軸")

    # 載入數據
    with st.spinner("正在載入經濟日曆數據..."):
        calendar_data = load_economic_calendar()

    if calendar_data is None:
        st.warning("⚠️ 無法載入經濟日曆數據，請確認 TRADING_ECONOMICS_API_KEY 已正確設定")
        st.info("""
        **💡 設定步驟**：
        1. 在 `.env` 文件中設定 `TRADING_ECONOMICS_API_KEY`
        2. 重新啟動 Streamlit 應用
        """)
    else:
        events_by_date = calendar_data.get('events_by_date', {})

        if not events_by_date:
            st.info("未來兩週暫無重要經濟事件")
        else:
            from backend.data_sources.trading_economics_client import TradingEconomicsClient

            # 計算總事件數（過濾前）
            original_days = len(events_by_date)
            original_events = sum(len(events) for events in events_by_date.values())

            # 過濾器選項
            col_filter1, col_filter2, col_filter3 = st.columns([2, 2, 3])

            with col_filter1:
                importance_filter = st.multiselect(
                    "重要性篩選",
                    options=["⭐⭐⭐ 高", "⭐⭐ 中", "⭐ 低"],
                    default=["⭐⭐⭐ 高", "⭐⭐ 中", "⭐ 低"],
                    key="importance_filter"
                )

            with col_filter2:
                show_past = st.checkbox("顯示已過事件", value=False, key="show_past")

            with col_filter3:
                # 先顯示原始統計，稍後會更新為過濾後的統計
                stats_placeholder = st.empty()

            # 準備表格數據
            table_data = []
            today = datetime.now().strftime('%Y-%m-%d')
            now = datetime.now()

            importance_map = {"⭐⭐⭐ 高": 3, "⭐⭐ 中": 2, "⭐ 低": 1}
            allowed_levels = {importance_map[f] for f in importance_filter}

            for date_str, events in events_by_date.items():
                for event in events:
                    importance_level = event.get('importance_level', 1)

                    # 應用重要性篩選
                    if importance_level not in allowed_levels:
                        continue

                    # 判斷是否已過
                    try:
                        event_datetime_str = f"{date_str} {event.get('時間', '00:00')}"
                        event_datetime = datetime.strptime(event_datetime_str, '%Y-%m-%d %H:%M')
                        is_past = event_datetime < now
                    except:
                        is_past = False

                    # 應用已過事件篩選
                    if is_past and not show_past:
                        continue

                    # 格式化日期顯示
                    try:
                        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                        weekday = date_obj.strftime('%a')
                        if date_str == today:
                            date_display = f"📅 今天 ({weekday})"
                        else:
                            date_display = f"{date_str} ({weekday})"
                    except:
                        date_display = date_str

                    # 生成新聞連結（優先使用 Investing.com 事件連結）
                    links_display = ""
                    event_url = event.get('event_url', '')

                    if event_url:
                        # 如果有 Investing.com 事件連結，優先使用
                        links_display = f"[🔍詳情]({event_url})"
                    else:
                        # 回退到 Google 新聞搜尋
                        news_links = TradingEconomicsClient.generate_news_links(event)
                        if news_links:
                            link_parts = []
                            for source, url in news_links.items():
                                if source == 'google_news':
                                    link_parts.append(f"[🔍GN]({url})")
                                elif source == 'cnyes':
                                    link_parts.append(f"[📰鉅亨]({url})")
                                elif source == 'ctee':
                                    link_parts.append(f"[📰工商]({url})")
                            links_display = " ".join(link_parts)

                    table_data.append({
                        "日期": date_display,
                        "時間": event.get('時間', '-'),
                        "事件": event.get('事件', 'N/A'),
                        "⭐": event.get('重要性', '⭐'),
                        "預期": event.get('預期', '-'),
                        "前值": event.get('前值', '-'),
                        "實際": event.get('實際', '-'),
                        "新聞": links_display,
                        "_importance": importance_level,  # 隱藏欄位用於排序
                        "_is_past": is_past  # 隱藏欄位用於樣式
                    })

            # 計算過濾後的統計數據
            if table_data:
                filtered_days = len(set(row["日期"] for row in table_data))
                filtered_events = len(table_data)
            else:
                filtered_days = 0
                filtered_events = 0

            # 更新統計顯示
            with stats_placeholder:
                if filtered_events < original_events:
                    # 有過濾時，顯示對比
                    st.info(f"📊 API 返回: {original_days} 天 {original_events} 個事件 | 顯示: {filtered_days} 天 {filtered_events} 個事件")
                else:
                    # 無過濾時，只顯示總數
                    st.info(f"📊 共 {original_days} 天 {original_events} 個事件")

            if not table_data:
                st.warning("⚠️ 沒有符合篩選條件的事件，請調整篩選器")
            else:
                # 顯示表格
                st.markdown("### 📊 經濟事件總覽")

                # 按日期和時間排序
                table_data_sorted = sorted(table_data, key=lambda x: (x["日期"], x["時間"]))

                # 分組顯示（按日期）
                current_date = None
                for row in table_data_sorted:
                    row_date = row["日期"]

                    # 日期標題（sticky header風格）
                    if row_date != current_date:
                        current_date = row_date
                        is_today_row = "今天" in row_date

                        if is_today_row:
                            st.markdown(f'<div class="economic-calendar-today"><h4 style="margin: 0;">🌟 {row_date}</h4></div>', unsafe_allow_html=True)
                        else:
                            st.markdown(f'<div class="economic-calendar-date"><h4 style="margin: 0;">📅 {row_date}</h4></div>', unsafe_allow_html=True)

                    # 事件行（根據重要性使用不同樣式）
                    importance = row["_importance"]
                    is_past = row["_is_past"]

                    # 根據重要性選擇 CSS class
                    if importance >= 3:
                        css_class = "event-high-importance"
                    elif importance == 2:
                        css_class = "event-medium-importance"
                    else:
                        css_class = "event-low-importance"

                    # 建立事件行
                    with st.container():
                        st.markdown(f'<div class="{css_class}">', unsafe_allow_html=True)

                        col1, col2, col3, col4, col5, col6 = st.columns([1, 5, 1, 1.5, 1.5, 2])

                        with col1:
                            st.caption(row["時間"])

                        with col2:
                            # 根據重要性顯示不同顏色和樣式
                            event_name = row["事件"]
                            if importance >= 3:
                                st.markdown(f"**{event_name}** 🔴")
                            elif importance == 2:
                                st.write(event_name)
                            else:
                                st.markdown(f"<span style='opacity: 0.7'>{event_name}</span>", unsafe_allow_html=True)

                        with col3:
                            st.caption(row["⭐"])

                        with col4:
                            forecast_val = row['預期']
                            st.caption(f"預: {forecast_val}")

                        with col5:
                            previous_val = row['前值']
                            st.caption(f"前: {previous_val}")

                        with col6:
                            if row["新聞"]:
                                st.markdown(row["新聞"], unsafe_allow_html=False)

                        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("---")

        st.success(f"""
        ✅ **數據來源**: Trading Economics API
        - 時間軸顯示未來兩週經濟事件
        - 橫向滾動查看所有日期
        - 點擊新聞連結查看詳細報導
        - 更新時間: {calendar_data.get('updated_at', 'N/A')}
        """)

# ========== 頁腳 ==========

st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 1rem;">
    <p>📊 數據僅供參考，投資決策請自行判斷</p>
</div>
""", unsafe_allow_html=True)

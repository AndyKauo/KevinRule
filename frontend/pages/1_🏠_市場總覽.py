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
            st.info(f"💡 橫向滾動查看所有日期的事件  |  共 {len(events_by_date)} 天 {sum(len(events) for events in events_by_date.values())} 個事件")

            # 使用 Streamlit columns 實現橫向布局（簡化 HTML 結構）
            from backend.data_sources.trading_economics_client import TradingEconomicsClient

            # 創建橫向滾動容器
            st.markdown('<div style="overflow-x: auto; white-space: nowrap; padding: 1rem 0;">', unsafe_allow_html=True)

            today = datetime.now().strftime('%Y-%m-%d')

            # 使用 Streamlit columns（最多顯示 14 天）
            date_list = list(events_by_date.items())

            # 為每個日期創建列
            cols = st.columns(len(date_list))

            for idx, (date_str, events) in enumerate(date_list):
                with cols[idx]:
                    # 判斷是否為今天
                    is_today = date_str == today

                    # 格式化日期顯示
                    try:
                        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                        weekday = date_obj.strftime('%a')
                        if is_today:
                            display_date = f"<b>今天</b><br>{date_str}<br>({weekday})"
                        else:
                            display_date = f"{date_str}<br>({weekday})"
                    except:
                        display_date = date_str

                    # 日期標題顏色（今天用金色，其他用藍色）
                    header_bg = "linear-gradient(135deg, #ffd700 0%, #ff9800 100%)" if is_today else "linear-gradient(135deg, #00d4ff 0%, #0088cc 100%)"

                    # 構建日期列 HTML（簡化版：3 層嵌套 + 全內聯樣式）
                    date_html = f'''
                    <div style="min-width: 260px; max-width: 260px; background: #262730; border-radius: 12px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.2); margin-bottom: 1rem;">
                        <div style="background: {header_bg}; color: white; padding: 0.8rem; text-align: center; font-weight: 600; font-size: 0.95rem;">
                            {display_date}
                        </div>
                        <div style="padding: 0.75rem; background: #1a1d24; min-height: 200px;">
                    '''

                    # 事件卡片
                    for event in events:
                        importance_level = event.get('importance_level', 1)

                        # 高重要性事件使用紅色邊框
                        border_color = "#ff6b6b" if importance_level >= 3 else "#00d4ff"
                        border_width = "4px" if importance_level >= 3 else "3px"

                        # 生成新聞連結（簡化版：內聯樣式）
                        news_links = TradingEconomicsClient.generate_news_links(event)
                        links_html = ''

                        if news_links:
                            links_html = '<div style="display: flex; gap: 0.3rem; margin-top: 0.5rem; flex-wrap: wrap;">'
                            if 'trading_economics' in news_links:
                                links_html += f'<a href="{news_links["trading_economics"]}" target="_blank" style="background: #0066ff; color: white; padding: 3px 8px; border-radius: 3px; font-size: 0.7rem; text-decoration: none; display: inline-block;">📊 TE</a>'
                            if 'google_news' in news_links:
                                links_html += f'<a href="{news_links["google_news"]}" target="_blank" style="background: #34a853; color: white; padding: 3px 8px; border-radius: 3px; font-size: 0.7rem; text-decoration: none; display: inline-block;">🔍 GN</a>'
                            if 'cnyes' in news_links:
                                links_html += f'<a href="{news_links["cnyes"]}" target="_blank" style="background: #ff9800; color: white; padding: 3px 8px; border-radius: 3px; font-size: 0.7rem; text-decoration: none; display: inline-block;">📰 鉅亨</a>'
                            if 'ctee' in news_links:
                                links_html += f'<a href="{news_links["ctee"]}" target="_blank" style="background: #e91e63; color: white; padding: 3px 8px; border-radius: 3px; font-size: 0.7rem; text-decoration: none; display: inline-block;">📰 工商</a>'
                            links_html += '</div>'

                        # 事件卡片 HTML（簡化：減少嵌套）
                        date_html += f'''
                        <div style="background: #262730; padding: 0.8rem; border-radius: 6px; border-left: {border_width} solid {border_color}; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 0.5rem;">
                            <div style="font-size: 0.9rem; font-weight: 600; color: #fafafa; margin-bottom: 0.4rem; line-height: 1.3;">{event.get('事件', 'N/A')}</div>
                            <div style="font-size: 0.8rem; color: #a0aec0; margin-bottom: 0.3rem;">⏰ {event.get('時間', 'N/A')}</div>
                            <div style="display: flex; justify-content: space-between; align-items: center; font-size: 0.75rem; color: #cbd5e0; margin-top: 0.4rem;">
                                <span style="font-size: 0.9rem;">{event.get('重要性', '⭐')}</span>
                                <span style="font-size: 0.75rem; color: #a0aec0;">預: {event.get('預期', '-')}</span>
                            </div>
                            {links_html}
                        </div>
                        '''

                    # 結束日期列
                    date_html += '</div></div>'

                    # 渲染單個日期列
                    st.markdown(date_html, unsafe_allow_html=True)

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

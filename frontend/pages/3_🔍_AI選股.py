"""
AI選股頁面
執行6個量化策略，展示選股結果
"""

import streamlit as st
import pandas as pd
import sys
from pathlib import Path
import traceback
from datetime import datetime

# 添加專案根目錄到路徑
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.data_sources.finlab_client import FinLabClient
from backend.strategies.strategy_manager import StrategyManager
from backend.database.duckdb_client import DuckDBClient
from config.settings import settings
from frontend.theme import Theme

# ========== 頁面配置 ==========

st.set_page_config(
    page_title="AI選股 - KevinRule",
    page_icon="🔍",
    layout="wide"
)

# ========== 主題初始化 ==========
if 'theme' not in st.session_state:
    st.session_state.theme = 'dark'  # 預設深色主題

# ========== 應用主題 CSS ==========
st.markdown(Theme.generate_css(st.session_state.theme), unsafe_allow_html=True)

# ========== 初始化 Session State ==========

if 'data_loaded' not in st.session_state:
    st.session_state.data_loaded = False
    st.session_state.data = None
    st.session_state.results = None
    st.session_state.last_update = None

# ========== 頁面標題 ==========

st.title("🔍 AI 智能選股")
st.markdown("執行 6 種量化策略，找出優質投資標的")
st.markdown("---")

# ========== 側邊欄控制 ==========

with st.sidebar:
    st.header("⚙️ 選股設定")

    # 策略選擇
    st.subheader("策略選擇")

    all_strategies = st.checkbox("執行所有策略", value=True)

    if not all_strategies:
        selected_strategies = st.multiselect(
            "選擇要執行的策略",
            options=[
                "revenue_momentum",
                "low_price_small",
                "breakout",
                "inst_buying",
                "capital_increase",
                "cash_growth"
            ],
            default=["revenue_momentum", "breakout"],
            format_func=lambda x: {
                "revenue_momentum": "營收動能",
                "low_price_small": "低價小本",
                "breakout": "突破整理",
                "inst_buying": "大戶買超",
                "capital_increase": "大現增",
                "cash_growth": "現金累積"
            }[x]
        )
    else:
        selected_strategies = [
            "revenue_momentum",
            "low_price_small",
            "breakout",
            "inst_buying",
            "capital_increase",
            "cash_growth"
        ]

    st.markdown("---")

    # 進階設定
    st.subheader("進階設定")

    top_n = st.slider("每個策略顯示前 N 名", 5, 30, 10)

    save_to_db = st.checkbox("保存結果到資料庫", value=True)

    st.markdown("---")

    # 執行按鈕
    run_button = st.button("🚀 開始選股", type="primary", width='stretch')

    if st.session_state.data_loaded:
        st.success(f"✅ 數據已載入")
        if st.session_state.last_update:
            st.info(f"更新時間: {st.session_state.last_update.strftime('%Y-%m-%d %H:%M')}")

    # 清除快取
    if st.button("🔄 重新載入數據", width='stretch'):
        st.session_state.data_loaded = False
        st.session_state.data = None
        st.session_state.results = None
        st.rerun()

# ========== 主要內容 ==========

# 檢查配置
is_valid, errors = settings.validate()
if not is_valid:
    st.error("❌ 系統配置不完整，請先完成設定！")
    for error in errors:
        st.warning(error)
    st.stop()

# 執行選股
if run_button:
    try:
        # 進度條
        progress_bar = st.progress(0)
        status_text = st.empty()

        # Step 1: 載入數據
        status_text.text("📊 正在載入 FinLab 數據...")
        progress_bar.progress(10)

        if not st.session_state.data_loaded:
            with st.spinner("連接 FinLab API..."):
                client = FinLabClient()
                st.session_state.data = client.get_all_data()
                st.session_state.data_loaded = True
                st.session_state.last_update = datetime.now()

        progress_bar.progress(30)
        status_text.text("✅ 數據載入完成")

        # Step 2: 執行策略
        status_text.text("🎯 正在執行選股策略...")
        progress_bar.progress(40)

        manager = StrategyManager()

        results = {}
        strategy_progress = 0
        strategy_count = len(selected_strategies)

        for i, strategy_key in enumerate(selected_strategies):
            status_text.text(f"🔄 執行策略 {i+1}/{strategy_count}: {manager.get_strategy(strategy_key).name}")

            try:
                result = manager.run_strategy(strategy_key, st.session_state.data)
                results[strategy_key] = result

                # 保存到資料庫
                if save_to_db and not result.empty:
                    with DuckDBClient() as db:
                        db.upsert_strategy_selection(
                            strategy_name=strategy_key,
                            selection_date=datetime.now().date(),
                            selections=result
                        )

            except Exception as e:
                st.error(f"策略 {strategy_key} 執行失敗: {str(e)}")
                results[strategy_key] = pd.DataFrame()

            # 更新進度
            strategy_progress = 40 + int((i + 1) / strategy_count * 50)
            progress_bar.progress(strategy_progress)

        st.session_state.results = results

        # Step 3: 完成
        progress_bar.progress(100)
        status_text.text("✅ 所有策略執行完成！")

        st.success("🎉 選股完成！")

    except Exception as e:
        st.error(f"❌ 執行過程發生錯誤: {str(e)}")
        st.code(traceback.format_exc())
        st.stop()

# ========== 顯示結果 ==========

if st.session_state.results:
    results = st.session_state.results
    manager = StrategyManager()

    st.markdown("---")
    st.header("📊 選股結果")

    # 總覽統計
    col1, col2, col3, col4 = st.columns(4)

    total_selections = sum(len(df) for df in results.values() if not df.empty)
    strategies_with_results = sum(1 for df in results.values() if not df.empty)

    with col1:
        st.markdown(f"""
        <div class="metric-box">
            <h3>{strategies_with_results}</h3>
            <p>策略有結果</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="metric-box">
            <h3>{total_selections}</h3>
            <p>推薦股票總數</p>
        </div>
        """, unsafe_allow_html=True)

    # 計算策略重疊
    stock_appearances = manager.get_stock_appearances(results)

    if not stock_appearances.empty:
        max_appearances = stock_appearances['appearances'].max()
        overlapping_stocks = len(stock_appearances[stock_appearances['appearances'] > 1])

        with col3:
            st.markdown(f"""
            <div class="metric-box">
                <h3>{overlapping_stocks}</h3>
                <p>多策略推薦</p>
            </div>
            """, unsafe_allow_html=True)

        with col4:
            st.markdown(f"""
            <div class="metric-box">
                <h3>{max_appearances}</h3>
                <p>最高重疊數</p>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")

    # Tab 切換
    tabs = st.tabs([
        "🎯 策略重疊分析",
        "📋 各策略詳細結果",
        "📊 綜合排名"
    ])

    # Tab 1: 策略重疊分析
    with tabs[0]:
        st.subheader("🎯 多策略推薦股票（高信心度）")

        if not stock_appearances.empty:
            # 篩選多策略推薦
            multi_strategy = stock_appearances[stock_appearances['appearances'] > 1].copy()

            if not multi_strategy.empty:
                st.info(f"✨ 找到 {len(multi_strategy)} 檔被多個策略推薦的股票，這些標的可能更值得關注！")

                # 顯示表格
                st.dataframe(
                    multi_strategy,
                    width='stretch',
                    column_config={
                        "stock_id": st.column_config.TextColumn("股票代碼", width="small"),
                        "appearances": st.column_config.NumberColumn("推薦次數", width="small"),
                        "avg_score": st.column_config.NumberColumn("平均評分", format="%.2f", width="small"),
                        "strategies_list": st.column_config.TextColumn("推薦策略", width="large")
                    },
                    hide_index=True
                )

                # 加入自選功能
                st.markdown("---")
                st.subheader("💼 加入自選股")

                selected_stock = st.selectbox(
                    "選擇要加入自選的股票",
                    multi_strategy['stock_id'].tolist()
                )

                col1, col2 = st.columns(2)

                with col1:
                    buy_price = st.number_input("買入價格", min_value=0.0, value=0.0, step=0.1)

                with col2:
                    shares = st.number_input("持股數量", min_value=0, value=0, step=100)

                notes = st.text_area("備註", placeholder="投資理由、停損設定等...")

                if st.button("➕ 加入自選股", type="primary"):
                    try:
                        with DuckDBClient() as db:
                            db.add_to_watchlist(
                                stock_id=selected_stock,
                                stock_name=selected_stock,  # TODO: 從數據中獲取股票名稱
                                buy_price=buy_price if buy_price > 0 else None,
                                shares=shares if shares > 0 else None,
                                notes=notes
                            )
                        st.success(f"✅ 已將 {selected_stock} 加入自選股！")
                    except Exception as e:
                        st.error(f"❌ 加入失敗: {str(e)}")
            else:
                st.warning("⚠️ 目前沒有被多個策略同時推薦的股票")
        else:
            st.warning("⚠️ 無選股結果")

    # Tab 2: 各策略詳細結果
    with tabs[1]:
        st.subheader("📋 各策略選股詳情")

        for strategy_key, result_df in results.items():
            if result_df.empty:
                continue

            strategy = manager.get_strategy(strategy_key)

            with st.expander(f"**{strategy.name}** - 選出 {len(result_df)} 檔股票", expanded=False):
                st.markdown(f"_{strategy.description}_")

                # 顯示前N名
                display_df = result_df.head(top_n)

                st.dataframe(
                    display_df,
                    width='stretch',
                    column_config={
                        "stock_id": st.column_config.TextColumn("代碼"),
                        "score": st.column_config.NumberColumn("評分", format="%.2f"),
                        "rank": st.column_config.NumberColumn("排名"),
                    },
                    hide_index=True
                )

                # 下載按鈕
                csv = result_df.to_csv(index=False, encoding='utf-8-sig')
                st.download_button(
                    label="📥 下載完整結果 (CSV)",
                    data=csv,
                    file_name=f"{strategy_key}_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )

    # Tab 3: 綜合排名
    with tabs[2]:
        st.subheader("📊 所有推薦股票綜合排名")

        if not stock_appearances.empty:
            st.info("💡 排序依據：推薦次數（高→低）→ 平均評分（高→低）")

            st.dataframe(
                stock_appearances,
                width='stretch',
                column_config={
                    "stock_id": st.column_config.TextColumn("股票代碼"),
                    "appearances": st.column_config.NumberColumn("推薦次數"),
                    "avg_score": st.column_config.NumberColumn("平均評分", format="%.2f"),
                    "strategies_list": st.column_config.TextColumn("推薦策略")
                },
                hide_index=True
            )

            # 下載按鈕
            csv = stock_appearances.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="📥 下載綜合結果 (CSV)",
                data=csv,
                file_name=f"all_strategies_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
        else:
            st.warning("⚠️ 無選股結果")

else:
    # 提示信息
    st.info("""
    ### 👋 歡迎使用 AI 智能選股！

    **使用步驟：**
    1. 📝 在左側側邊欄選擇要執行的策略
    2. ⚙️ 調整顯示數量等設定
    3. 🚀 點擊「開始選股」按鈕
    4. ⏳ 等待數據載入和策略執行（首次約需 2-5 分鐘）
    5. 📊 查看選股結果並加入自選股

    **策略說明：**
    - **營收動能**: 月營收高成長且持續向上
    - **低價小本**: 小型股營收創新高（彈性大）
    - **突破整理**: 底部穩固後突破（技術面）
    - **大戶買超**: 連續量增價漲（籌碼面）
    - **大現增**: 現金增資後資金到位
    - **現金累積**: 營業現金流強勁（高品質）

    💡 **建議**: 優先關注被多個策略同時推薦的股票！
    """)

# ========== 頁腳 ==========

st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 1rem;">
    <p>⚠️ 本系統僅供參考，不構成投資建議。投資有風險，請謹慎評估。</p>
</div>
""", unsafe_allow_html=True)

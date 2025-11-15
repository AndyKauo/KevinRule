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
from backend.strategies.original.strategy_manager_original import StrategyManagerOriginal
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

# ========== 數據加載函數（使用 Streamlit Cache）==========

@st.cache_data(ttl=86400, show_spinner=False)  # 1天緩存，FinLab 數據日更
def load_strategy_data(data_keys: tuple, progress_callback=None) -> dict:
    """
    按需加載策略所需數據（使用 Streamlit 緩存）

    Args:
        data_keys: 需要載入的數據鍵集合（tuple 可 hashable）
        progress_callback: 進度回調函數

    Returns:
        包含請求數據的字典
    """
    client = FinLabClient(progress_callback=progress_callback)
    return client.get_data_bundle(set(data_keys))

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

# ========== 初始化 Session State ==========

# 注意：不再使用 session_state 存儲大數據
# 數據通過 @st.cache_data 管理，自動緩存和清理

if 'results' not in st.session_state:
    st.session_state.results = None

if 'strategy_engine' not in st.session_state:
    st.session_state.strategy_engine = '學術優化版'

# ========== 頁面標題 ==========

st.title("🔍 AI 智能選股")
st.markdown("執行 6 種量化策略，找出優質投資標的")

# ========== 策略引擎選擇器 ==========

col1, col2 = st.columns([3, 1])

with col1:
    st.markdown("### 選擇策略引擎")

    # 引擎選擇器
    engine_choice = st.radio(
        "請選擇要使用的策略引擎版本：",
        ["🎓 學術優化版", "📋 原始 Kevin 版"],
        horizontal=True,
        key="engine_selector"
    )

    # 更新 session state
    if engine_choice == "🎓 學術優化版":
        st.session_state.strategy_engine = "學術優化版"
        engine_description = "基於量化金融研究優化的策略，使用進階技術指標和評分系統"
    else:
        st.session_state.strategy_engine = "原始 Kevin 版"
        engine_description = "嚴格按照 Kevin 原始 Excel 需求實作，保留原始選股邏輯"

    st.info(f"ℹ️ **{st.session_state.strategy_engine}**: {engine_description}")

with col2:
    st.write("")  # 佔位，保持對齊

# 版本對比 - 使用可摺疊的 expander（預設摺疊，不佔用空間）
with st.expander("🔄 雙引擎版本對比", expanded=False):
    comparison_data = pd.DataFrame({
        '項目': [
            '數據來源',
            '策略數量',
            '實作方式',
            '評分系統',
            '篩選條件',
            '適用場景',
            '數據完整性',
            '推薦對象'
        ],
        '🎓 學術優化版': [
            'FinLab API',
            '6 個核心策略',
            '學術研究優化，使用進階指標',
            '標準化評分 + 多因子加權',
            '彈性篩選，使用可用數據',
            '適合量化交易、自動化選股',
            '✅ 完整實作（使用可用數據）',
            '量化投資者、程式交易者'
        ],
        '📋 原始 Kevin 版': [
            'FinLab API',
            '6 個核心策略',
            '嚴格按照 Excel 原始需求',
            '標準化評分（與 Excel 一致）',
            '嚴格條件（部分數據缺失）',
            '貼近人工選股邏輯',
            '⚠️ 部分條件缺失（標記 TODO）',
            '個人投資者、原始邏輯驗證'
        ]
    })

    st.table(comparison_data)

    st.warning("""
    ⚠️ **原始 Kevin 版數據限制說明**：
    - 部分 Excel 需求的數據在 FinLab API 中不可用（如：券商買超、現增繳款日期）
    - 這些條件已使用間接指標替代，並在策略執行時顯示警告
    - 詳細數據限制請參考：`docs/MISSING_DATA_REPORT.md`
    """)

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

    # 清除快取（清除 Streamlit cache 和結果）
    if st.button("🔄 重新載入數據", width='stretch'):
        st.cache_data.clear()
        st.session_state.results = None
        st.success("✅ 緩存已清除")
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

        # Step 1: 準備策略管理器並計算所需數據鍵
        progress_bar.progress(5)
        status_text.text("🔍 分析策略數據需求...")

        # 根據選擇的引擎初始化對應的策略管理器
        if st.session_state.strategy_engine == "學術優化版":
            manager = StrategyManager()
            engine_label = "🎓 學術優化版"
        else:
            manager = StrategyManagerOriginal()
            engine_label = "📋 原始 Kevin 版"

        st.info(f"使用引擎: {engine_label}")

        # 計算所有選中策略需要的數據鍵
        required_keys = set()
        for strategy_key in selected_strategies:
            if hasattr(manager, 'get_strategy'):
                strategy = manager.get_strategy(strategy_key)
            else:
                # StrategyManagerOriginal 使用 strategies 字典
                strategy = manager.strategies[strategy_key]

            # 獲取策略需要的數據鍵
            if hasattr(strategy, 'get_required_data_keys'):
                required_keys.update(strategy.get_required_data_keys())
            # Kevin 原始版策略沒有 get_required_data_keys，使用 required_data_keys 屬性
            elif hasattr(strategy, 'required_data_keys'):
                from backend.strategies.base_strategy import StrategyBase
                required_keys.update(StrategyBase.BASE_REQUIRED_KEYS)
                required_keys.update(strategy.required_data_keys)

        st.info(f"📊 需要載入 {len(required_keys)} 個數據字段")

        # Step 2: 載入數據（使用緩存）
        progress_bar.progress(15)
        status_text.text("📊 正在載入 FinLab 數據...")

        with st.status("📊 載入策略數據中...", expanded=True) as loading_status:
            progress_messages = []

            # 定義進度回調函數
            def update_progress(message):
                """接收 FinLabClient 的進度訊息並顯示在 UI"""
                progress_messages.append(message)
                st.write(message)

            # 使用緩存函數加載數據（tuple 可 hashable）
            data = load_strategy_data(tuple(sorted(required_keys)), update_progress)

            loading_status.update(
                label=f"✅ 數據載入完成 (共 {len(required_keys)} 個字段)",
                state="complete"
            )

        progress_bar.progress(30)
        status_text.text("✅ 數據載入完成")

        # Step 3: 執行策略
        status_text.text("🎯 正在執行選股策略...")
        progress_bar.progress(40)

        results = {}
        strategy_progress = 0
        strategy_count = len(selected_strategies)

        for i, strategy_key in enumerate(selected_strategies):
            # 獲取策略名稱（兩個管理器接口略有不同）
            if hasattr(manager, 'get_strategy'):
                strategy_name = manager.get_strategy(strategy_key).name
            else:
                # StrategyManagerOriginal 使用 strategies 字典
                strategy_name = manager.strategies[strategy_key].strategy_name

            status_text.text(f"🔄 執行策略 {i+1}/{strategy_count}: {strategy_name}")

            try:
                result = manager.run_strategy(strategy_key, data)
                # 使用 copy() 避免引用問題：防止 upsert 修改原 DataFrame
                results[strategy_key] = result.copy() if not result.empty else result

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

    # 根據執行時選擇的引擎，使用對應的 manager
    if st.session_state.strategy_engine == "學術優化版":
        manager = StrategyManager()
    else:
        manager = StrategyManagerOriginal()

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

            # 獲取策略對象（兩個 manager 接口不同）
            if hasattr(manager, 'get_strategy'):
                strategy = manager.get_strategy(strategy_key)
                strategy_name = strategy.name
                strategy_description = strategy.description
            else:
                # StrategyManagerOriginal 使用 strategies 字典
                strategy = manager.strategies[strategy_key]
                strategy_name = strategy.strategy_name
                strategy_description = strategy.description

            with st.expander(f"**{strategy_name}** - 選出 {len(result_df)} 檔股票", expanded=False):
                st.markdown(f"_{strategy_description}_")

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

# ========== 策略詳細說明區塊 ==========

st.markdown("---")
st.markdown("## 📚 策略詳細說明")

# 顯示當前引擎標籤
if st.session_state.strategy_engine == "學術優化版":
    st.markdown("深入了解每種策略的選股邏輯、使用指標和計算方法")
    st.info("ℹ️ 當前顯示：**🎓 學術優化版** 策略說明")
else:
    st.markdown("Kevin 原始 Excel 需求的策略說明，標記數據限制和替代方案")
    st.info("ℹ️ 當前顯示：**📋 原始 Kevin 版** 策略說明")
    st.success("""
    ✅ **實作狀態**：6 個策略中 **4 個已完全實現** Excel 原始需求
    - 策略 1, 2, 3, 6：✅ 所有條件完整實現
    - 策略 4, 5：⚠️ 使用間接指標替代（券商買超、繳款日期）
    - 詳細報告：`docs/MISSING_DATA_REPORT.md`
    """)

strategy_tabs = st.tabs([
    "策略 1: 營收動能",
    "策略 2: 低價小本",
    "策略 3: 突破整理",
    "策略 4: 大戶買超",
    "策略 5: 大現增",
    "策略 6: 現金累積"
])

# === Tab 1: 營收動能 ===
with strategy_tabs[0]:
    if st.session_state.strategy_engine == "學術優化版":
        # 學術優化版文檔
        st.subheader("📈 策略 1: 營收動能高於同業平均")

        st.markdown("### 🎯 使用指標")
        st.markdown("""
        - **月營收年增率 (YoY)**: 當月營收相比去年同月的成長率
        - **月營收月增率 (MoM)**: 當月營收相比上月的成長率
        - **營收動能趨勢**: 近3個月YoY的線性回歸斜率
        - **產業中位數**: 同產業股票的YoY中位數
        - **股價**: 當前收盤價
        """)
    else:
        # 原始 Kevin 版文檔
        st.subheader("📋 策略 1: 營收動能高於同業平均（Kevin 原始版）")

        st.markdown("### 📝 Excel 原始需求")
        st.markdown("""
        - 月營收年增率 > 20%
        - 月營收月增率 > 20%
        - 營收動能高於同業平均
        - 連續兩季 EPS 成長
        - 收盤價 < 100 元
        """)

        st.success("✅ **完整實作**：此策略所需數據全部可用，已完整實現 Excel 需求")

        st.markdown("### 🎯 當前實作指標")
        st.markdown("""
        - **月營收年增率 (YoY)**: 當月營收相比去年同月的成長率
        - **月營收月增率 (MoM)**: 當月營收相比上月的成長率
        - **股價**: 當前收盤價
        """)

    st.markdown("### 🔍 篩選條件")
    conditions = pd.DataFrame({
        '條件': [
            '1. 營收年增率 > 20%',
            '2. 營收月增率 > 0',
            '3. 近3個月YoY呈上升趨勢',
            '4. YoY高於產業中位數',
            '5. 股價 < 150元',
            '6. 基本篩選（流動性、市值等）'
        ],
        '說明': [
            '營收高成長',
            '持續成長中',
            '動能加速',
            '優於同業',
            '避免高價股',
            '排除問題股、確保流動性'
        ]
    })
    st.table(conditions)

    st.markdown("### 🧮 計算方法")
    formulas = pd.DataFrame({
        '指標': ['YoY', 'MoM', '趨勢'],
        '計算公式': [
            '(當月營收 - 去年同月營收) / 去年同月營收',
            '(當月營收 - 上月營收) / 上月營收',
            '近3個月YoY數據的線性回歸斜率'
        ],
        '數據來源': ['月營收', '月營收', '月營收']
    })
    st.table(formulas)

    st.markdown("### 📊 評分公式")
    st.code("""
綜合評分 = 60% × YoY標準化分數
         + 20% × MoM標準化分數
         + 20% × 趨勢分數
    """)

    st.markdown("### 💡 投資邏輯")
    st.info("""
    **適合投資人**: 成長型投資者

    **策略特點**:
    - ✅ 捕捉業績高成長的公司
    - ✅ 動能加速代表成長趨勢延續
    - ✅ 高於同業表示競爭力強

    **風險提示**:
    - ⚠️ 高成長不一定持續
    - ⚠️ 需注意營收品質（毛利率、獲利能力）
    - ⚠️ 建議搭配基本面分析
    """)

# === Tab 2: 低價小本 ===
with strategy_tabs[1]:
    if st.session_state.strategy_engine == "學術優化版":
        # 學術優化版文檔
        st.subheader("🚀 策略 2: 低價小股本營收創一年高")

        st.markdown("### 🎯 使用指標")
        st.markdown("""
        - **股價**: 當前收盤價
        - **市值**: 公司總市值
        - **當月營收**: 最新公布的月營收
        - **近12個月營收**: 過去一年的月營收數據
        - **營收年增率 (YoY)**: 營收成長率
        """)
    else:
        # 原始 Kevin 版文檔
        st.subheader("📋 策略 2: 低價小股本營收創一年高（Kevin 原始版）")

        st.markdown("### 📝 Excel 原始需求")
        st.markdown("""
        - 收盤價 < 20 元
        - 月營收創 12 個月新高
        - 普通股股本 < 20 億（仟元）
        """)

        st.success("✅ **完整實作**：此策略所需數據全部可用，已完整實現 Excel 需求")

        st.markdown("### 🎯 使用指標")
        st.markdown("""
        - **股價**: 當前收盤價
        - **月營收**: 最新公布的月營收
        - **12 個月營收歷史**: 用於判斷新高
        - **普通股股本**: 公司股本規模
        - **ROE**: 股東權益報酬率（額外品質篩選）
        """)

    st.markdown("### 🔍 篩選條件")
    conditions = pd.DataFrame({
        '條件': [
            '1. 股價 < 100元',
            '2. 市值 < 100億',
            '3. 當月營收創12個月新高',
            '4. 營收YoY > 15%',
            '5. 市值 > 10億',
            '6. 流動性篩選（前60%）'
        ],
        '說明': [
            '低價股，易吸引散戶',
            '小型股，彈性大',
            '業績突破',
            '持續成長',
            '避免過小公司',
            '確保足夠流動性'
        ]
    })
    st.table(conditions)

    st.markdown("### 🧮 計算方法")
    formulas = pd.DataFrame({
        '指標': ['營收比率', '市值（億）', 'YoY'],
        '計算公式': [
            '當月營收 / 近12個月平均營收',
            '市值 / 1億',
            '(當月營收 - 去年同月) / 去年同月'
        ],
        '用途': ['衡量營收突破程度', '判斷公司規模', '成長率指標']
    })
    st.table(formulas)

    st.markdown("### 📊 評分公式")
    st.code("""
綜合評分 = 40% × 營收新高程度（標準化）
         + 30% × YoY（標準化）
         + 30% × 小市值偏好（負向標準化）
    """)

    st.markdown("### 💡 投資邏輯")
    st.info("""
    **適合投資人**: 積極型投資者

    **策略特點**:
    - ✅ 小型股業績轉機，潛在報酬高
    - ✅ 營收創新高代表業務突破
    - ✅ 低價股易形成主升段

    **風險提示**:
    - ⚠️ 波動性大，需設停損
    - ⚠️ 流動性相對較差
    - ⚠️ 建議分散投資，控制單一持股比例
    """)

# === Tab 3: 突破整理 ===
with strategy_tabs[2]:
    if st.session_state.strategy_engine == "學術優化版":
        # 學術優化版文檔
        st.subheader("📊 策略 3: 長時間未破底後創新高")

        st.markdown("### 🎯 使用指標")
        st.markdown("""
        - **60天最低價**: 過去60個交易日的最低價
        - **20天最高價**: 過去20個交易日的最高價
        - **波動率**: 股價的標準差除以均值
        - **成交量**: 5日均量 vs 20日均量
        - **相對強度**: 20日報酬率
        """)
    else:
        # 原始 Kevin 版文檔
        st.subheader("📋 策略 3: 長時間未破底後創新高（Kevin 原始版）")

        st.markdown("### 📝 Excel 原始需求")
        st.markdown("""
        - 90 天未破底（最低點在前 40 天）
        - 盤整區間漲幅 < 25%
        - ROE > 25% **OR** 連續三年現金股利 > 2元
        - 收盤價 < 20 元
        - 月營收創 36 個月新高
        - 普通股股本 < 20 億
        - 成交量 > 20 日均量 × 2.5 倍
        """)

        st.success("✅ **完整實作**：所有數據可用，包含 ROE 和股利數據，已完整實現 Excel 需求")

        st.info("""
        📌 **基本面篩選邏輯**：
        - 使用 **ROE > 25%** 或 **連續三年股利 > 2元** 二選一（符合 Excel 的 OR 條件）
        - 盤整區間計算：從 90 天最低價到當前價格的漲幅 < 25%
        """)

        st.markdown("### 🎯 當前實作指標")
        st.markdown("""
        - **90 天 / 40 天最低價**: 判斷底部形成
        - **20 天新高**: 突破訊號
        - **盤整區間漲幅**: 從 90 天最低到當前
        - **成交量比率**: 相對 20 日均量
        - **36 個月營收**: 營收歷史數據
        - **ROE**: 股東權益報酬率
        """)

    st.markdown("### 🔍 篩選條件")
    conditions = pd.DataFrame({
        '條件': [
            '1. 60天最低點在前40天',
            '2. 創20天新高',
            '3. 20天波動 < 60天波動',
            '4. 5日均量 > 20日均量 × 1.2',
            '5. 20日漲幅 > 0',
            '6. 20 < 股價 < 300元'
        ],
        '說明': [
            '底部穩固',
            '突破整理',
            '波動收斂',
            '成交量放大',
            '相對強勢',
            '價格合理'
        ]
    })
    st.table(conditions)

    st.markdown("### 🧮 計算方法")
    formulas = pd.DataFrame({
        '指標': ['波動率', '遠離低點', '接近高點', '量能放大'],
        '計算公式': [
            '標準差 / 均值',
            '(當前價 - 60天最低) / 60天最低',
            '(當前價 - 20天最高) / 20天最高',
            '5日均量 / 20日均量'
        ],
        '說明': ['衡量價格波動程度', '距離底部距離', '突破確認程度', '量能強度']
    })
    st.table(formulas)

    st.markdown("### 📊 評分公式")
    st.code("""
綜合評分 = 25% × 遠離低點（標準化）
         + 20% × 接近高點（負向，越近越好）
         + 20% × 波動收斂（負向）
         + 20% × 量能放大（標準化）
         + 15% × 相對強度（標準化）
    """)

    st.markdown("### 💡 投資邏輯")
    st.info("""
    **適合投資人**: 波段操作者

    **策略特點**:
    - ✅ 類似 VCP (Volatility Contraction Pattern) 型態
    - ✅ 長時間整理代表籌碼穩定
    - ✅ 突破配合量增，買盤進場確認

    **風險提示**:
    - ⚠️ 假突破風險，需注意量價配合
    - ⚠️ 建議設置停損於突破點下方
    - ⚠️ 適合中短線操作，不建議長期持有
    """)

# === Tab 4: 大戶買超 ===
with strategy_tabs[3]:
    if st.session_state.strategy_engine == "學術優化版":
        # 學術優化版文檔
        st.subheader("💰 策略 4: 連兩日大戶大買超")

        st.markdown("### 🎯 使用指標")
        st.markdown("""
        - **連續2日收盤價**: 今天、昨天、前天的收盤價
        - **連續2日成交量**: 最近2日的成交量
        - **20日平均成交量**: 過去20日的平均成交量
        - **融資餘額**: 連續2日的融資餘額變化
        - **單日漲幅**: 每日的漲跌幅度
        """)
    else:
        # 原始 Kevin 版文檔
        st.subheader("📋 策略 4: 連兩日大戶大買超（Kevin 原始版）")

        st.markdown("### 📝 Excel 原始需求")
        st.markdown("""
        - ⚠️ **[數據缺失]** 近兩日關鍵券商合計買超占成交量 > 10%
        - 連續兩季每股稅後淨利（元）成長
        - 收盤價 < 70 元
        """)

        st.markdown("### ⚠️ 數據限制與替代方案")
        limitations = pd.DataFrame({
            '條件': ['券商買超數據'],
            '狀態': ['❌ 數據缺失'],
            '替代方案': ['使用間接指標：連續2日價格上漲 + 成交量放大 + 融資減少']
        })
        st.table(limitations)

        st.markdown("### 🎯 當前實作指標（間接訊號）")
        st.markdown("""
        - **連續 2 日價格上漲**: 代表買盤力道
        - **連續 2 日成交量 > 1.5 倍**: 成交量放大
        - **連續 2 日融資減少**: 主力非融資買進
        - **價格 < 70 元**: 價格條件
        """)

    st.markdown("### 🔍 篩選條件")
    conditions = pd.DataFrame({
        '條件': [
            '1. 連續2日上漲',
            '2. 連續2日量 > 20日均量 × 1.5',
            '3. 連續2日融資減少',
            '4. 單日漲幅 < 7%',
            '5. 20 < 股價 < 200元',
            '6. 當日量 > 市場中位數'
        ],
        '說明': [
            '價格趨勢向上',
            '成交量大幅放大',
            '散戶賣、主力接',
            '避免追漲停',
            '價格合理範圍',
            '活躍度足夠'
        ]
    })
    st.table(conditions)

    st.markdown("### 🧮 計算方法")
    formulas = pd.DataFrame({
        '指標': ['量能倍數', '2日累積漲幅', '融資變化率'],
        '計算公式': [
            '(今日量 + 昨日量) / 2 / 20日均量',
            '(今日收盤 / 前天收盤) - 1',
            '(今日融資 - 前天融資) / 前天融資'
        ],
        '說明': ['平均放大倍數', '2日總漲幅', '融資增減比例']
    })
    st.table(formulas)

    st.markdown("### 📊 評分公式")
    st.code("""
綜合評分 = 40% × 成交量放大倍數（標準化）
         + 30% × 2日累積漲幅（標準化）
         + 30% × 融資減少程度（負向標準化）
    """)

    st.markdown("### 💡 投資邏輯")
    st.info("""
    **適合投資人**: 短線操作者

    **策略特點**:
    - ✅ 量增價漲 + 融資減 = 主力吸籌訊號
    - ✅ 連續2日確認，非單日異常
    - ✅ 適合捕捉短期強勢股

    **風險提示**:
    - ⚠️ 需快速反應，不宜遲疑
    - ⚠️ 避免追高，注意漲幅限制
    - ⚠️ 建議當日或隔日進場，不要拖太久

    **注意**:
    此策略使用間接指標（量價、融資）推測主力行為，
    並非真實的法人買賣超數據。
    """)

# === Tab 5: 大現增 ===
with strategy_tabs[4]:
    if st.session_state.strategy_engine == "學術優化版":
        # 學術優化版文檔
        st.subheader("💵 策略 5: 大現增快繳款結束")

        st.markdown("### 🎯 使用指標")
        st.markdown("""
        - **普通股股本**: 公司的股本總額（季度數據）
        - **現金及約當現金**: 公司持有的現金（季度數據）
        - **ROE**: 股東權益報酬率
        - **營收年增率**: 營收成長率
        - **現金/股本比**: 現金充裕程度
        """)
    else:
        # 原始 Kevin 版文檔
        st.subheader("📋 策略 5: 大現增快繳款結束（Kevin 原始版）")

        st.markdown("### 📝 Excel 原始需求")
        st.markdown("""
        - ⚠️ **[數據缺失]** 現增繳款日期離今天 < 2 天
        - 現增比率 > 5%
        """)

        st.markdown("### ⚠️ 數據限制與替代方案")
        limitations = pd.DataFrame({
            '條件': ['現增繳款日期'],
            '狀態': ['❌ 數據缺失'],
            '替代方案': [
                '使用間接指標：近期（3期內）股本增加>5% + 現金增加>20%'
            ]
        })
        st.table(limitations)

        st.warning("📌 **無法精確判斷繳款日 < 2 天**，改用近期股本和現金增加作為替代訊號")

        st.markdown("### 🎯 當前實作指標（間接訊號）")
        st.markdown("""
        - **近期股本增加**: 3 期內最大增幅 > 5%
        - **近期現金增加**: 3 期內最大增幅 > 20%
        - **ROE > 10%**: 確保品質
        - **營收年增率 > 0%**: 成長篩選
        """)

    st.markdown("### 🔍 篩選條件")
    conditions = pd.DataFrame({
        '條件': [
            '1. 股本增加 > 5%',
            '2. 現金增加 > 20%',
            '3. ROE > 10%',
            '4. 營收YoY > 0',
            '5. 20 < 股價 < 150元',
            '6. 現金/股本 > 30%'
        ],
        '說明': [
            '可能是現金增資',
            '繳款完成',
            '基本面良好',
            '營收成長',
            '價格合理',
            '現金充裕'
        ]
    })
    st.table(conditions)

    st.markdown("### 🧮 計算方法")
    formulas = pd.DataFrame({
        '指標': ['股本增加率', '現金增加率', '現金占股本比'],
        '計算公式': [
            '(當季股本 - 上季股本) / 上季股本',
            '(當季現金 - 上季現金) / 上季現金',
            '當季現金（仟元） / 當季股本（仟元）'
        ],
        '數據來源': ['財務報表', '財務報表', '財務報表']
    })
    st.table(formulas)

    st.markdown("### 📊 評分公式")
    st.code("""
綜合評分 = 30% × 現金增加率（標準化）
         + 20% × 股本增加率（標準化）
         + 25% × ROE（標準化）
         + 25% × 營收成長率（標準化）
    """)

    st.markdown("### 💡 投資邏輯")
    st.info("""
    **適合投資人**: 中線投資者

    **策略特點**:
    - ✅ 現增繳款後，股價壓力解除
    - ✅ 公司取得資金，有擴張計畫
    - ✅ 適合中線布局

    **風險提示**:
    - ⚠️ 現增稀釋股權，需評估用途
    - ⚠️ 建議查證公司公告，確認現增用途
    - ⚠️ 注意是否為財務困難而現增

    **重要提醒**:
    此策略使用間接指標（股本+現金變化）判斷，
    建議手動查證公開資訊觀測站的現增公告，
    確認繳款狀態和資金用途。
    """)

# === Tab 6: 現金累積 ===
with strategy_tabs[5]:
    if st.session_state.strategy_engine == "學術優化版":
        # 學術優化版文檔
        st.subheader("💎 策略 6: 現金快速累積中")

        st.markdown("### 🎯 使用指標")
        st.markdown("""
        - **營業現金流 (OCF)**: Operating Cash Flow，本業賺錢能力
        - **投資現金流 (ICF)**: Investing Cash Flow，資本支出
        - **融資現金流 (FCF_financing)**: Financing Cash Flow，借貸情況
        - **自由現金流 (FCF)**: Free Cash Flow = OCF + ICF
        - **現金及約當現金**: 公司持有的現金
        - **總資產**: 公司的資產總額
        - **ROE**: 股東權益報酬率
        """)
    else:
        # 原始 Kevin 版文檔
        st.subheader("📋 策略 6: 現金快速累積中（Kevin 原始版）")

        st.markdown("### 📝 Excel 原始需求")
        st.markdown("""
        - 連續四季現金及約當現金增加 > 5%
        - 月營收月增率 (MoM) > 20%
        - 連續兩季每股稅後淨利（元）成長
        """)

        st.success("✅ **完整實作**：此策略所需數據全部可用，已完整實現 Excel 需求")

        st.info("""
        📌 **實作邏輯說明**：
        - 連續四季現金增加：使用 **QoQ（環比）** 判斷，相比上一季增加 > 5%
        - 原因：Excel 原文「連續四季」強調連續性，QoQ 才能判斷連續趨勢
        """)

        st.markdown("### 🎯 當前實作指標")
        st.markdown("""
        - **連續 4 期現金增加**: 簡化判斷，相比上一期 > 5%
        - **月營收月增率 (MoM)**: > 20%
        - **OCF > 0**: 確保現金流品質
        - **ROE > 10%**: 確保獲利能力
        """)

    st.markdown("### 🔍 篩選條件")
    conditions = pd.DataFrame({
        '條件': [
            '1. 營業現金流連續3期 > 0',
            '2. 現金連續2期增加',
            '3. 自由現金流 > 0',
            '4. 融資現金流 < 營業現金流',
            '5. 現金年增長率 > 20%',
            '6. OCF/總資產 > 5%',
            '7. ROE > 10%'
        ],
        '說明': [
            '持續造血',
            '現金累積中',
            '有資金餘裕',
            '不過度依賴融資',
            '快速累積',
            '現金品質高',
            '獲利能力良好'
        ]
    })
    st.table(conditions)

    st.markdown("### 🧮 計算方法")
    formulas = pd.DataFrame({
        '指標': ['自由現金流', '現金年增長率', 'OCF/資產比'],
        '計算公式': [
            '營業現金流 + 投資現金流',
            '(當期現金 - 去年同期) / 去年同期',
            '營業現金流 / 總資產'
        ],
        '說明': ['扣除資本支出後的現金', '現金累積速度', '現金流品質指標']
    })
    st.table(formulas)

    st.markdown("### 📊 評分公式")
    st.code("""
綜合評分 = 30% × 營業現金流（標準化）
         + 25% × 現金年增長率（標準化）
         + 20% × 自由現金流（標準化）
         + 15% × OCF/資產比（標準化）
         + 10% × ROE（標準化）
    """)

    st.markdown("### 💡 投資邏輯")
    st.info("""
    **適合投資人**: 價值投資者、長期投資者

    **策略特點**:
    - ✅ 現金持續增加 = 賺錢能力強
    - ✅ 不靠融資 = 本業賺錢，非財務操作
    - ✅ 抗風險能力強，有擴張本錢
    - ✅ 可能配發高股息

    **風險提示**:
    - ⚠️ 現金多不代表股價一定漲
    - ⚠️ 需注意現金用途（投資、配息、購併）
    - ⚠️ 建議搭配本益比、殖利率評估

    **財務指標說明**:
    - **OCF**: 營業活動產生的現金，越多越好
    - **ICF**: 投資活動現金流出，通常為負（買設備、投資）
    - **FCF**: 扣除必要投資後的自由現金，最重要指標
    - **OCF/資產**: 衡量資產運用效率創造現金的能力
    """)

st.markdown("---")

# ========== 頁腳 ==========

st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 1rem;">
    <p>⚠️ 本系統僅供參考，不構成投資建議。投資有風險，請謹慎評估。</p>
</div>
""", unsafe_allow_html=True)

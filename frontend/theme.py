"""
KevinRule 主題配色系統
Theme Color System for KevinRule

提供深色（專業金融風）和淺色主題
"""

from typing import Dict, Any


class Theme:
    """主題配色類"""

    # ========== 深色主題（專業金融風格 - 類似 Bloomberg Terminal） ==========
    DARK = {
        # 背景色（更暗，降低亮度）
        'bg_primary': '#000000',        # 主背景（純黑）
        'bg_secondary': '#0a0a0a',      # 次要背景（接近黑）
        'bg_card': '#111111',           # 卡片背景（深灰黑）
        'bg_sidebar': '#050505',        # 側邊欄背景（極深灰）
        'bg_header': '#0a0a0a',         # 頭部背景

        # 前景色（文字 - 降低亮度）
        'text_primary': '#b8bcc4',      # 主要文字（中等灰，更柔和）
        'text_secondary': '#7a8088',    # 次要文字（暗灰）
        'text_muted': '#555555',        # 弱化文字（更暗）
        'text_inverse': '#ffffff',      # 反色文字（用於亮色背景）

        # 強調色（降低飽和度和亮度）
        'accent_primary': '#0055cc',    # 主強調色（更暗的藍）
        'accent_secondary': '#0088dd',  # 次要強調色
        'accent_gold': '#cc8800',       # 金色（更暗）

        # 數據色（金融專用 - 降低亮度）
        'data_positive': '#00a043',     # 上漲/正值（更暗的綠）
        'data_negative': '#cc3333',     # 下跌/負值（更暗的紅）
        'data_neutral': '#7a8088',      # 持平/中性（灰）
        'data_warning': '#cc9900',      # 警告（暗黃）

        # 邊框和分隔線（更暗）
        'border_light': '#1a1a1a',      # 淺邊框
        'border_medium': '#222222',     # 中等邊框
        'border_heavy': '#333333',      # 重邊框

        # 陰影（更深）
        'shadow_sm': 'rgba(0, 0, 0, 0.5)',
        'shadow_md': 'rgba(0, 0, 0, 0.7)',
        'shadow_lg': 'rgba(0, 0, 0, 0.9)',

        # 特殊效果（降低亮度）
        'glow_blue': 'rgba(0, 85, 204, 0.2)',
        'glow_gold': 'rgba(204, 136, 0, 0.2)',
        'overlay': 'rgba(0, 0, 0, 0.9)',
    }

    # ========== 淺色主題（現代簡約風格）==========
    LIGHT = {
        # 背景色
        'bg_primary': '#f5f7fa',        # 主背景（淺灰）
        'bg_secondary': '#e8ecf1',      # 次要背景
        'bg_card': '#ffffff',           # 卡片背景（白色，與主背景形成對比）
        'bg_sidebar': '#ffffff',        # 側邊欄背景（白色）
        'bg_header': '#ffffff',         # 頭部背景

        # 前景色（文字）
        'text_primary': '#1a202c',      # 主要文字（深色，對比度強）
        'text_secondary': '#4a5568',    # 次要文字
        'text_muted': '#718096',        # 弱化文字
        'text_inverse': '#ffffff',      # 反色文字（用於暗色背景）

        # 強調色
        'accent_primary': '#0066ff',    # 主強調色（科技藍）
        'accent_secondary': '#0080ff',  # 次要強調色
        'accent_gold': '#ff9800',       # 金色

        # 數據色（金融專用）
        'data_positive': '#00a854',     # 上漲/正值（深綠，更易讀）
        'data_negative': '#f5222d',     # 下跌/負值（深紅，更易讀）
        'data_neutral': '#595959',      # 持平/中性（深灰，更易讀）
        'data_warning': '#fa8c16',      # 警告（橙）

        # 邊框和分隔線
        'border_light': '#d9d9d9',      # 淺邊框（更明顯）
        'border_medium': '#bfbfbf',     # 中等邊框
        'border_heavy': '#8c8c8c',      # 重邊框

        # 陰影
        'shadow_sm': 'rgba(0, 0, 0, 0.08)',
        'shadow_md': 'rgba(0, 0, 0, 0.12)',
        'shadow_lg': 'rgba(0, 0, 0, 0.16)',

        # 特殊效果
        'glow_blue': 'rgba(0, 102, 255, 0.15)',
        'glow_gold': 'rgba(255, 152, 0, 0.15)',
        'overlay': 'rgba(255, 255, 255, 0.95)',
    }

    @staticmethod
    def get_theme(theme_name: str = 'dark') -> Dict[str, str]:
        """
        獲取指定主題的配色

        Args:
            theme_name: 主題名稱（'dark' 或 'light'）

        Returns:
            主題配色字典
        """
        if theme_name.lower() == 'light':
            return Theme.LIGHT
        return Theme.DARK

    @staticmethod
    def generate_css(theme_name: str = 'dark') -> str:
        """
        生成主題 CSS 樣式

        Args:
            theme_name: 主題名稱（'dark' 或 'light'）

        Returns:
            CSS 樣式字符串
        """
        colors = Theme.get_theme(theme_name)

        css = f"""
        <style>
            /* ========== 全局樣式 ========== */
            :root {{
                --bg-primary: {colors['bg_primary']};
                --bg-secondary: {colors['bg_secondary']};
                --bg-card: {colors['bg_card']};
                --text-primary: {colors['text_primary']};
                --text-secondary: {colors['text_secondary']};
                --accent-primary: {colors['accent_primary']};
                --data-positive: {colors['data_positive']};
                --data-negative: {colors['data_negative']};
            }}

            /* Streamlit 容器背景 */
            .stApp {{
                background-color: {colors['bg_primary']};
                color: {colors['text_primary']};
            }}

            /* 側邊欄 */
            section[data-testid="stSidebar"] {{
                background-color: {colors['bg_sidebar']};
                border-right: 1px solid {colors['border_medium']};
            }}

            /* 側邊欄導航標題優化（多種選擇器適配不同 Streamlit 版本）*/
            section[data-testid="stSidebar"] h2,
            section[data-testid="stSidebar"] .css-17lntkn,
            section[data-testid="stSidebar"] [class*="css-"] h2,
            section[data-testid="stSidebar"] > div > div > div > h2 {{
                font-size: 0px !important;  /* 隱藏原始 "app" 文字 */
            }}

            section[data-testid="stSidebar"] h2::before,
            section[data-testid="stSidebar"] .css-17lntkn::before,
            section[data-testid="stSidebar"] > div > div > div > h2::before {{
                content: "🧭 導航" !important;
                font-size: 1rem !important;
                color: {colors['text_primary']} !important;
                font-weight: 600 !important;
                display: block !important;
            }}

            /* 移除數字圖標 */
            section[data-testid="stSidebar"] h2::after,
            section[data-testid="stSidebar"] .css-17lntkn::after,
            section[data-testid="stSidebar"] > div > div > div > h2::after {{
                content: "" !important;
                display: none !important;
            }}

            /* 側邊欄導航連結樣式 */
            section[data-testid="stSidebar"] [data-testid="stSidebarNav"] {{
                padding-top: 1rem;
            }}

            section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a {{
                color: {colors['text_primary']} !important;
                text-decoration: none !important;
                padding: 0.75rem 1rem !important;
                border-radius: 8px !important;
                margin: 0.25rem 0 !important;
                transition: all 0.2s ease !important;
            }}

            section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a:hover {{
                background-color: {colors['bg_secondary']} !important;
                transform: translateX(4px) !important;
            }}

            section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a[aria-current="page"] {{
                background-color: {colors['accent_primary']} !important;
                color: white !important;
                font-weight: 600 !important;
            }}

            /* 主內容區 */
            .main .block-container {{
                padding-top: 2rem;
                padding-bottom: 2rem;
                background-color: {colors['bg_primary']};
            }}

            /* ========== 卡片樣式 ========== */
            .metric-card {{
                background: linear-gradient(135deg, {colors['bg_card']} 0%, {colors['bg_secondary']} 100%);
                padding: 1.5rem;
                border-radius: 12px;
                box-shadow: 0 4px 6px {colors['shadow_md']};
                border: 1px solid {colors['border_light']};
                text-align: center;
                transition: all 0.3s ease;
                position: relative;
                overflow: hidden;
            }}

            .metric-card:hover {{
                transform: translateY(-4px);
                box-shadow: 0 8px 12px {colors['shadow_lg']};
                border-color: {colors['accent_primary']};
            }}

            .metric-card::before {{
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                height: 3px;
                background: linear-gradient(90deg, {colors['accent_primary']}, {colors['accent_secondary']});
            }}

            .metric-card h3 {{
                color: {colors['accent_primary']};
                font-size: 2.5rem;
                font-weight: 700;
                margin: 0.5rem 0;
                font-family: 'Roboto Mono', monospace;
            }}

            .metric-card p {{
                color: {colors['text_secondary']};
                font-size: 0.95rem;
                margin: 0;
                font-weight: 500;
            }}

            /* ========== 市場數據卡片 ========== */
            .market-card {{
                background: {colors['bg_card']};
                padding: 1.5rem;
                border-radius: 10px;
                box-shadow: 0 2px 8px {colors['shadow_sm']};
                border: 1px solid {colors['border_light']};
                margin-bottom: 1rem;
                transition: all 0.3s ease;
            }}

            .market-card:hover {{
                border-color: {colors['accent_primary']};
                box-shadow: 0 4px 12px {colors['shadow_md']};
            }}

            .market-card h4 {{
                color: {colors['text_primary']};
                font-size: 1.1rem;
                font-weight: 600;
                margin: 0 0 1rem 0;
                border-bottom: 2px solid {colors['border_light']};
                padding-bottom: 0.5rem;
            }}

            .market-card p {{
                color: {colors['text_primary']};
                margin: 0.5rem 0;
            }}

            /* ========== 功能卡片 ========== */
            .feature-card {{
                background: linear-gradient(135deg, {colors['accent_primary']} 0%, {colors['accent_secondary']} 100%);
                color: {colors['text_inverse']};
                padding: 2rem;
                border-radius: 16px;
                text-align: center;
                margin: 1rem 0;
                cursor: pointer;
                transition: all 0.3s ease;
                box-shadow: 0 4px 12px {colors['glow_blue']};
                position: relative;
                overflow: hidden;
            }}

            .feature-card::before {{
                content: '';
                position: absolute;
                top: -50%;
                left: -50%;
                width: 200%;
                height: 200%;
                background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
                opacity: 0;
                transition: opacity 0.3s ease;
            }}

            .feature-card:hover {{
                transform: translateY(-8px) scale(1.02);
                box-shadow: 0 8px 24px {colors['glow_blue']};
            }}

            .feature-card:hover::before {{
                opacity: 1;
            }}

            .feature-card h3 {{
                font-size: 1.5rem;
                font-weight: 700;
                margin-bottom: 0.5rem;
            }}

            .feature-card p {{
                font-size: 1rem;
                opacity: 0.9;
                margin: 0.3rem 0;
            }}

            /* ========== 經濟日曆事件 ========== */
            .calendar-event {{
                background: {colors['bg_card']};
                padding: 1.2rem;
                border-left: 4px solid {colors['accent_primary']};
                margin-bottom: 0.8rem;
                border-radius: 8px;
                box-shadow: 0 2px 4px {colors['shadow_sm']};
                transition: all 0.3s ease;
            }}

            .calendar-event:hover {{
                border-left-width: 6px;
                box-shadow: 0 4px 8px {colors['shadow_md']};
                transform: translateX(4px);
            }}

            .calendar-event h4 {{
                color: {colors['text_primary']};
                font-size: 1.1rem;
                font-weight: 600;
                margin: 0 0 0.8rem 0;
            }}

            .calendar-event p {{
                color: {colors['text_secondary']};
                font-size: 0.9rem;
                margin: 0.3rem 0;
            }}

            .calendar-important {{
                border-left-color: {colors['data_negative']};
                background: linear-gradient(90deg, rgba(255, 82, 82, 0.05) 0%, {colors['bg_card']} 20%);
            }}

            /* ========== 時間軸網格佈局（已簡化為內聯樣式，此區塊保留備用）========== */
            /* 時間軸相關樣式已改用內聯樣式實現，提高 Streamlit 兼容性 */

            /* ========== 數據顏色（金融專用）========== */
            .positive {{
                color: {colors['data_positive']};
                font-weight: 600;
            }}

            .negative {{
                color: {colors['data_negative']};
                font-weight: 600;
            }}

            .neutral {{
                color: {colors['data_neutral']};
            }}

            /* ========== 按鈕樣式 ========== */
            .stButton > button {{
                background: linear-gradient(135deg, {colors['accent_primary']} 0%, {colors['accent_secondary']} 100%);
                color: {colors['text_inverse']};
                border: none;
                border-radius: 8px;
                padding: 0.75rem 2rem;
                font-weight: 600;
                font-size: 1rem;
                transition: all 0.3s ease;
                box-shadow: 0 4px 8px {colors['glow_blue']};
                text-transform: none;
            }}

            .stButton > button:hover {{
                transform: translateY(-2px);
                box-shadow: 0 6px 16px {colors['glow_blue']};
            }}

            /* ========== 標題樣式 ========== */
            .main-title {{
                font-size: 2.8rem;
                font-weight: 700;
                background: linear-gradient(135deg, {colors['accent_primary']} 0%, {colors['accent_gold']} 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
                text-align: center;
                margin-bottom: 1rem;
                letter-spacing: -0.5px;
            }}

            .sub-title {{
                font-size: 1.2rem;
                color: {colors['text_secondary']};
                text-align: center;
                margin-bottom: 2rem;
                font-weight: 400;
            }}

            /* ========== Streamlit 原生元件樣式覆蓋 ========== */
            .stMetric {{
                background-color: {colors['bg_card']};
                padding: 1rem;
                border-radius: 8px;
                border: 1px solid {colors['border_light']};
            }}

            .stMetric label {{
                color: {colors['text_secondary']} !important;
            }}

            .stMetric [data-testid="stMetricValue"] {{
                color: {colors['text_primary']} !important;
                font-size: 2rem !important;
            }}

            /* 輸入框 */
            .stTextInput > div > div > input {{
                background-color: {colors['bg_card']};
                color: {colors['text_primary']};
                border: 1px solid {colors['border_medium']};
                border-radius: 6px;
            }}

            /* 選擇框 */
            .stSelectbox > div > div {{
                background-color: {colors['bg_card']};
                color: {colors['text_primary']};
            }}

            /* ========== 表格樣式 ========== */
            .dataframe {{
                background-color: {colors['bg_card']} !important;
                border: 1px solid {colors['border_light']} !important;
                border-radius: 8px;
                overflow: hidden;
            }}

            .dataframe th {{
                background-color: {colors['bg_secondary']} !important;
                color: {colors['text_primary']} !important;
                border-bottom: 2px solid {colors['accent_primary']} !important;
                padding: 12px !important;
                font-weight: 600 !important;
            }}

            .dataframe td {{
                color: {colors['text_primary']} !important;
                border-bottom: 1px solid {colors['border_light']} !important;
                padding: 10px !important;
            }}

            .dataframe tr:hover {{
                background-color: {colors['bg_secondary']} !important;
            }}

            /* ========== 分隔線 ========== */
            hr {{
                border-color: {colors['border_medium']};
                margin: 2rem 0;
            }}

            /* ========== 滾動條 ========== */
            ::-webkit-scrollbar {{
                width: 10px;
                height: 10px;
            }}

            ::-webkit-scrollbar-track {{
                background: {colors['bg_secondary']};
            }}

            ::-webkit-scrollbar-thumb {{
                background: {colors['border_heavy']};
                border-radius: 5px;
            }}

            ::-webkit-scrollbar-thumb:hover {{
                background: {colors['accent_primary']};
            }}

            /* ========== 動畫 ========== */
            @keyframes fadeIn {{
                from {{ opacity: 0; transform: translateY(20px); }}
                to {{ opacity: 1; transform: translateY(0); }}
            }}

            .metric-card, .market-card, .feature-card, .calendar-event {{
                animation: fadeIn 0.5s ease-out;
            }}

            /* ========== Streamlit 核心文字元件明確樣式 ========== */
            /* 強制所有 Streamlit markdown 文字使用主題顏色 */
            .stMarkdown, .stMarkdown p, .stMarkdown span, .stMarkdown div {{
                color: {colors['text_primary']} !important;
            }}

            .stMarkdown h1, .stMarkdown h2, .stMarkdown h3,
            .stMarkdown h4, .stMarkdown h5, .stMarkdown h6 {{
                color: {colors['text_primary']} !important;
            }}

            /* Streamlit 標題元件 */
            h1, h2, h3, h4, h5, h6 {{
                color: {colors['text_primary']} !important;
            }}

            /* Streamlit 段落和文字 */
            p, span, div {{
                color: {colors['text_primary']} !important;
            }}

            /* Streamlit caption */
            .stCaptionContainer, .caption {{
                color: {colors['text_secondary']} !important;
            }}

            /* Streamlit code blocks */
            .stCodeBlock, code {{
                background-color: {colors['bg_secondary']} !important;
                color: {colors['text_primary']} !important;
            }}

            /* Streamlit info/success/warning/error boxes */
            .stAlert {{
                background-color: {colors['bg_card']} !important;
                color: {colors['text_primary']} !important;
            }}

            /* Streamlit expander */
            .streamlit-expanderHeader {{
                background-color: {colors['bg_card']} !important;
                color: {colors['text_primary']} !important;
            }}

            .streamlit-expanderContent {{
                background-color: {colors['bg_secondary']} !important;
                color: {colors['text_primary']} !important;
            }}

            /* ========== 經濟日曆表格樣式 ========== */
            /* 日期標題 - 今天的特殊樣式 */
            .economic-calendar-today {{
                background: linear-gradient(135deg, #ffd700 0%, #ff9800 100%);
                color: {colors['text_inverse']} !important;
                padding: 0.8rem 1rem;
                border-radius: 8px;
                margin: 1rem 0 0.5rem 0;
                font-weight: 700 !important;
                box-shadow: 0 4px 8px rgba(255, 215, 0, 0.3);
            }}

            /* 日期標題 - 一般日期 */
            .economic-calendar-date {{
                background: {colors['bg_card']};
                color: {colors['text_primary']} !important;
                padding: 0.6rem 1rem;
                border-radius: 6px;
                border-left: 4px solid {colors['accent_primary']};
                margin: 0.8rem 0 0.4rem 0;
                font-weight: 600 !important;
            }}

            /* 事件行 - 高重要性 */
            .event-high-importance {{
                background: linear-gradient(90deg, rgba(255,68,68,0.1) 0%, transparent 100%);
                border-left: 4px solid {colors['data_negative']};
                padding: 0.6rem 0.8rem;
                margin: 0.3rem 0;
                border-radius: 4px;
                transition: all 0.2s ease;
            }}

            .event-high-importance:hover {{
                background: linear-gradient(90deg, rgba(255,68,68,0.15) 0%, transparent 100%);
                transform: translateX(4px);
                box-shadow: 0 2px 8px rgba(255,68,68,0.2);
            }}

            /* 事件行 - 中重要性 */
            .event-medium-importance {{
                background: transparent;
                border-left: 3px solid rgba(255,152,0,0.5);
                padding: 0.5rem 0.8rem;
                margin: 0.2rem 0;
                border-radius: 4px;
                transition: all 0.2s ease;
            }}

            .event-medium-importance:hover {{
                background: rgba(255,152,0,0.05);
                transform: translateX(2px);
            }}

            /* 事件行 - 低重要性 */
            .event-low-importance {{
                background: transparent;
                border-left: 2px solid rgba(255,255,255,0.1);
                padding: 0.4rem 0.8rem;
                margin: 0.1rem 0;
                opacity: 0.7;
                transition: all 0.2s ease;
            }}

            .event-low-importance:hover {{
                opacity: 1;
            }}

            /* 過濾器組件樣式 */
            .stMultiSelect label {{
                font-weight: 600 !important;
                color: {colors['text_primary']} !important;
            }}

            .stCheckbox label {{
                font-weight: 500 !important;
                color: {colors['text_primary']} !important;
            }}

            /* ========== 響應式設計 ========== */
            @media (max-width: 768px) {{
                .metric-card h3 {{
                    font-size: 2rem;
                }}

                .main-title {{
                    font-size: 2rem;
                }}

                .sub-title {{
                    font-size: 1rem;
                }}
            }}
        </style>
        """

        return css


# ========== 主題圖標和標籤 ==========
THEME_ICONS = {
    'dark': '🌙',
    'light': '☀️'
}

THEME_LABELS = {
    'dark': '深色模式',
    'light': '淺色模式'
}


def get_theme_toggle_label(current_theme: str) -> str:
    """
    獲取主題切換按鈕的標籤

    Args:
        current_theme: 當前主題（'dark' 或 'light'）

    Returns:
        切換按鈕標籤
    """
    next_theme = 'light' if current_theme == 'dark' else 'dark'
    return f"{THEME_ICONS[next_theme]} 切換至{THEME_LABELS[next_theme]}"


def get_floating_theme_toggle_html(current_theme: str) -> str:
    """
    生成浮動主題切換按鈕的 HTML/CSS

    Args:
        current_theme: 當前主題（'dark' 或 'light'）

    Returns:
        包含浮動按鈕的 HTML 字符串
    """
    # 根據當前主題決定顯示的圖標（顯示下一個主題的圖標）
    next_theme = 'light' if current_theme == 'dark' else 'dark'
    icon = THEME_ICONS[next_theme]
    label = THEME_LABELS[next_theme]

    # 根據當前主題決定按鈕顏色
    if current_theme == 'dark':
        bg_color = '#1a2332'
        text_color = '#e6e8ec'
        hover_bg = '#2a3342'
        border_color = '#3d4758'
    else:
        bg_color = '#ffffff'
        text_color = '#1a202c'
        hover_bg = '#f5f7fa'
        border_color = '#d9d9d9'

    html = f"""
    <style>
        .floating-theme-toggle {{
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 9999;
            background-color: {bg_color};
            color: {text_color};
            border: 2px solid {border_color};
            border-radius: 50%;
            width: 50px;
            height: 50px;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            font-size: 24px;
        }}

        .floating-theme-toggle:hover {{
            background-color: {hover_bg};
            transform: scale(1.1) rotate(15deg);
            box-shadow: 0 6px 16px rgba(0, 0, 0, 0.25);
        }}

        .floating-theme-toggle:active {{
            transform: scale(0.95);
        }}

        .theme-toggle-tooltip {{
            position: absolute;
            right: 60px;
            top: 50%;
            transform: translateY(-50%);
            background-color: {bg_color};
            color: {text_color};
            padding: 8px 12px;
            border-radius: 6px;
            white-space: nowrap;
            opacity: 0;
            pointer-events: none;
            transition: opacity 0.3s ease;
            border: 1px solid {border_color};
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
            font-size: 14px;
        }}

        .floating-theme-toggle:hover .theme-toggle-tooltip {{
            opacity: 1;
        }}
    </style>
    <div class="floating-theme-toggle" title="切換至{label}">
        <span>{icon}</span>
        <div class="theme-toggle-tooltip">切換至{label}</div>
    </div>
    """

    return html

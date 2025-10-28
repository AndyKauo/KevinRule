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
        # 背景色
        'bg_primary': '#0a0e27',        # 主背景（深藍黑）
        'bg_secondary': '#141b2d',      # 次要背景
        'bg_card': '#1a2332',           # 卡片背景
        'bg_sidebar': '#0d1117',        # 側邊欄背景
        'bg_header': '#161d2f',         # 頭部背景

        # 前景色（文字）
        'text_primary': '#e6e8ec',      # 主要文字
        'text_secondary': '#a0a7b4',    # 次要文字
        'text_muted': '#6c7589',        # 弱化文字
        'text_inverse': '#0a0e27',      # 反色文字（用於亮色背景）

        # 強調色
        'accent_primary': '#0066ff',    # 主強調色（科技藍）
        'accent_secondary': '#00a6ff',  # 次要強調色（亮藍）
        'accent_gold': '#ffa500',       # 金色（用於重要指標）

        # 數據色（金融專用）
        'data_positive': '#00c853',     # 上漲/正值（綠）
        'data_negative': '#ff5252',     # 下跌/負值（紅）
        'data_neutral': '#a0a7b4',      # 持平/中性（灰）
        'data_warning': '#ffc107',      # 警告（黃）

        # 邊框和分隔線
        'border_light': '#2d3748',      # 淺邊框
        'border_medium': '#3d4758',     # 中等邊框
        'border_heavy': '#4d5768',      # 重邊框

        # 陰影
        'shadow_sm': 'rgba(0, 0, 0, 0.3)',
        'shadow_md': 'rgba(0, 0, 0, 0.5)',
        'shadow_lg': 'rgba(0, 0, 0, 0.7)',

        # 特殊效果
        'glow_blue': 'rgba(0, 102, 255, 0.3)',
        'glow_gold': 'rgba(255, 165, 0, 0.3)',
        'overlay': 'rgba(10, 14, 39, 0.8)',
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

            /* 側邊欄導航標題優化 */
            section[data-testid="stSidebar"] .css-17lntkn {{
                font-size: 0px !important;  /* 隱藏原始 "app" 文字 */
            }}

            section[data-testid="stSidebar"] .css-17lntkn::before {{
                content: "🧭 導航" !important;
                font-size: 1rem !important;
                color: {colors['text_primary']} !important;
                font-weight: 600 !important;
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

            /* ========== 時間軸網格佈局 ========== */
            .timeline-container {{
                display: flex;
                overflow-x: auto;
                overflow-y: hidden;
                padding: 1rem 0;
                gap: 1rem;
                scroll-behavior: smooth;
            }}

            .timeline-container::-webkit-scrollbar {{
                height: 8px;
            }}

            .timeline-date-column {{
                min-width: 280px;
                max-width: 280px;
                flex-shrink: 0;
            }}

            .timeline-date-header {{
                background: linear-gradient(135deg, {colors['accent_primary']} 0%, {colors['accent_secondary']} 100%);
                color: white;
                padding: 0.8rem;
                border-radius: 8px 8px 0 0;
                text-align: center;
                font-weight: 600;
                font-size: 1rem;
                position: sticky;
                top: 0;
                z-index: 1;
            }}

            .timeline-date-header.today {{
                background: linear-gradient(135deg, {colors['accent_gold']} 0%, #ff9800 100%);
            }}

            .timeline-events-list {{
                display: flex;
                flex-direction: column;
                gap: 0.75rem;
                padding: 0.75rem;
                background: {colors['bg_secondary']};
                border-radius: 0 0 8px 8px;
                min-height: 200px;
                border: 1px solid {colors['border_light']};
                border-top: none;
            }}

            .timeline-event-card {{
                background: {colors['bg_card']};
                padding: 0.8rem;
                border-radius: 6px;
                border-left: 3px solid {colors['accent_primary']};
                box-shadow: 0 2px 4px {colors['shadow_sm']};
                transition: all 0.2s ease;
                cursor: pointer;
            }}

            .timeline-event-card:hover {{
                transform: translateY(-2px);
                box-shadow: 0 4px 8px {colors['shadow_md']};
                border-left-width: 4px;
            }}

            .timeline-event-card.important {{
                border-left-color: {colors['data_negative']};
                background: linear-gradient(90deg, {colors['bg_card']} 95%, rgba(255, 82, 82, 0.1) 100%);
            }}

            .timeline-event-title {{
                font-size: 0.9rem;
                font-weight: 600;
                color: {colors['text_primary']};
                margin-bottom: 0.4rem;
                line-height: 1.3;
            }}

            .timeline-event-time {{
                font-size: 0.8rem;
                color: {colors['text_muted']};
                margin-bottom: 0.3rem;
            }}

            .timeline-event-meta {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                font-size: 0.75rem;
                color: {colors['text_secondary']};
                margin-top: 0.4rem;
            }}

            .timeline-event-importance {{
                font-size: 0.9rem;
            }}

            .timeline-event-data {{
                font-size: 0.75rem;
                color: {colors['text_muted']};
            }}

            .timeline-news-links {{
                display: flex;
                gap: 0.3rem;
                margin-top: 0.5rem;
                flex-wrap: wrap;
            }}

            .timeline-news-link {{
                background: {colors['accent_primary']};
                color: white !important;
                padding: 3px 8px;
                border-radius: 3px;
                font-size: 0.7rem;
                text-decoration: none !important;
                transition: all 0.2s ease;
                display: inline-block;
            }}

            .timeline-news-link:hover {{
                opacity: 0.8;
                transform: scale(1.05);
            }}

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

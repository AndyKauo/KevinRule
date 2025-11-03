"""
Trading Economics API 客戶端封裝
Trading Economics API Client Wrapper

使用 tradingeconomics 獲取經濟日曆數據
如果 API 不可用，則使用 Investing.com 爬蟲作為備用數據源
"""

import pandas as pd
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from config.settings import settings
from backend.data_sources.investing_com_scraper import InvestingComScraper


class TradingEconomicsClient:
    """Trading Economics API 客戶端"""

    def __init__(self, api_key: Optional[str] = None, use_scraper: bool = True):
        """
        初始化 Trading Economics 客戶端

        Args:
            api_key: API Key（如果不提供則從 settings 讀取）
            use_scraper: 是否優先使用 Investing.com 爬蟲（默認 True）
        """
        self.api_key = api_key or settings.trading_economics_api_key
        self.use_scraper = use_scraper
        self.scraper = InvestingComScraper() if use_scraper else None

        if not self.api_key:
            print("⚠️  未設定 TRADING_ECONOMICS_API_KEY")
            if use_scraper:
                print("✅ 將使用 Investing.com 爬蟲作為數據源")
                self.enabled = True
            else:
                print("❌ 經濟日曆功能將無法使用")
                self.enabled = False
        else:
            self.enabled = True
            self._login()

    def _login(self):
        """登入 Trading Economics API"""
        try:
            import tradingeconomics as te
            te.login(self.api_key)
            print("✅ Trading Economics API 登入成功")
        except ImportError:
            print("❌ 無法導入 tradingeconomics 套件，請執行: pip install tradingeconomics")
            self.enabled = False
        except Exception as e:
            print(f"❌ Trading Economics API 登入失敗: {e}")
            self.enabled = False

    def get_calendar(
        self,
        country: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        days: int = 7
    ) -> pd.DataFrame:
        """
        獲取經濟日曆

        Args:
            country: 國家代碼（例如：'United States', 'China'），None 表示所有國家
            start_date: 開始日期（YYYY-MM-DD）
            end_date: 結束日期（YYYY-MM-DD）
            days: 如果沒有指定日期，則獲取未來 N 天的事件

        Returns:
            經濟事件 DataFrame
        """
        if not self.enabled:
            print("❌ 經濟日曆功能未啟用")
            return pd.DataFrame()

        # 優先使用 Investing.com 爬蟲（數據更完整）
        if self.use_scraper and self.scraper:
            print(f"📊 使用 Investing.com 爬蟲獲取經濟日曆數據...")
            try:
                df = self.scraper.scrape_calendar(days=days)

                # 如果指定了國家，進行過濾
                if not df.empty and country:
                    df = df[df['Country'] == country]
                    print(f"   - 已過濾國家: {country}，剩餘 {len(df)} 個事件")

                if not df.empty:
                    print(f"✅ Investing.com 爬蟲成功獲取 {len(df)} 個事件")
                    return df
                else:
                    print("⚠️  Investing.com 爬蟲未獲取到數據，嘗試使用 TE API...")
            except Exception as e:
                print(f"❌ Investing.com 爬蟲失敗: {e}")
                print("⚠️  嘗試使用 TE API...")

        # 備用方案：使用 Trading Economics API
        if not self.api_key:
            print("❌ Trading Economics API 未設定，且爬蟲失敗")
            return pd.DataFrame()

        try:
            import tradingeconomics as te

            # 如果沒有指定日期，使用預設範圍
            if not start_date:
                start_date = datetime.now().strftime('%Y-%m-%d')
            if not end_date:
                end_date = (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d')

            print(f"\n{'='*60}")
            print(f"🔍 [DEBUG] API 請求參數:")
            print(f"   - country: {country}")
            print(f"   - start_date: {start_date}")
            print(f"   - end_date: {end_date}")
            print(f"   - days 參數: {days}")
            print(f"{'='*60}\n")

            print(f"📅 正在使用 TE API 獲取經濟日曆 ({start_date} 至 {end_date})...")

            # 獲取經濟日曆（根據官方文檔，不傳遞 country 參數以獲取所有國家數據）
            # 參考：https://docs.tradingeconomics.com/economic_calendar/
            calendar = te.getCalendarData(initDate=start_date, endDate=end_date)

            if calendar is None or (isinstance(calendar, list) and len(calendar) == 0):
                print("⚠️  未獲取到經濟事件")
                return pd.DataFrame()

            # 轉換為 DataFrame
            if isinstance(calendar, list):
                df = pd.DataFrame(calendar)
            else:
                df = calendar

            print(f"\n{'='*60}")
            print(f"📊 [DEBUG] API 返回原始數據:")
            print(f"   - 總事件數: {len(df)}")

            if not df.empty and 'Date' in df.columns:
                # 提取所有日期
                dates = df['Date'].apply(lambda x: str(x)[:10] if pd.notna(x) else 'N/A').unique()
                print(f"   - 涵蓋日期: {sorted([d for d in dates if d != 'N/A'])}")
                print(f"   - 日期數量: {len([d for d in dates if d != 'N/A'])} 天")

            if not df.empty:
                print(f"   - 數據欄位: {list(df.columns)}")
                print(f"\n   - 前3筆原始數據樣本:")
                for idx, row in df.head(3).iterrows():
                    date_val = row.get('Date', 'N/A')
                    event_val = row.get('Event', 'N/A')
                    country_val = row.get('Country', 'N/A')
                    print(f"     [{idx}] {date_val} | {country_val} | {event_val}")

            print(f"{'='*60}\n")

            print(f"✅ TE API 獲取到 {len(df)} 個經濟事件")

            return df

        except Exception as e:
            print(f"❌ TE API 獲取經濟日曆失敗: {e}")
            return pd.DataFrame()

    def format_events(
        self,
        df: pd.DataFrame,
        importance_filter: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        格式化經濟事件數據

        Args:
            df: 經濟事件 DataFrame
            importance_filter: 重要性篩選（1=低, 2=中, 3=高），None 表示不篩選

        Returns:
            格式化的事件列表
        """
        if df.empty:
            return []

        print(f"\n{'='*60}")
        print(f"🔍 [DEBUG] 開始格式化事件:")
        print(f"   - 輸入事件數: {len(df)}")
        print(f"   - 重要性篩選: {importance_filter}")

        events = []
        skipped_empty = 0
        skipped_importance = 0

        for _, row in df.iterrows():
            try:
                # 數據驗證：過濾無效事件
                event_name = row.get('Event', '')

                # 跳過空事件名稱
                if not event_name or event_name == 'N/A' or str(event_name).strip() == '':
                    skipped_empty += 1
                    continue

                # 提取數據欄位（預期、前值、實際）
                # 注意：不強制要求這些欄位有值，允許顯示"待公布"的未來事件
                forecast = row.get('Forecast')
                previous = row.get('Previous')
                actual = row.get('Actual')

                # 篩選重要性
                importance = row.get('Importance', 1)
                if importance_filter and importance < importance_filter:
                    skipped_importance += 1
                    continue

                # 格式化日期時間
                date_str = row.get('Date', '')
                if isinstance(date_str, str):
                    try:
                        dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                        date_display = dt.strftime('%Y-%m-%d (%a)')
                        time_display = dt.strftime('%H:%M')
                    except:
                        date_display = date_str
                        time_display = ''
                else:
                    date_display = str(date_str)
                    time_display = ''

                # 重要性星級
                importance_stars = '⭐' * int(importance) if importance else '⭐'

                # 國家/地區 emoji
                country = row.get('Country', '')
                country_emoji = {
                    'United States': '🇺🇸',
                    'China': '🇨🇳',
                    'Taiwan': '🇹🇼',
                    'Japan': '🇯🇵',
                    'Germany': '🇩🇪',
                    'United Kingdom': '🇬🇧',
                    'Euro Area': '🇪🇺',
                }.get(country, '🌍')

                event = {
                    '日期': date_display,
                    '時間': time_display or '全天',
                    '事件': f"{country_emoji} {event_name}",
                    '重要性': importance_stars,
                    '預期': str(forecast) if pd.notna(forecast) else '-',
                    '前值': str(previous) if pd.notna(previous) else '-',
                    '實際': str(actual) if pd.notna(actual) else '-',
                    'importance_level': int(importance),
                    'country': country,  # 保留國家信息用於新聞連結
                    'event_name_raw': event_name,  # 保留原始事件名稱用於新聞連結
                    'event_url': row.get('EventURL', '')  # 保留事件連結（來自 Investing.com）
                }

                events.append(event)

            except Exception as e:
                print(f"⚠️  格式化事件失敗: {e}")
                continue

        print(f"\n📊 [DEBUG] 格式化結果:")
        print(f"   - 成功格式化: {len(events)} 個事件")
        print(f"   - 跳過空事件: {skipped_empty} 個")
        print(f"   - 跳過低重要性: {skipped_importance} 個")
        print(f"   - 總處理: {len(df)} 個")
        print(f"{'='*60}\n")

        return events

    def get_formatted_calendar(
        self,
        country: Optional[str] = None,
        days: int = 7,
        importance_filter: Optional[int] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        獲取格式化的經濟日曆（按週分組）

        Args:
            country: 國家代碼
            days: 獲取未來 N 天
            importance_filter: 重要性篩選

        Returns:
            按週分組的事件字典 {'本週': [...], '下週': [...]}
        """
        # 獲取原始數據
        df = self.get_calendar(country=country, days=days)

        if df.empty:
            return {'本週': [], '下週': []}

        # 格式化事件
        all_events = self.format_events(df, importance_filter=importance_filter)

        # 分組：本週和下週
        now = datetime.now()
        end_of_this_week = now + timedelta(days=(6 - now.weekday()))

        this_week = []
        next_week = []

        for event in all_events:
            try:
                date_str = event['日期'].split('(')[0].strip()
                event_date = datetime.strptime(date_str, '%Y-%m-%d')

                if event_date <= end_of_this_week:
                    this_week.append(event)
                else:
                    next_week.append(event)
            except:
                this_week.append(event)

        return {
            '本週': this_week,
            '下週': next_week
        }

    def get_calendar_by_date(
        self,
        country: Optional[str] = None,
        days: int = 14,
        importance_filter: Optional[int] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        獲取按日期分組的經濟日曆（用於時間軸顯示）

        Args:
            country: 國家代碼
            days: 獲取未來 N 天
            importance_filter: 重要性篩選

        Returns:
            按日期分組的事件字典 {'2025-10-28': [...], '2025-10-29': [...]}
        """
        # 獲取原始數據
        df = self.get_calendar(country=country, days=days)

        if df.empty:
            return {}

        # 格式化事件
        all_events = self.format_events(df, importance_filter=importance_filter)

        # 按日期分組
        events_by_date = {}

        for event in all_events:
            try:
                # 提取日期
                date_str = event['日期'].split('(')[0].strip()

                if date_str not in events_by_date:
                    events_by_date[date_str] = []

                events_by_date[date_str].append(event)
            except Exception as e:
                print(f"⚠️  分組事件失敗: {e}")
                continue

        # 按日期排序
        sorted_dates = sorted(events_by_date.keys())
        sorted_events = {date: events_by_date[date] for date in sorted_dates}

        return sorted_events

    @staticmethod
    def generate_news_links(event: Dict[str, Any]) -> Dict[str, str]:
        """
        為經濟事件生成新聞連結

        Args:
            event: 經濟事件字典（需包含 'event_name_raw' 和 'country' 欄位）

        Returns:
            包含各種新聞來源連結的字典
        """
        import urllib.parse

        event_name = event.get('event_name_raw', '')
        country = event.get('country', '')

        # URL encode 事件名稱
        encoded_event = urllib.parse.quote(event_name)

        links = {}

        # 1. Google 新聞搜尋連結（最可靠的新聞來源）
        search_query = f"{country} {event_name}" if country else event_name
        encoded_search = urllib.parse.quote(search_query)
        links['google_news'] = f"https://news.google.com/search?q={encoded_search}&hl=zh-TW"

        # 2. 台灣財經媒體連結（僅在相關時顯示）
        taiwan_related = country in ['Taiwan', 'China'] or any(keyword in event_name.lower() for keyword in ['taiwan', 'china', 'asia'])

        if taiwan_related:
            # 鉅亨網
            links['cnyes'] = f"https://news.cnyes.com/search?q={encoded_event}"
            # 工商時報
            links['ctee'] = f"https://ctee.com.tw/search/{encoded_event}"

        return links


# ========== 測試代碼 ==========

def test_trading_economics_client():
    """測試 Trading Economics 客戶端"""
    print("=== Trading Economics 客戶端測試 ===")
    print()

    try:
        client = TradingEconomicsClient()

        if not client.enabled:
            print("⚠️  Trading Economics API 未啟用，請設定 TRADING_ECONOMICS_API_KEY")
            return

        print("✅ 客戶端初始化成功")
        print()

        # 測試獲取經濟日曆
        print("測試獲取經濟日曆（未來7天）...")
        calendar = client.get_formatted_calendar(days=7, importance_filter=2)

        print(f"\n本週事件數: {len(calendar['本週'])}")
        if calendar['本週']:
            print("\n本週前3個事件:")
            for event in calendar['本週'][:3]:
                print(f"  - {event['事件']} ({event['日期']} {event['時間']})")

        print(f"\n下週事件數: {len(calendar['下週'])}")

        print("\n✅ 測試完成")

    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_trading_economics_client()

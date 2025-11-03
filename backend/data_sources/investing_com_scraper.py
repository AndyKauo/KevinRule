"""
Investing.com Economic Calendar Scraper
爬取 Investing.com 經濟日曆數據（免費完整數據源）
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import time


class InvestingComScraper:
    """Investing.com 經濟日曆爬蟲"""

    def __init__(self):
        self.base_url = "https://www.investing.com/economic-calendar/"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7',
            'Connection': 'keep-alive',
        }
        self.cache = {}
        self.cache_duration = 1800  # 30分鐘快取（秒）- 優化自 15分鐘

        # 國家代碼對應
        self.country_map = {
            'usa': 'United States',
            'eur': 'Euro Area',
            'gbp': 'United Kingdom',
            'jpy': 'Japan',
            'cny': 'China',
            'aud': 'Australia',
            'cad': 'Canada',
            'chf': 'Switzerland',
            'nzd': 'New Zealand',
            'sek': 'Sweden',
            'nok': 'Norway',
            'dkk': 'Denmark',
            'mxn': 'Mexico',
            'thb': 'Thailand',
            'sgd': 'Singapore',
            'hkd': 'Hong Kong',
            'krw': 'South Korea',
            'inr': 'India',
            'brl': 'Brazil',
            'zar': 'South Africa'
        }

        # 重要性對應
        self.importance_map = {
            'bull1': 1,  # 低
            'bull2': 2,  # 中
            'bull3': 3   # 高
        }

    def scrape_calendar(self, days=14) -> pd.DataFrame:
        """
        爬取經濟日曆數據

        Args:
            days: 獲取未來 N 天的數據

        Returns:
            DataFrame with columns: Date, Country, Event, Importance, Actual, Previous, Forecast
        """
        # 檢查快取
        cache_key = f"calendar_{days}"
        if cache_key in self.cache:
            cached_time, cached_data = self.cache[cache_key]
            if (time.time() - cached_time) < self.cache_duration:
                print(f"✅ 使用快取數據（{int(time.time() - cached_time)}秒前）")
                return cached_data

        print(f"🌐 正在爬取 Investing.com 經濟日曆（未來 {days} 天）...")

        try:
            # 發送請求
            response = requests.get(
                self.base_url,
                headers=self.headers,
                timeout=15
            )
            response.raise_for_status()

            # 解析 HTML
            soup = BeautifulSoup(response.content, 'html.parser')

            # 查找經濟日曆表格
            events_table = soup.find('table', {'id': 'economicCalendarData'})

            if not events_table:
                print("❌ 未找到經濟日曆表格")
                return pd.DataFrame()

            # 解析事件
            events = []
            rows = events_table.find_all('tr', {'class': 'js-event-item'})

            print(f"📊 找到 {len(rows)} 個事件")

            for row in rows:
                event = self._parse_event_row(row)
                if event:
                    events.append(event)

            # 轉換為 DataFrame
            df = pd.DataFrame(events)

            if not df.empty:
                # 過濾日期範圍（保留今天及未來 N 天，使用日期比較而非時間）
                today = datetime.now().date()
                end_date = today + timedelta(days=days)

                df['Date_parsed'] = pd.to_datetime(df['Date'], errors='coerce')
                df['Date_only'] = df['Date_parsed'].dt.date
                df = df[
                    (df['Date_only'] >= today) &
                    (df['Date_only'] <= end_date)
                ]
                df = df.drop(['Date_parsed', 'Date_only'], axis=1)

            print(f"✅ 成功爬取 {len(df)} 個事件")

            # 更新快取
            self.cache[cache_key] = (time.time(), df)

            return df

        except Exception as e:
            print(f"❌ 爬取失敗: {e}")
            return pd.DataFrame()

    def _parse_event_row(self, row) -> Optional[Dict]:
        """
        解析單個事件行

        Args:
            row: BeautifulSoup row element

        Returns:
            Event dictionary or None
        """
        try:
            # 提取時間
            time_cell = row.find('td', {'class': 'time'})
            event_time = time_cell.text.strip() if time_cell else '00:00'

            # 提取國家（從 flag span 的 title 屬性）
            flag_cell = row.find('td', {'class': 'flagCur'})
            country = 'Unknown'
            if flag_cell:
                flag_span = flag_cell.find('span', {'class': 'ceFlags'})
                if flag_span and flag_span.get('title'):
                    country = flag_span['title']

            # 提取事件名稱和連結
            event_cell = row.find('td', {'class': 'event'})
            event_name = event_cell.text.strip() if event_cell else ''
            event_url = ''

            if event_cell:
                event_link = event_cell.find('a')
                if event_link and event_link.get('href'):
                    # Investing.com 相對連結轉絕對連結
                    event_url = f"https://www.investing.com{event_link['href']}"

            if not event_name:
                return None

            # 提取重要性（計算 bull 圖標數量）
            importance_cell = row.find('td', {'class': 'sentiment'})
            importance = 1
            if importance_cell:
                # 計算填滿的 bull 圖標數量（1-3 顆星）
                bull_icons = importance_cell.find_all('i', {'class': 'grayFullBullishIcon'})
                importance = len(bull_icons) if bull_icons else 1

            # 提取實際值（使用 class 選擇器）
            actual_cell = row.find('td', {'class': 'bold'})
            actual = actual_cell.text.strip() if actual_cell else ''

            # 提取預測值
            forecast_cell = row.find('td', {'class': 'fore'})
            forecast = forecast_cell.text.strip() if forecast_cell else ''

            # 提取前值
            previous_cell = row.find('td', {'class': 'prev'})
            previous = previous_cell.text.strip() if previous_cell else ''

            # 提取日期（從 data-event-datetime 屬性）
            event_datetime = row.get('data-event-datetime', '')
            if event_datetime:
                # 格式: "2025/10/30 08:00:00"
                try:
                    dt = datetime.strptime(event_datetime, '%Y/%m/%d %H:%M:%S')
                    date_str = dt.isoformat()
                except:
                    date_str = datetime.now().isoformat()
            else:
                # 使用今天日期 + 時間
                today = datetime.now()
                try:
                    time_parts = event_time.split(':')
                    dt = today.replace(hour=int(time_parts[0]), minute=int(time_parts[1]), second=0)
                    date_str = dt.isoformat()
                except:
                    date_str = today.isoformat()

            return {
                'Date': date_str,
                'Country': country,
                'Event': event_name,
                'EventURL': event_url,
                'Importance': importance,
                'Actual': actual,
                'Previous': previous,
                'Forecast': forecast
            }

        except Exception as e:
            print(f"⚠️  解析事件失敗: {e}")
            return None


# ========== 測試代碼 ==========

def test_investing_scraper():
    """測試 Investing.com 爬蟲"""
    print("=== Investing.com 爬蟲測試 ===\n")

    scraper = InvestingComScraper()
    df = scraper.scrape_calendar(days=7)

    if not df.empty:
        print(f"\n✅ 成功爬取 {len(df)} 個事件")
        print(f"\n前 5 個事件:")
        print(df.head())

        print(f"\n數據欄位: {list(df.columns)}")
        print(f"\n國家分布:")
        print(df['Country'].value_counts())
        print(f"\n重要性分布:")
        print(df['Importance'].value_counts())
    else:
        print("❌ 未獲取到數據")


if __name__ == "__main__":
    test_investing_scraper()

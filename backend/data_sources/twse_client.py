"""
TWSE (台灣證券交易所) API 客戶端封裝
Taiwan Stock Exchange API Client Wrapper

使用 TWSE 公開 API 獲取三大法人買賣超、市場統計等數據
"""

import requests
import pandas as pd
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import time


class TWSEClient:
    """台灣證券交易所 API 客戶端"""

    BASE_URL = "https://www.twse.com.tw"

    def __init__(self):
        """初始化客戶端"""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def _get_latest_trading_date(self) -> str:
        """
        取得最近的交易日（排除週末）

        Returns:
            日期字串 (YYYYMMDD)
        """
        today = datetime.now()

        # 如果是週末，往回推到週五
        if today.weekday() == 5:  # 星期六
            today = today - timedelta(days=1)
        elif today.weekday() == 6:  # 星期日
            today = today - timedelta(days=2)

        # 如果是今天且時間還早（14:00前），使用前一個交易日
        if today.date() == datetime.now().date() and datetime.now().hour < 14:
            today = today - timedelta(days=1)
            # 再次檢查週末
            if today.weekday() == 5:
                today = today - timedelta(days=1)
            elif today.weekday() == 6:
                today = today - timedelta(days=2)

        return today.strftime('%Y%m%d')

    def get_institutional_investors(self, date: Optional[str] = None) -> Dict[str, Any]:
        """
        獲取三大法人買賣超數據

        Args:
            date: 日期 (YYYYMMDD)，None 表示最近交易日

        Returns:
            包含外資、投信、自營商買賣超的字典
        """
        if not date:
            date = self._get_latest_trading_date()

        url = f"{self.BASE_URL}/rwd/zh/fund/T86"
        params = {
            'response': 'json',
            'date': date
        }

        try:
            print(f"📊 正在獲取三大法人買賣超數據 ({date})...")
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()

            # 檢查是否有數據
            if 'data' not in data or not data['data']:
                print(f"⚠️  {date} 無交易資料（可能是假日）")
                # 嘗試前一天
                prev_date = (datetime.strptime(date, '%Y%m%d') - timedelta(days=1)).strftime('%Y%m%d')
                return self.get_institutional_investors(prev_date)

            # 解析三大法人數據（取最後一列的總計數據）
            summary_data = data['data'][-1]  # 最後一列是總計

            # 數據格式：['外資及陸資(不含外資自營商)', '買進金額', '賣出金額', '買賣差額', ...]
            result = {
                'date': date,
                'foreign': {
                    'buy': float(summary_data[1].replace(',', '')) if summary_data[1] else 0,
                    'sell': float(summary_data[2].replace(',', '')) if summary_data[2] else 0,
                    'net': float(summary_data[3].replace(',', '')) if summary_data[3] else 0,
                },
                'investment_trust': {
                    'buy': float(summary_data[4].replace(',', '')) if summary_data[4] else 0,
                    'sell': float(summary_data[5].replace(',', '')) if summary_data[5] else 0,
                    'net': float(summary_data[6].replace(',', '')) if summary_data[6] else 0,
                },
                'dealer': {
                    'buy': float(summary_data[7].replace(',', '')) if summary_data[7] else 0,
                    'sell': float(summary_data[8].replace(',', '')) if summary_data[8] else 0,
                    'net': float(summary_data[9].replace(',', '')) if summary_data[9] else 0,
                },
            }

            # 轉換為億元
            for key in result:
                if key != 'date':
                    result[key]['net_billion'] = result[key]['net'] / 100000000

            print(f"✅ 成功獲取三大法人數據")
            print(f"  外資買賣超: {result['foreign']['net_billion']:.2f} 億")
            print(f"  投信買賣超: {result['investment_trust']['net_billion']:.2f} 億")
            print(f"  自營商買賣超: {result['dealer']['net_billion']:.2f} 億")

            return result

        except requests.exceptions.RequestException as e:
            print(f"❌ 獲取三大法人數據失敗: {e}")
            return {}
        except (KeyError, IndexError, ValueError) as e:
            print(f"❌ 解析三大法人數據失敗: {e}")
            return {}

    def get_market_statistics(self, date: Optional[str] = None) -> Dict[str, Any]:
        """
        獲取大盤統計數據（漲跌家數、成交量等）

        Args:
            date: 日期 (YYYYMMDD)，None 表示最近交易日

        Returns:
            市場統計數據字典
        """
        if not date:
            date = self._get_latest_trading_date()

        url = f"{self.BASE_URL}/rwd/zh/afterTrading/MI_INDEX"
        params = {
            'response': 'json',
            'date': date
        }

        try:
            print(f"📈 正在獲取大盤統計數據 ({date})...")
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()

            # 檢查是否有數據
            if 'data8' not in data or not data['data8']:
                print(f"⚠️  {date} 無交易資料（可能是假日）")
                # 嘗試前一天
                prev_date = (datetime.strptime(date, '%Y%m%d') - timedelta(days=1)).strftime('%Y%m%d')
                return self.get_market_statistics(prev_date)

            # 解析漲跌家數統計
            stats = {}
            for item in data['data8']:
                label = item[0]
                value = item[1]

                if '上漲' in label:
                    stats['up_stocks'] = int(value.replace(',', ''))
                elif '下跌' in label:
                    stats['down_stocks'] = int(value.replace(',', ''))
                elif '平盤' in label:
                    stats['flat_stocks'] = int(value.replace(',', ''))
                elif '漲停' in label:
                    stats['limit_up'] = int(value.replace(',', ''))
                elif '跌停' in label:
                    stats['limit_down'] = int(value.replace(',', ''))

            # 計算總家數和比例
            if stats:
                total = stats.get('up_stocks', 0) + stats.get('down_stocks', 0) + stats.get('flat_stocks', 0)
                stats['total_stocks'] = total
                if total > 0:
                    stats['up_ratio'] = (stats.get('up_stocks', 0) / total) * 100
                    stats['down_ratio'] = (stats.get('down_stocks', 0) / total) * 100
                    stats['flat_ratio'] = (stats.get('flat_stocks', 0) / total) * 100

            stats['date'] = date

            print(f"✅ 成功獲取大盤統計數據")
            print(f"  上漲: {stats.get('up_stocks', 0)} 家 ({stats.get('up_ratio', 0):.1f}%)")
            print(f"  下跌: {stats.get('down_stocks', 0)} 家 ({stats.get('down_ratio', 0):.1f}%)")
            print(f"  平盤: {stats.get('flat_stocks', 0)} 家 ({stats.get('flat_ratio', 0):.1f}%)")

            return stats

        except requests.exceptions.RequestException as e:
            print(f"❌ 獲取大盤統計數據失敗: {e}")
            return {}
        except (KeyError, IndexError, ValueError) as e:
            print(f"❌ 解析大盤統計數據失敗: {e}")
            return {}

    def get_all_market_data(self, date: Optional[str] = None) -> Dict[str, Any]:
        """
        一次性獲取所有 TWSE 數據

        Args:
            date: 日期 (YYYYMMDD)，None 表示最近交易日

        Returns:
            包含所有數據的字典
        """
        print("=" * 70)
        print("📦 開始獲取 TWSE 市場數據...")
        print("=" * 70)

        result = {
            'institutional_investors': self.get_institutional_investors(date),
            'market_statistics': self.get_market_statistics(date),
            'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        print()
        print("=" * 70)
        print("✅ TWSE 市場數據獲取完成!")
        print("=" * 70)

        return result


# ========== 測試代碼 ==========

def test_twse_client():
    """測試 TWSE 客戶端"""
    print("=== TWSE 客戶端測試 ===")
    print()

    try:
        client = TWSEClient()
        print("✅ TWSE 客戶端初始化成功")
        print()

        # 測試獲取三大法人
        print("測試獲取三大法人買賣超...")
        institutional = client.get_institutional_investors()
        print()

        # 測試獲取市場統計
        print("測試獲取大盤統計...")
        stats = client.get_market_statistics()
        print()

        # 測試獲取所有數據
        print("測試獲取所有數據...")
        all_data = client.get_all_market_data()
        print()

        print("✅ 所有測試通過")

    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_twse_client()

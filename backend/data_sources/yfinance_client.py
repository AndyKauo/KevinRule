"""
Yahoo Finance API 客戶端封裝
Yahoo Finance API Client Wrapper

使用 yfinance 獲取國際市場數據、加密貨幣和匯率
"""

import yfinance as yf
import pandas as pd
from typing import Dict, List, Optional, Any
from datetime import datetime
import time


class YFinanceClient:
    """Yahoo Finance API 客戶端"""

    # 股票代碼對應表
    TICKER_MAP = {
        # 美股指數
        'DJI': '^DJI',           # 道瓊工業指數
        'SP500': '^GSPC',        # S&P 500
        'NASDAQ': '^IXIC',       # 那斯達克綜合指數
        'SOX': '^SOX',           # 費城半導體指數
        'VIX': '^VIX',           # VIX 恐慌指數
        'DXY': 'DX-Y.NYB',       # 美元指數

        # 加密貨幣
        'BTC': 'BTC-USD',        # 比特幣
        'ETH': 'ETH-USD',        # 以太坊

        # 台灣市場
        'TWII': '^TWII',         # 台灣加權指數
        'TWO': '^TWO',           # 櫃買指數
        '0050.TW': '0050.TW',    # 台灣50 ETF
        'TAIEX': '^TWII',        # 台灣加權指數（別名）

        # 亞洲市場
        'N225': '^N225',         # 日經225
        'KS11': '^KS11',         # 韓國綜合指數
        'HSI': '^HSI',           # 香港恆生指數
        'SSEC': '000001.SS',     # 上證綜合指數
        'SZSE': '399001.SZ',     # 深證成指

        # 匯率
        'USDTWD': 'TWD=X',       # 美元兌台幣
    }

    def __init__(self):
        """初始化客戶端"""
        pass

    def _get_quote(self, ticker: str, retry: int = 3) -> Optional[Dict[str, Any]]:
        """
        獲取單一標的報價

        Args:
            ticker: 股票代碼
            retry: 重試次數

        Returns:
            報價資訊字典
        """
        for attempt in range(retry):
            try:
                stock = yf.Ticker(ticker)
                info = stock.info

                # 獲取當前價格
                current_price = info.get('currentPrice') or info.get('regularMarketPrice')

                # 獲取昨收價
                prev_close = info.get('previousClose') or info.get('regularMarketPreviousClose')

                if current_price is None or prev_close is None:
                    # 嘗試從歷史數據獲取
                    hist = stock.history(period='2d')
                    if not hist.empty:
                        current_price = hist['Close'].iloc[-1]
                        if len(hist) > 1:
                            prev_close = hist['Close'].iloc[-2]
                        else:
                            prev_close = current_price

                if current_price is None:
                    return None

                # 計算漲跌
                change = current_price - prev_close if prev_close else 0
                change_percent = (change / prev_close * 100) if prev_close else 0

                return {
                    'price': round(float(current_price), 2),
                    'change': round(float(change), 2),
                    'change_percent': round(float(change_percent), 2),
                    'prev_close': round(float(prev_close), 2) if prev_close else None
                }

            except Exception as e:
                if attempt == retry - 1:
                    print(f"❌ 獲取 {ticker} 報價失敗: {e}")
                    return None
                time.sleep(1)  # 重試前等待1秒

        return None

    def get_us_indices(self) -> Dict[str, Dict[str, Any]]:
        """
        獲取美股指數

        Returns:
            美股指數字典
        """
        print("📊 正在獲取美股指數數據...")

        indices = ['DJI', 'SP500', 'NASDAQ', 'SOX', 'VIX', 'DXY']
        result = {}

        for key in indices:
            ticker = self.TICKER_MAP[key]
            quote = self._get_quote(ticker)
            if quote:
                result[key] = quote

        return result

    def get_crypto(self) -> Dict[str, Dict[str, Any]]:
        """
        獲取加密貨幣價格

        Returns:
            加密貨幣字典
        """
        print("₿ 正在獲取加密貨幣數據...")

        cryptos = ['BTC', 'ETH']
        result = {}

        for key in cryptos:
            ticker = self.TICKER_MAP[key]
            quote = self._get_quote(ticker)
            if quote:
                result[key] = quote

        return result

    def get_asia_markets(self) -> Dict[str, Dict[str, Any]]:
        """
        獲取亞洲市場指數

        Returns:
            亞洲市場字典
        """
        print("🌏 正在獲取亞洲市場數據...")

        markets = ['N225', 'KS11', 'HSI', 'SSEC', 'SZSE']
        result = {}

        for key in markets:
            ticker = self.TICKER_MAP[key]
            quote = self._get_quote(ticker)
            if quote:
                result[key] = quote

        return result

    def get_forex(self, pair: str = 'USDTWD') -> Optional[Dict[str, Any]]:
        """
        獲取匯率

        Args:
            pair: 貨幣對（預設：美元兌台幣）

        Returns:
            匯率資訊
        """
        print(f"💱 正在獲取 {pair} 匯率...")

        ticker = self.TICKER_MAP.get(pair)
        if not ticker:
            print(f"❌ 不支援的貨幣對: {pair}")
            return None

        return self._get_quote(ticker)

    def get_taiwan_indices(self) -> Dict[str, Dict[str, Any]]:
        """
        獲取台股指數

        Returns:
            台股指數字典
        """
        print("🇹🇼 正在獲取台股指數數據...")

        indices = ['TWII', 'TWO', '0050.TW']
        result = {}

        for key in indices:
            ticker = self.TICKER_MAP[key]
            quote = self._get_quote(ticker)
            if quote:
                result[key] = quote

        return result

    def get_all_market_data(self) -> Dict[str, Any]:
        """
        一次性獲取所有市場數據

        Returns:
            包含所有市場數據的字典
        """
        print("=" * 70)
        print("📦 開始獲取國際市場數據...")
        print("=" * 70)

        result = {
            'us_indices': self.get_us_indices(),
            'crypto': self.get_crypto(),
            'asia_markets': self.get_asia_markets(),
            'forex': {
                'USDTWD': self.get_forex('USDTWD')
            },
            'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        print()
        print("=" * 70)
        print("✅ 國際市場數據獲取完成!")
        print("=" * 70)

        return result


# ========== 測試代碼 ==========

def test_yfinance_client():
    """測試 Yahoo Finance 客戶端"""
    print("=== Yahoo Finance 客戶端測試 ===")
    print()

    try:
        client = YFinanceClient()
        print("✅ 客戶端初始化成功")
        print()

        # 測試美股指數
        print("測試美股指數...")
        us_indices = client.get_us_indices()
        print(f"  獲取到 {len(us_indices)} 個美股指數")
        if 'SP500' in us_indices:
            print(f"  S&P 500: {us_indices['SP500']}")
        print()

        # 測試加密貨幣
        print("測試加密貨幣...")
        crypto = client.get_crypto()
        print(f"  獲取到 {len(crypto)} 種加密貨幣")
        if 'BTC' in crypto:
            print(f"  BTC: {crypto['BTC']}")
        print()

        # 測試亞洲市場
        print("測試亞洲市場...")
        asia = client.get_asia_markets()
        print(f"  獲取到 {len(asia)} 個亞洲市場")
        print()

        # 測試匯率
        print("測試匯率...")
        forex = client.get_forex('USDTWD')
        if forex:
            print(f"  USD/TWD: {forex}")
        print()

        print("✅ 所有測試通過")

    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_yfinance_client()

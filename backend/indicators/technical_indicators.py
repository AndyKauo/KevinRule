"""
技術指標計算模組
Technical Indicators Calculation Module

使用 pandas 和 pandas-ta 計算常用技術指標
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Union


def calculate_ma(
    prices: Union[pd.Series, pd.DataFrame],
    periods: List[int] = [5, 20, 60]
) -> Dict[str, float]:
    """
    計算移動平均線

    Args:
        prices: 價格序列或 DataFrame（如果是 DataFrame 會取最後一列）
        periods: 計算週期列表

    Returns:
        移動平均線字典 {ma_5: 123.45, ma_20: 120.00, ...}
    """
    try:
        # 如果是 DataFrame，轉換為 Series
        if isinstance(prices, pd.DataFrame):
            if prices.empty:
                return {f'ma_{p}': None for p in periods}
            prices = prices.iloc[:, 0] if len(prices.columns) > 0 else prices.iloc[:, 0]

        if prices.empty or len(prices) == 0:
            return {f'ma_{p}': None for p in periods}

        result = {}
        for period in periods:
            if len(prices) >= period:
                ma = prices.rolling(window=period).mean().iloc[-1]
                result[f'ma_{period}'] = round(float(ma), 2) if pd.notna(ma) else None
            else:
                result[f'ma_{period}'] = None

        return result

    except Exception as e:
        print(f"❌ 計算移動平均線失敗: {e}")
        return {f'ma_{p}': None for p in periods}


def calculate_rsi(
    prices: Union[pd.Series, pd.DataFrame],
    period: int = 14
) -> Optional[float]:
    """
    計算 RSI (Relative Strength Index)

    Args:
        prices: 價格序列
        period: RSI 週期（預設 14）

    Returns:
        RSI 值（0-100）
    """
    try:
        # 如果是 DataFrame，轉換為 Series
        if isinstance(prices, pd.DataFrame):
            if prices.empty:
                return None
            prices = prices.iloc[:, 0]

        if prices.empty or len(prices) < period + 1:
            return None

        # 計算價格變化
        delta = prices.diff()

        # 分離漲跌
        gain = delta.where(delta > 0, 0.0)
        loss = -delta.where(delta < 0, 0.0)

        # 計算平均漲跌
        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()

        # 計算 RS
        rs = avg_gain / avg_loss

        # 計算 RSI
        rsi = 100 - (100 / (1 + rs))

        latest_rsi = rsi.iloc[-1]

        return round(float(latest_rsi), 2) if pd.notna(latest_rsi) else None

    except Exception as e:
        print(f"❌ 計算 RSI 失敗: {e}")
        return None


def calculate_macd(
    prices: Union[pd.Series, pd.DataFrame],
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9
) -> Dict[str, Optional[float]]:
    """
    計算 MACD (Moving Average Convergence Divergence)

    Args:
        prices: 價格序列
        fast_period: 快線週期（預設 12）
        slow_period: 慢線週期（預設 26）
        signal_period: 訊號線週期（預設 9）

    Returns:
        MACD 字典 {macd: 1.23, signal: 1.10, histogram: 0.13, trend: '多頭'}
    """
    try:
        # 如果是 DataFrame，轉換為 Series
        if isinstance(prices, pd.DataFrame):
            if prices.empty:
                return {'macd': None, 'signal': None, 'histogram': None, 'trend': None}
            prices = prices.iloc[:, 0]

        if prices.empty or len(prices) < slow_period + signal_period:
            return {'macd': None, 'signal': None, 'histogram': None, 'trend': None}

        # 計算快速和慢速 EMA
        ema_fast = prices.ewm(span=fast_period, adjust=False).mean()
        ema_slow = prices.ewm(span=slow_period, adjust=False).mean()

        # 計算 MACD 線
        macd_line = ema_fast - ema_slow

        # 計算訊號線
        signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()

        # 計算柱狀圖
        histogram = macd_line - signal_line

        # 獲取最新值
        latest_macd = macd_line.iloc[-1]
        latest_signal = signal_line.iloc[-1]
        latest_histogram = histogram.iloc[-1]

        # 判斷趨勢
        if pd.notna(latest_histogram):
            trend = '多頭' if latest_histogram > 0 else '空頭'
        else:
            trend = None

        return {
            'macd': round(float(latest_macd), 2) if pd.notna(latest_macd) else None,
            'signal': round(float(latest_signal), 2) if pd.notna(latest_signal) else None,
            'histogram': round(float(latest_histogram), 2) if pd.notna(latest_histogram) else None,
            'trend': trend
        }

    except Exception as e:
        print(f"❌ 計算 MACD 失敗: {e}")
        return {'macd': None, 'signal': None, 'histogram': None, 'trend': None}


def get_stock_indicators(
    stock_id: str,
    price_data: Union[pd.Series, pd.DataFrame],
    ma_periods: List[int] = [5, 20, 60],
    rsi_period: int = 14
) -> Dict[str, Union[float, str, None]]:
    """
    獲取單支股票的所有技術指標

    Args:
        stock_id: 股票代碼
        price_data: 價格數據（Series 或 DataFrame）
        ma_periods: 移動平均線週期
        rsi_period: RSI 週期

    Returns:
        包含所有指標的字典
    """
    try:
        # 計算移動平均線
        ma_values = calculate_ma(price_data, periods=ma_periods)

        # 計算 RSI
        rsi_value = calculate_rsi(price_data, period=rsi_period)

        # 計算 MACD
        macd_values = calculate_macd(price_data)

        # 合併結果
        indicators = {
            'stock_id': stock_id,
            **ma_values,
            'rsi': rsi_value,
            **macd_values
        }

        return indicators

    except Exception as e:
        print(f"❌ 獲取 {stock_id} 技術指標失敗: {e}")
        return {
            'stock_id': stock_id,
            **{f'ma_{p}': None for p in ma_periods},
            'rsi': None,
            'macd': None,
            'signal': None,
            'histogram': None,
            'trend': None
        }


# ========== 測試代碼 ==========

def test_indicators():
    """測試技術指標計算"""
    print("=== 技術指標計算測試 ===")
    print()

    # 建立測試數據
    dates = pd.date_range('2024-01-01', periods=100, freq='D')
    prices = pd.Series(
        np.random.randn(100).cumsum() + 100,
        index=dates
    )

    print(f"測試數據: {len(prices)} 天的價格數據")
    print(f"最新價格: {prices.iloc[-1]:.2f}")
    print()

    # 測試移動平均線
    print("1. 測試移動平均線:")
    ma = calculate_ma(prices)
    for key, value in ma.items():
        print(f"   {key}: {value}")
    print()

    # 測試 RSI
    print("2. 測試 RSI:")
    rsi = calculate_rsi(prices)
    print(f"   RSI(14): {rsi}")
    print()

    # 測試 MACD
    print("3. 測試 MACD:")
    macd = calculate_macd(prices)
    for key, value in macd.items():
        print(f"   {key}: {value}")
    print()

    # 測試綜合指標
    print("4. 測試綜合指標:")
    all_indicators = get_stock_indicators('TEST', prices)
    for key, value in all_indicators.items():
        print(f"   {key}: {value}")
    print()

    print("✅ 測試完成")


if __name__ == "__main__":
    test_indicators()

"""
FinLab API 客戶端封裝
FinLab API Client Wrapper

參考來源: reference/stockCC-claude/快速開始.py
Patterns copied from reference examples
"""

from typing import Optional, Dict, Any
import pandas as pd
from datetime import datetime
from config.settings import ensure_finlab_login
from backend.etl.finlab_compat import convert_to_pandas, is_finlab_dataframe


class FinLabClient:
    """FinLab API 客戶端"""

    def __init__(self):
        """初始化FinLab客戶端"""
        self._ensure_login()
        self._data = None

    def _ensure_login(self):
        """確保FinLab已登入"""
        if not ensure_finlab_login(verbose=False):
            raise RuntimeError("FinLab API登入失敗")

    def _get_data_module(self):
        """獲取FinLab data模組（延遲導入）"""
        if self._data is None:
            from finlab import data
            self._data = data
        return self._data

    def _get_and_convert(self, field: str) -> pd.DataFrame:
        """
        獲取數據並轉換為pandas DataFrame

        Args:
            field: 數據欄位 (格式: 'table:field')

        Returns:
            pandas DataFrame
        """
        try:
            data = self._get_data_module()
            result = data.get(field)

            # 轉換為pandas DataFrame
            if is_finlab_dataframe(result):
                result = convert_to_pandas(result)

            return result

        except Exception as e:
            print(f"❌ 獲取 {field} 失敗: {e}")
            return pd.DataFrame()

    # ========== 價格數據 ==========

    def get_price_data(self) -> Dict[str, pd.DataFrame]:
        """
        獲取價格相關數據

        Returns:
            包含收盤價、開盤價、最高價、最低價、成交量等的字典
        """
        print("📊 正在獲取價格數據...")
        return {
            'close': self._get_and_convert('price:收盤價'),
            'open': self._get_and_convert('price:開盤價'),
            'high': self._get_and_convert('price:最高價'),
            'low': self._get_and_convert('price:最低價'),
            'volume': self._get_and_convert('price:成交股數'),
            'amount': self._get_and_convert('price:成交金額'),
        }

    def get_close(self) -> pd.DataFrame:
        """獲取收盤價"""
        return self._get_and_convert('price:收盤價')

    def get_volume(self) -> pd.DataFrame:
        """獲取成交量"""
        return self._get_and_convert('price:成交股數')

    # ========== 市值數據 ==========

    def get_market_cap(self) -> pd.DataFrame:
        """
        獲取市值數據（推薦使用，已處理股票分割）

        Returns:
            市值數據 (單位: 元)
        """
        print("💰 正在獲取市值數據...")
        return self._get_and_convert('etl:market_value')

    # ========== 財務報表數據 ==========

    def get_financial_data(self) -> Dict[str, pd.DataFrame]:
        """
        獲取財務報表數據

        Returns:
            包含資產、負債、權益、營收、淨利等的字典
            注意: 所有單位為「仟元」
        """
        print("📋 正在獲取財務報表數據...")
        return {
            # 資產負債表
            'total_assets': self._get_and_convert('financial_statement:資產總額'),
            'total_liabilities': self._get_and_convert('financial_statement:負債總額'),
            'equity': self._get_and_convert('financial_statement:股東權益總額'),
            'cash': self._get_and_convert('financial_statement:現金及約當現金'),
            'inventory': self._get_and_convert('financial_statement:存貨'),
            'current_assets': self._get_and_convert('financial_statement:流動資產'),
            'current_liabilities': self._get_and_convert('financial_statement:流動負債'),
            'common_stock': self._get_and_convert('financial_statement:普通股股本'),

            # 損益表
            'revenue': self._get_and_convert('financial_statement:營業收入淨額'),
            'gross_profit': self._get_and_convert('financial_statement:營業毛利'),
            'operating_income': self._get_and_convert('financial_statement:營業利益'),
            'net_income': self._get_and_convert('financial_statement:歸屬母公司淨利_損'),

            # 現金流量表
            'operating_cash_flow': self._get_and_convert('financial_statement:營業活動之淨現金流入_流出'),
            'investing_cash_flow': self._get_and_convert('financial_statement:投資活動之淨現金流入_流出'),
            'financing_cash_flow': self._get_and_convert('financial_statement:籌資活動之淨現金流入_流出'),
        }

    # ========== 月營收數據 ==========

    def get_monthly_revenue(self) -> Dict[str, pd.DataFrame]:
        """
        獲取月營收數據（台股特有）

        Returns:
            包含當月營收的字典
            注意: 單位為「仟元」
        """
        print("📊 正在獲取月營收數據...")
        revenue = self._get_and_convert('monthly_revenue:當月營收')

        # 計算年增率和月增率
        revenue_yoy = revenue.pct_change(12, fill_method=None) if not revenue.empty else pd.DataFrame()
        revenue_mom = revenue.pct_change(1, fill_method=None) if not revenue.empty else pd.DataFrame()

        return {
            'revenue': revenue,
            'revenue_yoy': revenue_yoy,  # 年增率
            'revenue_mom': revenue_mom,  # 月增率
        }

    # ========== 基本面指標 ==========

    def get_fundamental_ratios(self) -> Dict[str, pd.DataFrame]:
        """
        獲取基本面指標

        Returns:
            包含ROE、ROA、負債比等的字典
        """
        print("📈 正在獲取基本面指標...")
        return {
            'roe': self._get_and_convert('fundamental_features:ROE稅後'),
            'roa': self._get_and_convert('fundamental_features:ROA稅後息前'),
            'debt_ratio': self._get_and_convert('fundamental_features:負債比率'),
            'current_ratio': self._get_and_convert('fundamental_features:流動比率'),
            'quick_ratio': self._get_and_convert('fundamental_features:速動比率'),
        }

    # ========== 殖利率數據 ==========

    def get_dividend_yield(self) -> pd.DataFrame:
        """
        獲取殖利率（推薦使用，已計算好）

        Returns:
            殖利率數據 (單位: %)
        """
        print("💰 正在獲取殖利率數據...")
        dividend_yield = self._get_and_convert('price_earning_ratio:殖利率(%)')
        # 轉換為小數形式 (%)
        return dividend_yield / 100 if not dividend_yield.empty else pd.DataFrame()

    def get_pe_ratio(self) -> pd.DataFrame:
        """獲取本益比"""
        return self._get_and_convert('price_earning_ratio:本益比')

    def get_pb_ratio(self) -> pd.DataFrame:
        """獲取股價淨值比"""
        return self._get_and_convert('price_earning_ratio:股價淨值比')

    # ========== 融資融券數據 ==========

    def get_margin_data(self) -> Dict[str, pd.DataFrame]:
        """
        獲取融資融券數據（台股特有）

        Returns:
            包含融資使用率、融券使用率等的字典
        """
        print("📊 正在獲取融資融券數據...")
        return {
            'margin_ratio': self._get_and_convert('margin_transactions:融資使用率'),
            'short_ratio': self._get_and_convert('margin_transactions:融券使用率'),
            'margin_balance': self._get_and_convert('margin_transactions:融資今日餘額'),
            'short_balance': self._get_and_convert('margin_transactions:融券今日餘額'),
            'margin_buy': self._get_and_convert('margin_transactions:融資買進'),
            'margin_sell': self._get_and_convert('margin_transactions:融資賣出'),
        }

    # ========== 三大法人買賣超 ==========

    def get_institutional_investors_trading(self) -> Dict[str, pd.DataFrame]:
        """
        獲取三大法人買賣超數據（台股特有）

        Returns:
            包含外資、投信、自營商買賣超的字典
        """
        print("💼 正在獲取三大法人買賣超數據...")
        data = self._get_and_convert('institutional_investors_trading_summary:外陸資買賣超股數(不含外資自營商)')

        return {
            'foreign_buy': self._get_and_convert('institutional_investors_trading_summary:外陸資買進股數(不含外資自營商)'),
            'foreign_sell': self._get_and_convert('institutional_investors_trading_summary:外陸資賣出股數(不含外資自營商)'),
            'foreign_net': self._get_and_convert('institutional_investors_trading_summary:外陸資買賣超股數(不含外資自營商)'),
            'investment_trust_buy': self._get_and_convert('institutional_investors_trading_summary:投信買進股數'),
            'investment_trust_sell': self._get_and_convert('institutional_investors_trading_summary:投信賣出股數'),
            'investment_trust_net': self._get_and_convert('institutional_investors_trading_summary:投信買賣超股數'),
            'dealer_buy': self._get_and_convert('institutional_investors_trading_summary:自營商買進股數(自行買賣)'),
            'dealer_sell': self._get_and_convert('institutional_investors_trading_summary:自營商賣出股數(自行買賣)'),
            'dealer_net': self._get_and_convert('institutional_investors_trading_summary:自營商買賣超股數(自行買賣)'),
        }

    # ========== 篩選器 ==========

    def get_filters(self) -> Dict[str, pd.DataFrame]:
        """
        獲取篩選條件（排除問題股票）

        Returns:
            包含全額交割股、注意股等篩選條件的字典
        """
        print("🔍 正在獲取篩選條件...")
        return {
            'exclude_cash_delivery': self._get_and_convert('etl:full_cash_delivery_stock_filter'),
            'exclude_attention': self._get_and_convert('etl:noticed_stock_filter'),
        }

    # ========== 綜合數據獲取 ==========

    def get_all_data(self) -> Dict[str, Any]:
        """
        一次性獲取所有常用數據（用於策略計算）

        Returns:
            包含所有數據的字典
        """
        print("=" * 70)
        print("📦 開始獲取所有數據...")
        print("=" * 70)

        data_dict = {}

        try:
            # 價格數據
            data_dict.update(self.get_price_data())

            # 市值
            data_dict['market_cap'] = self.get_market_cap()

            # 財務報表
            financial = self.get_financial_data()
            data_dict.update(financial)

            # 月營收
            revenue = self.get_monthly_revenue()
            data_dict.update(revenue)

            # 基本面指標
            ratios = self.get_fundamental_ratios()
            data_dict.update(ratios)

            # 殖利率
            data_dict['dividend_yield'] = self.get_dividend_yield()

            # PE/PB
            data_dict['pe_ratio'] = self.get_pe_ratio()
            data_dict['pb_ratio'] = self.get_pb_ratio()

            # 融資融券
            margin = self.get_margin_data()
            data_dict.update(margin)

            # 篩選器
            filters = self.get_filters()
            data_dict.update(filters)

            print()
            print("=" * 70)
            print("✅ 所有數據獲取完成!")
            print("=" * 70)

            return data_dict

        except Exception as e:
            print(f"❌ 數據獲取過程中發生錯誤: {e}")
            return data_dict


# ========== 測試代碼 ==========

def test_finlab_client():
    """測試FinLab客戶端"""
    print("=== FinLab客戶端測試 ===")
    print()

    try:
        client = FinLabClient()
        print("✅ FinLab客戶端初始化成功")
        print()

        # 測試獲取收盤價
        print("測試獲取收盤價...")
        close = client.get_close()
        print(f"  收盤價數據形狀: {close.shape}")
        print(f"  最新日期: {close.index[-1] if not close.empty else 'N/A'}")
        print()

        # 測試獲取市值
        print("測試獲取市值...")
        market_cap = client.get_market_cap()
        print(f"  市值數據形狀: {market_cap.shape}")
        print()

        print("✅ 所有測試通過")

    except Exception as e:
        print(f"❌ 測試失敗: {e}")


if __name__ == "__main__":
    test_finlab_client()

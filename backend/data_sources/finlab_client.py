"""
FinLab API 客戶端封裝
FinLab API Client Wrapper

參考來源: reference/stockCC-claude/快速開始.py
Patterns copied from reference examples
"""

from typing import Optional, Dict, Any, Collection, Set
import pandas as pd
from datetime import datetime
from config.settings import ensure_finlab_login
from backend.etl.finlab_compat import convert_to_pandas, is_finlab_dataframe


# ========== 數據字段常量（用於按需加載）==========

PRICE_FIELDS = {"close", "open", "high", "low", "volume", "amount"}
FINANCIAL_FIELDS = {
    "total_assets",
    "total_liabilities",
    "equity",
    "cash",
    "inventory",
    "current_assets",
    "current_liabilities",
    "common_stock",
    "gross_profit",
    "operating_income",
    "net_income",
    "operating_cash_flow",
    "investing_cash_flow",
    "financing_cash_flow",
    "eps",
}
MONTHLY_REVENUE_FIELDS = {"revenue", "revenue_yoy", "revenue_mom"}
FUNDAMENTAL_RATIO_FIELDS = {"roe", "roa", "debt_ratio", "current_ratio", "quick_ratio"}
MARGIN_FIELDS = {
    "margin_ratio",
    "short_ratio",
    "margin_balance",
    "short_balance",
    "margin_buy",
    "margin_sell",
}
FILTER_FIELDS = {"exclude_cash_delivery", "exclude_attention"}
COMPANY_INFO_FIELDS = {"industry", "company_name", "company_short_name"}
SINGLE_FIELD_KEYS = {"market_cap", "dividend_yield", "pe_ratio", "pb_ratio", "dividend_announcement"}

# 所有可用的數據字段
ALL_AVAILABLE_KEYS: Set[str] = (
    PRICE_FIELDS
    | FINANCIAL_FIELDS
    | MONTHLY_REVENUE_FIELDS
    | FUNDAMENTAL_RATIO_FIELDS
    | MARGIN_FIELDS
    | FILTER_FIELDS
    | COMPANY_INFO_FIELDS
    | SINGLE_FIELD_KEYS
)


class FinLabClient:
    """FinLab API 客戶端"""

    def __init__(self, progress_callback=None):
        """
        初始化FinLab客戶端

        Args:
            progress_callback: 可選的進度回調函數，用於更新 UI 進度顯示
        """
        self._ensure_login()
        self._data = None
        self.progress_callback = progress_callback

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

    def _update_progress(self, message: str):
        """
        更新進度（同時輸出到終端和回調 UI）

        Args:
            message: 進度訊息
        """
        # 保留終端 DEBUG 輸出
        print(message)

        # 如果有提供回調函數，同時更新 UI
        if self.progress_callback:
            self.progress_callback(message)

    def _get_and_convert(self, field: str):
        """
        獲取 FinLab 數據（保留 FinlabDataFrame 原生格式）

        Args:
            field: 數據欄位 (格式: 'table:field')

        Returns:
            FinlabDataFrame（保留原生格式以利用自動對齊功能）

        重要提示:
            FinlabDataFrame 在進行運算時會自動對齊不同頻率的數據：
            - index 取聯集（保留所有時間點）
            - column 取交集（只保留共同股票）
            不要轉換為 pandas DataFrame，否則會失去自動對齊能力！

        參考: reference/finlab_site/finlab_docs_md/reference/dataframe/index.md
        """
        try:
            data = self._get_data_module()
            result = data.get(field)

            # ✅ 直接返回 FinlabDataFrame，保留自動對齊能力
            # ❌ 不要轉換為 pandas：convert_to_pandas(result)
            #
            # 為什麼？當策略中執行 AND 運算時：
            # - FinlabDataFrame: 自動對齊 index（聯集）和 column（交集）
            # - pandas DataFrame: 只取交集，容易變成空集合

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
        self._update_progress("📊 正在獲取價格數據...")
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
        self._update_progress("💰 正在獲取市值數據...")
        return self._get_and_convert('etl:market_value')

    # ========== 財務報表數據 ==========

    def get_financial_data(self) -> Dict[str, pd.DataFrame]:
        """
        獲取財務報表數據

        Returns:
            包含資產、負債、權益、營收、淨利等的字典
            注意: 所有單位為「仟元」
        """
        self._update_progress("📋 正在獲取財務報表數據...")
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

            # 每股盈餘
            'eps': self._get_and_convert('financial_statement:每股盈餘'),
        }

    # ========== 月營收數據 ==========

    def get_monthly_revenue(self) -> Dict[str, pd.DataFrame]:
        """
        獲取月營收數據（台股特有）

        Returns:
            包含當月營收的字典
            注意: 單位為「仟元」
        """
        self._update_progress("📊 正在獲取月營收數據...")
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
        self._update_progress("📈 正在獲取基本面指標...")
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
        self._update_progress("💰 正在獲取殖利率數據...")
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
        self._update_progress("📊 正在獲取融資融券數據...")
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
        self._update_progress("💼 正在獲取三大法人買賣超數據...")
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

    # ========== 公司基本資訊 ==========

    def get_company_info(self) -> Dict[str, pd.Series]:
        """
        獲取公司基本資訊

        Returns:
            包含產業類別等資訊的字典
            注意: 已將 stock_id 設為 index
        """
        self._update_progress("🏢 正在獲取公司基本資訊...")
        company_info = self._get_and_convert('company_basic_info')

        if not company_info.empty:
            # 設置 stock_id 為 index（關鍵步驟！）
            company_info = company_info.set_index('stock_id')

            return {
                'industry': company_info['產業類別'],
                'company_name': company_info['公司名稱'],
                'company_short_name': company_info['公司簡稱'],
            }
        else:
            return {
                'industry': pd.Series(),
                'company_name': pd.Series(),
                'company_short_name': pd.Series(),
            }

    # ========== 股利數據 ==========

    def get_dividend_data(self) -> pd.DataFrame:
        """
        獲取股利數據（Event Table 格式）

        Returns:
            DataFrame: 除權息資訊公告 (Event Table)
                - 每行 = 一筆股利公告事件
                - 重要欄位:
                  • stock_id: 股票代碼
                  • 股利所屬期間: 股利年度 (例如: '111年')
                  • 盈餘分配之股東現金股利(元/股): 現金股利金額
                  • 除息交易日: 除息日期
                  • 公告日期: 公告日期

        注意:
            - 這是 Type 2 (Event Table) 格式，不是 Type 1 (Time Series)
            - 需要使用 stock_id 欄位篩選特定股票
            - 股利所屬期間為民國年，需要轉換為西元年 (民國年 + 1911)
        """
        self._update_progress("💰 正在獲取股利數據...")

        dividend_ann = self._get_and_convert('dividend_announcement')

        if dividend_ann.empty:
            self._log_warning("⚠️  股利數據為空")
            return pd.DataFrame()

        return dividend_ann

    # ========== 篩選器 ==========

    def get_filters(self) -> Dict[str, pd.DataFrame]:
        """
        獲取篩選條件（排除問題股票）

        Returns:
            包含全額交割股、注意股等篩選條件的字典
        """
        self._update_progress("🔍 正在獲取篩選條件...")
        return {
            'exclude_cash_delivery': self._get_and_convert('etl:full_cash_delivery_stock_filter'),
            'exclude_attention': self._get_and_convert('etl:noticed_stock_filter'),
        }

    # ========== 按需數據加載 ==========

    def get_data_bundle(self, keys: Collection[str]) -> Dict[str, Any]:
        """
        根據需求僅載入指定的資料欄位，減少記憶體占用

        Args:
            keys: 需要載入的資料欄位集合

        Returns:
            包含請求資料的字典
        """
        requested: Set[str] = set(keys)
        data_dict: Dict[str, Any] = {}

        if not requested:
            return data_dict

        def include_group(group_keys, loader):
            """載入整個資料組（如果有任何欄位被請求）"""
            matched = requested & group_keys
            if not matched:
                return
            group_data = loader()
            for key in matched:
                if isinstance(group_data, dict):
                    if key in group_data:
                        data_dict[key] = group_data[key]
                else:
                    data_dict[key] = group_data
            requested.difference_update(matched)

        # 價格數據
        include_group(PRICE_FIELDS, self.get_price_data)

        # 市值
        if "market_cap" in requested:
            data_dict["market_cap"] = self.get_market_cap()
            requested.remove("market_cap")

        # 財務數據
        include_group(FINANCIAL_FIELDS, self.get_financial_data)

        # 月營收
        include_group(MONTHLY_REVENUE_FIELDS, self.get_monthly_revenue)

        # 基本面比率
        include_group(FUNDAMENTAL_RATIO_FIELDS, self.get_fundamental_ratios)

        # 殖利率
        if "dividend_yield" in requested:
            data_dict["dividend_yield"] = self.get_dividend_yield()
            requested.remove("dividend_yield")

        # PE/PB
        if "pe_ratio" in requested:
            data_dict["pe_ratio"] = self.get_pe_ratio()
            requested.remove("pe_ratio")

        if "pb_ratio" in requested:
            data_dict["pb_ratio"] = self.get_pb_ratio()
            requested.remove("pb_ratio")

        # 融資融券
        include_group(MARGIN_FIELDS, self.get_margin_data)

        # 公司資訊
        include_group(COMPANY_INFO_FIELDS, self.get_company_info)

        # 股利數據
        if "dividend_announcement" in requested:
            data_dict["dividend_announcement"] = self.get_dividend_data()
            requested.remove("dividend_announcement")

        # 篩選器
        include_group(FILTER_FIELDS, self.get_filters)

        return data_dict

    # ========== 綜合數據獲取 ==========

    def get_all_data(self) -> Dict[str, Any]:
        """
        一次性獲取所有常用數據（用於策略計算）

        Returns:
            包含所有數據的字典
        """
        self._update_progress("=" * 70)
        self._update_progress("📦 開始獲取所有數據...")
        self._update_progress("=" * 70)

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

            # 公司基本資訊（產業分類等）
            company_info = self.get_company_info()
            data_dict['industry'] = company_info['industry']

            # 股利數據（Event Table）
            data_dict['dividend_announcement'] = self.get_dividend_data()

            # 篩選器
            filters = self.get_filters()
            data_dict.update(filters)

            self._update_progress("")
            self._update_progress("=" * 70)
            self._update_progress("✅ 所有數據獲取完成!")
            self._update_progress("=" * 70)

            return data_dict

        except Exception as e:
            error_msg = f"❌ 數據獲取過程中發生錯誤: {e}"
            self._update_progress(error_msg)
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

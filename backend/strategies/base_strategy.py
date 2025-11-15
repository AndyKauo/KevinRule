"""
策略基類
Base Strategy Class

所有選股策略的基礎類別
參考來源: reference/stockCC-claude/finlab_實戰策略範例.py
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Tuple, Set
import pandas as pd
import numpy as np
from datetime import date, datetime
from config.settings import settings


class StrategyBase(ABC):
    """策略基類"""

    # 共用的基礎資料需求。幾乎所有策略都會使用價格、成交量、市值與篩選器。
    BASE_REQUIRED_KEYS: Set[str] = {
        "close",
        "volume",
        "market_cap",
        "exclude_attention",
        "exclude_cash_delivery",
    }

    # 子類可以覆寫或擴充的資料需求集合
    required_data_keys: Set[str] = frozenset()

    def __init__(self, name: str, description: str):
        """
        初始化策略

        Args:
            name: 策略名稱
            description: 策略描述
        """
        self.name = name
        self.description = description

    @abstractmethod
    def screen(
        self,
        data: Dict[str, pd.DataFrame],
        as_of: Optional[date] = None
    ) -> pd.DataFrame:
        """
        執行選股邏輯（子類必須實現）

        Args:
            data: 包含所有必要數據的字典
            as_of: 選股基準日期，None表示使用最新數據

        Returns:
            選股結果 DataFrame，包含以下欄位:
            - stock_id: 股票代碼
            - score: 評分
            - rank: 排名
            - metadata: 其他資訊（JSON格式）
        """
        pass

    def apply_basic_filters(
        self,
        data: Dict[str, pd.DataFrame],
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        min_volume: Optional[int] = None,
        min_market_cap: Optional[float] = None,
        liquidity_percentile: Optional[float] = None,
        exclude_attention: bool = True,
        exclude_cash_delivery: bool = True
    ) -> pd.Series:
        """
        應用基本篩選條件

        Args:
            data: 數據字典
            min_price: 最低價格
            max_price: 最高價格
            min_volume: 最低成交量
            min_market_cap: 最低市值
            liquidity_percentile: 流動性百分位數（保留前X%）
            exclude_attention: 排除注意股
            exclude_cash_delivery: 排除全額交割股

        Returns:
            布林遮罩 Series
        """
        close = data.get('close', pd.DataFrame())
        volume = data.get('volume', pd.DataFrame())
        market_cap = data.get('market_cap', pd.DataFrame())

        # 初始化遮罩（全部True）
        if close.empty:
            return pd.Series(dtype=bool)

        mask = pd.Series(True, index=close.columns)

        # 價格篩選
        if min_price is not None and not close.empty:
            latest_close = close.iloc[-1]
            price_min_mask = (latest_close >= min_price)
            mask &= price_min_mask.reindex(mask.index, fill_value=False)

        if max_price is not None and not close.empty:
            latest_close = close.iloc[-1]
            price_max_mask = (latest_close <= max_price)
            mask &= price_max_mask.reindex(mask.index, fill_value=False)

        # 成交量篩選
        if min_volume is not None and not volume.empty:
            # 20日平均成交量
            avg_volume = volume.rolling(20).mean()
            latest_avg_volume = avg_volume.iloc[-1]
            volume_mask = (latest_avg_volume >= min_volume)
            mask &= volume_mask.reindex(mask.index, fill_value=False)

        # 市值篩選
        if min_market_cap is not None and not market_cap.empty:
            latest_market_cap = market_cap.iloc[-1]
            # 只篩選有市值數據的股票
            market_cap_mask = latest_market_cap >= min_market_cap
            mask &= market_cap_mask.reindex(mask.index, fill_value=False)

        # 流動性篩選
        if liquidity_percentile is not None and not volume.empty:
            avg_volume = volume.rolling(20).mean()
            latest_avg_volume = avg_volume.iloc[-1]
            threshold = latest_avg_volume.quantile(liquidity_percentile)
            liquidity_mask = (latest_avg_volume >= threshold)
            mask &= liquidity_mask.reindex(mask.index, fill_value=False)

        # 排除問題股票
        # 注意: FinLab的filter邏輯是反轉的
        # True = 股票OK (不是注意股/全額交割股)
        # False = 應該排除 (是注意股/全額交割股)
        if exclude_attention and 'exclude_attention' in data:
            exclude_attention_mask = data['exclude_attention']
            if not exclude_attention_mask.empty:
                latest_filter = exclude_attention_mask.iloc[-1]
                # True表示可以保留，直接使用
                mask &= latest_filter.reindex(mask.index, fill_value=False)

        if exclude_cash_delivery and 'exclude_cash_delivery' in data:
            exclude_cash_delivery_mask = data['exclude_cash_delivery']
            if not exclude_cash_delivery_mask.empty:
                latest_filter = exclude_cash_delivery_mask.iloc[-1]
                # True表示可以保留，直接使用
                mask &= latest_filter.reindex(mask.index, fill_value=False)

        return mask

    def get_required_data_keys(self) -> Set[str]:
        """
        取得策略執行所需的資料欄位鍵集合

        Returns:
            包含基礎需求和策略特定需求的資料鍵集合
        """
        return set(self.BASE_REQUIRED_KEYS) | set(self.required_data_keys)

    def standardize(self, factor: pd.DataFrame) -> pd.DataFrame:
        """
        Z-score 標準化

        參考來源: reference/stockCC-claude/快速開始.py

        Args:
            factor: 因子數據

        Returns:
            標準化後的因子
        """
        if factor.empty:
            return factor

        mean = factor.mean(axis=1)
        std = factor.std(axis=1)

        # 避免除以0
        std = std.replace(0, np.nan)

        # 每個時間點進行標準化
        standardized = factor.sub(mean, axis=0).div(std, axis=0)

        return standardized

    def rank_percentile(self, factor: pd.DataFrame, ascending: bool = True) -> pd.DataFrame:
        """
        百分位排名（0-1之間）

        Args:
            factor: 因子數據
            ascending: True表示數值越小排名越高

        Returns:
            百分位排名數據
        """
        if factor.empty:
            return factor

        return factor.rank(axis=1, method='average', ascending=ascending, pct=True)

    def combine_factors(
        self,
        factors: Dict[str, pd.DataFrame],
        weights: Optional[Dict[str, float]] = None
    ) -> pd.DataFrame:
        """
        組合多個因子

        Args:
            factors: 因子字典 {name: dataframe}
            weights: 權重字典 {name: weight}，None表示等權重

        Returns:
            組合後的因子分數
        """
        if not factors:
            return pd.DataFrame()

        # 標準化所有因子
        standardized_factors = {
            name: self.standardize(factor)
            for name, factor in factors.items()
            if not factor.empty
        }

        if not standardized_factors:
            return pd.DataFrame()

        # 設定權重
        if weights is None:
            weights = {name: 1.0 / len(standardized_factors) for name in standardized_factors}

        # 組合因子
        combined = None
        for name, factor in standardized_factors.items():
            weight = weights.get(name, 0)
            if combined is None:
                combined = factor * weight
            else:
                combined = combined + (factor * weight)

        return combined

    def format_result(
        self,
        selections: pd.Series,
        scores: Optional[pd.Series] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> pd.DataFrame:
        """
        格式化選股結果

        Args:
            selections: 選中的股票（布林Series或股票列表）
            scores: 評分Series
            metadata: 額外資訊

        Returns:
            格式化的結果DataFrame
        """
        # 處理selections
        if isinstance(selections, pd.Series):
            if selections.dtype == bool:
                stock_ids = selections[selections].index.tolist()
            else:
                stock_ids = selections.tolist()
        elif isinstance(selections, list):
            stock_ids = selections
        else:
            stock_ids = []

        if not stock_ids:
            return pd.DataFrame(columns=['stock_id', 'score', 'rank', 'metadata'])

        # 建立結果DataFrame
        result = pd.DataFrame({
            'stock_id': stock_ids
        })

        # 添加評分
        if scores is not None:
            result['score'] = result['stock_id'].map(scores)
            result = result.sort_values('score', ascending=False)
        else:
            result['score'] = 100.0

        # 添加排名
        result['rank'] = range(1, len(result) + 1)

        # 添加元數據
        if metadata:
            import json
            result['metadata'] = json.dumps(metadata, ensure_ascii=False)
        else:
            result['metadata'] = '{}'

        return result.reset_index(drop=True)

    def backtest(
        self,
        positions: pd.DataFrame,
        price_data: pd.DataFrame,
        start_date: Optional[str] = None,
        fee_ratio: float = 0.001425,
        tax_ratio: float = 0.003,
        slip: float = 0.001
    ) -> Dict[str, Any]:
        """
        簡易回測（需要安裝finlab）

        Args:
            positions: 持倉DataFrame (日期 x 股票)
            price_data: 價格數據
            start_date: 回測開始日期
            fee_ratio: 手續費率
            tax_ratio: 證交稅率
            slip: 滑價

        Returns:
            回測結果字典
        """
        try:
            from finlab.backtest import sim

            report = sim(
                positions,
                resample='M',
                upload=False,
                fee_ratio=fee_ratio,
                tax_ratio=tax_ratio,
                slip=slip
            )

            return {
                'success': True,
                'report': report
            }

        except ImportError:
            return {
                'success': False,
                'error': '需要安裝finlab套件才能執行回測'
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def calculate_returns(
        self,
        selections: pd.DataFrame,
        price_data: pd.DataFrame,
        periods: List[int] = [1, 5, 20, 60]
    ) -> pd.DataFrame:
        """
        計算選股後的報酬率

        Args:
            selections: 選股結果
            price_data: 價格數據
            periods: 持有期間（交易日）

        Returns:
            包含報酬率的DataFrame
        """
        if selections.empty or price_data.empty:
            return selections

        result = selections.copy()

        for period in periods:
            returns = []
            for stock_id in selections['stock_id']:
                if stock_id in price_data.columns:
                    prices = price_data[stock_id]
                    if len(prices) > period:
                        ret = (prices.iloc[-1] / prices.iloc[-period-1] - 1) * 100
                        returns.append(ret)
                    else:
                        returns.append(np.nan)
                else:
                    returns.append(np.nan)

            result[f'return_{period}d'] = returns

        return result

    def __str__(self):
        """字串表示"""
        return f"{self.name}: {self.description}"

    def __repr__(self):
        """字串表示"""
        return self.__str__()


# ========== 測試代碼 ==========

class DemoStrategy(StrategyBase):
    """示範策略（用於測試）"""

    def __init__(self):
        super().__init__(
            name="示範策略",
            description="這是一個示範策略，選擇市值最大的前10檔股票"
        )

    def screen(
        self,
        data: Dict[str, pd.DataFrame],
        as_of: Optional[date] = None
    ) -> pd.DataFrame:
        """選擇市值最大的前10檔"""
        market_cap = data.get('market_cap', pd.DataFrame())

        if market_cap.empty:
            return pd.DataFrame(columns=['stock_id', 'score', 'rank', 'metadata'])

        # 獲取最新市值
        latest_market_cap = market_cap.iloc[-1]

        # 應用基本篩選
        mask = self.apply_basic_filters(
            data,
            min_price=10,
            min_market_cap=settings.min_market_cap,
            liquidity_percentile=settings.min_liquidity_percentile
        )

        # 篩選後的市值
        filtered_market_cap = latest_market_cap[mask]

        # 選擇前10名
        top_10 = filtered_market_cap.nlargest(10)

        # 格式化結果
        return self.format_result(
            selections=top_10.index.tolist(),
            scores=top_10,
            metadata={'strategy': 'demo', 'top_n': 10}
        )


def test_base_strategy():
    """測試基類"""
    print("=== 策略基類測試 ===")
    print()

    # 創建示範數據
    dates = pd.date_range('2024-01-01', periods=100, freq='D')
    stocks = ['2330', '2317', '2454', '2881', '2882']

    price_data = pd.DataFrame(
        np.random.randn(100, 5) * 10 + 100,
        index=dates,
        columns=stocks
    )

    volume_data = pd.DataFrame(
        np.random.randint(1000000, 10000000, (100, 5)),
        index=dates,
        columns=stocks
    )

    market_cap_data = pd.DataFrame(
        np.random.randn(100, 5) * 1e9 + 5e10,
        index=dates,
        columns=stocks
    )

    data = {
        'close': price_data,
        'volume': volume_data,
        'market_cap': market_cap_data
    }

    # 測試示範策略
    strategy = DemoStrategy()
    print(f"策略: {strategy}")
    print()

    result = strategy.screen(data)
    print("選股結果:")
    print(result)
    print()

    print("✅ 測試完成")


if __name__ == "__main__":
    test_base_strategy()

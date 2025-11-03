"""
Kevin 原始版選股策略模組
嚴格按照 Excel 原始需求實作的策略

使用方式：
    from backend.strategies.original.strategy_manager_original import StrategyManagerOriginal

    manager = StrategyManagerOriginal()
    results = manager.run_all_strategies(data)
"""

from .revenue_momentum_original import RevenueMomentumOriginalStrategy
from .low_price_small_original import LowPriceSmallOriginalStrategy
from .breakout_original import BreakoutOriginalStrategy
from .inst_buying_original import InstBuyingOriginalStrategy
from .capital_increase_original import CapitalIncreaseOriginalStrategy
from .cash_growth_original import CashGrowthOriginalStrategy
from .strategy_manager_original import StrategyManagerOriginal

__all__ = [
    'RevenueMomentumOriginalStrategy',
    'LowPriceSmallOriginalStrategy',
    'BreakoutOriginalStrategy',
    'InstBuyingOriginalStrategy',
    'CapitalIncreaseOriginalStrategy',
    'CashGrowthOriginalStrategy',
    'StrategyManagerOriginal',
]

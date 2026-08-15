"""
手账商城计价引擎 (Pricing Engine)
实现多规则匹配、向下取整（math.floor）、保底 1 蛋能量与最优价比价算法
"""

import math
from typing import List, Optional, Tuple
from ...models import PromotionTarget


def calculate_item_price(
    original_price: int,
    item_type: str,
    shop_item_id: int,
    series_id: Optional[int],
    active_targets: List[PromotionTarget]
) -> Tuple[int, bool]:
    """
    根据当前所有生效活动规则，采用向下取整（Floor）与最优价原则（Min Price）计算最终实付蛋能量
    
    返回:
        (current_price: int, is_on_sale: bool)
    """
    best_price = original_price
    is_on_sale = False

    for target in active_targets:
        matched = False
        if target.target_scope == "ALL":
            matched = True
        elif target.target_scope == "ITEM_TYPE" and target.target_type == item_type:
            matched = True
        elif target.target_scope == "SERIES" and target.target_type == item_type and series_id is not None and series_id == target.target_id:
            matched = True
        elif target.target_scope == "SHOP_ITEM" and target.target_id == shop_item_id:
            matched = True

        if matched:
            price_candidate = original_price
            if target.fixed_price is not None:
                price_candidate = target.fixed_price
            elif target.discount_rate is not None:
                # 严格向下取整（math.floor），保底最低 1 能量
                price_candidate = max(1, math.floor(original_price * target.discount_rate))
            
            if price_candidate < best_price:
                best_price = price_candidate
                is_on_sale = True

    return max(1, best_price), is_on_sale

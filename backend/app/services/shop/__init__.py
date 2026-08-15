"""
手账商城与促销活动核心服务包
包含统一商品管理、促销活动管理、向下取整计价引擎及平滑数据迁移
"""

from .migration import migrate_shop_items, get_next_shop_item_id

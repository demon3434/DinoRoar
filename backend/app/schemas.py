import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field, model_validator


# Token Schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
    is_admin: bool = False

# User Schemas
class UserBase(BaseModel):
    username: str
    nickname: Optional[str] = None

class UserCreate(UserBase):
    password: Optional[str] = None


class UserUpdateLock(BaseModel):
    lock_pattern: str

class UserResetLock(BaseModel):
    lock_pattern: str


class UserResponse(UserBase):
    id: int
    is_admin: bool
    lock_pattern: str
    lock_reset_flag: str
    theme: Optional[str] = "dark-neon"
    egg_energy: int = 0
    is_active: bool = True
    created_at: datetime.datetime


    model_config = ConfigDict(from_attributes=True)

# Attachment Schemas
class AttachmentResponse(BaseModel):
    uuid: str
    file_name: str
    mime_type: str
    file_size: int
    md5: Optional[str] = None
    title: Optional[str] = None
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)

# PersonCategory Schemas
class PersonCategoryBase(BaseModel):
    uuid: str
    name: str
    sort_order: int = 0
    is_deleted: bool = False
    created_at: Optional[datetime.datetime] = None

class PersonCategoryCreate(PersonCategoryBase):
    pass

class PersonCategoryResponse(PersonCategoryBase):
    id: int
    user_id: int
    is_deleted: bool

    model_config = ConfigDict(from_attributes=True)

class PersonCategorySyncPayload(BaseModel):
    categories: List[PersonCategoryCreate]
    deleted_uuids: List[str] = []

# Person Schemas
class PersonBase(BaseModel):
    uuid: str
    name: str
    abbreviation: str
    relationship: str
    category_uuid: Optional[str] = None
    sort_order: int = 0
    color_tag: Optional[str] = "red"
    is_temporary: bool = False
    is_deleted: bool = False

    @model_validator(mode='after')
    def check_category(self) -> 'PersonBase':
        if not self.is_deleted and not self.category_uuid:
            raise ValueError("All active persons must belong to a category")
        return self


class PersonCreate(PersonBase):
    pass

class PersonResponse(PersonBase):
    id: int
    user_id: int
    created_at: datetime.datetime
    is_deleted: bool

    model_config = ConfigDict(from_attributes=True)

class PersonSyncPayload(BaseModel):
    persons: List[PersonCreate]
    deleted_uuids: List[str] = []

# DinoConfig Schemas
class DinoConfigResponse(BaseModel):
    id: int
    legacy_key: str
    name: str
    mood_label: str
    mood_tip: Optional[str] = None
    image_url: str
    mood_score: int
    sort_order: int
    is_active: bool

    model_config = ConfigDict(from_attributes=True)

# Log Schemas
class LogBase(BaseModel):
    uuid: str
    title: Optional[str] = None
    incident_date: datetime.datetime
    mood_dino_id: int
    content: str
    own_thoughts: Optional[str] = None
    updated_at: Optional[datetime.datetime] = None
    version: int = 1
    person_uuids: List[str] = []
    canvas_instance_id: Optional[int] = None
    canvas_aspect_ratio: str = "2:1"

class LogCreate(LogBase):
    pass

class LogResponse(LogBase):
    id: int
    user_id: int
    created_at: datetime.datetime
    is_deleted: bool
    attachments: List[AttachmentResponse] = []
    person_uuids: List[str] = []
    canvas_image_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class LogSyncPayload(BaseModel):
    logs: List[LogCreate]
    deleted_uuids: List[str] = []

class PaginatedLogResponse(BaseModel):
    total: int
    page: int
    limit: int
    items: List[LogResponse]


# Sticker Schemas
class StickerSyncPayload(BaseModel):
    sticker_inventory: str = Field(..., min_length=1, description="本地贴纸库存数据串")
    egg_energy: int = Field(..., ge=0, description="本地累计蛋能量")

class StickerInventoryResponse(BaseModel):
    sticker_inventory: str
    egg_energy: int

    model_config = ConfigDict(from_attributes=True)

class StickerConfigResponse(BaseModel):
    id: int
    series_id: Optional[int] = None
    name: str
    image_url: str
    description: Optional[str] = None
    sort_order: int
    exchange_price: int
    original_price: Optional[int] = None
    is_on_sale: Optional[bool] = False
    is_active: bool = True
    is_deleted: bool = False
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)

class StickerSeriesResponse(BaseModel):
    id: int
    name: str
    sort_order: int
    is_active: bool = True
    is_deleted: bool = False
    created_at: datetime.datetime
    stickers: List[StickerConfigResponse] = []

    model_config = ConfigDict(from_attributes=True)



class StickerSeriesCreate(BaseModel):
    name: str
    sort_order: int = 0

class StickerExchangeRequest(BaseModel):
    sticker_id: int

class StickerSortRequest(BaseModel):
    sticker_ids: Optional[List[int]] = None
    ordered_ids: Optional[List[int]] = None

    def get_ids(self) -> List[int]:
        return self.ordered_ids or self.sticker_ids or []

class StickerSeriesRenameRequest(BaseModel):
    name: str

class StickerSeriesToggleActiveRequest(BaseModel):
    is_active: bool

class StickerSeriesSortRequest(BaseModel):
    series_ids: Optional[List[int]] = None
    ordered_ids: Optional[List[int]] = None

    def get_ids(self) -> List[int]:
        return self.ordered_ids or self.series_ids or []

class StickerUpdateRequest(BaseModel):
    name: str
    exchange_price: int
    sort_order: int
    description: Optional[str] = None
    image_url: Optional[str] = None

class StickerImportConfirmRequest(BaseModel):
    temp_token: str
    selected_series_names: List[str]
    conflict_resolution: str = "rename"

class StickerBatchDeleteRequest(BaseModel):
    sticker_ids: List[int]



# Canvas Schemas
class CanvasInstanceResponse(BaseModel):
    id: int
    canvas_set_id: int
    aspect_ratio: str
    image_url: str
    width: int
    height: int
    is_active: bool = True
    is_deleted: bool = False
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class CanvasSetResponse(BaseModel):
    id: int
    series_id: Optional[int] = None
    name: str
    description: Optional[str] = None
    sort_order: int
    exchange_price: int
    original_price: Optional[int] = None
    is_on_sale: Optional[bool] = False
    is_active: bool = True
    is_deleted: bool = False
    created_at: datetime.datetime
    instances: List[CanvasInstanceResponse] = []

    model_config = ConfigDict(from_attributes=True)



class CanvasSeriesResponse(BaseModel):
    id: int
    name: str
    sort_order: int
    is_active: bool = True
    is_deleted: bool = False
    created_at: datetime.datetime
    sets: List[CanvasSetResponse] = []

    model_config = ConfigDict(from_attributes=True)


class CanvasSyncPayload(BaseModel):
    canvas_inventory: str = ""
    egg_energy: int


# ==========================================
# 统一手账商城与促销活动 (Shop & Promotions)
# ==========================================

class ShopItemResponse(BaseModel):
    shop_item_id: int
    item_type: str
    target_id: int
    original_price: int
    current_price: int
    is_on_sale: bool
    is_active: bool
    sort_order: int
    is_owned: bool = False
    owned_count: int = 0
    asset: dict = {}

    model_config = ConfigDict(from_attributes=True)


class ShopExchangeRequest(BaseModel):
    shop_item_ids: List[int] = Field(..., min_length=1, description="待兑换的统一商品 ID 列表")


class PromotionTargetCreate(BaseModel):
    target_scope: str = Field("ALL", description="作用范围: ALL | ITEM_TYPE | SERIES | SHOP_ITEM")
    target_type: Optional[str] = Field(None, description="STICKER | CANVAS_SET")
    target_id: Optional[int] = Field(None, description="系列 ID 或 shop_item_id")
    discount_rate: Optional[float] = Field(None, ge=0.01, le=1.0, description="折扣率，如 0.8 表示 8 折")
    fixed_price: Optional[int] = Field(None, ge=1, description="单品指定特惠一口价蛋能量")


class PromotionCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="活动名称")
    description: Optional[str] = Field(None, description="活动说明")
    start_time: datetime.datetime = Field(..., description="生效开始时间")
    end_time: datetime.datetime = Field(..., description="生效结束时间")
    is_active: bool = Field(True, description="是否启用")
    targets: List[PromotionTargetCreate] = Field(default_factory=list, description="优惠规则列表")


class PromotionUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    start_time: Optional[datetime.datetime] = None
    end_time: Optional[datetime.datetime] = None
    is_active: Optional[bool] = None
    targets: Optional[List[PromotionTargetCreate]] = None


class PromotionToggleActiveRequest(BaseModel):
    is_active: bool


class PromotionTargetResponse(BaseModel):
    id: int
    promotion_id: int
    target_scope: str
    target_type: Optional[str] = None
    target_id: Optional[int] = None
    discount_rate: Optional[float] = None
    fixed_price: Optional[int] = None
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class PromotionResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    start_time: datetime.datetime
    end_time: datetime.datetime
    is_active: bool
    is_deleted: bool
    created_at: datetime.datetime
    targets: List[PromotionTargetResponse] = []

    model_config = ConfigDict(from_attributes=True)


class PromotionPaginationResponse(BaseModel):
    items: List[PromotionResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# ===================================================================
# 签到与蛋能量变动账本模型 (Check-in & Egg Energy Ledger Schemas)
# ===================================================================

class CheckInRequest(BaseModel):
    request_uuid: str


class CheckInRecordDto(BaseModel):
    id: int
    energy_reward: int
    streak_bonus: int
    is_crit: bool
    streak_days: int
    created_at: str


class WeeklyCheckInDayDto(BaseModel):
    date: str
    day_of_week: int
    checked_in: bool
    energy_reward: int
    streak_bonus: int
    is_crit: bool


class CheckInStatusResponse(BaseModel):
    has_checked_in_today: bool
    today_date: str
    streak_days: int
    current_egg_energy: int
    today_record: Optional[CheckInRecordDto] = None
    weekly_history: List[WeeklyCheckInDayDto] = []


class CheckInResultResponse(BaseModel):
    success: bool
    already_checked_in: bool
    checkin_id: int
    total_reward: int
    base_reward: int
    streak_bonus: int
    is_crit: bool
    streak_days: int
    total_egg_energy: int
    message: str


class CheckInConfigDto(BaseModel):
    base_min: int
    base_max: int
    crit_rate: float
    crit_min: int
    crit_max: int
    streak_enabled: bool
    streak_rules_json: str


class EnergyAssetDisplayDto(BaseModel):
    title: str
    subtitle: Optional[str] = ""
    badge_label: str
    type_icon: Optional[str] = "default"
    image_url: Optional[str] = None
    theme_color: str = "#10B981"
    direction: Optional[str] = "EARN"
    detail_info: Optional[dict] = None


class EnergyTransactionDto(BaseModel):
    id: int
    event_type_id: int
    event_name: str
    change_amount: int
    balance_after: int
    target_type_id: int
    target_id: int
    request_uuid: Optional[str] = None
    transaction_uuid: Optional[str] = None
    created_at: str
    month_group: str = ""
    title: Optional[str] = None
    subtitle: Optional[str] = ""
    badge_label: Optional[str] = None
    type_icon: Optional[str] = "default"
    image_url: Optional[str] = None
    theme_color: Optional[str] = "#10B981"
    direction: Optional[str] = "EARN"
    detail_info: Optional[dict] = None
    asset_display: Optional[EnergyAssetDisplayDto] = None


class EnergySummaryDto(BaseModel):
    current_balance: int = 0
    today_income: int = 0
    today_expense: int = 0
    week_income: int = 0
    week_expense: int = 0
    month_total_income: int = 0
    month_total_expense: int = 0
    month_net: int = 0
    last_month_income: int = 0
    last_month_expense: int = 0
    year_income: int = 0
    year_expense: int = 0



class EnergyTransactionPageResponse(BaseModel):
    total: int
    page: int
    page_size: int
    summary: Optional[EnergySummaryDto] = None
    items: List[EnergyTransactionDto]


class AdminEnergyTransactionDto(EnergyTransactionDto):
    user_id: int
    username: str
    nickname: Optional[str] = None


class AdminEnergyTransactionPageResponse(BaseModel):
    total: int
    page: int
    page_size: int
    total_granted: int = 0
    total_consumed: int = 0
    net_circulation: int = 0
    items: List[AdminEnergyTransactionDto]











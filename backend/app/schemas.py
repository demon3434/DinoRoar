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

# System Settings Schemas
class SystemSettingResponse(BaseModel):
    host_ip: str
    host_port: int
    stt_url: str

    model_config = ConfigDict(from_attributes=True)

class SystemSettingUpdate(BaseModel):
    host_ip: str
    host_port: int
    stt_url: str


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
    sticker_ids: List[int]

class StickerSeriesRenameRequest(BaseModel):
    name: str

class StickerSeriesToggleActiveRequest(BaseModel):
    is_active: bool

class StickerSeriesSortRequest(BaseModel):
    series_ids: List[int]

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







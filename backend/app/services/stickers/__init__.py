"""
Stickers service package exposing CRUD, inventory, import/export, and hierarchical storage modules.
"""

from .crud import (
    get_nested_stickers_config,
    sort_stickers,
    rename_sticker_series,
    toggle_sticker_series_active,
    soft_delete_sticker,
    soft_delete_sticker_series,
    sort_sticker_series,
    update_sticker,
    cascade_delete_series,
    batch_delete_stickers,
    reorder_stickers_in_series,
)

from .inventory import (
    get_user_inventory,
    update_user_inventory,
    exchange_sticker_transaction,
    update_user_sticker_inventory,
)

from .import_export import (
    export_sticker_series_zip,
    preview_import_zip,
    confirm_import_stickers,
    cancel_import_temp,
)

from .storage import (
    STATIC_DIR,
    STICKERS_UPLOAD_DIR,
    TEMP_IMPORT_DIR,
    get_series_upload_dir,
    save_sticker_image_file,
    migrate_legacy_sticker_files,
    cleanup_sticker_orphans,
)

from .image_processor import remove_background_and_shadow

__all__ = [
    "get_nested_stickers_config",
    "sort_stickers",
    "rename_sticker_series",
    "toggle_sticker_series_active",
    "soft_delete_sticker",
    "soft_delete_sticker_series",
    "sort_sticker_series",
    "update_sticker",
    "cascade_delete_series",
    "batch_delete_stickers",
    "get_user_inventory",
    "update_user_inventory",
    "exchange_sticker_transaction",
    "update_user_sticker_inventory",
    "export_sticker_series_zip",
    "preview_import_zip",
    "confirm_import_stickers",
    "cancel_import_temp",
    "STATIC_DIR",
    "STICKERS_UPLOAD_DIR",
    "TEMP_IMPORT_DIR",
    "get_series_upload_dir",
    "save_sticker_image_file",
    "migrate_legacy_sticker_files",
    "cleanup_sticker_orphans",
    "remove_background_and_shadow",
]

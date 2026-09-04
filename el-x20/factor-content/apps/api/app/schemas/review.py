import uuid

from pydantic import BaseModel


class ReviewMediaOut(BaseModel):
    media_asset_id: uuid.UUID
    preview_url: str  # URL firmada, expira (ver storage/s3_client.py)
    asset_type: str


class ReviewItemOut(BaseModel):
    content_item_id: uuid.UUID
    title: str | None
    status: str
    rights_status: str
    factor_score: int
    ai_output: dict | None  # hook/sections/cta/title/hashtags/keywords, editable
    preview: ReviewMediaOut | None


class RejectPayload(BaseModel):
    reason: str | None = None


class CopyrightReviewPayload(BaseModel):
    reason: str | None = None


class BulkActionPayload(BaseModel):
    content_item_ids: list[uuid.UUID]
    action: str  # approve | reject | mark_copyright_review
    reason: str | None = None


class BulkActionResult(BaseModel):
    succeeded: list[str]
    failed: list[dict]


class MetadataEditPayload(BaseModel):
    """Edición de metadata desde Review (spec 11: editar title/caption/
    hashtags). Reutiliza el mismo AIGeneration — marca edited_by_user."""
    title: str | None = None
    cta: str | None = None
    hook: str | None = None
    hashtags: list[str] | None = None
    keywords: list[str] | None = None
    sections: dict[str, str] | None = None

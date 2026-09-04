import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class PostMetricsOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    post_id: uuid.UUID
    collected_at: datetime
    views: int
    likes: int
    comments: int
    shares: int
    saves: int
    completion_rate: float
    followers_gained: int


class DashboardKPIs(BaseModel):
    total_views: int
    views_per_post: float
    median_views: int
    engagement_rate: float
    avg_completion_rate: float
    followers_gained: int

"""Factory de adapters — el scheduler pide un adapter por nombre de
plataforma, nunca importa TikTokAdapter/InstagramAdapter/FacebookAdapter
directamente (ADR 0006)."""
from app.publishers.base import PublisherAdapter
from app.publishers.facebook import FacebookAdapter
from app.publishers.instagram import InstagramAdapter
from app.publishers.mock import MockPublisherAdapter
from app.publishers.tiktok import TikTokAdapter

_ADAPTERS: dict[str, type[PublisherAdapter]] = {
    "tiktok": TikTokAdapter,
    "instagram": InstagramAdapter,
    "facebook": FacebookAdapter,
}


def get_adapter(platform: str, *, use_mock: bool = False) -> PublisherAdapter:
    if use_mock:
        return MockPublisherAdapter()
    adapter_cls = _ADAPTERS.get(platform)
    if not adapter_cls:
        raise ValueError(f"Plataforma no soportada: {platform}")
    return adapter_cls()

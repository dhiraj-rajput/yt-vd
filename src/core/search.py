"""YouTube search via yt-dlp for yt-vd.

Provides a simple search interface using yt-dlp's ``ytsearch`` extractor,
returning results as ``VideoInfo`` dataclass instances.
"""

from __future__ import annotations

import logging
from typing import Any

import yt_dlp

from constants import VideoInfo
from core.ydl_options import with_base_ydl_opts

logger = logging.getLogger(__name__)


def search_youtube(query: str, max_results: int = 10) -> list[VideoInfo]:
    """Search YouTube for videos matching a query.

    Uses yt-dlp's ``ytsearch`` extractor for reliable results without
    needing an API key.

    Args:
        query: Search query string.
        max_results: Maximum number of results to return (1–50).

    Returns:
        A list of ``VideoInfo`` instances for each search result.

    Examples:
        >>> results = search_youtube("python tutorial", max_results=5)
        >>> len(results) <= 5
        True
    """
    max_results = max(1, min(max_results, 50))

    opts: dict[str, Any] = with_base_ydl_opts({
        "skip_download": True,
        "extract_flat": "in_playlist",
        "ignoreerrors": True,
        "default_search": "auto",
    })

    search_url = f"ytsearch{max_results}:{query}"
    results: list[VideoInfo] = []

    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(search_url, download=False)

        if info is None:
            return results

        entries: list[dict[str, Any]] = info.get("entries") or []

        for entry in entries:
            if entry is None:
                continue

            video_info = VideoInfo(
                title=entry.get("title", "Unknown"),
                url=_entry_url(entry),
                video_id=entry.get("id", ""),
                uploader=entry.get("uploader", "Unknown"),
                duration=float(entry.get("duration") or 0.0),
                view_count=int(entry.get("view_count") or 0),
                upload_date=entry.get("upload_date", ""),
                description=entry.get("description", ""),
                thumbnail_url=entry.get("thumbnail", ""),
                formats=[],
                available_qualities=[],
                chapters=entry.get("chapters") or [],
                subtitles=entry.get("subtitles") or {},
            )
            results.append(video_info)

    except Exception:
        logger.exception("YouTube search failed for query: %r", query)

    logger.info("Search for %r returned %d results", query, len(results))
    return results


def _entry_url(entry: dict[str, Any]) -> str:
    webpage_url = entry.get("webpage_url")
    if webpage_url:
        return str(webpage_url)

    url = str(entry.get("url") or "")
    if url.startswith(("http://", "https://")):
        return url

    video_id = str(entry.get("id") or url)
    if video_id:
        return f"https://www.youtube.com/watch?v={video_id}"
    return ""

"""Telegram post havolalaridan message_id ajratish."""

from __future__ import annotations

import re
from typing import Optional, Tuple

from telegram import Bot


def parse_private_channel_link(text: str) -> Optional[Tuple[int, int]]:
    """
    https://t.me/c/1234567890123/55 → (-1001234567890123, 55)
    """
    m = re.search(r"(?:https?://)?t\.me/c/(\d+)/(\d+)", text.strip())
    if not m:
        return None
    internal = int(m.group(1))
    mid = int(m.group(2))
    chat_id = int(f"-100{internal}")
    return chat_id, mid


def parse_public_post_link(text: str) -> Optional[Tuple[str, int]]:
    """https://t.me/username/55 → ('username', 55)"""
    m = re.search(r"(?:https?://)?t\.me/([A-Za-z0-9_]+)/(\d+)", text.strip())
    if not m or m.group(1).lower() == "c":
        return None
    return m.group(1), int(m.group(2))


async def resolve_post_link(
    bot: Bot,
    text: str,
    expected_channel_id: int,
) -> Optional[int]:
    pr = parse_private_channel_link(text)
    if pr:
        cid, mid = pr
        if cid != expected_channel_id:
            return None
        return mid
    pub = parse_public_post_link(text)
    if pub:
        username, mid = pub
        chat = await bot.get_chat(f"@{username}")
        if chat.id != expected_channel_id:
            return None
        return mid
    raw = text.strip()
    if raw.isdigit():
        return int(raw)
    return None

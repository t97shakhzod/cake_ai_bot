"""Muhit sozlamalari (.env)."""

import os
from dataclasses import dataclass
from typing import Optional


def _bool_env(name: str) -> bool:
    v = (os.environ.get(name) or "").strip().lower()
    return v in ("1", "true", "yes", "on")


def _int_env(name: str, default: Optional[int] = None) -> Optional[int]:
    raw = os.environ.get(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        return int(raw.strip())
    except ValueError as e:
        raise ValueError(f"{name} raqam bo‘lishi kerak, hozirgi qiymat: {raw!r}") from e


def _req_int(name: str, default: int) -> int:
    v = _int_env(name, default)
    return default if v is None else v


@dataclass(frozen=True)
class Settings:
    bot_token: str
    channel_id: Optional[int]
    comments_group_id: Optional[int]
    owner_user_id: Optional[int]
    daily_post_hour: int
    daily_post_minute: int
    timezone: str
    weekly_edu_weekday: Optional[int]
    weekly_edu_hour: int
    weekly_edu_minute: int
    owner_tip_weekday: Optional[int]
    owner_tip_hour: int
    owner_tip_minute: int


def load_settings() -> Settings:
    token = (os.environ.get("BOT_TOKEN") or "").strip()
    if not token:
        raise RuntimeError(
            "BOT_TOKEN yo‘q. `.env` faylida BotFather tokenini yozing."
        )
    weekly_off = _bool_env("WEEKLY_EDU_DISABLED")
    tip_off = _bool_env("OWNER_TIP_DISABLED")

    return Settings(
        bot_token=token,
        channel_id=_int_env("CHANNEL_ID"),
        comments_group_id=_int_env("COMMENTS_GROUP_ID"),
        owner_user_id=_int_env("OWNER_USER_ID"),
        daily_post_hour=_req_int("DAILY_POST_HOUR", 9),
        daily_post_minute=_req_int("DAILY_POST_MINUTE", 0),
        timezone=(os.environ.get("TIMEZONE") or "Asia/Tashkent").strip(),
        weekly_edu_weekday=None if weekly_off else _req_int("WEEKLY_EDU_WEEKDAY", 0),
        weekly_edu_hour=_req_int("WEEKLY_EDU_HOUR", 11),
        weekly_edu_minute=_req_int("WEEKLY_EDU_MINUTE", 0),
        owner_tip_weekday=None if tip_off else _req_int("OWNER_TIP_WEEKDAY", 3),
        owner_tip_hour=_req_int("OWNER_TIP_HOUR", 20),
        owner_tip_minute=_req_int("OWNER_TIP_MINUTE", 0),
    )

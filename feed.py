"""Kanal lentasi: qo‘lda + avtomatik yig‘ilgan postlar, haftalik dars, egaga maslahat."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, List, Optional

logger = logging.getLogger(__name__)

_ROOT = Path(__file__).resolve().parent
_DATA = _ROOT / "data"

_STATE_ROTATION = _DATA / "rotation_state.json"
_ROTATION_CFG = _DATA / "channel_rotation.json"
_WEEKLY_EDU = _DATA / "weekly_education.json"
_WEEKLY_EDU_STATE = _DATA / "weekly_edu_state.json"
_OWNER_TIPS = _DATA / "owner_growth_tips.json"
_OWNER_TIP_STATE = _DATA / "owner_tip_state.json"
_PROMO_SNIPPETS = _DATA / "promo_snippets.json"
_PROMO_SNIP_STATE = _DATA / "promo_snippet_state.json"


def _load(path: Path, default: Any) -> Any:
    if not path.is_file():
        return default
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def _save(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def _parse_id_list(raw: Any) -> List[int]:
    out: List[int] = []
    if not raw:
        return out
    for x in raw:
        try:
            out.append(int(x))
        except (TypeError, ValueError):
            logger.warning("channel_rotation: noto‘g‘ri id: %r", x)
    return out


def _rotation_file_data() -> dict:
    return _load(
        _ROTATION_CFG,
        {
            "auto_collect": True,
            "max_collected": 250,
            "manual_message_ids": [],
            "collected_message_ids": [],
        },
    )


def get_all_rotation_message_ids() -> List[int]:
    """Qo‘lda + kanaldan avtomatik yig‘ilgan postlar (takrorlarsiz, avval manual)."""
    cfg = _rotation_file_data()
    manual = _parse_id_list(cfg.get("manual_message_ids"))
    legacy = _parse_id_list(cfg.get("message_ids"))
    collected = _parse_id_list(cfg.get("collected_message_ids"))
    seen: set = set()
    out: List[int] = []
    for mid in manual + legacy + collected:
        if mid in seen:
            continue
        seen.add(mid)
        out.append(mid)
    return out


def record_channel_post_message_id(message_id: int) -> None:
    """Yangi kanal posti kelganda chaqiriladi (faqat bot ishlayotgan paytdan keyingi postlar)."""
    cfg = _rotation_file_data()
    if not cfg.get("auto_collect", True):
        return
    max_keep = int(cfg.get("max_collected") or 250)
    col = list(cfg.get("collected_message_ids") or [])
    if message_id in col:
        col.remove(message_id)
    col.append(message_id)
    while len(col) > max_keep:
        col.pop(0)
    cfg["collected_message_ids"] = col
    _save(_ROTATION_CFG, cfg)
    logger.info("Kanal posti saqlandi: message_id=%s (aylanmada jami ~%s)", message_id, len(col))


def add_manual_message_id(message_id: int) -> None:
    cfg = _rotation_file_data()
    manual = list(cfg.get("manual_message_ids") or [])
    if message_id not in manual:
        manual.append(message_id)
    cfg["manual_message_ids"] = manual
    _save(_ROTATION_CFG, cfg)
    logger.info("Qo‘lda qo‘shildi: message_id=%s", message_id)


def consume_next_rotation_message_id() -> Optional[int]:
    ids = get_all_rotation_message_ids()
    if not ids:
        return None
    state = _load(_STATE_ROTATION, {"next_index": 0})
    idx = int(state.get("next_index") or 0) % len(ids)
    mid = ids[idx]
    state["next_index"] = idx + 1
    _save(_STATE_ROTATION, state)
    return mid


def next_weekly_education_text() -> str:
    data = _load(_WEEKLY_EDU, {"posts": []})
    posts: List[dict] = []
    for p in data.get("posts") or []:
        if not isinstance(p, dict):
            continue
        title = str(p.get("title") or "").strip()
        body = str(p.get("body") or "").strip()
        if title.startswith("SIZ") or body.startswith("SIZ"):
            continue
        posts.append(p)
    if not posts:
        return ""
    st = _load(_WEEKLY_EDU_STATE, {"next_index": 0})
    idx = int(st.get("next_index") or 0) % len(posts)
    st["next_index"] = idx + 1
    _save(_WEEKLY_EDU_STATE, st)
    p = posts[idx]
    title = (p.get("title") or "").strip()
    body = (p.get("body") or "").strip()
    footer = (p.get("footer") or "").strip()
    if str(footer).strip().startswith("SIZ"):
        footer = ""
    parts = [x for x in (title, body, footer) if x]
    return "\n\n".join(parts)


def next_owner_growth_tip() -> str:
    data = _load(_OWNER_TIPS, {"tips": []})
    tips = [
        str(t).strip()
        for t in (data.get("tips") or [])
        if str(t).strip() and not str(t).strip().startswith("SIZ")
    ]
    if not tips:
        return ""
    st = _load(_OWNER_TIP_STATE, {"next_index": 0})
    idx = int(st.get("next_index") or 0) % len(tips)
    st["next_index"] = idx + 1
    _save(_OWNER_TIP_STATE, st)
    return tips[idx]


def next_promo_snippet_fallback() -> str:
    data = _load(_PROMO_SNIPPETS, {"snippets": []})
    snippets = [
        str(s).strip()
        for s in (data.get("snippets") or [])
        if str(s).strip() and not str(s).strip().startswith("SIZ")
    ]
    if not snippets:
        return ""
    st = _load(_PROMO_SNIP_STATE, {"next_index": 0})
    idx = int(st.get("next_index") or 0) % len(snippets)
    st["next_index"] = idx + 1
    _save(_PROMO_SNIP_STATE, st)
    return snippets[idx]


def random_owner_growth_tip() -> str:
    import random

    data = _load(_OWNER_TIPS, {"tips": []})
    tips = [
        str(t).strip()
        for t in (data.get("tips") or [])
        if isinstance(t, str) and str(t).strip() and not str(t).strip().startswith("SIZ")
    ]
    if not tips:
        return ""
    return random.choice(tips)

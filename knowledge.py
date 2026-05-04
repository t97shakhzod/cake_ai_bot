"""Katalogdan javoblar: cakes & sweets eksperti ohangi."""

from __future__ import annotations

import json
import random
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

_CATALOG_PATH = Path(__file__).resolve().parent / "data" / "catalog.json"


def _uz_price(n: int) -> str:
    s = f"{n:,}".replace(",", " ")
    return f"{s} so‘m"


def _is_placeholder(text: Any) -> bool:
    return bool(str(text or "").strip().startswith("SIZ"))


def load_catalog(path=None):
    p = path or _CATALOG_PATH
    if not p.is_file():
        return {"cakes": [], "delivery": {}, "daily_tips": []}
    with p.open(encoding="utf-8") as f:
        return json.load(f)


def _pick_voice(lines: Optional[List[Any]]) -> Optional[str]:
    if not lines:
        return None
    clean = [
        str(x).strip()
        for x in lines
        if x is not None and str(x).strip() and not str(x).strip().startswith("SIZ")
    ]
    if not clean:
        return None
    return random.choice(clean)


def with_group_wait_line(reply: str, catalog: Dict[str, Any]) -> str:
    """Guruhda: ekspert javob + kanal egasini kutish (chiroyli yakun)."""
    foot = catalog.get("group_reassurance_footer")
    if not foot or _is_placeholder(str(foot)):
        foot = (
            "💬 Aniq tasdiq va batafsil javob uchun kanal egasi ham xabaringizni ko‘radi — "
            "biroz sabr qiling, tez orada aloqaga chiqamiz. Rahmat ishonchingiz uchun!"
        )
    return f"{reply.rstrip()}\n\n{str(foot).strip()}".strip()


def polish_reply(reply: str, catalog: Dict[str, Any]) -> str:
    """Savdo va ishonch ohangida qisqa bezatish (ochish/yakun)."""
    bv = catalog.get("brand_voice") or {}
    parts: List[str] = []
    if random.random() < 0.38:
        op = _pick_voice(bv.get("openers"))
        if op:
            parts.append(op)
    parts.append(reply.strip())
    if random.random() < 0.38:
        cl = _pick_voice(bv.get("closings"))
        if cl:
            parts.append(cl)
    return "\n".join(p for p in parts if p).strip()


def build_reply(user_text: str, catalog: Dict[str, Any]) -> Tuple[str, bool]:
    """
    (javob_matni, kanal_egasiga_xabar_yuborilsinmi)
    """
    t_raw = user_text.strip()
    t = t_raw.lower()
    t = re.sub(r"\s+", " ", t)

    greetings = (
        "salom",
        "assalom",
        "hi",
        "hello",
        "hayrli kun",
    )
    if t in greetings or (len(t) <= 12 and any(t.startswith(g) for g in greetings)):
        msg = (
            "Salom! Bizda bugun ham tort va shirinliklar bo‘yicha yordam tayyor. "
            "Qaysi tort yoki narx / yetkazib berish haqida so‘ramoqchisiz?"
        )
        return (polish_reply(msg, catalog), False)

    owner_triggers = (
        "buyurtma",
        "zakaz",
        "заказ",
        "telefon",
        "telifon",
        "qo‘ng‘iroq",
        "qongiroq",
        "individual",
        "to‘y",
        "toy tort",
        "shikoyat",
        "muammo",
    )
    if any(k in t for k in owner_triggers):
        msg = (
            "Rahmat — so‘rovingizni oldik. Kanal egasi tez orada siz bilan bog‘lanadi; "
            "shu paytda eng ommabop tortlarimiz kanal lentasida."
        )
        return (polish_reply(msg, catalog), True)

    delivery = catalog.get("delivery") or {}
    if any(k in t for k in ("dostavka", "yetkaz", "yetkazib", "доставк", "dastavka")):
        if delivery.get("available"):
            summ = delivery.get("summary") or ""
            if _is_placeholder(summ):
                parts = ["Yetkazib berish mavjud — aniq zonalar va narxni kanal egasidan so‘rashingiz mumkin."]
            else:
                parts = [summ or "Yetkazib berish mavjud — buyurtmalar faol."]
            det = delivery.get("detail")
            if det and not _is_placeholder(det):
                parts.append(str(det))
            expert = _pick_voice((catalog.get("brand_voice") or {}).get("expert_lines"))
            body = "\n\n".join(parts)
            if expert:
                body = body + "\n\n" + expert
            return (polish_reply(body, catalog), False)
        return (
            polish_reply("Hozircha yetkazib berish cheklangan — aniq holatni egadan so‘rashingiz mumkin.", catalog),
            False,
        )

    if any(k in t for k in ("narx", "qancha", "narxi", "puli", "sum", "so‘m", "som", "ming", "минг")):
        cakes = [
            c
            for c in (catalog.get("cakes") or [])
            if not str(c.get("name") or "").strip().startswith("SIZ")
        ]
        if not cakes:
            return (
                polish_reply("Narxlarni aniqlash uchun kanal egasi bilan bog‘laning — sizga mos variantni tanlaymiz.", catalog),
                True,
            )
        lines = [
            "Bizda sifat va tarkibga e’tibor beriladi — narxlardan namuna:",
        ]
        for c in cakes:
            name = c.get("name") or c.get("id") or "?"
            price = int(c.get("price_uzs") or 0)
            lines.append(f"• {name}: {_uz_price(price)}")
        lines.append("Aniq buyurtma bo‘yicha egamiz tasdiqlaydi — yozib qoldiring, javob beramiz.")
        return (polish_reply("\n".join(lines), catalog), False)

    cakes = catalog.get("cakes") or []
    for c in cakes:
        if str(c.get("name") or "").strip().startswith("SIZ"):
            continue
        hay = [str(c.get("name") or "").lower()]
        hay.extend(str(k).lower() for k in (c.get("keywords") or []) if k)
        hay = [x for x in hay if len(x) >= 2]
        if any(x in t for x in hay):
            price = int(c.get("price_uzs") or 0)
            short = (c.get("short") or "").strip()
            name = c.get("name") or c.get("id")
            deliv = catalog.get("delivery") or {}
            dnote = (
                "Yetkazib berish: mavjud — zonani aniqlash uchun yozing."
                if deliv.get("available")
                else "Yetkazib berish hozircha cheklangan."
            )
            bits = [
                f"«{name}» — {_uz_price(price)}. {short}".strip(),
                dnote,
                "Buyurtma uchun izohlarda qoldiring — egamiz siz bilan bog‘lanadi.",
            ]
            return (polish_reply(" ".join(b for b in bits if b), catalog), False)

    msg = (
        "Savolingizni tushundim — iltimos javobimizni kuting. "
        "Kanal egasiga xabar ketdi; vaqtingiz bo'lsa yangi postlarni ham ko‘rib chiqing — eng yaxshi takliflar shu yerda."
    )
    return (polish_reply(msg, catalog), True)


def pick_daily_post_text(catalog: Dict[str, Any]) -> str:
    raw_tips = catalog.get("daily_tips") or []
    tips = [
        str(x).strip()
        for x in raw_tips
        if str(x).strip() and not str(x).strip().startswith("SIZ")
    ]
    cakes = [
        c
        for c in (catalog.get("cakes") or [])
        if not str(c.get("name") or "").strip().startswith("SIZ")
    ]
    shop_raw = (catalog.get("shop_name") or "Do‘konimiz").strip()
    shop = shop_raw if not shop_raw.startswith("SIZ") else "Do‘konimiz"
    bv = catalog.get("brand_voice") or {}

    if tips and cakes and random.random() < 0.5:
        c = random.choice(cakes)
        price = int(c.get("price_uzs") or 0)
        name = c.get("name") or c.get("id")
        extra = random.choice(tips) if tips else ""
        hype = _pick_voice(bv.get("hype_lines")) or "Bugun ham buyurtmalar faol."
        line = f"🔥 {shop}: «{name}» — {_uz_price(price)}. {hype}"
        return f"{line}\n\n{extra}".strip()

    if tips:
        line = random.choice(tips)
        op = _pick_voice(bv.get("openers"))
        if op and random.random() < 0.45:
            return f"{op}\n\n{line}".strip()
        return line
    return f"{shop}: tort va shirinliklar — izohlarda savol qoldiring, qisqa javob beramiz."

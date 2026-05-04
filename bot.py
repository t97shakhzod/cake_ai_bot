"""Cake AI — kanal lentasi, izohlar guruhi, haftalik kontent, egaga maslahat."""

from __future__ import annotations

import logging
from datetime import time

from telegram import Update
from telegram.ext import (
    Application,
    CallbackContext,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
from zoneinfo import ZoneInfo

import feed
from config import Settings
from knowledge import (
    build_reply,
    load_catalog,
    pick_daily_post_text,
    with_group_wait_line,
)
from links import resolve_post_link

logger = logging.getLogger(__name__)

MANBA_UZ = (
    "📚 Qayerdan qiziqarli kontent topish (cakes & sweets)\n\n"
    "1) YouTube: «cake decorating», «pastry basics», «buttercream techniques» — "
    "qisqa faktlarni o‘zbekcha qayta so‘zlash va o‘z brendingizga moslashtirish.\n\n"
    "2) Pinterest / Instagram: trenddagi bezaklar, rang palitrasi — g‘oya uchun; "
    "matnni ko‘chirmang, o‘z suratingiz va jarayoningiz bilan tasdiqlang.\n\n"
    "3) Kitob va kurslar: klassik pastry adabiyotlari (ingliz/rus) — "
    "«nima uchun shunday ishlaydi» qismini soddalashtirib auditoriyangizga etkazing.\n\n"
    "4) Raqobatchilar va boshqa shahar tort ustalarining kanallari — "
    "narx/formatni emas, kontent g‘oyasini tahlil qiling (etika: g‘iybat emas, o‘rganish).\n\n"
    "5) Ilmiy qism: ovqat xavfsizligi, saqlash harorati, allergenlar — "
    "qisqa eslatmalar sifatida (masalan WHO, mahalliy sanitariya qoidalari havolalari).\n\n"
    "6) O‘z ishlab chiqarishingiz: «bugun qanday qatlamladi», «xato va tuzatish» — "
    "eng kuchli kontent odatda shu: haqiqiy jarayon + halol narrativ.\n\n"
    "Maslahat: haftada 1 ta chuqur post + 2–3 ta yengil post — ritm barqaror bo‘ladi."
)


def _timezone(settings: Settings) -> ZoneInfo:
    try:
        return ZoneInfo(settings.timezone)
    except Exception:
        logger.exception("Vaqt zonasi noto‘g‘ri: %s — Asia/Tashkent ishlatiladi", settings.timezone)
        return ZoneInfo("Asia/Tashkent")


async def _notify_owner(
    context: ContextTypes.DEFAULT_TYPE,
    settings: Settings,
    update: Update,
    prefix: str,
    body: str,
) -> None:
    if not settings.owner_user_id:
        logger.warning("OWNER_USER_ID yo‘q — egaga Telegram orqali xabar ketmaydi.")
        return
    user = update.effective_user
    chat = update.effective_chat
    label = (
        f"@{user.username}"
        if user and user.username
        else (f"id:{user.id}" if user else "noma'lum")
    )
    chat_label = ""
    if chat:
        title = chat.title or ""
        chat_label = f"{title} ({chat.id})".strip()
    text = f"{prefix}\nFoydalanuvchi: {label}\nJoy: {chat_label}\n\n{body}"[:4000]
    try:
        await context.bot.send_message(chat_id=settings.owner_user_id, text=text)
    except Exception:
        logger.exception("Kanal egasiga xabar yuborilmadi (chat boshlanganmi?)")


async def on_channel_post(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Kanalga yangi post tushganda message_id ni avtomatik saqlash (Bot API tarixni o‘qiy olmaydi)."""
    settings: Settings = context.application.bot_data["settings"]
    if settings.channel_id is None:
        return
    msg = update.effective_message
    if not msg or msg.chat_id != settings.channel_id:
        return
    feed.record_channel_post_message_id(msg.message_id)


async def daily_channel_post(context: CallbackContext) -> None:
    settings: Settings = context.application.bot_data["settings"]
    cid = context.job.chat_id
    if cid is None:
        return
    mid = feed.consume_next_rotation_message_id()
    try:
        if mid is not None:
            await context.bot.copy_message(
                chat_id=cid,
                from_chat_id=cid,
                message_id=mid,
            )
            return
        catalog = load_catalog()
        snippet = feed.next_promo_snippet_fallback()
        core = pick_daily_post_text(catalog)
        text = core if not snippet else f"{snippet}\n\n{core}"
        await context.bot.send_message(chat_id=cid, text=text[:4000])
    except Exception:
        logger.exception(
            "Kunlik kanal posti yuborilmadi — admin huquqi, CHANNEL_ID yoki message_id ni tekshiring"
        )


async def weekly_education_post(context: CallbackContext) -> None:
    cid = context.job.chat_id
    if cid is None:
        return
    body = feed.next_weekly_education_text()
    if not body.strip():
        logger.info("weekly_education: weekly_education.json bo‘sh — post yuborilmadi.")
        return
    header = "📚 Haftalik cakes & sweets bilimi\n\n"
    try:
        await context.bot.send_message(chat_id=cid, text=(header + body)[:4000])
    except Exception:
        logger.exception("Haftalik ta’lim posti yuborilmadi")


async def owner_tip_job(context: CallbackContext) -> None:
    uid = context.job.user_id
    if uid is None:
        return
    tip = feed.next_owner_growth_tip()
    if not tip.strip():
        logger.info("owner_tip: owner_growth_tips.json bo‘sh.")
        return
    header = "📈 Kanalni o‘sirish — qisqa maslahat\n\n"
    try:
        await context.bot.send_message(chat_id=uid, text=(header + tip)[:4000])
    except Exception:
        logger.exception("Egaga maslahat yuborilmadi (/start yuborilganini tekshiring)")


async def on_comments_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings: Settings = context.application.bot_data["settings"]
    msg = update.message
    if not msg or not msg.text:
        return

    user_id = update.effective_user.id

    # 1. FILTR: Agar yozayotgan odam OWNER bo'lsa - indama
    # (settings.owner_user_id bitta raqam yoki ro'yxat bo'lishiga qarab)
    if isinstance(settings.owner_user_id, list):
        if user_id in settings.owner_user_id:
            return
    elif user_id == settings.owner_user_id:
        return

    # 2. FILTR: Agar yozayotgan odam guruh ADMINI bo'lsa - indama
    try:
        chat_member = await context.bot.get_chat_member(update.effective_chat.id, user_id)
        if chat_member.status in ['administrator', 'creator']:
            return
    except Exception:
        # Agar adminlikni tekshirib bo'lmasa, davom etaveradi
        pass

    # Faqat yuqoridagi filtrlardan o'tgan (ya'ni oddiy mijoz) xabarlariga javob beriladi
    catalog = load_catalog()
    reply, _need_owner_flag = build_reply(msg.text, catalog)
    reply = with_group_wait_line(reply, catalog)
    await msg.reply_text(reply[:4000])
    
    await _notify_owner(
        context,
        settings,
        update,
        "📩 Guruhdan yangi murojaat (bot javob berdi; egaga nazorat va yakuniy javob uchun):",
        msg.text,
    )



async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return
    chat = update.effective_chat
    if chat and chat.type == "private":
        await update.message.reply_text(
            "Salom! Men Cake AI yordamchi botman.\n\n"
            "• Kanal: yangi postlar avtomatik aylanmaga qo‘shiladi; kunlik copy + ohang.\n"
            "• Haftada bir: mini-dars post.\n"
            "• Guruh: ekspert javob + egaga xabar.\n"
            "• Ega: /maslahat /manba /qosh\n\n"
            "/help — sozlash"
        )


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return
    chat = update.effective_chat
    if chat and chat.type != "private":
        return
    await update.message.reply_text(
        "Siz faqat quyidagilarni to‘ldirasiz:\n\n"
        "`.env` — BOT_TOKEN, CHANNEL_ID, COMMENTS_GROUP_ID, OWNER_USER_ID, vaqt (va ixtiyoriy WEEKLY_*).\n\n"
        "Kanal postlari:\n"
        "• Bot ishlay boshlagach — yangi har bir post avtomatik `channel_rotation.json` ga yoziladi.\n"
        "• Eski postlar: kanaldan post havolasini oling va egaga: `/qosh https://t.me/...`\n"
        "(Telegram Bot API kanal tarixini o‘qiy olmaydi — bu cheklov.)\n\n"
        "Kontent va ohang: `data/catalog.json` (tortlar, narxlar, yetkazib berish) — tayyor shablon bor, "
        "xohlasangiz o‘zgartirasiz.\n\n"
        "GitHub / server: `docs/PORTFOLIO_UZ.md` ni o‘qing."
    )


async def cmd_maslahat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.effective_user:
        return
    if update.effective_chat.type != "private":
        return
    settings: Settings = context.application.bot_data["settings"]
    if settings.owner_user_id is None or update.effective_user.id != settings.owner_user_id:
        return
    tip = feed.random_owner_growth_tip()
    if not tip:
        await update.message.reply_text("Hozircha maslahatlar yo‘q.")
        return
    await update.message.reply_text(f"📈 Maslahat:\n\n{tip}"[:4000])


async def cmd_manba(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.effective_user:
        return
    if update.effective_chat.type != "private":
        return
    settings: Settings = context.application.bot_data["settings"]
    if settings.owner_user_id is None or update.effective_user.id != settings.owner_user_id:
        return
    await update.message.reply_text(MANBA_UZ[:4000])


async def cmd_qosh(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.effective_user:
        return
    if update.effective_chat.type != "private":
        return
    settings: Settings = context.application.bot_data["settings"]
    if settings.owner_user_id is None or update.effective_user.id != settings.owner_user_id:
        return
    if settings.channel_id is None:
        await update.message.reply_text("Avval .env da CHANNEL_ID ni yozing.")
        return
    arg = " ".join(context.args or [])
    if not arg:
        await update.message.reply_text(
            "Misol:\n"
            "/qosh https://t.me/c/1234567890123/42\n"
            "/qosh https://t.me/kanalingiz/42\n"
            "/qosh 42"
        )
        return
    mid = await resolve_post_link(context.bot, arg, settings.channel_id)
    if mid is None:
        await update.message.reply_text(
            "Havola noto‘g‘ri yoki kanal CHANNEL_ID bilan mos emas. "
            "Maxfiy kanal uchun odatda t.me/c/... havolasi kerak."
        )
        return
    feed.add_manual_message_id(mid)
    await update.message.reply_text(
        f"✅ message_id={mid} aylanmaga qo‘shildi. Ertaga kunlik post vaqtida navbat bilan chiqadi."
    )


def create_application(settings: Settings) -> Application:
    application = Application.builder().token(settings.bot_token).build()
    application.bot_data["settings"] = settings

    application.add_handler(CommandHandler("start", cmd_start))
    application.add_handler(CommandHandler("help", cmd_help))
    application.add_handler(CommandHandler("maslahat", cmd_maslahat))
    application.add_handler(CommandHandler("manba", cmd_manba))
    application.add_handler(CommandHandler("qosh", cmd_qosh))

    if settings.channel_id is not None:
        application.add_handler(
            MessageHandler(
                filters.Chat(chat_id=settings.channel_id)
                & filters.UpdateType.CHANNEL_POSTS,
                on_channel_post,
            )
        )
        logger.info("Kanal postlarini avtomatik yig‘ish: channel_id=%s", settings.channel_id)

    if settings.comments_group_id:
        application.add_handler(
            MessageHandler(
                filters.Chat(chat_id=settings.comments_group_id)
                & filters.TEXT
                & ~filters.COMMAND,
                on_comments_message,
            )
        )
        logger.info("Izohlar guruhi: chat_id=%s", settings.comments_group_id)
    else:
        logger.warning("COMMENTS_GROUP_ID yo‘q — guruh javoblari o‘chirilgan.")

    tz = _timezone(settings)
    jq = application.job_queue

    if jq and settings.channel_id:
        jq.run_daily(
            daily_channel_post,
            time=time(
                hour=settings.daily_post_hour,
                minute=settings.daily_post_minute,
                tzinfo=tz,
            ),
            chat_id=settings.channel_id,
            name="daily_channel_rotation",
        )
        logger.info(
            "Kunlik kanal: %02d:%02d (%s)",
            settings.daily_post_hour,
            settings.daily_post_minute,
            settings.timezone,
        )

        if settings.weekly_edu_weekday is not None:
            jq.run_daily(
                weekly_education_post,
                time=time(
                    hour=settings.weekly_edu_hour,
                    minute=settings.weekly_edu_minute,
                    tzinfo=tz,
                ),
                days=(int(settings.weekly_edu_weekday),),
                chat_id=settings.channel_id,
                name="weekly_education",
            )
            logger.info(
                "Haftalik ta’lim: hafta kuni=%s (0=Dush), %02d:%02d",
                settings.weekly_edu_weekday,
                settings.weekly_edu_hour,
                settings.weekly_edu_minute,
            )

        if settings.owner_user_id is not None and settings.owner_tip_weekday is not None:
            jq.run_daily(
                owner_tip_job,
                time=time(
                    hour=settings.owner_tip_hour,
                    minute=settings.owner_tip_minute,
                    tzinfo=tz,
                ),
                days=(int(settings.owner_tip_weekday),),
                user_id=settings.owner_user_id,
                name="owner_growth_tip",
            )
            logger.info(
                "Ega maslahati: hafta kuni=%s, %02d:%02d",
                settings.owner_tip_weekday,
                settings.owner_tip_hour,
                settings.owner_tip_minute,
            )
    elif settings.channel_id:
        logger.warning(
            'JobQueue yo‘q — reja ishlamaydi. pip install "python-telegram-bot[job-queue]"'
        )

    return application

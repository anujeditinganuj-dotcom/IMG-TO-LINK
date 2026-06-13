"""
ImgBB Telegram Bot — "Image To Link | Img To URL Bot"
v4.0.1 — Pyrogram + ButtonStyle colored buttons
FIX: upload_to_imgbb now uses data= instead of files= (400 Bad Request fix)
"""

import os
import base64
import logging
import time
import asyncio
import random
import aiohttp
from datetime import datetime, timezone

import pyrogram
from pyrogram import Client, filters
from pyrogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
)

try:
    from pyrogram.enums import ButtonStyle, ParseMode
    BUTTON_STYLE_SUPPORTED = True
except ImportError:
    BUTTON_STYLE_SUPPORTED = False
    from pyrogram.enums import ParseMode

# ─────────────────────── config ────────────────────────────────
BOT_TOKEN      = os.getenv("BOT_TOKEN", "7512964694:AAGnG9S83rpDtkqoE8EFzwAWcKw0jfLRzN4")
API_ID         = int(os.getenv("API_ID", "37476811"))
API_HASH       = os.getenv("API_HASH", "7aa60670b871050820086c6267371ee6")
IMGBB_KEY      = os.getenv("IMGBB_KEY", "21ce6d305652e32718d28a9bfb613585")
IMGBB_URL      = "https://api.imgbb.com/1/upload"

UPDATE_CHANNEL = os.getenv("UPDATE_CHANNEL", "https://t.me/log_ak_bots")
SUPPORT_GROUP  = os.getenv("SUPPORT_GROUP",  "https://t.me/log_ak_bots")

# ─────────────────────── Wallhaven Config ──────────────────────
WALLHAVEN_API_KEY = os.getenv("WALLHAVEN_API_KEY", "FsXt5pwoerVZrsV3DwhRctls8YzUev9H")

WALLHAVEN_QUERIES = [
    "anime+girl+portrait", "anime+portrait+face", "anime+girl+close+up",
    "anime+beautiful+face", "anime+school+girl", "anime+school+uniform",
    "anime+fantasy+girl", "anime+magic+girl", "anime+witch+girl",
    "anime+elf+girl", "anime+princess", "anime+dark+girl",
    "anime+gothic+girl", "anime+girl+sakura", "anime+girl+nature",
    "anime+girl+sunset", "anime+girl+rain", "anime+girl+snow",
    "anime+girl+flowers", "anime+girl+forest", "anime+girl+summer",
    "anime+kawaii+girl", "anime+cute+girl", "anime+warrior+girl",
    "anime+cyberpunk+girl", "anime+girl+ocean", "anime+girl+sky",
    "anime+girl+night", "anime+girl+stars", "anime+girl+moon",
    "anime+pink+hair+girl", "anime+blue+hair+girl", "anime+white+hair+girl",
    "anime+kimono+girl", "anime+yukata+girl", "anime+shrine+maiden",
    "anime+waifu", "anime+girl+4k", "anime+cherry+blossom",
    "beautiful+girl+portrait", "asian+girl+portrait+4k",
    "aesthetic+girl+photography", "beautiful+woman+4k",
    "girl+nature+portrait", "cute+girl+wallpaper",
    "girl+sunset+photography", "girl+flowers+photography",
    "girl+rain+photography", "girl+city+night+photography",
]

FALLBACK_PHOTO = "https://i.ibb.co/N6D7D9k0/photo-AQADUw9r-Gz7sa-VV.jpg"

# ─────────────────────── Plain Emojis ──────────────────────────
E_CHECK   = '✔️'
E_CROSS   = '❌'
E_STAR    = '⭐️'
E_ROCKET  = '🚀'
E_IMAGE   = '🖼'
E_LINK    = '🔗'
E_STOP    = '⛔️'
E_INFO    = 'ℹ️'
E_SHIELD  = '🛡'
E_CROWN   = '👑'
E_BOLT    = '⚡️'
E_GEAR    = '⚙️'
E_PENCIL  = '✏️'
E_DIAMOND = '💎'
E_CLOCK   = '⌛'
E_ARROW   = '➡️'
E_PHOTO   = '📷'
E_EXPIRY  = '⏰'
E_TIP     = '💡'
E_WARN    = '⚠️'

# ─────────────────────── Button Emoji IDs ──────────────────────
ICON_INFO    = 5334544901428229844
ICON_CHANNEL = 5271604874419647061
ICON_SUPPORT = 5325547803936572038
ICON_LINK    = 5271604874419647061
ICON_EXPIRY  = 5386367538735104399
ICON_BACK    = 5447183459602669338
ICON_CLOSE   = 5210952531676504517
ICON_GEAR    = 5341715473882955310

# ─────────────────────── Reactions ─────────────────────────────
REACTIONS = [
    "👍", "❤️", "🔥", "🥰", "👏", "😁", "🤯", "😱",
    "🎉", "🤩", "💯", "🤣", "⚡", "🏆", "😎", "👾",
    "🌟", "✨", "💫", "🎯", "🚀", "💎", "👑",
    "🥹", "🫶", "🤌", "💝", "💖", "💗",
]

# ─────────────────────── Expiry config ─────────────────────────
EXPIRY_LABEL_MAP = {
    3600:    "1 Hour",
    86400:   "1 Day",
    604800:  "7 Days",
    2592000: "30 Days",
    None:    "Never",
}

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# ─────────────────────── Pyrogram App ──────────────────────────
app = Client(
    "imgbb_bot",
    bot_token=BOT_TOKEN,
    api_id=API_ID,
    api_hash=API_HASH,
    in_memory=True,
)

# ─────────────────────── per-user state ────────────────────────
user_expiry: dict[int, int | None] = {}
user_state:  dict[int, str] = {}

# ─────────────────────── Wallhaven Fetcher ─────────────────────
async def fetch_random_wallpaper() -> str:
    try:
        query = random.choice(WALLHAVEN_QUERIES)
        page  = random.randint(1, 3)
        url = (
            f"https://wallhaven.cc/api/v1/search"
            f"?categories=011&purity=100&q={query}"
            f"&sorting=random&page={page}&apikey={WALLHAVEN_API_KEY}"
        )
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                resp.raise_for_status()
                data = await resp.json()
                images = data.get("data", [])
                if not images:
                    url_fb = (
                        f"https://wallhaven.cc/api/v1/search"
                        f"?categories=011&purity=100&sorting=random&apikey={WALLHAVEN_API_KEY}"
                    )
                    async with session.get(url_fb, timeout=aiohttp.ClientTimeout(total=10)) as r2:
                        d2 = await r2.json()
                        images = d2.get("data", [])
                if not images:
                    return FALLBACK_PHOTO
                chosen = random.choice(images)
                return chosen.get("path", FALLBACK_PHOTO)
    except Exception as e:
        log.error(f"Wallhaven fetch failed: {e}")
        return FALLBACK_PHOTO

# ─────────────────────── Button Builder ────────────────────────
def make_button(text, callback_data=None, url=None,
                icon_custom_emoji_id=None, style=None):
    kwargs = {"text": text}
    if callback_data:
        kwargs["callback_data"] = callback_data
    if url:
        kwargs["url"] = url
    if BUTTON_STYLE_SUPPORTED:
        if icon_custom_emoji_id:
            kwargs["icon_custom_emoji_id"] = icon_custom_emoji_id
        if style is not None:
            kwargs["style"] = style
    return InlineKeyboardButton(**kwargs)

# ─────────────────────── Keyboards ─────────────────────────────
def start_inline_kb() -> InlineKeyboardMarkup:
    if BUTTON_STYLE_SUPPORTED:
        S = ButtonStyle
        return InlineKeyboardMarkup([
            [
                make_button(" 📢 Update Channel ", url=UPDATE_CHANNEL,
                            icon_custom_emoji_id=ICON_CHANNEL, style=S.PRIMARY),
                make_button(" 💬 Support Group ", url=SUPPORT_GROUP,
                            icon_custom_emoji_id=ICON_SUPPORT, style=S.PRIMARY),
            ],
            [
                make_button(" ℹ️ About Bot ", callback_data="about",
                            icon_custom_emoji_id=ICON_INFO, style=S.PRIMARY),
            ],
        ])
    else:
        return InlineKeyboardMarkup([
            [
                make_button(" 📢 Update Channel ", url=UPDATE_CHANNEL),
                make_button(" 💬 Support Group ", url=SUPPORT_GROUP),
            ],
            [
                make_button(" ℹ️ About Bot ", callback_data="about"),
            ],
        ])

def result_inline_kb(direct_url: str) -> InlineKeyboardMarkup:
    if BUTTON_STYLE_SUPPORTED:
        S = ButtonStyle
        return InlineKeyboardMarkup([
            [
                make_button(" 📋 Copy Link ", url=direct_url,
                            icon_custom_emoji_id=ICON_LINK, style=S.PRIMARY),
                make_button(" ↗️ Share Link ", url=f"https://t.me/share/url?url={direct_url}",
                            icon_custom_emoji_id=ICON_LINK, style=S.PRIMARY),
            ]
        ])
    else:
        return InlineKeyboardMarkup([
            [
                make_button(" 📋 Copy Link ", url=direct_url),
                make_button(" ↗️ Share Link ", url=f"https://t.me/share/url?url={direct_url}"),
            ]
        ])

def main_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📷 Upload Image"), KeyboardButton(text="🔗 Upload URL")],
            [KeyboardButton(text="⏰ Set Expiry"),   KeyboardButton(text="❓ Help")],
        ],
        resize_keyboard=True,
    )

def expiry_inline_kb() -> InlineKeyboardMarkup:
    if BUTTON_STYLE_SUPPORTED:
        S = ButtonStyle
        return InlineKeyboardMarkup([
            [
                make_button(" ⏰ 1 Hour ",  callback_data="exp_3600",    style=S.PRIMARY),
                make_button(" 📅 1 Day ",   callback_data="exp_86400",   style=S.PRIMARY),
            ],
            [
                make_button(" 📅 7 Days ",  callback_data="exp_604800",  style=S.PRIMARY),
                make_button(" 📅 30 Days ", callback_data="exp_2592000", style=S.PRIMARY),
            ],
            [make_button(" ∞ Never ",       callback_data="exp_never",   style=S.PRIMARY)],
            [make_button(" ⬅️ Back ",       callback_data="back_main",
                         icon_custom_emoji_id=ICON_BACK, style=S.DANGER)],
        ])
    else:
        return InlineKeyboardMarkup([
            [
                make_button(" ⏰ 1 Hour ",  callback_data="exp_3600"),
                make_button(" 📅 1 Day ",   callback_data="exp_86400"),
            ],
            [
                make_button(" 📅 7 Days ",  callback_data="exp_604800"),
                make_button(" 📅 30 Days ", callback_data="exp_2592000"),
            ],
            [make_button(" ∞ Never ",       callback_data="exp_never")],
            [make_button(" ⬅️ Back ",       callback_data="back_main")],
        ])

# ─────────────────────── Helpers ───────────────────────────────
def get_expiry(uid: int) -> int | None:
    return user_expiry.get(uid, None)

def expiry_str(uid: int) -> str:
    return EXPIRY_LABEL_MAP.get(get_expiry(uid), "Never")

async def upload_to_imgbb(image_data: str, name: str = None, expiration: int = None) -> dict:
    import requests as _requests

    req_url = f"{IMGBB_URL}?key={IMGBB_KEY}"
    if expiration:
        req_url += f"&expiration={expiration}"

    payload = {"image": image_data}
    if name:
        payload["name"] = name

    loop = asyncio.get_event_loop()
    resp = await loop.run_in_executor(
        None,
        lambda: _requests.post(req_url, data=payload, timeout=60)
    )

    if resp.status_code != 200:
        try:
            err = resp.json().get("error", {}).get("message", resp.text[:200])
        except Exception:
            err = resp.text[:200]
        raise RuntimeError(f"ImgBB {resp.status_code}: {err}")

    data = resp.json()
    if not data.get("success"):
        raise RuntimeError(data.get("error", {}).get("message", "Upload failed"))
    d   = data["data"]
    img = d["image"]
    thr = d.get("thumb", {})
    total_bytes = int(d.get("size", 0))
    size_kb  = total_bytes // 1024
    size_rem = total_bytes % 1024
    exp_label = EXPIRY_LABEL_MAP.get(expiration if expiration else None, "Never")
    ts = int(d.get("time", 0))
    now_utc = (
        datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y/%m/%d - %H:%M:%S")
        if ts else datetime.now(timezone.utc).strftime("%Y/%m/%d - %H:%M:%S")
    )
    return {
        "url":         d["url"],
        "viewer":      d["url_viewer"],
        "thumb":       thr.get("url", d["url"]),
        "width":       d.get("width", "?"),
        "height":      d.get("height", "?"),
        "size_kb":     size_kb,
        "size_bytes":  size_rem,
        "filename":    img["filename"],
        "mime":        img["mime"],
        "ext":         img["extension"],
        "expiry":      exp_label,
        "upload_time": now_utc,
        "name":        d.get("title", img.get("name", img["filename"])),
    }

def build_result_text(r: dict, user_name: str, user_id: int, elapsed: float) -> str:
    return (
        f"{E_CHECK} <b>Image Uploaded Successfully!</b>\n\n"
        "<blockquote>"
        f"{E_IMAGE} <b>Name:</b> {r['name']}\n"
        f"{E_LINK} <b>Direct URL:</b> <a href=\"{r['url']}\">{r['url']}</a>\n"
        f"{E_ARROW} <b>Viewer:</b> <a href=\"{r['viewer']}\">{r['viewer']}</a>\n"
        f"{E_INFO} <b>Size:</b> {r['width']}x{r['height']} | {r['size_kb']} KB\n"
        f"{E_PENCIL} <b>File:</b> {r['filename']} ({r['ext']})\n"
        f"{E_EXPIRY} <b>Expiry:</b> {r['expiry']}\n"
        f"{E_CLOCK} <b>Time:</b> {r['upload_time']} UTC"
        "</blockquote>\n\n"
        f"{E_BOLT} <b>Took:</b> {int(elapsed)}s\n"
        f"{E_CROWN} <b>User:</b> {user_name} (<code>{user_id}</code>)"
    )

# ─────────────────────── /start ────────────────────────────────
@app.on_message(filters.command("start") & filters.private)
async def cmd_start(client: Client, msg: Message):
    user_state.pop(msg.from_user.id, None)
    welcome_text = (
        f"{E_STAR} <b>Welcome to {E_IMAGE} Image To Link Bot | {E_LINK} Img To URL Bot!</b>\n\n"
        f"<blockquote>{E_ROCKET} <b>Lightning Fast Image Hosting</b>\n"
        f"Send me any image or URL, and I will instantly upload it to the cloud, "
        f"providing you with a permanent, direct URL.</blockquote>\n\n"
        f"{E_STOP} <b>18+ content is strictly prohibited!</b> Violators will be banned permanently.\n\n"
        f"<blockquote>{E_INFO} <b>System Specifications</b>\n"
        f"{E_CHECK} Supported Formats: JPG, PNG, BMP, GIF, TIFF, WEBP\n"
        f"{E_SHIELD} Maximum File Size: 32MB</blockquote>\n\n"
        f"{E_CROWN} <b>Session:</b> {msg.from_user.first_name} (ID: <code>{msg.from_user.id}</code>)"
    )
    try:
        photo_url = await asyncio.wait_for(fetch_random_wallpaper(), timeout=5.0)
    except Exception:
        photo_url = FALLBACK_PHOTO
    try:
        await client.send_photo(
            chat_id=msg.chat.id,
            photo=photo_url,
            caption=welcome_text,
            reply_markup=start_inline_kb(),
            parse_mode=ParseMode.HTML,
        )
    except Exception:
        try:
            await client.send_photo(
                chat_id=msg.chat.id,
                photo=FALLBACK_PHOTO,
                caption=welcome_text,
                reply_markup=start_inline_kb(),
                parse_mode=ParseMode.HTML,
            )
        except Exception:
            await msg.reply(welcome_text, reply_markup=start_inline_kb(), parse_mode=ParseMode.HTML)

    await msg.reply(
        f"{E_ARROW} <b>Choose an option:</b>",
        reply_markup=main_kb(),
        parse_mode=ParseMode.HTML,
    )
    try:
        await msg.react(random.choice(REACTIONS), big=True)
    except Exception:
        pass

# ─────────────────────── /help ─────────────────────────────────
@app.on_message(filters.command("help") & filters.private)
@app.on_message(filters.regex("^❓ Help$") & filters.private)
async def cmd_help(client: Client, msg: Message):
    user_state.pop(msg.from_user.id, None)
    uid = msg.from_user.id
    await msg.reply(
        f"📖 <b>Hᴏᴡ Tᴏ Uꜱᴇ Iᴍᴀɢᴇ Tᴏ Lɪɴᴋ Bᴏᴛ</b>\n\n"
        f"1️⃣ Sᴇɴᴅ ᴍᴇ ᴀɴʏ ɪᴍᴀɢᴇ (ᴘʜᴏᴛᴏ ᴏʀ ꜰɪʟᴇ).\n"
        f"2️⃣ I ᴡɪʟʟ ᴜᴘʟᴏᴀᴅ ɪᴛ ᴛᴏ IᴍɢBB ᴄʟᴏᴜᴅ ꜱᴛᴏʀᴀɢᴇ.\n"
        f"3️⃣ Yᴏᴜ ᴡɪʟʟ ɢᴇᴛ ᴀ ᴘᴇʀᴍᴀɴᴇɴᴛ ᴅɪʀᴇᴄᴛ URL!\n\n"
        f"📌 Sᴜᴘᴘᴏʀᴛᴇᴅ Fᴏʀᴍᴀᴛꜱ: JPG, PNG, BMP, GIF, TIFF, WEBP\n"
        f"📦 Mᴀx Sɪᴢᴇ: 32MB\n\n"
        f"🤖 <b>Fᴇᴀᴛᴜʀᴇꜱ:</b>\n"
        f"  📷 Uᴘʟᴏᴀᴅ Iᴍᴀɢᴇ — Sᴇɴᴅ ᴀɴʏ ɪᴍᴀɢᴇ ᴛᴏ ᴜᴘʟᴏᴀᴅ\n"
        f"  🔗 Uᴘʟᴏᴀᴅ URL — Uᴘʟᴏᴀᴅ ɪᴍᴀɢᴇ ꜰʀᴏᴍ ᴀ URL\n"
        f"  ⏰ Sᴇᴛ Exᴘɪʀʏ — Sᴇᴛ ᴀᴜᴛᴏ-ᴅᴇʟᴇᴛᴇ ᴛɪᴍᴇʀ\n"
        f"  {E_PENCIL} Cᴀᴘᴛɪᴏɴ — Aᴅᴅ ᴄᴀᴘᴛɪᴏɴ ꜰᴏʀ ᴄᴜꜱᴛᴏᴍ ꜰɪʟᴇɴᴀᴍᴇ\n\n"
        f"{E_EXPIRY} Current Expiry: <b>{expiry_str(uid)}</b>",
        reply_markup=main_kb(),
        parse_mode=ParseMode.HTML,
    )

# ─────────────────────── /about command ──────────────────────
@app.on_message(filters.command("about") & filters.private)
async def cmd_about(client: Client, msg: Message):
    text = (
        f"{E_INFO} <b>ABOUT IMAGE TO LINK BOT</b>\n\n"
        f"<blockquote>{E_ROCKET} <b>Bot Info:</b>\n"
        f"{E_STAR} <b>Name:</b> Image To Link Bot\n"
        f"{E_GEAR} <b>Version:</b> 4.0.1 (Pyrogram)\n"
        f"{E_SHIELD} <b>Features:</b> Wallhaven Wallpapers + ImgBB Hosting\n"
        f"{E_BOLT} <b>Library:</b> Pyrogram async</blockquote>\n\n"
        f"{E_STOP} <b>18+ content strictly prohibited!</b>\n"
        f"Violation = Permanent Ban {E_CROSS}"
    )
    await msg.reply(text, reply_markup=main_kb(), parse_mode=ParseMode.HTML)

# ─────────────────────── About callback ───────────────────────
@app.on_callback_query(filters.regex("^about$"))
async def about_cb(client: Client, cb: CallbackQuery):
    text = (
        f"{E_INFO} <b>ABOUT IMAGE TO LINK BOT</b>\n\n"
        f"<blockquote>{E_ROCKET} <b>Bot Info:</b>\n"
        f"{E_STAR} <b>Name:</b> Image To Link Bot\n"
        f"{E_GEAR} <b>Version:</b> 4.0.1 (Pyrogram)\n"
        f"{E_SHIELD} <b>Features:</b> Wallhaven Wallpapers + ImgBB Hosting\n"
        f"{E_BOLT} <b>Library:</b> Pyrogram async</blockquote>\n\n"
        f"{E_STOP} <b>18+ content strictly prohibited!</b>\n"
        f"Violation = Permanent Ban {E_CROSS}"
    )
    if BUTTON_STYLE_SUPPORTED:
        back_btn = InlineKeyboardMarkup([[
            make_button(" ⬅️ Back ", callback_data="back_start",
                        icon_custom_emoji_id=ICON_BACK, style=ButtonStyle.DANGER)
        ]])
    else:
        back_btn = InlineKeyboardMarkup([[
            make_button(" ⬅️ Back ", callback_data="back_start")
        ]])
    try:
        await cb.edit_message_caption(caption=text, reply_markup=back_btn, parse_mode=ParseMode.HTML)
    except Exception:
        await cb.message.reply(text, reply_markup=back_btn, parse_mode=ParseMode.HTML)
    await cb.answer()

@app.on_callback_query(filters.regex("^back_start$"))
async def back_start_cb(client: Client, cb: CallbackQuery):
    welcome_text = (
        f"{E_STAR} <b>Welcome to {E_IMAGE} Image To Link Bot!</b>\n\n"
        f"<blockquote>{E_ROCKET} <b>Lightning Fast Image Hosting</b>\n"
        f"Send any image or URL — get a permanent direct link instantly!</blockquote>\n\n"
        f"{E_STOP} <b>18+ content is strictly prohibited!</b>\n\n"
        f"<blockquote>{E_INFO} <b>Supported:</b> JPG, PNG, BMP, GIF, TIFF, WEBP\n"
        f"{E_SHIELD} <b>Max Size:</b> 32MB</blockquote>"
    )
    try:
        photo_url = await asyncio.wait_for(fetch_random_wallpaper(), timeout=5.0)
    except Exception:
        photo_url = FALLBACK_PHOTO
    try:
        from pyrogram.types import InputMediaPhoto
        await cb.edit_message_media(
            media=InputMediaPhoto(media=photo_url, caption=welcome_text),
            reply_markup=start_inline_kb(),
        )
    except Exception:
        await cb.edit_message_caption(
            caption=welcome_text,
            reply_markup=start_inline_kb(),
            parse_mode=ParseMode.HTML,
        )
    await cb.answer()

# ─────────────────────── Upload Image ──────────────────────────
@app.on_message(filters.regex("^📷 Upload Image$") & filters.private)
async def ask_for_image(client: Client, msg: Message):
    user_state[msg.from_user.id] = "image"
    await msg.reply(
        f"{E_PHOTO} <b>Upload Image</b>\n\n"
        f"{E_ARROW} Send me any image (photo or file)!\n"
        f"{E_TIP} Send /cancel to cancel.",
        reply_markup=main_kb(),
        parse_mode=ParseMode.HTML,
    )

# ─────────────────────── Upload URL ────────────────────────────
@app.on_message(filters.regex("^🔗 Upload URL$") & filters.private)
async def ask_for_url(client: Client, msg: Message):
    user_state[msg.from_user.id] = "url"
    await msg.reply(
        f"{E_LINK} <b>Upload URL</b>\n\n"
        f"{E_ARROW} Send me an image URL!\n"
        f"{E_TIP} Send /cancel to cancel.",
        reply_markup=main_kb(),
        parse_mode=ParseMode.HTML,
    )

# ─────────────────────── Set Expiry ────────────────────────────
@app.on_message(filters.regex("^⏰ Set Expiry$") & filters.private)
async def ask_expiry(client: Client, msg: Message):
    uid = msg.from_user.id
    await msg.reply(
        f"{E_EXPIRY} <b>Select Auto-Delete Timer</b>\n\n"
        f"{E_INFO} Current: <b>{expiry_str(uid)}</b>",
        reply_markup=expiry_inline_kb(),
        parse_mode=ParseMode.HTML,
    )

# ─────────────────────── Expiry callbacks ──────────────────────
@app.on_callback_query(filters.regex("^exp_"))
async def expiry_cb(client: Client, cb: CallbackQuery):
    uid  = cb.from_user.id
    data = cb.data
    if data == "exp_never":
        user_expiry[uid] = None
        label = "Never"
    else:
        secs = int(data.split("_")[1])
        user_expiry[uid] = secs
        label = EXPIRY_LABEL_MAP.get(secs, "Never")
    await cb.answer(f"✅ Expiry set to {label}", show_alert=True)
    await cb.message.delete()

@app.on_callback_query(filters.regex("^back_main$"))
async def back_main_cb(client: Client, cb: CallbackQuery):
    await cb.message.delete()
    await cb.answer()

# ─────────────────────── Back / Cancel ─────────────────────────
@app.on_message(filters.regex("^⬅️ Back$") & filters.private)
async def go_back(client: Client, msg: Message):
    user_state.pop(msg.from_user.id, None)
    await msg.reply(f"{E_ARROW} Main Menu", reply_markup=main_kb())

@app.on_message(filters.command("cancel") & filters.private)
async def cmd_cancel(client: Client, msg: Message):
    user_state.pop(msg.from_user.id, None)
    await msg.reply(f"{E_CHECK} Cancelled.", reply_markup=main_kb(), parse_mode=ParseMode.HTML)

# ─────────────────────── Handle Image ──────────────────────────
async def _do_upload_image(client: Client, msg: Message):
    uid   = msg.from_user.id
    uname = msg.from_user.first_name
    name  = msg.caption or None
    user_state.pop(uid, None)

    status_msg = await msg.reply(f"{E_CLOCK} <b>Uploading...</b>", parse_mode=ParseMode.HTML)
    t_start = time.monotonic()

    try:
        if msg.document:
            file_id = msg.document.file_id
        else:
            # msg.photo is a Photo object, not a list — use .file_id directly
            file_id = msg.photo.file_id

        file_path = await client.download_media(file_id, in_memory=True)
        if hasattr(file_path, 'read'):
            file_path.seek(0)
            raw = file_path.read()
        elif hasattr(file_path, 'getvalue'):
            raw = file_path.getvalue()
        else:
            with open(str(file_path), 'rb') as f:
                raw = f.read()

        if not raw:
            raise RuntimeError("Downloaded file is empty")

        b64 = base64.b64encode(raw).decode()
        result  = await upload_to_imgbb(b64, name=name, expiration=get_expiry(uid))
        elapsed = time.monotonic() - t_start

        await status_msg.delete()
        text = build_result_text(result, uname, uid, elapsed)
        kb   = result_inline_kb(result["url"])
        await client.send_photo(
            chat_id=msg.chat.id, photo=result["url"],
            caption=text, reply_markup=kb, parse_mode=ParseMode.HTML,
        )
        try:
            await msg.react(random.choice(["🤩", "🔥", "✨", "💎", "⚡"]), big=True)
        except Exception:
            pass
    except Exception as e:
        try:
            await status_msg.delete()
        except Exception:
            pass
        await msg.reply(f"{E_CROSS} <b>Upload failed:</b> {e}", parse_mode=ParseMode.HTML)

@app.on_message(filters.private & (filters.photo | filters.document))
async def handle_image(client: Client, msg: Message):
    await _do_upload_image(client, msg)

# ─────────────────────── Handle URL ────────────────────────────
KEYBOARD_TEXTS = [
    "📷 Upload Image", "🔗 Upload URL", "⏰ Set Expiry",
    "❓ Help", "⬅️ Back", "⏰ 1 Hour", "📅 1 Day",
    "📅 7 Days", "📅 30 Days", "∞ Never",
]

@app.on_message(filters.private & filters.text & ~filters.command(["start","help","cancel","about"]))
async def handle_text(client: Client, msg: Message):
    uid  = msg.from_user.id
    text = msg.text.strip()

    if text in KEYBOARD_TEXTS:
        return

    if user_state.get(uid) != "url":
        return

    if not text.startswith("http"):
        await msg.reply(f"{E_CROSS} Invalid URL. Send a valid http/https image URL.")
        return

    user_state.pop(uid, None)
    uname   = msg.from_user.first_name
    status  = await msg.reply(f"{E_CLOCK} <b>Uploading...</b>", parse_mode=ParseMode.HTML)
    t_start = time.monotonic()

    try:
        result  = await upload_to_imgbb(text, expiration=get_expiry(uid))
        elapsed = time.monotonic() - t_start
        await status.delete()
        result_text = build_result_text(result, uname, uid, elapsed)
        kb = result_inline_kb(result["url"])
        await client.send_photo(
            chat_id=msg.chat.id, photo=result["url"],
            caption=result_text, reply_markup=kb, parse_mode=ParseMode.HTML,
        )
        try:
            await msg.react(random.choice(["🤩", "🔥", "✨", "💎", "⚡"]), big=True)
        except Exception:
            pass
    except Exception as e:
        try:
            await status.delete()
        except Exception:
            pass
        await msg.reply(f"{E_CROSS} <b>Upload failed:</b> {e}", parse_mode=ParseMode.HTML)

# ─────────────────────── Run ───────────────────────────────────
if __name__ == "__main__":
    app.run()

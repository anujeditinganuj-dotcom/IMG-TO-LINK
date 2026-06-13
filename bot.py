"""
ImgBB Telegram Bot — "Image To Link | Img To URL Bot"
v3.0.0 — Wallhaven random wallpaper + Premium emoji + ButtonStyle
"""

import os
import base64
import logging
import time
import asyncio
import random
import aiohttp
from datetime import datetime, timezone

import requests
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReactionTypeEmoji,
)

# ─────────────────────── config ────────────────────────────────
BOT_TOKEN      = os.getenv("BOT_TOKEN", "7512964694:AAFz7d7LoMLPm6z2P5wVKtJl_kKDN4JTDmo")
IMGBB_KEY      = os.getenv("IMGBB_KEY",  "70ee073479a71bce3aed7598ace7eee8")
IMGBB_URL      = "https://api.imgbb.com/1/upload"

UPDATE_CHANNEL = os.getenv("UPDATE_CHANNEL", "https://t.me/log_ak_bots")
SUPPORT_GROUP  = os.getenv("SUPPORT_GROUP",  "https://t.me/log_ak_bots")

# ─────────────────────── Wallhaven Config ──────────────────────
WALLHAVEN_API_KEY = os.getenv("WALLHAVEN_API_KEY", "FsXt5pwoerVZrsV3DwhRctls8YzUev9H")

WALLHAVEN_QUERIES = [
    "anime+girl+portrait", "anime+portrait+face", "anime+girl+close+up",
    "anime+beautiful+face", "anime+school+girl", "anime+school+uniform",
    "anime+sailor+uniform", "anime+fantasy+girl", "anime+magic+girl",
    "anime+witch+girl", "anime+elf+girl", "anime+princess",
    "anime+dark+girl", "anime+gothic+girl", "anime+demon+girl",
    "anime+vampire+girl", "anime+girl+sakura", "anime+girl+nature",
    "anime+girl+sunset", "anime+girl+rain", "anime+girl+snow",
    "anime+girl+flowers", "anime+girl+forest", "anime+girl+summer",
    "anime+girl+winter", "anime+girl+spring", "anime+girl+autumn",
    "anime+kawaii+girl", "anime+cute+girl", "anime+chibi+girl",
    "anime+warrior+girl", "anime+sword+girl", "anime+ninja+girl",
    "anime+knight+girl", "anime+cyberpunk+girl", "anime+girl+ocean",
    "anime+girl+sky", "anime+girl+clouds", "anime+mermaid",
    "anime+girl+night", "anime+girl+stars", "anime+girl+moon",
    "anime+girl+galaxy", "anime+pink+hair+girl", "anime+blue+hair+girl",
    "anime+white+hair+girl", "anime+silver+hair+girl", "anime+red+hair+girl",
    "anime+blonde+anime+girl", "anime+girl+smile", "anime+girl+serious",
    "anime+kimono+girl", "anime+yukata+girl", "anime+shrine+maiden",
    "anime+japanese+girl", "anime+waifu", "anime+girl+4k",
    "anime+girl+aesthetic", "anime+girl+minimal", "anime+cherry+blossom",
    "anime+boy+cool", "anime+couple", "anime+art",
    "beautiful+girl+portrait", "asian+girl+portrait+4k",
    "aesthetic+girl+photography", "beautiful+woman+4k",
    "girl+nature+portrait", "model+photography+portrait",
    "cute+girl+wallpaper", "pretty+girl+face+portrait",
    "girl+sunset+photography", "woman+aesthetic+wallpaper",
    "girl+flowers+photography", "beautiful+eyes+portrait",
    "girl+rain+photography", "woman+forest+portrait",
    "girl+city+night+photography",
]

FALLBACK_PHOTO = "https://i.ibb.co/N6D7D9k0/photo-AQADUw9r-Gz7sa-VV.jpg"

# ─────────────────────── Premium Emoji IDs ─────────────────────
E_WARN    = '<emoji id=5447644880824181073>⚠️</emoji>'
E_INFO    = '<emoji id=5334544901428229844>ℹ️</emoji>'
E_CROWN   = '<emoji id=5217822164362739968>👑</emoji>'
E_SPARK   = '<emoji id=5325547803936572038>✨</emoji>'
E_CHECK   = '<emoji id=5206607081334906820>✔️</emoji>'
E_BOLT    = '<emoji id=5456140674028019486>⚡️</emoji>'
E_GEAR    = '<emoji id=5341715473882955310>⚙️</emoji>'
E_STAR    = '<emoji id=5438496463044752972>⭐️</emoji>'
E_STOP    = '<emoji id=5260293700088511294>⛔️</emoji>'
E_GREEN   = '<emoji id=5416081784641168838>🟢</emoji>'
E_RED     = '<emoji id=5411225014148014586>🔴</emoji>'
E_LINK    = '<emoji id=5271604874419647061>🔗</emoji>'
E_PENCIL  = '<emoji id=5395444784611480792>✏️</emoji>'
E_TIP     = '<emoji id=5422439311196834318>💡</emoji>'
E_IMAGE   = '<emoji id=5395444784611480792>🖼</emoji>'
E_CROSS   = '<emoji id=5210952531676504517>❌</emoji>'
E_LOCK    = '<emoji id=5296369303661067030>🔒</emoji>'
E_DIAMOND = '<emoji id=5217822164362739968>💎</emoji>'
E_ROCKET  = '<emoji id=5456140674028019486>🚀</emoji>'
E_SHIELD  = '<emoji id=5251203410396458957>🛡</emoji>'
E_CLOCK   = '<emoji id=5386367538735104399>⌛</emoji>'
E_ARROW   = '<emoji id=5416117059207572332>➡️</emoji>'
E_UPLOAD  = '<emoji id=5271604874419647061>📤</emoji>'
E_PHOTO   = '<emoji id=5395444784611480792>📷</emoji>'
E_EXPIRY  = '<emoji id=5386367538735104399>⏰</emoji>'
E_HELP    = '<emoji id=5334544901428229844>❓</emoji>'

# ─────────────────────── Button Icon Emoji IDs ─────────────────
ICON_INFO      = 5334544901428229844
ICON_HELP      = 5443038326535759644
ICON_DEV       = 5823268688874179761
ICON_BACK      = 5447183459602669338
ICON_GEAR      = 5341715473882955310
ICON_PENCIL    = 5395444784611480792
ICON_REFRESH   = 5375338737028841420
ICON_PREMIUM   = 5217822164362739968
ICON_IMAGE     = 5395444784611480792
ICON_CHANNEL   = 5271604874419647061
ICON_CLOSE     = 5210952531676504517
ICON_HOME      = 5447183459602669338
ICON_UPLOAD    = 5271604874419647061
ICON_EXPIRY    = 5386367538735104399
ICON_SUPPORT   = 5325547803936572038
ICON_ABOUT     = 5334544901428229844
ICON_WARNING   = 5447644880824181073

# ─────────────────────── Reactions ─────────────────────────────
REACTIONS = [
    "👍", "❤️", "🔥", "🥰", "👏", "😁", "🤯", "😱",
    "🎉", "🤩", "💯", "🤣", "⚡", "🏆", "😎", "👾",
    "🌟", "✨", "💫", "🎯", "🚀", "💎", "👑", "🔥",
    "🥹", "🫶", "🤌", "💝", "💖", "💗", "💓",
]

# ─────────────────────── Expiry config ─────────────────────────
EXPIRY_OPTIONS = {
    "⏰ 1 Hour":  3600,
    "📅 1 Day":   86400,
    "📅 7 Days":  604800,
    "📅 30 Days": 2592000,
    "∞ Never":    None,
}

EXPIRY_LABEL_MAP = {
    3600:    "1 Hour",
    86400:   "1 Day",
    604800:  "7 Days",
    2592000: "30 Days",
    None:    "Never",
}

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN)
dp  = Dispatcher(storage=MemoryStorage())

# ─────────────────────── FSM ───────────────────────────────────
class UploadState(StatesGroup):
    waiting_for_image = State()
    waiting_for_url   = State()

# ─────────────────────── per-user state ────────────────────────
user_expiry: dict[int, int | None] = {}

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
                    url_fallback = (
                        f"https://wallhaven.cc/api/v1/search"
                        f"?categories=011&purity=100&sorting=random&apikey={WALLHAVEN_API_KEY}"
                    )
                    async with session.get(url_fallback, timeout=aiohttp.ClientTimeout(total=10)) as resp2:
                        data2 = await resp2.json()
                        images = data2.get("data", [])
                if not images:
                    return FALLBACK_PHOTO
                chosen = random.choice(images)
                image_url = chosen.get("path", FALLBACK_PHOTO)
                log.info(f"Wallhaven | Query: {query} | Page: {page} | Image: {image_url}")
                return image_url
    except Exception as e:
        log.error(f"Wallhaven fetch failed: {e}")
        return FALLBACK_PHOTO

# ─────────────────────── keyboards ─────────────────────────────
def main_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📷 Upload Image"), KeyboardButton(text="🔗 Upload URL")],
            [KeyboardButton(text="⏰ Set Expiry"),   KeyboardButton(text="❓ Help")],
        ],
        resize_keyboard=True,
        is_persistent=False,
    )

def expiry_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="⏰ 1 Hour"),  KeyboardButton(text="📅 1 Day")],
            [KeyboardButton(text="📅 7 Days"),  KeyboardButton(text="📅 30 Days")],
            [KeyboardButton(text="∞ Never"),    KeyboardButton(text="⬅️ Back")],
        ],
        resize_keyboard=True,
        is_persistent=False,
    )

def start_inline_kb() -> InlineKeyboardMarkup:
    """Inline buttons with small caps — channel, support, about."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📢 ᴜᴘᴅᴀᴛᴇ ᴄʜᴀɴɴᴇʟ ↗️", url=UPDATE_CHANNEL),
            InlineKeyboardButton(text="💬 sᴜᴘᴘᴏʀᴛ ɢʀᴏᴜᴘ ↗️",  url=SUPPORT_GROUP),
        ],
        [
            InlineKeyboardButton(text="• ℹ️ ᴀʙᴏᴜᴛ •", callback_data="about"),
        ],
    ])

def result_inline_kb(direct_url: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📋 ᴄᴏᴘʏ ʟɪɴᴋ 🔗", url=direct_url),
            InlineKeyboardButton(text="↗️ sʜᴀʀᴇ ʟɪɴᴋ 🔗", url=f"https://t.me/share/url?url={direct_url}"),
        ]
    ])

# ─────────────────────── reaction helper ───────────────────────
async def react(msg: Message, emoji: str = "🤩"):
    try:
        await bot.set_message_reaction(
            chat_id=msg.chat.id,
            message_id=msg.message_id,
            reaction=[ReactionTypeEmoji(type="emoji", emoji=emoji)],
            is_big=False,
        )
    except Exception:
        pass

# ─────────────────────── helpers ───────────────────────────────
def get_expiry(uid: int) -> int | None:
    return user_expiry.get(uid, None)

def expiry_str(uid: int) -> str:
    return EXPIRY_LABEL_MAP.get(get_expiry(uid), "Never")

async def upload_to_imgbb(
    image_data: str,
    name: str = None,
    expiration: int = None,
) -> dict:
    params = {"key": IMGBB_KEY}
    if expiration:
        params["expiration"] = expiration

    form = {"image": image_data}
    if name:
        form["name"] = name

    resp = requests.post(IMGBB_URL, params=params, data=form, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    if not data.get("success"):
        raise RuntimeError(data.get("error", {}).get("message", "Upload failed"))

    d   = data["data"]
    img = d["image"]
    thr = d.get("thumb", {})

    total_bytes = int(d.get("size", 0))
    size_kb     = total_bytes // 1024
    size_rem    = total_bytes % 1024

    expiration_val = expiration if expiration else None
    exp_label   = EXPIRY_LABEL_MAP.get(expiration_val, "Never")

    ts      = int(d.get("time", 0))
    now_utc = (
        datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y/%m/%d - %H:%M:%S")
        if ts else
        datetime.now(timezone.utc).strftime("%Y/%m/%d - %H:%M:%S")
    )

    return {
        "url":         d["url"],
        "display_url": d.get("display_url", d["url"]),
        "viewer":      d["url_viewer"],
        "delete_url":  d["delete_url"],
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
    elapsed_s = int(elapsed)
    return (
        f"{E_CHECK} <b>Image Uploaded Successfully!</b>\n\n"
        "<blockquote>"
        f"{E_IMAGE} <b>Name:</b> {r['name']}\n"
        f"{E_LINK} <b>Direct URL:</b> <a href=\"{r['url']}\">{r['url']}</a>\n"
        f"{E_ARROW} <b>Viewer Page:</b> <a href=\"{r['viewer']}\">{r['viewer']}</a>\n"
        f"{E_PHOTO} <b>Thumbnail:</b> <a href=\"{r['thumb']}\">{r['thumb']}</a>\n"
        f"{E_INFO} <b>Width:</b> {r['width']} | <b>Height:</b> {r['height']}\n"
        f"{E_DIAMOND} <b>Size:</b> {r['size_kb']} KB and {r['size_bytes']} Bytes\n"
        f"{E_PENCIL} <b>File Name:</b> {r['filename']}\n"
        f"{E_GEAR} <b>Mime:</b> {r['mime']} | <b>Ext:</b> {r['ext']}\n"
        f"{E_EXPIRY} <b>Expiry:</b> {r['expiry']}\n"
        f"{E_CLOCK} <b>Upload Time:</b> {r['upload_time']} UTC"
        "</blockquote>\n\n"
        f"{E_BOLT} <b>Time Taken:</b> {elapsed_s}s\n"
        f"{E_CROWN} <b>User:</b> {user_name} (ID: <code>{user_id}</code>)"
    )

# ─────────────────────── /start ────────────────────────────────
@dp.message(CommandStart())
async def cmd_start(msg: Message, state: FSMContext):
    await state.clear()

    welcome_text = (
        f"{E_STAR} <b>Welcome to {E_IMAGE} Image To Link Bot | {E_LINK} Img To URL Bot!</b>\n\n"
        f"<blockquote>{E_ROCKET} <b>Lightning Fast Image Hosting</b>\n"
        f"Send me any image or URL, and I will instantly upload it to "
        f"the cloud, providing you with a permanent, direct URL.</blockquote>\n\n"
        f"{E_STOP} <b>18+ content is strictly prohibited!</b> "
        f"Violators will be banned permanently.\n\n"
        f"<blockquote>{E_INFO} <b>System Specifications</b>\n"
        f"{E_CHECK} Supported Formats: JPG, PNG, BMP, GIF, TIFF, WEBP\n"
        f"{E_SHIELD} Maximum File Size: 32MB</blockquote>\n\n"
        f"{E_CROWN} Session: {msg.from_user.first_name} (ID: <code>{msg.from_user.id}</code>)"
    )

    # Fetch random Wallhaven wallpaper
    photo_url = await fetch_random_wallpaper()

    try:
        await msg.answer_photo(
            photo=photo_url,
            caption=welcome_text,
            parse_mode="HTML",
            reply_markup=start_inline_kb(),
        )
    except Exception:
        # fallback to static photo if wallhaven fails
        try:
            await msg.answer_photo(
                photo=FALLBACK_PHOTO,
                caption=welcome_text,
                parse_mode="HTML",
                reply_markup=start_inline_kb(),
            )
        except Exception:
            await msg.answer(
                welcome_text,
                parse_mode="HTML",
                reply_markup=start_inline_kb(),
            )

    await msg.answer(
        f"{E_ARROW} <b>Choose an option:</b>",
        parse_mode="HTML",
        reply_markup=main_kb(),
    )

    # Random reaction on start
    try:
        await react(msg, random.choice(REACTIONS))
    except Exception:
        pass

# ─────────────────────── /help ─────────────────────────────────
@dp.message(Command("help"))
@dp.message(F.text == "❓ Help")
async def cmd_help(msg: Message, state: FSMContext):
    await state.clear()
    uid = msg.from_user.id
    await msg.answer(
        f"{E_INFO} <b>How To Use Image To Link Bot</b>\n\n"
        f"{E_ARROW} 1️⃣ Send me any image (photo or file).\n"
        f"{E_ARROW} 2️⃣ I will upload it to ImgBB cloud storage.\n"
        f"{E_ARROW} 3️⃣ You will get a permanent direct URL!\n\n"
        f"<blockquote>{E_GEAR} Supported Formats: JPG, PNG, BMP, GIF, TIFF, WEBP\n"
        f"{E_DIAMOND} Max Size: 32MB</blockquote>\n\n"
        f"{E_ROCKET} <b>Features:</b>\n"
        f"  {E_PHOTO} <b>Upload Image</b> — Send any image to upload\n"
        f"  {E_LINK} <b>Upload URL</b> — Upload image from a URL\n"
        f"  {E_EXPIRY} <b>Set Expiry</b> — Set auto-delete timer (current: {expiry_str(uid)})\n"
        f"  {E_PENCIL} <b>Caption</b> — Add caption for custom filename",
        parse_mode="HTML",
        reply_markup=main_kb(),
    )

# ─────────────────────── /about ────────────────────────────────
async def send_about(target):
    text = (
        f"{E_INFO} <b>ABOUT IMAGE TO LINK BOT</b>\n\n"
        f"<blockquote>{E_ROCKET} <b>Bot Info:</b>\n"
        f"{E_STAR} Name: Image To Link Bot\n"
        f"{E_GEAR} Version: 3.0.0 (aiogram)\n"
        f"{E_SHIELD} Features: Wallhaven Wallpapers + NSFW Detection & Auto-Ban\n"
        f"{E_BOLT} Library: aiogram async</blockquote>\n\n"
        f"{E_STOP} <b>18+ content strictly prohibited!</b>\n"
        f"Violation = Permanent Ban {E_CROSS}"
    )
    if isinstance(target, Message):
        await target.answer(text, parse_mode="HTML", reply_markup=main_kb())
    else:
        await target.message.answer(text, parse_mode="HTML", reply_markup=main_kb())
        await target.answer()

@dp.message(Command("about"))
async def cmd_about(msg: Message):
    await send_about(msg)

@dp.callback_query(F.data == "about")
async def about_cb(cb: CallbackQuery):
    await send_about(cb)

# ─────────────────────── Copy Link callback (legacy) ───────────
@dp.callback_query(F.data.startswith("copy|"))
async def copy_link_cb(cb: CallbackQuery):
    url = cb.data.split("|", 1)[1]
    await cb.answer(url, show_alert=True)

# ─────────────────────── Upload Image ──────────────────────────
@dp.message(F.text == "📷 Upload Image")
async def ask_for_image(msg: Message, state: FSMContext):
    await state.set_state(UploadState.waiting_for_image)
    await msg.answer(
        f"{E_PHOTO} <b>Upload Image</b>\n\n"
        f"{E_ARROW} Send me any image (photo or file) to upload!\n\n"
        f"{E_TIP} Tap any button to cancel.",
        parse_mode="HTML",
        reply_markup=main_kb(),
    )

async def _do_upload_image(msg: Message, state: FSMContext):
    await state.clear()
    uid    = msg.from_user.id
    uname  = msg.from_user.first_name
    name   = msg.caption or None

    status_msg = await msg.answer(f"{E_CLOCK} <b>Uploading...</b>", parse_mode="HTML")
    t_start    = time.monotonic()

    try:
        if msg.document:
            file_id = msg.document.file_id
        else:
            file_id = msg.photo[-1].file_id

        file     = await bot.get_file(file_id)
        file_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file.file_path}"
        raw      = requests.get(file_url, timeout=30).content
        b64      = base64.b64encode(raw).decode()

        result  = await upload_to_imgbb(b64, name=name, expiration=get_expiry(uid))
        elapsed = time.monotonic() - t_start

        await status_msg.delete()

        text = build_result_text(result, uname, uid, elapsed)
        kb   = result_inline_kb(result["url"])

        sent = await msg.answer_photo(
            photo=result["url"],
            caption=text,
            parse_mode="HTML",
            reply_markup=kb,
        )
        await react(msg, random.choice(["🤩", "🔥", "✨", "💎", "⚡"]))
        await react(sent, "🔗")

    except Exception as e:
        await status_msg.delete()
        await msg.answer(f"{E_CROSS} <b>Upload failed:</b> {e}", parse_mode="HTML")

@dp.message(UploadState.waiting_for_image, F.photo | F.document)
async def handle_image_in_state(msg: Message, state: FSMContext):
    await _do_upload_image(msg, state)

@dp.message(F.photo | F.document)
async def handle_direct_image(msg: Message, state: FSMContext):
    await _do_upload_image(msg, state)

# ─────────────────────── Upload URL ────────────────────────────
@dp.message(F.text == "🔗 Upload URL")
async def ask_for_url(msg: Message, state: FSMContext):
    await state.set_state(UploadState.waiting_for_url)
    await msg.answer(
        f"{E_LINK} <b>Upload URL</b>\n\n"
        f"{E_ARROW} Send me an image URL to upload.\n\n"
        f"{E_TIP} Tap any button to cancel.",
        parse_mode="HTML",
        reply_markup=main_kb(),
    )

@dp.message(UploadState.waiting_for_url, F.text)
async def handle_url(msg: Message, state: FSMContext):
    url = msg.text.strip()
    if not url.startswith("http"):
        await msg.answer(f"{E_CROSS} Invalid URL. Send a valid http/https image URL.")
        return

    await state.clear()
    uid    = msg.from_user.id
    uname  = msg.from_user.first_name

    status  = await msg.answer(f"{E_CLOCK} <b>Uploading...</b>", parse_mode="HTML")
    t_start = time.monotonic()

    try:
        result  = await upload_to_imgbb(url, expiration=get_expiry(uid))
        elapsed = time.monotonic() - t_start

        await status.delete()

        text = build_result_text(result, uname, uid, elapsed)
        kb   = result_inline_kb(result["url"])

        sent = await msg.answer_photo(
            photo=result["url"],
            caption=text,
            parse_mode="HTML",
            reply_markup=kb,
        )
        await react(msg, random.choice(["🤩", "🔥", "✨", "💎", "⚡"]))
        await react(sent, "🔗")
    except Exception as e:
        await status.delete()
        await msg.answer(f"{E_CROSS} <b>Upload failed:</b> {e}", parse_mode="HTML")

# ─────────────────────── Set Expiry ────────────────────────────
@dp.message(F.text == "⏰ Set Expiry")
async def ask_expiry(msg: Message, state: FSMContext):
    await state.clear()
    uid = msg.from_user.id
    await msg.answer(
        f"{E_EXPIRY} <b>Select Auto-Delete Timer</b>\n\n"
        f"{E_INFO} Current Setting: <b>{expiry_str(uid)}</b>",
        parse_mode="HTML",
        reply_markup=expiry_kb(),
    )

@dp.message(F.text.in_(EXPIRY_OPTIONS.keys()))
async def set_expiry(msg: Message):
    uid  = msg.from_user.id
    secs = EXPIRY_OPTIONS[msg.text]
    user_expiry[uid] = secs
    label = EXPIRY_LABEL_MAP.get(secs, "Never")
    await msg.answer(
        f"{E_CHECK} <b>Expiry Set To: {label}</b>",
        parse_mode="HTML",
        reply_markup=main_kb(),
    )

@dp.message(F.text == "⬅️ Back")
async def go_back(msg: Message, state: FSMContext):
    await state.clear()
    await msg.answer(f"{E_ARROW} Main Menu", reply_markup=main_kb())

# ─────────────────────── run ───────────────────────────────────
async def main():
    log.info("Bot starting...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

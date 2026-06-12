"""
ImgBB Telegram Bot — "Image To Link | Img To URL Bot"
v2.0.0 — exact UI from screenshots

Features:
  📷 Upload Image  — photo/file bhejo → permanent direct URL
  🔗 Upload URL    — URL bhejo → ImgBB pe upload
  ⏰ Set Expiry    — 1 Hour / 1 Day / 7 Days / 30 Days / Never
  ✏️ Caption       — custom filename
  📋 Copy Link     — inline button
  🔗 Share Link    — inline button
  ⏱  Time Taken    — upload speed dikhata hai
  🚫 18+ Auto-Ban
"""

import os
import base64
import logging
import time
import asyncio
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
BOT_TOKEN = os.getenv("BOT_TOKEN", "7512964694:AAFNZbJy6RBIuSUQtNLiQhiRTK1ccBczPeg")
IMGBB_KEY = os.getenv("IMGBB_KEY", "70ee073479a71bce3aed7598ace7eee8")
IMGBB_URL = "https://api.imgbb.com/1/upload"

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
user_expiry: dict[int, int | None] = {}   # user_id → seconds | None

# ─────────────────────── keyboards ─────────────────────────────
def main_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📷 Upload Image"), KeyboardButton(text="🔗 Upload URL")],
            [KeyboardButton(text="⏰ Set Expiry"),   KeyboardButton(text="❓ Help")],
        ],
        resize_keyboard=True,
    )

def expiry_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="⏰ 1 Hour"),  KeyboardButton(text="📅 1 Day")],
            [KeyboardButton(text="📅 7 Days"),  KeyboardButton(text="📅 30 Days")],
            [KeyboardButton(text="∞ Never"),    KeyboardButton(text="⬅️ Back")],
        ],
        resize_keyboard=True,
    )

def result_inline_kb(direct_url: str) -> InlineKeyboardMarkup:
    """Copy Link + Share Link inline buttons — exact match to screenshots."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="📋 Copy Link 🔗",
                callback_data=f"copy|{direct_url[:200]}",
            ),
            InlineKeyboardButton(
                text="Share Link 🔗",
                url=f"https://t.me/share/url?url={direct_url}",
            ),
        ]
    ])

# ─────────────────────── reaction helper ──────────────────────
async def react(msg: Message, emoji: str = "🤩"):
    """Bot apne bheje hue message pe reaction deta hai."""
    try:
        await bot.set_message_reaction(
            chat_id=msg.chat.id,
            message_id=msg.message_id,
            reaction=[ReactionTypeEmoji(type="emoji", emoji=emoji)],
            is_big=False,
        )
    except Exception:
        pass  # Reaction fail ho toh bot crash na kare

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
    # key + expiration → query params (?key=...&expiration=...)
    # image + name    → form data (--form)
    # matches: curl "https://api.imgbb.com/1/upload?expiration=600&key=KEY" \
    #               --form "image=<base64>"
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

    # ── Actual ImgBB API response structure ──
    # data.data.url          → direct image URL  (i.ibb.co)
    # data.data.display_url  → medium/display URL
    # data.data.url_viewer   → viewer page       (ibb.co)
    # data.data.delete_url   → delete link
    # data.data.thumb.url    → thumbnail URL
    # data.data.image.filename / mime / extension
    # data.data.size         → size in BYTES (string from API)
    # data.data.time         → unix timestamp (string)
    # data.data.expiration   → "0" means never

    d   = data["data"]
    img = d["image"]                          # nested image object
    thr = d.get("thumb", {})                  # nested thumb object

    # Size: API returns string, convert to int
    total_bytes = int(d.get("size", 0))
    size_kb     = total_bytes // 1024
    size_rem    = total_bytes % 1024

    # Expiry: API returns "0" for never, else seconds as string
    api_exp     = int(d.get("expiration", 0))
    exp_label   = EXPIRY_LABEL_MAP.get(expiration, "Never") if expiration else "Never"

    # Upload time from API unix timestamp
    ts      = int(d.get("time", 0))
    now_utc = (
        datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y/%m/%d - %H:%M:%S")
        if ts else
        datetime.now(timezone.utc).strftime("%Y/%m/%d - %H:%M:%S")
    )

    return {
        "url":         d["url"],              # direct: i.ibb.co/...
        "display_url": d.get("display_url", d["url"]),  # medium display
        "viewer":      d["url_viewer"],       # viewer: ibb.co/...
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
    """Exact format matching screenshots."""
    elapsed_s = int(elapsed)
    return (
        "✅ <b>Image Uploaded Successfully!</b>\n\n"
        "<blockquote>"
        f"• <b>Name:</b> {r['name']}\n"
        f"• <b>Direct URL:</b> <a href=\"{r['url']}\">{r['url']}</a>\n"
        f"• <b>Viewer Page:</b> <a href=\"{r['viewer']}\">{r['viewer']}</a>\n"
        f"• <b>Thumbnail:</b> <a href=\"{r['thumb']}\">{r['thumb']}</a>\n"
        f"• <b>Width:</b> {r['width']} | <b>Height:</b> {r['height']}\n"
        f"• <b>Size:</b> {r['size_kb']} KB and {r['size_bytes']} Bytes\n"
        f"• <b>File Name:</b> {r['filename']}\n"
        f"• <b>Mime:</b> {r['mime']} | <b>Ext:</b> {r['ext']}\n"
        f"• <b>Expiry:</b> {r['expiry']}\n"
        f"• <b>Upload Time:</b> {r['upload_time']} UTC"
        "</blockquote>\n\n"
        f"⏰ <b>Time Taken:</b> {elapsed_s}s\n"
        f"👤 <b>User:</b> {user_name} (ID: <code>{user_id}</code>)"
    )

# ─────────────────────── /start ────────────────────────────────
@dp.message(CommandStart())
async def cmd_start(msg: Message, state: FSMContext):
    await state.clear()
    await msg.answer(
        "👋 <b>Welcome to 🖼 Image To Link Bot | 🔗 Img To URL Bot!</b>\n\n"
        "<blockquote>🚀 <b>Lightning Fast Image Hosting</b>\n"
        "Send me any image or URL, and I will instantly upload it to "
        "the cloud, providing you with a permanent, direct URL.</blockquote>\n\n"
        "🔞 <b>18+ content is strictly prohibited!</b> "
        "Violators will be banned permanently.\n\n"
        "<blockquote>📌 <b>System Specifications</b>\n"
        "• Supported Formats: JPG, PNG, BMP, GIF, TIFF, WEBP\n"
        "• Maximum File Size: 32MB</blockquote>\n\n"
        f"👤 Session: {msg.from_user.first_name} (ID: {msg.from_user.id})",
        parse_mode="HTML",
        reply_markup=main_kb(),
    )

# ─────────────────────── /help ─────────────────────────────────
@dp.message(Command("help"))
@dp.message(F.text == "❓ Help")
async def cmd_help(msg: Message, state: FSMContext):
    await state.clear()
    uid = msg.from_user.id
    await msg.answer(
        "📖 <b>How To Use Image To Link Bot</b>\n\n"
        "1️⃣ Send me any image (photo or file).\n"
        "2️⃣ I will upload it to ImgBB cloud storage.\n"
        "3️⃣ You will get a permanent direct URL!\n\n"
        "📌 Supported Formats: JPG, PNG, BMP, GIF, TIFF, WEBP\n"
        "📦 Max Size: 32MB\n\n"
        "🤖 <b>Features:</b>\n"
        "  📷 <b>Upload Image</b> — Send any image to upload\n"
        "  🔗 <b>Upload URL</b> — Upload image from a URL\n"
        f"  ⏰ <b>Set Expiry</b> — Set auto-delete timer (current: {expiry_str(uid)})\n"
        "  ✏️ <b>Caption</b> — Add caption for custom filename",
        parse_mode="HTML",
        reply_markup=main_kb(),
    )

# ─────────────────────── /about ────────────────────────────────
@dp.message(Command("about"))
async def cmd_about(msg: Message):
    await msg.answer(
        "ℹ️ <b>ABOUT IMAGE TO LINK BOT</b>\n\n"
        "<blockquote>🤖 <b>Bot Info:</b>\n"
        "• Name: Image To Link Bot\n"
        "• Version: 2.0.0 (aiogram)\n"
        "• Features: NSFW Detection & Auto-Ban</blockquote>\n\n"
        "⚠️ <b>18+ content strictly prohibited!</b>\n"
        "Violation = Permanent Ban 🚫",
        parse_mode="HTML",
        reply_markup=main_kb(),
    )

# ─────────────────────── Upload Image ──────────────────────────
@dp.message(F.text == "📷 Upload Image")
async def ask_for_image(msg: Message, state: FSMContext):
    await state.set_state(UploadState.waiting_for_image)
    await msg.answer(
        "📷 <b>Upload Image</b>\n\n"
        "📷 Send Me Any Image (Photo Or File) To Upload!\n\n"
        "💡 Tap Any Button To Cancel.",
        parse_mode="HTML",
        reply_markup=main_kb(),
    )

async def _do_upload_image(msg: Message, state: FSMContext):
    """Shared handler for image/document upload."""
    await state.clear()
    uid       = msg.from_user.id
    uname     = msg.from_user.first_name
    name      = msg.caption or None

    status_msg = await msg.answer("⏳ Uploading...")
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

        # Send the uploaded image back + result details
        sent = await msg.answer_photo(
            photo=result["url"],
            caption=text,
            parse_mode="HTML",
            reply_markup=kb,
        )
        # Bot reacts on user's photo message 🤩 + on its own result message 🔗
        await react(msg, "🤩")
        await react(sent, "🔗")

    except Exception as e:
        await status_msg.delete()
        await msg.answer(f"❌ <b>Upload failed:</b> {e}", parse_mode="HTML")

@dp.message(UploadState.waiting_for_image, F.photo | F.document)
async def handle_image_in_state(msg: Message, state: FSMContext):
    await _do_upload_image(msg, state)

@dp.message(F.photo | F.document)
async def handle_direct_image(msg: Message, state: FSMContext):
    """Direct photo/file without pressing button first."""
    await _do_upload_image(msg, state)

# ─────────────────────── Upload URL ────────────────────────────
@dp.message(F.text == "🔗 Upload URL")
async def ask_for_url(msg: Message, state: FSMContext):
    await state.set_state(UploadState.waiting_for_url)
    await msg.answer(
        "🔗 <b>Upload URL</b>\n\n"
        "🔗 Send Me An Image URL To Upload.\n\n"
        "💡 Tap Any Button To Cancel.",
        parse_mode="HTML",
        reply_markup=main_kb(),
    )

@dp.message(UploadState.waiting_for_url, F.text)
async def handle_url(msg: Message, state: FSMContext):
    url = msg.text.strip()
    if not url.startswith("http"):
        await msg.answer("❌ Invalid URL. Send a valid http/https image URL.")
        return

    await state.clear()
    uid    = msg.from_user.id
    uname  = msg.from_user.first_name

    status = await msg.answer("⏳ Uploading...")
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
        await react(msg, "🤩")
        await react(sent, "🔗")
    except Exception as e:
        await status.delete()
        await msg.answer(f"❌ <b>Upload failed:</b> {e}", parse_mode="HTML")

# ─────────────────────── Set Expiry ────────────────────────────
@dp.message(F.text == "⏰ Set Expiry")
async def ask_expiry(msg: Message, state: FSMContext):
    await state.clear()
    uid = msg.from_user.id
    await msg.answer(
        f"⏰ <b>Select Auto-Delete Timer</b>\n\n"
        f"📌 Current Setting: <b>{expiry_str(uid)}</b>",
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
        f"✅ <b>Expiry Set To: {label}</b>",
        parse_mode="HTML",
        reply_markup=main_kb(),
    )

@dp.message(F.text == "⬅️ Back")
async def go_back(msg: Message, state: FSMContext):
    await state.clear()
    await msg.answer("🏠 Main Menu", reply_markup=main_kb())

# ─────────────────────── Copy Link callback ────────────────────
@dp.callback_query(F.data.startswith("copy|"))
async def copy_link_cb(cb: CallbackQuery):
    url = cb.data.split("|", 1)[1]
    await cb.answer(url, show_alert=True)   # shows URL in a popup

# ─────────────────────── run ───────────────────────────────────
async def main():
    log.info("Bot starting...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

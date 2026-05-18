"""
Atsawin AI - Telegram Bot
Connects to FastAPI backend for AI responses, system status, trading data.
"""

import logging
import os
import requests
import aiohttp
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# --- Configuration ---
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
BOT_API_KEY = os.getenv("BOT_API_KEY", "atsawin-bot-secret-2026")
ADMIN_USER_ID = os.getenv("ADMIN_USER_ID", "")  # optional: restrict to your user ID

# --- Logging ---
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
def call_api(path: str, params: dict = None, timeout: int = 120) -> requests.Response:
    """Call backend API with bot API key."""
    headers = {"X-API-Key": BOT_API_KEY}
    if params:
        return requests.get(f"{BACKEND_URL}{path}", params=params, headers=headers, timeout=timeout)
    return requests.get(f"{BACKEND_URL}{path}", headers=headers, timeout=timeout)


logger = logging.getLogger(__name__)


def check_authorization(user_id: int) -> bool:
    """Check if user is authorized to use the bot."""
    if not ADMIN_USER_ID:
        return True  # no restriction
    return str(user_id) == ADMIN_USER_ID


# ==================== Command Handlers ====================


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command."""
    user = update.effective_user
    welcome = (
        f"สวัสดี {user.first_name}! 👋\n\n"
        "ผมคือ Atsawin AI Bot 🤖\n"
        "คุณสามารถใช้คำสั่งต่อไปนี้:\n\n"
        "/ask <คำถาม> - ถาม AI\n"
        "/status - สถานะระบบ\n"
        "/price <สัญลักษณ์> - ราคาคริปโต (เช่น /price BTCUSDT)\n"
        "/signal <สัญลักษณ์> - สัญญาณเทรด\n"
        "/portfolio - ดูพอร์ตเทรด\n"
        "/help - วิธีใช้งาน\n\n"
        "📄 ส่งไฟล์โดยตรงได้เลย!\n"
        "  • ไฟล์โค้ด (.py, .js, .ts, .json, .html, .css, ...)\n"
        "  • รูปภาพ (.jpg, .png, .gif, .webp)\n"
        "  • พิมพ์คำถามตอนส่งไฟล์ได้ (เช่น อธิบายโค้ดนี้ให้หน่อย)\n\n"
        "หรือพิมพ์ข้อความตรงๆ ได้เลย ผมจะตอบผ่าน AI"
    )
    await update.message.reply_text(welcome)


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command."""
    help_text = (
        "📚 วิธีใช้งาน Atsawin AI Bot\n\n"
        "🔹 /ask <คำถาม> - ถาม AI อะไรก็ได้\n"
        "   ตัวอย่าง: /ask วิธีเขียน Python\n\n"
        "🔹 /status - ดูสถานะระบบทั้งหมด\n\n"
        "🔹 /price <symbol> - ดูราคาคริปโต\n"
        "   ตัวอย่าง: /price BTCUSDT\n\n"
        "🔹 /signal <symbol> - ดูสัญญาณเทรด\n"
        "   ตัวอย่าง: /signal ETHUSDT\n\n"
        "🔹 /portfolio - ดูพอร์ตเทรด\n\n"
        "📄 ส่งไฟล์โดยตรงได้เลย!\n"
        "   • ไฟล์โค้ด: .py .js .ts .json .html .css .md .csv .sh .sql\n"
        "   • รูปภาพ: .jpg .png .gif .webp\n"
        "   • พิมพ์คำถามตอนส่งไฟล์ได้เลย\n"
        "   • ขนาดสูงสุด: 10MB\n\n"
        "🔹 หรือพิมพ์ข้อความตรงๆ ได้เลย!"
    )
    await update.message.reply_text(help_text)


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /status command - check system health."""
    if not check_authorization(update.effective_user.id):
        await update.message.reply_text("❌ คุณไม่มีสิทธิ์ใช้งาน")
        return

    try:
        resp = call_api("/")
        if resp.status_code == 200:
            data = resp.json()
            services = data.get("services", {})
            features = data.get("features", {})

            status_lines = ["🟢 ระบบ Atsawin AI Core ทำงานปกติ\n"]
            status_lines.append("📡 Services:")
            for svc, state in services.items():
                icon = "✅" if state == "online" else "❌"
                status_lines.append(f"  {icon} {svc}: {state}")

            status_lines.append("\n⚡ Features:")
            for feat, state in features.items():
                icon = "✅" if state == "enabled" else "⚠️"
                status_lines.append(f"  {icon} {feat}: {state}")

            await update.message.reply_text("\n".join(status_lines))
        else:
            await update.message.reply_text(f"⚠️ Backend ตอบกลับด้วย status {resp.status_code}")
    except requests.exceptions.ConnectionError:
        await update.message.reply_text("❌ ไม่สามารถเชื่อมต่อกับ Backend ได้")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")


async def cmd_ask(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /ask <question> - send question to AI."""
    if not context.args:
        await update.message.reply_text("ใช้: /ask <คำถาม>\nตัวอย่าง: /ask สวัสดีครับ")
        return

    question = " ".join(context.args)
    # Truncate long questions
    if len(question) > 500:
        question = question[:500] + "..."
    await update.message.reply_text("🤔 กำลังคิด...")

    try:
        resp = call_api(f"/api/ask/{requests.utils.quote(question)}", timeout=120)
        if resp.status_code == 200:
            data = resp.json()
            model = data.get("model", "unknown")
            response = data.get("response", "ไม่ได้รับคำตอบ")
            await update.message.reply_text(
                f"🤖 [{model}]\n\n{response}"
            )
        else:
            await update.message.reply_text(f"❌ Backend error: {resp.status_code}")
    except requests.exceptions.Timeout:
        await update.message.reply_text("⏰ AI ใช้เวลานานเกินไป ลองใหม่อีกครั้ง")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")


async def cmd_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /price <symbol> - get crypto price."""
    if not context.args:
        await update.message.reply_text("ใช้: /price <symbol>\nตัวอย่าง: /price BTCUSDT")
        return

    symbol = context.args[0].upper()
    try:
        resp = call_api(f"/trading/market/price", params={"symbol": symbol})
        if resp.status_code == 200:
            data = resp.json()
            price = data.get("price", "N/A")
            await update.message.reply_text(
                f"💰 {symbol}\nราคาปัจจุบัน: ${price}"
            )
        else:
            await update.message.reply_text(f"❌ ไม่พบข้อมูล {symbol}")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")


async def cmd_signal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /signal <symbol> - get trading signal."""
    if not context.args:
        await update.message.reply_text("ใช้: /signal <symbol>\nตัวอย่าง: /signal BTCUSDT")
        return

    symbol = context.args[0].upper()
    await update.message.reply_text(f"📊 กำลังวิเคราะห์ {symbol}...")

    try:
        resp = call_api(f"/trading/analysis/signal", params={"symbol": symbol})
        if resp.status_code == 200:
            data = resp.json()
            signal = data.get("signal", "N/A")
            confidence = data.get("confidence", 0)
            indicators = data.get("indicators", {})

            icon = {"BUY": "🟢", "SELL": "🔴", "HOLD": "🟡"}.get(signal, "⚪")

            lines = [
                f"{icon} สัญญาณ: {signal}",
                f"📈 ความมั่นใจ: {confidence:.1%}",
                "\n📊 Indicators:",
            ]
            for name, value in indicators.items():
                if isinstance(value, (int, float)):
                    lines.append(f"  • {name}: {value:.4f}")
                else:
                    lines.append(f"  • {name}: {value}")

            await update.message.reply_text("\n".join(lines))
        else:
            await update.message.reply_text(f"❌ ไม่สามารถวิเคราะห์ {symbol} ได้")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")


async def cmd_portfolio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /portfolio - show portfolio status."""
    try:
        resp = call_api("/trading/portfolio")
        if resp.status_code == 200:
            data = resp.json()
            positions = data.get("positions", {})
            total_pnl = data.get("total_pnl", 0)

            lines = ["📂 พอร์ตเทรด\n"]
            lines.append(f"💵 Total PnL: ${total_pnl:,.2f}\n")

            if positions:
                for symbol, pos in positions.items():
                    qty = pos.get("quantity", 0)
                    avg = pos.get("avg_price", 0)
                    pnl = pos.get("pnl", 0)
                    pnl_icon = "📈" if pnl >= 0 else "📉"
                    lines.append(
                        f"{pnl_icon} {symbol}: {qty} @ ${avg:,.2f} (PnL: ${pnl:,.2f})"
                    )
            else:
                lines.append("ไม่มีพอซิชันเปิด")

            await update.message.reply_text("\n".join(lines))
        else:
            await update.message.reply_text("❌ ไม่สามารถดึงข้อมูลพอร์ตได้")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")


# ==================== Message Handler ====================

VISION_QUESTION_KEYWORDS = [
    "ดูรูป", "ดูภาพ", "วิเคราะห์รูป", "อธิบายรูป", "ส่งรูป",
    "can you see", "look at", "view image", "see this",
    "รูปนี้", "ภาพนี้", "this image", "this picture",
    "ทำไมรูป", "รูปเป็นอะไร",
]


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle plain text messages - send to AI."""
    text = update.message.text
    user = update.effective_user

    # Truncate long messages to avoid timeout
    if len(text) > 500:
        text = text[:500] + "..."
        logger.info(f"Truncated long message from {user.username or user.id}")

    logger.info(f"Message from {user.username or user.id}: {text}")

    # Check if user is asking about image capability
    text_lower = text.lower()
    if any(kw in text_lower for kw in VISION_QUESTION_KEYWORDS):
        await update.message.reply_text(
            "🖼️ ผมสามารถวิเคราะห์รูปภาพได้ครับ!\n\n"
            "📌 วิธีส่งรูป:\n"
            "  • กดปุ่ม 📎 (แนบไฟล์) แล้วเลือกรูปภาพ\n"
            "  • หรือส่งรูปโดยตรงในแชท\n"
            "  • รองรับ: .jpg, .png, .gif, .webp\n"
            "  • ขนาดสูงสุด: 5MB\n\n"
            "💡 พิมพ์คำถามตอนส่งรูปได้เลย เช่น 'อธิบายรูปนี้'"
        )
        return

    # Show typing indicator
    await update.message.chat.send_action(action="typing")

    try:
        resp = call_api(f"/api/ask/{requests.utils.quote(text)}", timeout=120)
        if resp.status_code == 200:
            data = resp.json()
            model = data.get("model", "unknown")
            response = data.get("response", "ไม่ได้รับคำตอบ")
            await update.message.reply_text(
                f"🤖 [{model}]\n\n{response}"
            )
        else:
            await update.message.reply_text("❌ ระบบมีปัญหา ลองใหม่อีกครั้ง")
    except requests.exceptions.Timeout:
        await update.message.reply_text("⏰ AI ใช้เวลานานเกินไป ลองใหม่อีกครั้ง")
    except Exception as e:
        logger.error(f"Error handling message: {e}")
        await update.message.reply_text("❌ เกิดข้อผิดพลาด ลองใหม่อีกครั้ง")


# ==================== File Handlers ====================


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle document/file uploads - download and send to AI for analysis."""
    doc = update.message.document
    if not doc:
        return

    file_name = doc.file_name or "unknown"
    file_size = doc.file_size or 0

    # Check file size (max 10MB)
    if file_size > 10 * 1024 * 1024:
        await update.message.reply_text("❌ ไฟล์ใหญ่เกินไป (สูงสุด 10MB)")
        return

    await update.message.reply_text(f"📄 กำลังวิเคราะห์ไฟล์: {file_name}...")

    try:
        # Download file from Telegram
        tg_file = await context.bot.get_file(doc.file_id)
        file_bytes = await tg_file.download_as_bytearray()

        # Send to backend for analysis
        async with aiohttp.ClientSession() as session:
            data = aiohttp.FormData()
            data.add_field(
                "file",
                bytes(file_bytes),
                filename=file_name,
                content_type=doc.mime_type or "application/octet-stream",
            )
            # Check if user included a question with the file
            caption = update.message.caption or ""
            if caption:
                data.add_field("question", caption)

            headers = {"X-API-Key": BOT_API_KEY}
            async with session.post(
                f"{BACKEND_URL}/api/file-analyze",
                data=data,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=120),
            ) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    response_text = result.get("response", "ไม่ได้รับคำตอบ")
                    file_type = result.get("type", "unknown")

                    if file_type == "text":
                        lines = result.get("lines", "?")
                        truncated = result.get("truncated", False)
                        model = result.get("model", "unknown")
                        header = f"📄 {file_name} ({lines} บรรทัด"
                        if truncated:
                            header += ", ตัดให้สั้น"
                        header += f")\n🤖 [{model}]\n\n"
                        await update.message.reply_text(header + response_text)
                    elif file_type == "image":
                        model = result.get("model", "unknown")
                        await update.message.reply_text(
                            f"🖼️ {file_name}\n🤖 [{model}]\n\n{response_text}"
                        )
                    elif file_type == "pdf":
                        pages = result.get("pages", "?")
                        truncated = result.get("truncated", False)
                        model = result.get("model", "unknown")
                        header = f"📑 {file_name} ({pages} หน้า"
                        if truncated:
                            header += ", ตัดให้สั้น"
                        header += f")\n🤖 [{model}]\n\n"
                        await update.message.reply_text(header + response_text)
                    else:
                        await update.message.reply_text(response_text)
                else:
                    error_text = await resp.text()
                    await update.message.reply_text(
                        f"❌ ไม่สามารถวิเคราะห์ไฟล์ได้ (HTTP {resp.status})"
                    )
    except Exception as e:
        logger.error(f"Error handling document: {e}")
        await update.message.reply_text(f"❌ เกิดข้อผิดพลาด: {str(e)}")


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle photo/image uploads - send to AI vision model."""
    # Get the largest photo (best quality)
    photos = update.message.photo
    if not photos:
        return

    photo = photos[-1]  # largest
    file_size = photo.file_size or 0

    await update.message.reply_text("🖼️ กำลังวิเคราะห์รูปภาพ...")

    try:
        # Download photo from Telegram
        tg_file = await context.bot.get_file(photo.file_id)
        file_bytes = await tg_file.download_as_bytearray()

        # Get caption as question
        caption = update.message.caption or ""

        # Send to backend for analysis
        async with aiohttp.ClientSession() as session:
            data = aiohttp.FormData()
            data.add_field(
                "file",
                bytes(file_bytes),
                filename="photo.jpg",
                content_type="image/jpeg",
            )
            if caption:
                data.add_field("question", caption)

            headers = {"X-API-Key": BOT_API_KEY}
            async with session.post(
                f"{BACKEND_URL}/api/file-analyze",
                data=data,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=120),
            ) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    response_text = result.get("response", "ไม่ได้รับคำตอบ")
                    model = result.get("model", "unknown")
                    await update.message.reply_text(
                        f"🖼️ วิเคราะห์รูปภาพ\n🤖 [{model}]\n\n{response_text}"
                    )
                else:
                    await update.message.reply_text(
                        f"❌ ไม่สามารถวิเคราะห์รูปได้ (HTTP {resp.status})"
                    )
    except Exception as e:
        logger.error(f"Error handling photo: {e}")
        await update.message.reply_text(f"❌ เกิดข้อผิดพลาด: {str(e)}")


# ==================== Error Handler ====================


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors."""
    logger.error(f"Update {update} caused error: {context.error}")


# ==================== Main ====================


def main():
    """Start the bot."""
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN is not set!")
        print("Error: Set TELEGRAM_BOT_TOKEN environment variable first.")
        print("Get one from @BotFather on Telegram.")
        return

    logger.info("Starting Atsawin AI Telegram Bot...")

    # Build application
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Register command handlers
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("ask", cmd_ask))
    app.add_handler(CommandHandler("price", cmd_price))
    app.add_handler(CommandHandler("signal", cmd_signal))
    app.add_handler(CommandHandler("portfolio", cmd_portfolio))

    # Register message handler (plain text)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Register file handlers
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    # Register error handler
    app.add_error_handler(error_handler)

    # Start polling
    logger.info("Bot is polling for updates...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()

import requests
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

BOT_TOKEN = "8911202709:AAHYd3slPlXHo9Nkbs99-d92tvaAgMgMF2U"

API_URL = "http://185.84.161.189:8000"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔥 ATSAWIN AI CORE ONLINE"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text

    try:
        response = requests.get(
            f"{API_URL}/ask/{text}"
        )

        data = response.json()

        reply = f"""
🧠 TASK: {text}

⚡ TYPE: {data['type']}
🤖 MODEL: {data['model']}
"""

        await update.message.reply_text(reply)

    except Exception as e:
        await update.message.reply_text(
            f"ERROR: {str(e)}"
        )

app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))

app.add_handler(
    MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        handle_message
    )
)

print("🔥 Telegram AI Agent Running...")

app.run_polling()

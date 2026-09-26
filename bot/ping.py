import time
from telegram import Update
from telegram.ext import CallbackContext

async def ping(update: Update, context: CallbackContext) -> None:
    start = time.perf_counter()
    message = await update.message.reply_text("🏓 Pong!")
    elapsed_ms = (time.perf_counter() - start) * 1000
    await message.edit_text(f"🏓 Pong!\n⏱ Response time: {elapsed_ms:.0f}ms")

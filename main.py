import sys
import os
import logging
import traceback
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from bot.start import start
from bot.help import help
from bot.alpha import alpha
from bot.ui import ui
from bot.releases import releases
from bot.source import source
from bot.contribute import contribute
from bot.apply import apply
from bot.devices import devices
from bot.ping import ping

def read_token():
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        token_path = os.path.join(base_dir, 'token.txt')
        with open(token_path, 'r') as file:
            return file.read().strip()
    except FileNotFoundError:
        print("Token file (token.txt) not found.", file=sys.stderr)
        return None

TOKEN = read_token()

if not TOKEN:
    print("Bot token is missing. Please make sure the token.txt file exists.", file=sys.stderr)
    sys.exit(1)

def main():
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.INFO,
    )
    app = Application.builder().token(TOKEN).job_queue(None).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help))
    app.add_handler(CommandHandler("alpha", alpha))
    app.add_handler(CommandHandler("ui", ui))
    app.add_handler(CommandHandler("releases", releases))
    app.add_handler(CommandHandler("source", source))
    app.add_handler(CommandHandler("contribute", contribute))
    app.add_handler(CommandHandler("apply", apply))
    app.add_handler(CommandHandler("devices", devices))
    app.add_handler(CommandHandler("ping", ping))
    app.add_error_handler(error_handler)

    app.run_polling()


async def error_handler(update: Update | None, context: ContextTypes.DEFAULT_TYPE) -> None:
    logging.getLogger(__name__).error(
        "Exception while handling an update:", exc_info=context.error
    )
    traceback.print_exception(
        type(context.error), context.error, context.error.__traceback__
    )
    if update and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "⚠️ Something went wrong while processing your request. Please try again later."
            )
        except Exception:
            pass

if __name__ == '__main__':
    main()

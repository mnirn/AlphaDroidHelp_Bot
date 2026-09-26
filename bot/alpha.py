import cachetools.func
import datetime as dt
import re
from html import escape
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext

@cachetools.func.ttl_cache(maxsize=128, ttl=1 * 60 * 60)
def get_default_branch(owner, repo):
    rest_url = f"https://api.github.com/repos/{owner}/{repo}"

    response = requests.get(rest_url, timeout=10)
    response.raise_for_status()
    data = response.json()
    return data.get("default_branch", "16.2")

def get_download_links(device_code):
    device_code = device_code.strip()
    default_branch = get_default_branch("AlphaDroid-devices", "OTA")

    json_url = f"https://raw.githubusercontent.com/AlphaDroid-devices/OTA/{default_branch}/{device_code}.json"
    changelog_url = f"https://github.com/AlphaDroid-devices/OTA/blob/{default_branch}/changelog_{device_code}.txt"

    try:
        response = requests.get(json_url, timeout=10)
        
        if response.status_code == 404:
            return f"❌ Device with codename <b>{escape(device_code)}</b> was not found. Please check the spelling.", None

        response.raise_for_status()
        data = response.json()
        roms = data.get("response", [])

        if not roms:
            return "❌ No builds found for this device.", None

        first_entry = roms[0]
        maintainer = escape(str(first_entry.get("maintainer", "Unknown")))
        version = escape(str(first_entry.get("version", "Unknown")))

        release_date = None
        release_date_str = "Unknown"
        try:
            timestamp = int(first_entry.get("timestamp") or 0)
            if timestamp > 0:
                release_date = dt.date.fromtimestamp(timestamp)
                release_date_str = escape(release_date.isoformat())
        except (ValueError, TypeError, OSError, OverflowError):
            release_date = None

        status_icon, status_text = "⚪", "Unknown"
        try:
            if release_date is not None:
                recent = dt.date.today() - release_date <= dt.timedelta(days=180)
                branch_match = re.search(r"(\d+)", str(default_branch))
                branch_major = int(branch_match.group(1)) if branch_match else None
                filename_match = re.search(r"AlphaDroid-(\d+)-", str(first_entry.get("filename", "")))
                rom_major = int(filename_match.group(1)) if filename_match else None
                if recent:
                    status_icon, status_text = "🟢", "Active"
                elif branch_major is not None and rom_major is not None:
                    if rom_major >= branch_major:
                        status_icon, status_text = "🟢", "Active"
                    else:
                        status_icon, status_text = "🔴", "Inactive"
                else:
                    status_icon, status_text = "🔴", "Inactive"
        except (ValueError, TypeError):
            pass

        build_types = set()
        for rom in roms:
            variant = escape(str(rom.get("buildvariant", rom.get("buildtype", "Vanilla"))).capitalize())
            build_types.add(variant)

        message = (
            f"✅ <b>Latest AlphaDroid for {escape(device_code)}:</b>\n\n"
            f"📱 Version: <b>{version}</b>\n"
            f"🗓 Release date: <b>{release_date_str}</b>\n"
            f"{status_icon} Status: <b>{status_text}</b>\n"
            f"🛠 Build Types: <b>{', '.join(sorted(build_types))}</b>\n"
            f"🧑‍💻 Maintainer: <b>{maintainer}</b>\n"
        )

        keyboard = []
        telegram_link = None

        for rom in roms:
            variant = rom.get("buildvariant", rom.get("buildtype", "Build")).capitalize()
            download_url = rom.get("download")
            if download_url:
                keyboard.append([InlineKeyboardButton(f"⬇️ Download {variant}", url=download_url)])
            
            if not telegram_link and rom.get("telegram"):
                telegram_link = rom.get("telegram")

        bottom_row = [InlineKeyboardButton("📃 Changelog", url=changelog_url)]
        if telegram_link:
            bottom_row.append(InlineKeyboardButton("❗ Telegram", url=telegram_link))
        
        keyboard.append(bottom_row)

        return message, InlineKeyboardMarkup(keyboard)

    except requests.exceptions.Timeout:
        return "⚠️ The server is taking too long to respond. Please try again later.", None
    except Exception as e:
        return f"❌ An unexpected error occurred: {escape(str(e))}", None

async def alpha(update: Update, context: CallbackContext) -> None:
    args = update.message.text.split()

    if len(args) < 2:
        await update.message.reply_text(
            "⚠️ Please provide a device code.\nExample: <code>/alpha sunny</code>",
            parse_mode="HTML"
        )
        return

    device_code = args[1]
    result_text, reply_markup = get_download_links(device_code)

    await update.message.reply_text(
        result_text,
        parse_mode="HTML",
        disable_web_page_preview=True,
        reply_markup=reply_markup
    )

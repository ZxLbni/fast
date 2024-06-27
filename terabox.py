# terabox.py

import asyncio
import logging
import os
import re

from dotenv import load_dotenv
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from pyrogram.enums import ChatMemberStatus

from video import download_video, upload_video
from web import keep_alive

# Load environment variables
load_dotenv('config.env', override=True)

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize Pyrogram client
api_id = os.getenv('TELEGRAM_API')
api_hash = os.getenv('TELEGRAM_HASH')
bot_token = os.getenv('BOT_TOKEN')
dump_id = int(os.getenv('DUMP_CHAT_ID'))
fsub_id = int(os.getenv('FSUB_ID'))

if not (api_id and api_hash and bot_token and dump_id and fsub_id):
    logging.error("One or more required environment variables are missing! Exiting.")
    exit(1)

app = Client("my_bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)

# Commands and message handlers
@app.on_message(filters.command("start"))
async def start_command(client, message):
    sticker_message = await message.reply_sticker("CAACAgIAAxkBAAJg7GZ7sYaS4-EmISN1X58UZcQmdtsxAALTBQACP5XMCp9au9JdR8cxNQQ")
    await asyncio.sleep(2)
    await sticker_message.delete()

    user_mention = message.from_user.mention
    reply_message = (
        f"ᴡᴇʟᴄᴏᴍᴇ, {user_mention}.\n\n"
        "🌟 ɪ ᴀᴍ ᴀ ᴛᴇʀᴀʙᴏx ᴅᴏᴡɴʟᴏᴀᴅᴇʀ ʙᴏᴛ. sᴇɴᴅ ᴍᴇ ᴀɴʏ ᴛᴇʀᴀʙᴏx ʟɪɴᴋ ɪ ᴡɪʟʟ ᴅᴏᴡɴʟᴏᴀᴅ ᴡɪᴛʜɪɴ ғᴇᴡ sᴇᴄᴏɴᴅs ᴀɴᴅ sᴇɴᴅ ɪᴛ ᴛᴏ ʏᴏᴜ ✨."
    )

    join_button = InlineKeyboardButton("ᴊᴏɪɴ ❤️🚀", url="https://t.me/Semma_Bots")
    developer_button = InlineKeyboardButton("ᴅᴇᴠᴇʟᴏᴘᴇʀ ⚡️", url="https://t.me/Semma_Bots")
    reply_markup = InlineKeyboardMarkup([[join_button, developer_button]])

    await message.reply_text(reply_message, reply_markup=reply_markup)

async def is_user_member(client, user_id):
    try:
        member = await client.get_chat_member(fsub_id, user_id)
        logging.info(f"User {user_id} membership status: {member.status}")
        return member.status in [ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]
    except Exception as e:
        logging.error(f"Error checking membership status for user {user_id}: {e}")
        return False

@app.on_message(filters.text)
async def handle_message(client, message: Message):
    user_id = message.from_user.id
    user_mention = message.from_user.mention
    is_member = await is_user_member(client, user_id)

    if not is_member:
        join_button = InlineKeyboardButton("ᴊᴏɪɴ ❤️🚀", url="https://t.me/Semma_Bots")
        reply_markup = InlineKeyboardMarkup([[join_button]])

        await message.reply_text("ʏᴏᴜ ᴍᴜsᴛ ᴊᴏɪɴ ᴍʏ ᴄʜᴀɴɴᴇʟ ᴛᴏ ᴜsᴇ ᴍᴇ.", reply_markup=reply_markup)
        return

    terabox_link = message.text.strip()
    valid_domains = [
        r"mirrobox\.com", r"nephobox\.com", r"freeterabox\.com",
        r"1024tera\.com", r"4funbox\.co", r"4funbox\.com",
        r"terabox\.app", r"terabox\.com", r"momerybox\.com",
        r"teraboxapp\.com", r"tibibox\.com", r"terasharelink\.com",
    ]

    if not any(re.search(domain, terabox_link) for domain in valid_domains):
        await message.reply_text("ᴘʟᴇᴀsᴇ sᴇɴᴅ ᴀ ᴠᴀʟɪᴅ ᴛᴇʀᴀʙᴏx ʟɪɴᴋ.")
        return

    reply_msg = await message.reply_text("sᴇɴᴅɪɴɢ ʏᴏᴜ ᴛʜᴇ ᴍᴇᴅɪᴀ...🤤")

    try:
        file_path, thumbnail_path, video_title = await download_video(terabox_link, reply_msg, user_mention, user_id)
        await upload_video(client, file_path, thumbnail_path, video_title, reply_msg, dump_id, user_mention, user_id, message)
    except Exception as e:
        logging.error(f"Error handling message: {e}")
        await reply_msg.edit_text(
            "ғᴀɪʟᴇᴅ ᴛᴏ ᴘʀᴏᴄᴇss ʏᴏᴜʀ ʀᴇǫᴜᴇsᴛ.\nɪғ ʏᴏᴜʀ ғɪʟᴇ sɪᴢᴇ ɪs ᴍᴏʀᴇ ᴛʜᴀɴ 120ᴍʙ ɪᴛ ᴍɪɢʜᴛ ғᴀɪʟ ᴛᴏ ᴅᴏᴡɴʟᴏᴀᴅ.\nᴛʜɪs ɪs ᴛʜᴇ ᴛᴇʀᴀʙᴏx ɪssᴜᴇ, sᴏᴍᴇ ʟɪɴᴋs ᴀʀᴇ ʙʀᴏᴋᴇɴ, sᴏ ᴅᴏɴᴛ ᴄᴏɴᴛᴀᴄᴛ ʙᴏᴛ's ᴏᴡɴᴇʀ"
        )

# Main entry point
if __name__ == "__main__":
    keep_alive()  # Keep the bot alive
    app.run()     # Run the Pyrogram client

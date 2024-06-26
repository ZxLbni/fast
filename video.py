import requests
import aria2p
from datetime import datetime
from status import format_progress_bar
import asyncio
import os
import time
import logging
from pyrogram import Client, Message

# Initialize aria2 client
aria2 = aria2p.API(
    aria2p.Client(
        host="http://localhost",
        port=6800,
        secret=""
    )
)

# Function to download video asynchronously
async def download_video(url, reply_msg, user_mention, user_id):
    try:
        response = requests.get(f"https://teraboxvideodownloader.nepcoderdevs.workers.dev/?url={url}")
        response.raise_for_status()
        data = response.json()

        resolutions = data["response"][0]["resolutions"]
        fast_download_link = resolutions.get("Fast Download")
        thumbnail_url = data["response"][0]["thumbnail"]
        video_title = data["response"][0]["title"]

        if not fast_download_link or not thumbnail_url or not video_title:
            await reply_msg.edit_text("Failed to retrieve necessary data for download.")
            return None, None, None

        # Check file size if possible before downloading
        head_response = requests.head(fast_download_link)
        file_size = int(head_response.headers.get('Content-Length', 0))
        if file_size > 120 * 1024 * 1024:  # 120 MB
            await reply_msg.edit_text("File size exceeds 120 MB. Aborting download.")
            return None, None, None

        # Start downloading with aria2
        download = aria2.add_uris([fast_download_link])
        start_time = datetime.now()

        last_progress_text = ""

        while not download.is_complete:
            download.update()
            percentage = download.progress
            done = download.completed_length
            total_size = download.total_length
            speed = download.download_speed
            eta = download.eta
            elapsed_time_seconds = (datetime.now() - start_time).total_seconds()

            progress_text = format_progress_bar(
                filename=video_title,
                percentage=percentage,
                done=done,
                total_size=total_size,
                status="Downloading",
                eta=eta,
                speed=speed,
                elapsed=elapsed_time_seconds,
                user_mention=user_mention,
                user_id=user_id,
                aria2p_gid=download.gid
            )

            if progress_text != last_progress_text:
                await reply_msg.edit_text(progress_text)
                last_progress_text = progress_text

            await asyncio.sleep(2)

        if download.is_complete:
            file_path = download.files[0].path

            thumbnail_path = "thumbnail.jpg"
            thumbnail_response = requests.get(thumbnail_url)
            with open(thumbnail_path, "wb") as thumb_file:
                thumb_file.write(thumbnail_response.content)

            await reply_msg.edit_text("Download complete.")

            return file_path, thumbnail_path, video_title
        else:
            raise Exception("Download failed")

    except Exception as e:
        logging.error(f"Error in download_video: {e}")
        await reply_msg.edit_text("An error occurred during download.")
        return None, None, None

# Function to upload video
async def upload_video(client, file_path, thumbnail_path, video_title, reply_msg, collection_channel_id, user_mention, user_id, message):
    try:
        file_size = os.path.getsize(file_path)
        uploaded = 0
        start_time = datetime.now()
        last_update_time = time.time()
        last_progress_text = ""

        async def progress(current, total):
            nonlocal uploaded, last_update_time, last_progress_text
            uploaded = current
            percentage = (current / total) * 100
            elapsed_time_seconds = (datetime.now() - start_time).total_seconds()

            progress_text = format_progress_bar(
                filename=video_title,
                percentage=percentage,
                done=current,
                total_size=total,
                status="Uploading",
                eta=(total - current) / (current / elapsed_time_seconds) if current > 0 else 0,
                speed=current / elapsed_time_seconds if current > 0 else 0,
                elapsed=elapsed_time_seconds,
                user_mention=user_mention,
                user_id=user_id,
                aria2p_gid=""
            )

            if progress_text != last_progress_text and time.time() - last_update_time > 2:
                try:
                    await reply_msg.edit_text(progress_text)
                    last_progress_text = progress_text
                    last_update_time = time.time()
                except Exception as e:
                    logging.warning(f"Error updating progress message: {e}")

        with open(file_path, 'rb') as file:
            collection_message = await client.send_video(
                chat_id=collection_channel_id,
                video=file,
                caption=f"🎞 File name: {video_title}\n⏰ Duration: \n👤 Task by: {user_mention}\n🔗 User's link: tg://user?id={user_id}",
                thumb=thumbnail_path,
                progress=progress
            )
            await client.copy_message(
                chat_id=message.chat.id,
                from_chat_id=collection_channel_id,
                message_id=collection_message.id
            )
            await asyncio.sleep(1)
            await message.delete()
            await message.reply_sticker("CAACAgIAAxkBAAEZdwRmJhCNfFRnXwR_lVKU1L9F3qzbtAAC4gUAAj-VzApzZV-v3phk4DQE")

        await reply_msg.delete()

        os.remove(file_path)
        os.remove(thumbnail_path)
        return collection_message.id

    except Exception as e:
        logging.error(f"Error in upload_video: {e}")
        await reply_msg.edit_text("An error occurred during upload.")
        return None

# Function to handle messages and download/upload videos
async def handle_message(m: Message):
    if m.is_group or m.is_channel:
        return

    username = m.sender.username
    first_name = m.sender.first_name
    user_id = m.sender_id

    if db.sismember("banned_users", user_id):
        await m.reply("You are banned from using this bot. Contact support for more info.")
        return

    url = get_urls_from_string(m.text)
    if not url:
        return await m.reply("Please enter a valid URL.")

    reply_msg = await m.reply("Downloading your video...")

    # Call download_video function to download the video
    file_path, thumbnail_path, video_title = await download_video(url, reply_msg, username, user_id)

    if file_path and thumbnail_path and video_title:
        # Replace with your Pyrogram client initialization
        client = Client("my_bot_session")

        # Replace with your actual channel ID
        collection_channel_id = "@your_channel_id"

        # Call upload_video function to upload the video
        await upload_video(client, file_path, thumbnail_path, video_title, reply_msg, collection_channel_id, username, user_id, m)

        # Close the Pyrogram client
        await client.close()

# Example usage of handling messages
@bot.on_message(filters.command(["start"]))
async def start_command(client, message):
    await handle_message(message)

@bot.on_message(filters.command(["help"]))
async def help_command(client, message):
    await message.reply("This is a help message.")

# You can add more handlers for other commands or events here

# Run the bot
bot.run()
            

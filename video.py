import requests
import aria2p
from datetime import datetime
import asyncio
import os
import time
import logging

# Assuming format_progress_bar and format_duration functions are imported correctly
from status import format_progress_bar, format_duration

aria2 = aria2p.API(
    aria2p.Client(
        host="http://localhost",
        port=6800,
        secret=""
    )
)

async def download_video(url, reply_msg, user_mention, user_id):
    try:
        response = requests.get(f"https://teraboxvideodownloader.nepcoderdevs.workers.dev/?url={url}")
        response.raise_for_status()
        data = response.json()

        resolutions = data["response"][0]["resolutions"]
        fast_download_link = resolutions["Fast Download"]
        thumbnail_url = data["response"][0]["thumbnail"]
        video_title = data["response"][0]["title"]
        duration = data["response"][0].get("duration", "Unknown")

        # Check file size if possible before downloading
        head_response = requests.head(fast_download_link)
        file_size = int(head_response.headers.get('Content-Length', 0))
        if file_size > 120 * 1024 * 1024:  # 120 MB
            await reply_msg.edit_text("ᴛʜᴇ ғɪʟᴇ sɪᴢᴇ ɪs ᴍᴏʀᴇ ᴛʜᴀɴ 120ᴍʙ. ᴅᴏᴡɴʟᴏᴀᴅ ғᴀɪʟᴇᴅ.")
            return

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
            
            progress_text = await format_progress_bar(
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
                aria2p_gid=download.gid,
                duration=duration
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

            await reply_msg.edit_text("ᴜᴘʟᴏᴀᴅɪɴɢ...")

            return file_path, thumbnail_path, video_title, duration
        else:
            raise Exception("Download failed")

    except Exception as e:
        logging.error(f"Error downloading video: {e}")
        await reply_msg.edit_text("Error occurred during download. Please try again later.")

async def upload_video(client, file_path, thumbnail_path, video_title, reply_msg, collection_channel_id, user_mention, user_id, message, duration):
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
            
            progress_text = await format_progress_bar(
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
                aria2p_gid="",
                duration=duration
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
                caption=f"✨ {video_title}\n👤 ʟᴇᴇᴄʜᴇᴅ ʙʏ : {user_mention}\n📥 ᴜsᴇʀ ʟɪɴᴋ: tg://user?id={user_id}",
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
        logging.error(f"Error uploading video: {e}")
        await reply_msg.edit_text("Error occurred during upload. Please try again later.")

async def format_progress_bar(filename, percentage, done, total_size, status, eta, speed, elapsed, user_mention, user_id, aria2p_gid, duration):
    progress_bar = f"[{'=' * int(percentage // 5)}{' ' * (20 - int(percentage // 5))}] {percentage:.2f}%"
    progress_text = (
        f"**{filename}**\n"
        f"{progress_bar}\n"
        f"**{status}**\n"
        f"Done: {done / (1024 ** 2):.2f} MB / {total_size / (1024 ** 2):.2f} MB\n"
        f"Speed: {speed / 1024:.2f} KB/s\n"
        f"ETA: {eta:.2f} seconds\n"  # Fixed formatting for ETA
        f"Elapsed: {elapsed:.2f} seconds\n"
        f"Duration: {duration}\n"
        f"User: {user_mention} (ID: {user_id})\n"
    )
    return progress_text

async def format_duration(seconds):
    if isinstance(seconds, (int, float)):
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = int(seconds % 60)
        return f"{hours:02}:{minutes:02}:{seconds:02}"
    return "Unknown"


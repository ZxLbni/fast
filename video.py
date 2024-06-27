import requests
import aria2p
from datetime import datetime
from status import format_progress_bar
import asyncio
import os
import logging
from moviepy.editor import VideoFileClip

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize aria2 API
aria2 = aria2p.API(
    aria2p.Client(
        host="http://localhost",
        port=6800,
        secret=""  # Add your secret here if applicable
    )
)

async def download_video(url, reply_msg, user_mention, user_id):
    try:
        # Example of downloading video from a URL
        response = requests.get(f"https://example.com/download?url={url}")
        response.raise_for_status()
        data = response.json()

        # Extract video details
        video_url = data["video_url"]
        video_title = data["title"]

        # Add video to aria2 for downloading
        download = aria2.add_uris([video_url])
        start_time = datetime.now()

        # Monitor download progress
        while not download.is_complete:
            download.update()
            percentage = download.progress
            done = download.completed_length
            total_size = download.total_length
            speed = download.download_speed
            eta = download.eta
            elapsed_time_seconds = (datetime.now() - start_time).total_seconds()

            # Format and update progress message
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
            await reply_msg.edit_text(progress_text)
            await asyncio.sleep(2)

        if download.is_complete:
            file_path = download.files[0].path
            # Optionally handle thumbnail and other metadata here
            return file_path, video_title
        else:
            raise Exception("Download failed")

    except Exception as e:
        logging.error(f"Error in download_video: {e}")
        raise

async def upload_video(client, file_path, video_title, reply_msg, collection_channel_id, user_mention, user_id):
    try:
        file_size = os.path.getsize(file_path)
        uploaded = 0
        start_time = datetime.now()
        last_update_time = 0  # Initialize last update time

        try:
            # Example of processing video duration using moviepy
            path = str(file_path)
            clip = VideoFileClip(path)
            duration = int(clip.duration)
            clip.close()
        except Exception as e:
            logging.warning(f"Failed to get video duration: {e}")
            duration = 0
        
        # Format duration into HH:MM:SS
        hours, remainder = divmod(duration, 3600)
        minutes, seconds = divmod(remainder, 60)
        conv_duration = f"{hours:02}:{minutes:02}:{seconds:02}"

        async def progress(current, total):
            nonlocal uploaded, last_update_time
            uploaded = current
            percentage = (current / total) * 100
            elapsed_time_seconds = (datetime.now() - start_time).total_seconds()

            # Example of formatting and updating progress message
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
            try:
                await reply_msg.edit_text(progress_text)
                last_update_time = time.time()
            except Exception as e:
                logging.warning(f"Error updating progress message: {e}")

        # Example of uploading video to client (Telegram)
        with open(file_path, 'rb') as file:
            collection_message = await client.send_video(
                chat_id=collection_channel_id,
                video=file,
                duration=duration,
                caption=f"✨ {video_title} \nDuration: {conv_duration} \nUploaded by: {user_mention}\nUser link: tg://user?id={user_id}",
                progress=progress
            )
            # Optionally copy message to another chat or handle further actions
            await client.copy_message(
                chat_id=message.chat.id,
                from_chat_id=collection_channel_id,
                message_id=collection_message.id
            )
            await asyncio.sleep(1)
            await message.delete()
            await message.reply_sticker("CAACAgIAAxkBAAEZdwRmJhCNfFRnXwR_lVKU1L9F3qzbtAAC4gUAAj-VzApzZV-v3phk4DQE")

        await reply_msg.delete()

        # Optionally clean up temporary files after upload
        os.remove(file_path)
        
    except Exception as e:
        logging.error(f"Error in upload_video: {e}")
        raise

# Example usage of the script
if __name__ == "__main__":
    # Example URL and user details
    url = "https://example.com/video"
    reply_msg = "Reply message object"
    user_mention = "@username"
    user_id = "user_id"
    collection_channel_id = "collection_channel_id"

    # Example of asyncio event loop for running async functions
    loop = asyncio.get_event_loop()
    try:
        # Example of running download and upload functions asynchronously
        file_path, video_title = loop.run_until_complete(download_video(url, reply_msg, user_mention, user_id))
        loop.run_until_complete(upload_video(client, file_path, video_title, reply_msg, collection_channel_id, user_mention, user_id))
    finally:
        loop.close()

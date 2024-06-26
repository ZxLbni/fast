import requests
import aria2p
from datetime import datetime
import asyncio
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

# Aria2 client setup
aria2 = aria2p.API(
    aria2p.Client(
        host="http://localhost",
        port=6800,
        secret="YOUR_SECRET_HERE"  # Replace with your aria2 RPC secret if configured
    )
)

# Function to download video using teraboxvideodownloader API
async def download_video(url, user_mention, user_id, reply_msg):
    try:
        response = requests.get(f"https://teraboxvideodownloader.nepcoderdevs.workers.dev/?url={url}")
        response.raise_for_status()
        data = response.json()

        resolutions = data["response"][0]["resolutions"]
        fast_download_link = resolutions.get("Fast Download")
        thumbnail_url = data["response"][0]["thumbnail"]
        video_title = data["response"][0]["title"]

        download = aria2.add_uris([fast_download_link])
        start_time = datetime.now()

        while not download.is_complete:
            download.update()
            percentage = download.progress
            done = download.completed_length
            total_size = download.total_length
            speed = download.download_speed
            eta = download.eta
            elapsed_time_seconds = (datetime.now() - start_time).total_seconds()

            # Printing or logging download progress
            logging.info(f"Downloading {video_title}: {percentage}% ({done}/{total_size}), Speed: {speed}, ETA: {eta}")

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
            return file_path, thumbnail_url, video_title
        else:
            raise Exception("Download failed")

    except Exception as e:
        logging.error(f"Error downloading video: {e}")
        raise

# Function to upload video to Telegram
async def upload_video(client, file_path, thumbnail_path, video_title, collection_channel_id, user_mention, user_id, reply_msg, message):
    try:
        file_size = os.path.getsize(file_path)
        start_time = datetime.now()

        with open(file_path, 'rb') as file:
            collection_message = await client.send_video(
                chat_id=collection_channel_id,
                video=file,
                caption=f"✨ {video_title}\n👤 Leech by: {user_mention}\n📥 User link: tg://user?id={user_id}",
                thumb=thumbnail_path
            )

            # Copying message to another chat
            await client.copy_message(
                chat_id=message.chat.id,
                from_chat_id=collection_channel_id,
                message_id=collection_message.id
            )

            # Deleting original message and sending a sticker
            await asyncio.sleep(1)
            await message.delete()
            await message.reply_sticker("CAACAgIAAxkBAAEZdwRmJhCNfFRnXwR_lVKU1L9F3qzbtAAC4gUAAj-VzApzZV-v3phk4DQE")

        logging.info(f"Video uploaded: {video_title}")

    except Exception as e:
        logging.error(f"Error uploading video: {e}")
        raise

    finally:
        # Cleanup: deleting local files
        os.remove(file_path)
        os.remove(thumbnail_path)

# Main function to orchestrate download and upload process
async def main(client, url, collection_channel_id, user_mention, user_id, message):
    try:
        reply_msg = await message.reply_text("Starting download...")

        # Downloading video
        file_path, thumbnail_url, video_title = await download_video(url, user_mention, user_id, reply_msg)
        thumbnail_path = "thumbnail.jpg"

        # Downloading thumbnail
        thumbnail_response = requests.get(thumbnail_url)
        with open(thumbnail_path, "wb") as thumb_file:
            thumb_file.write(thumbnail_response.content)

        await reply_msg.edit_text("Uploading...")

        # Uploading video
        await upload_video(client, file_path, thumbnail_path, video_title, collection_channel_id, user_mention, user_id, reply_msg, message)

    except Exception as e:
        logging.error(f"Error processing video: {e}")

# Example usage or integration with Telegram client
# Replace with your actual Telegram client setup and message handling
async def telegram_integration_example():
    try:
        # Example Telegram client setup and message handling
        # client = ...

        url = "https://example.com/video_url"
        collection_channel_id = "your_collection_channel_id"
        user_mention = "username"
        user_id = "user_id"
        message = "message_object"

        await main(client, url, collection_channel_id, user_mention, user_id, message)

    except Exception as e:
        logging.error(f"Error in Telegram integration: {e}")

# Running the main function
if __name__ == "__main__":
    asyncio.run(telegram_integration_example())


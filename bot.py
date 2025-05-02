#© @thealphabotz
import asyncio
import logging
from telethon import TelegramClient
from telethon.sessions import StringSession

logging.basicConfig(level=logging.INFO)

API_ID = 28462418
API_HASH = "dac7a169fd7ba76bbd19e7fba96629db"
SESSION_STRING = "AQFrGogAGJHWe4pPF_QqDvbx_Xk4KQwYMNzjVGLyvnh-tw7rOgzgYegWKiGiHyPqekLd3rrJ6fY7epILpFt8wAREY7IUwkO7wUgouihAE44RFbPmGHcB3IzV0vNC3xxWIOGdj9yO5Pkx1SLmqi3t-6lXQV1YavHdxDf8JokevTDcBS5-_BIskwP5DGQ2kEmV7t0LxlAjfl6w_06h_TkHp4bWbuCPnseaqAtMZzdMcTPW6IADyESFArPYDN8xJipsgUsJ5C5IwZQH20-hi39oJ8_Xv-8CMuF_FM9vdpO6_uw6ztZiBPzPnc-bMgoBEiAUaF-GWzrpfwPPFdFIRbCY3GP2rI1zagAAAAGzGCl8AA"
SOURCE_CHANNEL = -1002668250369
DESTINATION_CHANNEL = -1002655996750
START_POST_ID = 2

client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

async def get_channel_entity(channel_id):
    try:
        entity = await client.get_entity(channel_id)
        logging.info(f"Resolved channel entity: {entity.title} (ID: {entity.id})")
        return entity
    except ValueError as e:
        logging.error(f"Cannot resolve channel {channel_id}: {e}")
        logging.info("Ensure the account is a member of the source channel.")
        raise
    except Exception as e:
        logging.error(f"Unexpected error resolving entity: {e}")
        raise

async def forward_batch(start_id, batch_size=1000, delay=5, pause_hours=3):
    async with client:
        source_entity = await get_channel_entity(SOURCE_CHANNEL)
        logging.info("Bot started forwarding")
        
        message_id = start_id
        batch_count = 0
        
        while True:
            end_id = message_id + batch_size
            for msg_id in range(message_id, end_id):
                try:
                    message = await client.get_messages(source_entity, ids=msg_id)
                    if not message:
                        logging.info(f"No more messages found at ID {msg_id}")
                        return
                    
                    if message.media:
                    
                        file_path = await client.download_media(message.media)
                        if file_path:
                            
                            await client.send_file(
                                DESTINATION_CHANNEL,
                                file_path,
                                caption=message.text or "",
                                force_document=False  
                            )
                            logging.info(f"Uploaded media from file: {file_path}")
                        else:
                            logging.error(f"Failed to download media for message ID {msg_id}")
                    elif message.text:
                        
                        await client.send_message(DESTINATION_CHANNEL, message.text)
                    
                    logging.info(f"Forwarded message ID: {msg_id}")
                    if (msg_id - start_id + 1) % 10 == 1:
                        logging.info(f"Progress: Forwarded message {msg_id}")
                    
                    await asyncio.sleep(delay)
                
                except Exception as e:
                    logging.error(f"Error forwarding message ID {msg_id}: {e}")
                    await asyncio.sleep(delay)
            
            batch_count += 1
            message_id = end_id
            logging.info(f"Completed batch {batch_count} (Messages {message_id - batch_size} to {message_id - 1})")
            logging.info(f"Pausing for {pause_hours} hours...")
            await asyncio.sleep(pause_hours * 3600)

async def start_forwarding():
    await forward_batch(START_POST_ID)

client.loop.run_until_complete(start_forwarding())

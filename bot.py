#© @thealphabotz
import asyncio
import logging
from telethon import TelegramClient
from telethon.sessions import StringSession

logging.basicConfig(level=logging.INFO)

API_ID = 28462418
API_HASH = "dac7a169fd7ba76bbd19e7fba96629db"
SESSION_STRING = "1BZWaqwUAUAXlwZkLLEQvMLkUAdpp_VQoGtm39pCY26HAz6cG47_JdIZgv2A9BweaieO_iMxqb7FXSjfp5lXpaq-BrmdUjUjBiC3knhJYYJV8qh326ly6GCqwGNg0QWfmamp1vBAbA2k96s6hWDE3QfLitxxcD9HwkoHyJJr6xTH3Fy09rlp3i0KKb8zgTR9f1PQKsLgSQz--zg9lEFA3MxmsV073RtqU_pWEF55to35UOYyV64LTn2m8YAbe625kcIkO7MYI0GDii1va_b7uHiCck47gfXE8fYhPumV2f9I04v-lQttrvR2953QzYUjvoWH81vpmjlwHt3o4Z1GaOKDxF4lZVCU="
SOURCE_CHANNEL = -1002496964122
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

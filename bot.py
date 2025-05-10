#© @thealphabotz
import asyncio
import logging
import os
from telethon import TelegramClient
from telethon.sessions import StringSession

logging.basicConfig(level=logging.INFO)

API_ID = 28462418
API_HASH = "dac7a169fd7ba76bbd19e7fba96629db"
SESSION_STRING = ""

# Can be channel IDs or group IDs
SOURCE_ENTITY = -1002668250369
DESTINATION_ENTITY = -1002558951301
START_POST_ID = 2

client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

async def get_entity(entity_id):
    """
    Get entity for both channels and private groups
    
    Args:
        entity_id: The ID of the channel or group
        
    Returns:
        The entity object
    """
    try:
        entity = await client.get_entity(entity_id)
        entity_type = "channel" if hasattr(entity, "broadcast") and entity.broadcast else "group"
        logging.info(f"Resolved {entity_type} entity: {getattr(entity, 'title', 'Unknown')} (ID: {entity.id})")
        return entity
    except ValueError as e:
        logging.error(f"Cannot resolve entity {entity_id}: {e}")
        logging.info("Ensure the account is a member of the source entity (channel or group).")
        raise
    except Exception as e:
        logging.error(f"Unexpected error resolving entity: {e}")
        raise

async def forward_batch(start_id, batch_size=1000, delay=5, pause_hours=3):
    async with client:
        source_entity = await get_entity(SOURCE_ENTITY)
        destination_entity = await get_entity(DESTINATION_ENTITY)
        
        entity_type = "channel" if hasattr(source_entity, "broadcast") and source_entity.broadcast else "group"
        logging.info(f"Bot started forwarding from {entity_type} {getattr(source_entity, 'title', 'Unknown')}")
        
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
                                destination_entity,
                                file_path,
                                caption=message.text or "",
                                force_document=False  
                            )
                            logging.info(f"Uploaded media from file: {file_path}")
                            # Clean up downloaded file
                            try:
                                os.remove(file_path)
                            except:
                                pass
                        else:
                            logging.error(f"Failed to download media for message ID {msg_id}")
                    elif message.text:
                        await client.send_message(destination_entity, message.text)
                    
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

if __name__ == "__main__":
    client.loop.run_until_complete(start_forwarding())

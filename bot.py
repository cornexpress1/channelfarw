#!/usr/bin/env python3
#© @thealphabotz
import asyncio
import logging
import os
from telethon import TelegramClient
from telethon.sessions import StringSession

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Get environment variables with fallbacks to original values
API_ID = int(os.environ.get('API_ID', '28462418'))
API_HASH = os.environ.get('API_HASH', 'dac7a169fd7ba76bbd19e7fba96629db')
SESSION_STRING = os.environ.get('SESSION_STRING', '')

# Can be channel IDs or group IDs
SOURCE_ENTITY = int(os.environ.get('SOURCE_ENTITY', '-1002668250369'))
DESTINATION_ENTITY = int(os.environ.get('DESTINATION_ENTITY', '-1002558951301'))
START_POST_ID = int(os.environ.get('START_POST_ID', '2'))

# Log the configuration (but not sensitive values)
logger.info(f"Starting bot with SOURCE_ENTITY: {SOURCE_ENTITY}, DESTINATION_ENTITY: {DESTINATION_ENTITY}")
logger.info(f"Starting from message ID: {START_POST_ID}")

# Initialize client
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

async def forward_messages(start_id=None, delay=5):
    """
    Forward messages from source to destination, skipping any missing messages
    """
    async with client:
        source_entity = await get_entity(SOURCE_ENTITY)
        destination_entity = await get_entity(DESTINATION_ENTITY)
        
        entity_type = "channel" if hasattr(source_entity, "broadcast") and source_entity.broadcast else "group"
        logging.info(f"Bot started forwarding from {entity_type} {getattr(source_entity, 'title', 'Unknown')}")
        
        # Set the starting message ID
        current_id = start_id if start_id is not None else START_POST_ID
        logging.info(f"Starting from message ID: {current_id}")
        
        # Counter for consecutive missing messages
        missing_count = 0
        
        # Get the most recent message ID to know when we're caught up with history
        most_recent_id = None
        try:
            messages = await client.get_messages(source_entity, limit=1)
            if messages and len(messages) > 0:
                most_recent_id = messages[0].id
                logging.info(f"Most recent message ID: {most_recent_id}")
        except Exception as e:
            logging.error(f"Error getting most recent message: {e}")
        
        # Flag to track if we've reached real-time monitoring
        in_watch_mode = False
        
        # Main processing loop
        while True:
            try:
                # In watch mode, we check for new messages differently
                if in_watch_mode:
                    # Get new messages after the last processed ID
                    new_messages = await client.get_messages(source_entity, limit=10, offset_id=current_id-1)
                    
                    # If we found new messages
                    if new_messages and len(new_messages) > 0:
                        # Process them in chronological order (oldest first)
                        for message in reversed(new_messages):
                            if message.id > current_id:
                                logging.info(f"New message detected with ID: {message.id}")
                                await forward_single_message(message, destination_entity)
                                current_id = message.id + 1  # Set to next ID after this one
                    
                    # Wait before checking again
                    await asyncio.sleep(delay)
                    continue
                
                # In historical mode, we process messages one by one
                message = await client.get_messages(source_entity, ids=current_id)
                
                if message:
                    # Message exists, forward it
                    await forward_single_message(message, destination_entity)
                    missing_count = 0  # Reset missing count
                else:
                    # Message doesn't exist, log and skip
                    logging.info(f"No message found at ID {current_id}, skipping to next ID")
                    missing_count += 1
                
                # Move to next ID
                current_id += 1
                
                # Check if we've caught up to the most recent message
                if most_recent_id and current_id > most_recent_id:
                    logging.info(f"Processed all historical messages up to ID {most_recent_id}")
                    logging.info("Switching to real-time message monitoring mode")
                    in_watch_mode = True
                    
                    # Get the updated most recent message ID before entering watch mode
                    try:
                        messages = await client.get_messages(source_entity, limit=1)
                        if messages and len(messages) > 0:
                            current_id = messages[0].id + 1  # Start watching from after the most recent
                            logging.info(f"Now watching for messages after ID: {current_id-1}")
                    except Exception as e:
                        logging.error(f"Error updating most recent message before watch mode: {e}")
                
                # If we've skipped too many messages in a row, update the most recent ID check
                if missing_count >= 100:
                    logging.info("Many consecutive missing messages, checking for most recent message...")
                    try:
                        messages = await client.get_messages(source_entity, limit=1)
                        if messages and len(messages) > 0:
                            most_recent_id = messages[0].id
                            logging.info(f"Updated most recent message ID: {most_recent_id}")
                            # If we're far behind, jump ahead
                            if most_recent_id and (most_recent_id - current_id) > 500:
                                logging.info(f"Large gap detected. Jumping from ID {current_id} to {most_recent_id - 100}")
                                current_id = most_recent_id - 100  # Jump to near the end, process the last 100 messages
                    except Exception as e:
                        logging.error(f"Error updating most recent message: {e}")
                    missing_count = 0
                
                # Wait between processing messages
                await asyncio.sleep(delay)
                
            except Exception as e:
                logging.error(f"Error processing message ID {current_id}: {e}")
                await asyncio.sleep(delay)
                current_id += 1  # Move to next ID even after error

async def forward_single_message(message, destination_entity):
    """
    Forward a single message to the destination entity
    """
    try:
        if message.media:
            file_path = await client.download_media(message.media)
            if file_path:
                await client.send_file(
                    destination_entity,
                    file_path,
                    caption=message.text or "",
                    force_document=False
                )
                logging.info(f"Forwarded media message ID: {message.id}")
                # Clean up downloaded file
                try:
                    os.remove(file_path)
                except:
                    pass
            else:
                logging.error(f"Failed to download media for message ID {message.id}")
        elif message.text:
            await client.send_message(destination_entity, message.text)
            logging.info(f"Forwarded text message ID: {message.id}")
    except Exception as e:
        logging.error(f"Error forwarding message ID {message.id}: {e}")

if __name__ == "__main__":
    try:
        logger.info("Starting Telegram forwarding bot")
        # Start forwarding messages
        client.loop.run_until_complete(forward_messages())
        # Keep the bot running
        client.loop.run_until_complete(client.run_until_disconnected())
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)

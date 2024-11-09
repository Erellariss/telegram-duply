import os
import re
import shutil
import traceback
from time import sleep

from loguru import logger
from telethon import TelegramClient
from telethon.errors import FileReferenceExpiredError, FloodError, MessageTooLongError
from telethon.tl.types import Message, MessageMediaDocument, MessageMediaPoll, MessageMediaPhoto

from utils.env_link_parser import load_link_pairs
from utils.utils import load_regexp_patterns_from_env, split_long_text, is_voice, get_file_name, persist_offset, load_offset, \
    get_env_variable

SESSIONS_DIR = "data/sessions"
DOWNLOADS_DIR = "data/downloads"

client = TelegramClient(
    os.path.join(SESSIONS_DIR, "account_session"),
    api_id=int(get_env_variable('API_ID')),
    api_hash=get_env_variable('API_HASH'),
)

async def clone_messages_from_topic(group_id_from: int, topic_id_from: int | None , group_id_to: int, topic_id_to: int | None):
    base_path = os.path.join(DOWNLOADS_DIR, str(group_id_from), str(topic_id_from))
    os.makedirs(base_path, exist_ok=True)

    supergroup_from = await client.get_input_entity(group_id_from)
    supergroup_to = await client.get_input_entity(group_id_to)
    offset = load_offset(base_path)
    while True:
        init_offset = offset
        try:
            async for message in client.iter_messages(supergroup_from, reverse=True, min_id=offset, reply_to=topic_id_from, limit=50):
                if not isinstance(message, Message):
                    offset = message.id
                    continue
                logger.debug(f"Handling message https://t.me/c/{message.chat.id}/{message.id}")
                media = message.media
                message_path = os.path.join(base_path, str(message.id))
                try:
                    match media:
                        case MessageMediaDocument():
                            await forward_media_document(message_path, media, message, supergroup_to, topic_id_to)
                        case MessageMediaPhoto():
                            await forward_photo(message_path, message, supergroup_to, topic_id_to)
                        case MessageMediaPoll():
                            logger.info(f"Skipping message with id {message.id}, because it has poll.")
                        case None:
                            await client.send_message(
                                entity=supergroup_to,
                                reply_to=topic_id_to,
                                message=message.text
                            )
                        case _:
                            if not message.text:
                                logger.info(f"Skipping message (unknown media + no message text)")
                            else:
                                logger.warning(f"Skipping message media, trying to send just text...")
                                await client.send_message(
                                    entity=supergroup_to,
                                    reply_to=topic_id_to,
                                    message=message.text
                                )
                except MessageTooLongError:
                    logger.info(f"message was too long, splitting into two parts...")
                    text1, text2 = split_long_text(message.text)
                    await client.send_message(
                        entity=supergroup_to,
                        reply_to=topic_id_to,
                        message=text1
                    )
                    await client.send_message(
                        entity=supergroup_to,
                        reply_to=topic_id_to,
                        message=text2
                    )
                offset = message.id
                persist_offset(base_path, offset)
                shutil.rmtree(message_path, ignore_errors=True) # removing of processed message.
        except FileReferenceExpiredError:
            logger.warning(f"file from message with id {message.id} was expired, retry...")
            continue
        except FloodError as error:
            logger.error(error)
            if error.seconds:
                logger.info(f"Waiting {error.seconds + 1} seconds before sending new messages...")
                sleep(error.seconds + 1)
            else:
                logger.warning(f"Unable to parse message: {error.message}, waiting 100 seconds...")
                sleep(100)
            continue
        except Exception as error:
            logger.error(error)
            traceback.print_exc()
            exit(1)
        if offset == init_offset:
            logger.info(f"Group {group_id_from} + topic {topic_id_from} was cloned successfully")
            # Only for backward compatibility!
            logger.info(f"Cleanup of loaded data... (saving only offset)")
            shutil.rmtree(base_path)
            os.makedirs(base_path, exist_ok=True)
            persist_offset(base_path, offset)
            return


async def forward_media_document(message_path, media, message, supergroup_to, topic_id_to):
    os.makedirs(message_path, exist_ok=True)
    document = media.document
    filename_ = get_file_name(document.attributes)
    if re.search(FILE_IGNORE_PATTERN, filename_):
        logger.info(f"Skipping message with id {message.id}, as file ignore pattern matches")
        return
    file_path = os.path.join(message_path, filename_)
    if (not os.path.exists(file_path)
            or os.path.getsize(file_path) != document.size):
        logger.debug(f"Downloading file: {filename_}...")
        await client.download_media(media, file=file_path)
        logger.debug("Complete.")
    else:
        logger.debug(f"File by path {file_path}, already exists and matches destination size, skip.")
    text = text_cleanup(message.text)
    logger.debug(f"Sending message with id {message.id} \n\nwith attached file: {file_path}")
    await client.send_file(
        entity=supergroup_to,
        reply_to=topic_id_to,
        file=file_path,
        attributes=document.attributes,
        caption=text,
        voice_note=is_voice(document.attributes),
    )


async def forward_photo(message_path, message, supergroup_to, topic_id_to):
    os.makedirs(message_path, exist_ok=True)
    image = await client.download_media(message.media, os.path.join(message_path, "img"))
    msg_str = text_cleanup(message.text)
    logger.debug(f"Sending message with id {message.id} with attached photo")
    await client.send_message(
        entity=supergroup_to,
        reply_to=topic_id_to,
        file=image,
        message=msg_str
    )


async def load_message(group_id_from: int, topic_id_from: int | None, message_id):
    supergroup_from = await client.get_input_entity(group_id_from)
    async for message in client.iter_messages(supergroup_from, reverse=True, min_id=message_id - 1, reply_to=topic_id_from, limit=1):
        print(message)


def text_cleanup(text: str):
    return re.sub(MESSAGE_CLEANUP_PATTERN, '', text)


FILE_IGNORE_PATTERN, MESSAGE_CLEANUP_PATTERN = load_regexp_patterns_from_env()


# with client:
#     client.loop.run_until_complete(load_message(1750589044, None, 24502))


with client:
    link_pairs = load_link_pairs()

    logger.info("Loaded Link pairs:")
    for i, pair in enumerate(link_pairs, 1):
        logger.info(f"{i}. {pair}")

    for i, pair in enumerate(link_pairs, 1):
        group_id_from = pair.from_link.group_id
        topic_id_from = pair.from_link.topic_id
        group_id_to = pair.to_link.group_id
        topic_id_to = pair.to_link.topic_id
        logger.info(
            f"Handling pair number {i}: Cloning from group {group_id_from} + topic {topic_id_from} into group {group_id_to} + topic {topic_id_to}")
        client.loop.run_until_complete(clone_messages_from_topic(group_id_from, topic_id_from, group_id_to, topic_id_to))

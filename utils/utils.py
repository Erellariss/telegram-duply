import os
import re
from re import Pattern

from dotenv import load_dotenv
from telethon.tl.types import DocumentAttributeAudio, DocumentAttributeFilename


def get_env_variable(var_name, default=None):
    """
    Loads environment variables, ensuring they are read from a .env file if available.

    This function loads variables from the .env file into the environment if they aren't already
    present, then retrieves the specified variable.

    Parameters:
    -----------
    var_name : str
        The name of the environment variable to retrieve.

    default : Any, optional
        The default value to return if the environment variable is not found.

    Returns:
    --------
    str or Any
        The value of the environment variable if found, otherwise returns the default value.
    """
    # Load environment variables from .env file if they are not already loaded
    load_dotenv()

    # Retrieve the specified environment variable
    return os.getenv(var_name, default)


def load_regexp_patterns_from_env() -> tuple[Pattern[str | None], Pattern[str | None]]:
    """
    Get regexp patterns from environment variables with fallback to defaults.
    Returns tuple of (file_ignore_pattern, message_cleanup_pattern)
    """

    # Get patterns from env or use defaults
    load_dotenv()
    file_ignore_pattern = os.getenv('FILE_IGNORE_PATTERN')
    message_cleanup_pattern = os.getenv('MESSAGE_CLEANUP_PATTERN')

    # Validate patterns by trying to compile them
    try:
        file_regex = re.compile(file_ignore_pattern, re.IGNORECASE)
        message_regex = re.compile(message_cleanup_pattern, re.IGNORECASE)
    except re.error as e:
        raise ValueError(f"Invalid regular expression pattern: {e}")

    return file_regex, message_regex  # Now returning compiled regex objects


def split_long_text(text, max_length=4000):
    """
    Split a long text into two parts, ensuring each part is less than the specified maximum length.
    The second part will be `None` if the text is shorter than the maximum length.

    Parameters:
    text (str): The input text to be split.
    max_length (int): The maximum length of the first part (default is 4000 characters).

    Returns:
    tuple: A tuple containing the two parts of the split text. The second part will be `None` if the text is shorter than the maximum length.
    """
    if len(text) <= max_length:
        return text, None

    # Find the index of the nearest two consecutive newlines starting from max_length
    split_index = text.rfind("\n\n", 0, max_length)
    if split_index == -1:
        # If no two newlines are found, split at the maximum length
        split_index = max_length

    part1 = text[:split_index].strip()
    part2 = text[split_index + 2:].strip()

    return part1, None if not part2 else part2


def is_voice(attrs):
    """
    Checks if a message's attributes include a voice note indicator.

    This function inspects the provided attributes (`attrs`) to determine if the content
    is a voice message. It searches for instances of `DocumentAttributeAudio` with the
    `voice` property set to `True`.

    Parameters:
    -----------
    attrs : list
        A list of attributes associated with a Telegram message, expected to contain instances of `DocumentAttributeAudio`.

    Returns:
    --------
    bool
        Returns `True` if the attributes include a voice note, otherwise returns `False`.

    Usage:
    ------
    ```python
    is_voice(attrs)
    ```
    """
    resolved = [attr.voice for attr in attrs if isinstance(attr, DocumentAttributeAudio)]
    if resolved:
        return resolved[0]
    else:
        return False


def get_file_name(attrs):
    """
    Retrieves the file name from message attributes or assigns a default based on content type.

    This function searches for the file name within message attributes (`attrs`). If a filename is not specified
    and the message is a voice note, it defaults to "voice.oga". If neither is found, it defaults to "No title.oga".

    Parameters:
    -----------
    attrs : list
        A list of attributes associated with a Telegram message, expected to contain instances of `DocumentAttributeFilename`.

    Returns:
    --------
    str
        Returns the file name as a string or a default name based on content type.

    Usage:
    ------
    ```python
    get_file_name(attrs)
    ```
    """
    fnames = [attr.file_name for attr in attrs if isinstance(attr, DocumentAttributeFilename)]
    if fnames:
        return fnames[0]
    elif is_voice(attrs):
        return "voice.oga"
    else:
        return "No title.oga"


def persist_offset(base_path: str, offset: int):
    """
    Saves the offset value to a file for tracking message processing progress.

    This function writes an offset to a designated file (`OFFSET_FILE`) at the specified `base_path`.
    The offset represents a point in message processing, allowing subsequent operations to continue
    from where they left off.

    Parameters:
    -----------
    base_path : str
        The directory path where the offset file is located.

    offset : int
        The offset value to store, typically representing the last processed message ID.

    Returns:
    --------
    int
        Returns the saved offset if successful; otherwise, returns 0 if an error occurs.

    Usage:
    ------
    ```python
    persist_offset('/path/to/directory', 12345)
    ```
    """
    try:
        with open(os.path.join(base_path, OFFSET_FILE), 'w') as file:
            file.write(str(offset))
            return offset
    except (ValueError, FileNotFoundError):
        return 0


def load_offset(base_path: str):
    """
    Loads the last saved offset from a file to resume message processing.

    This function reads an offset value from a file at the specified `base_path`.
    The offset represents the last processed message ID, allowing processing to
    resume from that point.

    Parameters:
    -----------
    base_path : str
        The directory path where the offset file is located.

    Returns:
    --------
    int
        Returns the loaded offset value if successful; otherwise, returns 0 if an error occurs.

    Usage:
    ------
    ```python
    load_offset('/path/to/directory')
    ```
    """
    try:
        with open(os.path.join(base_path, OFFSET_FILE), 'r') as file:
            number_str = file.read().strip()
            return int(number_str)
    except (ValueError, FileNotFoundError):
        return 0


OFFSET_FILE = "offset.txt"

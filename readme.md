# Telegram-duply

**Telegram-duply** is a Python-based tool designed for duplicating messages from one Telegram group or topic to another. Using the `Telethon` library, it facilitates the automated copying of text, media, and documents between groups, allowing for efficient management of message duplication tasks. The tool supports various message types, provides error handling, and tracks offsets for reliable and continuous message transfer.


## Features

- **Message Duplication**: Seamlessly clones messages between Telegram groups and topics, maintaining their original structure.
- **Multi-Media Support**: Handles multiple media types, including images, videos, voice notes, and documents. Poll messages are ignored.
- **Automatic Error Handling**: Retries operations on errors and incorporates automatic message splitting for messages that exceed Telegram’s length limits.
- **Offset Tracking**: Saves and loads offsets to ensure smooth continuation of the cloning process.
- **Environment-Based Configuration**: Loads Telegram API credentials and configurable settings from a `.env` file for easy setup and maintenance.
- **Docker Support**: This project can be packed into a Docker container for easy deployment.


## Requirements

To run telegram-duply, ensure you have the following:

- **Python 3.10+**
- **Required Packages**:
  - [Telethon](https://pypi.org/project/Telethon/): Async library for working with the Telegram API.
  - [loguru](https://pypi.org/project/loguru/): For logging operations and error tracking.
  - [python-dotenv](https://pypi.org/project/python-dotenv/): For managing environment variables via a `.env` file.

    
## Configuration

1. **Set Up a `.env` File**: In the root directory, create a `.env` file to store your Telegram API credentials, patterns, and link pairs. Below is an example `.env` file:

   ```.env
   # Use your own values from my.telegram.org
   API_HASH='<hash>'
   API_ID=12345

   # Optional: Use Python regex to match files you want to ignore (e.g., teaser/promo files)
   FILE_IGNORE_PATTERN=""

   # Optional: Use regex to clean up parts of the message text (e.g., promo parts)
   MESSAGE_CLEANUP_PATTERN=""

   # List of source channels/topics (comma-separated)
   FROM=""

   # List of destination channels/topics (comma-separated)
   TO=""
   ```

2. **Environment Variables**: You can set these values directly as environment variables if preferred. The environment variables will take precedence over the `.env` file values.

3. **Links Pairing**: 
   - The `FROM` and `TO` fields in the `.env` file must contain an equal number of links, as they represent the source and destination pairs. For example:
   
     - `FROM`: `channel1_topic1, channel2_topic2`
     - `TO`: `channel1_destination, channel2_destination`

   - The links in `FROM` and `TO` will be handled in pairs, where the first source link (`FROM[0]`) will be copied to the first destination link (`TO[0]`), and so on.

4. **Optional Regular Expressions**:
   - `FILE_IGNORE_PATTERN`: Defines the pattern used to ignore specific files (e.g., promotional files).
   - `MESSAGE_CLEANUP_PATTERN`: Defines the pattern used to clean up unwanted parts from message text (e.g., promo text).


## Usage

### Local Mode

To run the project locally, you can execute the `main.py` file directly:

1. Ensure that you have all the required dependencies installed (see **Requirements** section).
2. Set up your `.env` file with your Telegram API credentials and other configurations.
3. Run the script using Python:

   ```bash
   python main.py
   ```

### Docker Mode

You can also run the project in Docker by building a Docker image. Follow these steps:

1. **Build the Docker Image**:

   In the root directory of the project, run the following command to build the Docker image:

   ```bash
   docker build -t duply .
   ```

2. **Optional**: Save the Docker image as a tarball file (for backup or sharing purposes):

   ```bash
   docker save -o duply.tar duply
   ```

3. **Run the Docker Container**:

   After building the image, you can run the container using the following command:

   ```bash
   docker run --env-file .env duply
   ```

   This will run the project inside a Docker container using the environment variables from your `.env` file.

   **Important**: It's highly recommended to mount the `/app/data` directory from the Docker container to your host system to persist data such as downloaded files and offsets. You can do this by adding a `-v` option to the `docker run` command:

   ```bash
   docker run --env-file .env -v /path/on/host:/app/data duply
   ```

   Replace `/path/on/host` with the path on your host machine where you'd like to store the data.
   
   You can also pass additional Docker flags or mount other volumes if needed, depending on your specific use case.

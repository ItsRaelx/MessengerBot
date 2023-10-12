# Messenger Bot with FastAPI

This project showcases a Messenger bot built using FastAPI, integrated with MongoDB for data storage. It can send broadcast messages, conduct polls, and process postback data from users.

## Requirements

- `fastapi`
- `uvicorn`
- `motor`
- `pymessenger`
- `python-decouple`
- A valid Facebook Messenger bot token.
- A MongoDB instance.

## Setup & Configuration

1. Clone this repository.

2. Install the required packages:

```bash
pip install -r requirements.txt
```

### Set up environment variables:
**`ACCESS_TOKEN`**: Your Facebook Messenger bot access token.
**`VERIFY_TOKEN`**: Your verification token used for the Facebook Webhooks integration.
**`MONGODB_URI`**: Your MongoDB connection URI.
For local development, you can create a .env file with the above variables and their respective values. The python-decouple library will read from this file.

### Run the FastAPI application:

```bash
python3 main.py
```

## Features

1. **Webhook Validation**: Validates incoming requests from Facebook Messenger.
2. **Message Processing**: Processes messages from users. If the message is from an admin (specified via `ADMIN_ID`), it can also trigger broadcasts.
3. **Broadcasting**: Send out messages or polls to all verified users in the database.
4. **Polling System**: Users can respond to polls, and their responses will be recorded in MongoDB.
5. **Database Interaction**: Uses asynchronous MongoDB operations for CRUD operations.

## Endpoints

- `GET /`: Health check.
- `POST /messaging`: Endpoint for receiving and processing messages from Facebook Messenger.
- `GET /messaging`: Endpoint for validating the Facebook Messenger webhook integration.

## Usage

1. **Broadcasting a Message**: Admin sends a message starting with `!`, and the bot will broadcast the following text to all verified users.

2. **Conducting a Poll**: Admin sends a message starting with `?`, followed by the question and the answer choices separated by `;`. Example: `?Do you like ice cream?;Yes;No`

3. **Processing Postback Data**: If a user interacts with the bot's postback (e.g., answering a poll), the bot will process the postback data and store or update information in the database as necessary.

## Notes

- Ensure your Facebook Messenger bot and webhook are correctly set up and integrated.
- Before deploying, always ensure your environment variables are securely configured.
- This is a basic implementation. For more advanced features or security measures, consider enhancing the codebase further.

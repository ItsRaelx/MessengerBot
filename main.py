import uuid
from datetime import datetime, timedelta

import motor.motor_asyncio
import uvicorn
from decouple import config
from fastapi import FastAPI, Request, Depends, HTTPException, Query
from fastapi.responses import PlainTextResponse
from pymessenger.bot import Bot

app = FastAPI()

ACCESS_TOKEN = config('ACCESS_TOKEN')
VERIFY_TOKEN = config('VERIFY_TOKEN')
MONGODB_URI = config('MONGODB_URI')
ADMIN_ID = "6423084651147559"

bot = Bot(ACCESS_TOKEN)

# Asynchronous connection using motor
client = motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URI)
db = client.messenger
questions = db.questions
users = db.users


async def get_all_mess_values():
    return [user["mess"] async for user in users.find({"verified": True})]


async def process_postback(payload, sender_id):
    # Check if the payload is WELCOME_MESSAGE
    if payload == "WELCOME_MESSAGE":
        # Check if user already exists in the database
        existing_user = await users.find_one({"mess": int(sender_id)})
        if existing_user:
            return "Jesteś już zarejestrowany w bazie danych."

        user_data = {
            "mess": int(sender_id),
            "lab": 1,
            "cwi": 1,
            "verified": False
        }
        await users.insert_one(user_data)
        return f"Twoje ID użytkownika to {sender_id}. Po weryfikacji administratora będziesz otrzymywać ogłoszenia i ankiety."
    elif "." not in payload:
        # Handle this error appropriately; for now, just returning a message.
        return sender_id, "Invalid payload format."

    question_id, answer_index = payload.split(".")
    answer_index = int(answer_index)

    question = await questions.find_one({"_id": question_id})

    if not question or not (0 <= answer_index < len(question['answers'])):
        return sender_id, "Invalid question."

    if question['ends'] < datetime.now():
        return f"Ankieta ID: {question_id} została zakończona."

    has_answered = any(sender_id in answer['votes'] for answer in question['answers'].values())
    if has_answered:
        return f"User {sender_id} has already answered question {question_id}. Skipping update."

    update_expression = {"$push": {f"answers.{answer_index}.votes": sender_id}}
    await questions.update_one({"_id": question_id}, update_expression)

    return "Dziękujemy za twój głos."


async def process_text_message(text, sender_id):
    if text.startswith('!') and sender_id == ADMIN_ID:
        message = text[1:]
        await broadcast_message(message)
    elif text.startswith('?') and sender_id == ADMIN_ID:
        await broadcast_poll(text[1:])
    else:
        return "Bot aktualnie nie przyjmuje wiadomości. Skontaktuj się z administratorem: https://m.me/itsraelx"


async def broadcast_message(message):
    for user in await get_all_mess_values():
        bot.send_text_message(user, message)


async def broadcast_poll(poll_data):
    question_data = poll_data.split(';')
    question = question_data[0]
    answers = question_data[1:]

    buttons = []
    answer_dict = {}
    random_id = uuid.uuid4().hex

    for i, title in enumerate(answers):
        answer_dict[str(i)] = {
            "name": title,
            "votes": []
        }
        buttons.append({
            "type": "postback",
            "title": title,
            "payload": f"{random_id}.{i}"
        })

    for user in await get_all_mess_values():
        bot.send_button_message(user, question, buttons)

    await questions.insert_one(
        {
            "_id": random_id,
            "question": question,
            "answers": answer_dict,
            "date": datetime.now(),
            "ends": datetime.now() + timedelta(days=1)
        }
    )


async def get_recipient_and_message(request: Request):
    output = await request.json()
    for event in output['entry']:
        messaging = event['messaging']
        for message in messaging:
            sender_id = message['sender']['id']
            if 'postback' in message:
                payload = message['postback']['payload']
                return sender_id, await process_postback(payload, sender_id)
            elif 'message' in message:
                if 'text' in message['message']:
                    text = message['message']['text']
                    return sender_id, await process_text_message(text, sender_id)
                else:
                    # Handle non-text messages here
                    return "OK"


@app.get("/")
def health_check():
    return {"message": "OK"}


@app.post("/messaging")
async def receive_message(data: tuple = Depends(get_recipient_and_message)):
    recipient_id, response = data
    bot.send_text_message(recipient_id, response)
    return {"message": "Message Processed"}


@app.get("/messaging")
def validate_token(mode: str = Query(..., alias="hub.mode"),
                   token: str = Query(..., alias="hub.verify_token"),
                   challenge: str = Query(..., alias="hub.challenge")):
    if mode == "subscribe" and token == VERIFY_TOKEN:
        return PlainTextResponse(challenge)
    raise HTTPException(status_code=403, detail="Forbidden")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

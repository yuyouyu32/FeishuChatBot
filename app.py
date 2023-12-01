import asyncio
import logging
import requests
from api import MessageApiClient
from event import MessageReceiveEvent, UrlVerificationEvent, EventManager, AddGoupEvent
from flask import Flask, jsonify
import time

from config import APP_ID, APP_SECRET, VERIFICATION_TOKEN, ENCRYPT_KEY, LARK_HOST, BotOpenID
from event_cache import event_cache, cache_lock
from utils import ActreeDirty

app = Flask(__name__)

# init service
message_api_client = MessageApiClient(APP_ID, APP_SECRET, LARK_HOST)
event_manager = EventManager()

@event_manager.register("url_verification")
def request_url_verify_handler(req_data: UrlVerificationEvent):
    # url verification, just need return challenge
    if req_data.event.token != VERIFICATION_TOKEN:
        raise Exception("VERIFICATION_TOKEN is invalid")
    return jsonify({"challenge": req_data.event.challenge})


@event_manager.register("im.message.receive_v1")
def message_receive_event_handler(req_data: MessageReceiveEvent):
    event_id = req_data.header.event_id
    with cache_lock:
        if event_id in event_cache: 
            print(f"***Event {event_id} has been processed***")
            return jsonify()
        event_cache[event_id] = {
            "status": "processing",
            "timestamp": time.time()
        }
    sender_id = req_data.event.sender.sender_id
    message = req_data.event.message
    if message.message_type != "text":
        logging.warn("Other types of messages have not been processed yet")
        return jsonify()
    
    text_content, chat_type, message_id = message.content, message.chat_type, message.message_id
    open_id = sender_id.open_id
    open_id_set = set()
    name_at_map = {}
    # replace @_user_1 to xxx
    for mention in req_data.mentions:
        open_id_set.add(mention['id']['open_id'])
        name_at_map[mention['key']] = mention['name']
    for mention in name_at_map:
        text_content = text_content.replace(mention, name_at_map[mention])
    # if message in group and bot not be @, return
    if chat_type == 'group' and BotOpenID not in open_id_set and '@_all' not in text_content:
        return jsonify()
    # proactivate send story
    if text_content.count('*') > 0:
        if chat_type == 'p2p':
            asyncio.run(message_api_client.proactivate_send_story('open_id', open_id, open_id, text_content, message_id))
        elif chat_type == 'group':
            chat_id = message.chat_id
            asyncio.run(message_api_client.proactivate_send_story('chat_id', chat_id, open_id, text_content, message_id))
        else:
            logging.warn("Other types of chat_type have not been processed yet")
        return jsonify()
    # chat
    for item in ActreeDirty.find_matches_as_strings(text_content):
        text_content = text_content.replace(item, '*' * len(item))
    if chat_type == 'p2p':
        asyncio.run(message_api_client.reply_message_p2p(open_id, text_content, message_id))
    elif chat_type == 'group':
            chat_id = message.chat_id
            asyncio.run(message_api_client.reply_message_group(chat_id, open_id, text_content, message_id))
    else:
        logging.warn("Other types of chat_type have not been processed yet")
    with cache_lock:
        event_cache[event_id]["status"] = "processed"
    return jsonify()

@event_manager.register("im.chat.member.bot.added_v1")
def bot_added_event_handler(req_data: AddGoupEvent):
    event_id = req_data.header.event_id
    with cache_lock:
        if event_id in event_cache: 
            print(f"***Event {event_id} has been processed***")
            return jsonify()
        event_cache[event_id] = {
            "status": "processing",
            "timestamp": time.time()
        }
    chat_id = req_data.event.chat_id
    asyncio.run(message_api_client.send_message_group(chat_id, event_id))
    with cache_lock:
        event_cache[event_id]["status"] = "processed"
    return jsonify()

@app.errorhandler
def msg_error_handler(ex):
    logging.error(ex)
    response = jsonify(message=str(ex))
    response.status_code = (
        ex.response.status_code if isinstance(ex, requests.HTTPError) else 500
    )
    return response


@app.route("/", methods=["POST"])
def callback_event_handler():
    # init callback instance and handle
    event_handler, event = event_manager.get_handler_with_event(VERIFICATION_TOKEN, ENCRYPT_KEY)

    return event_handler(event)
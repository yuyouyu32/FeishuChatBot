#! /usr/bin/env python3.8
import os
import logging
import requests
import websockets
import json
import re
from config import ModelURL, BotName
import uuid
import datetime
import time

APP_ID = os.getenv("APP_ID")
APP_SECRET = os.getenv("APP_SECRET")

# const
TENANT_ACCESS_TOKEN_URI = "/open-apis/auth/v3/tenant_access_token/internal"
MESSAGE_URI = "/open-apis/im/v1/messages"

class MessageApiClient(object):
    def __init__(self, app_id, app_secret, lark_host):
        self._app_id = app_id
        self._app_secret = app_secret
        self._lark_host = lark_host
        self._tenant_access_token = ""

    @property
    def tenant_access_token(self):
        return self._tenant_access_token
    
    @staticmethod
    def cut_sent(para: str):
        para = para.strip('\'"')
        para = re.sub('([。！？\?])([^”’])', r"\1\n\2", para)
        para = re.sub('(\.{6})([^”’])', r"\1\n\2", para)
        para = re.sub('(\…{2})([^”’])', r"\1\n\2", para)
        para = re.sub('([。！？\?][”’])([^，。！？\?])', r'\1\n\2', para)
        para = para.rstrip()
        return para.split("\n")
        
    async def get_rsp_from_query(self, open_id, query, name, action_type="chat"):
        async with websockets.connect(ModelURL) as websocket:
            # Creating the message to be sent
            message = {
            "session": {
                "user_id": open_id,
                "prototype_id": BotName,
                "user_name": name,
                "agent_id": open_id + "_" + BotName,
                "pair_id": open_id + "_" + BotName,

            },
            "config": {
                "use_knowledge": True,
                "use_memory": True,
                "use_chat_history": True
                },
            "observation": {
                "source": name,
                "query": query,
                "time": str(datetime.datetime.now()),
                },
            "action_type": action_type,
            }
            # Converting the message to a JSON string
            message_str = json.dumps(message, ensure_ascii=False)
            print("\nSEND to LLMs Model {}".format(message_str))
            # Sending the message to the server
            await websocket.send(message_str)

            # Receiving the response from the server
            response = await websocket.recv()
            response = json.loads(response)
            content, status = response["content"], response["status"]
            print("\nRECEIVED from LLMs Model {}".format(content))
            return content, json.dumps(status, ensure_ascii=False, indent=4)
        
    async def get_rsp_from_query_AFK(self, open_id, query, name, action_type="chat"):
        async with websockets.connect(ModelURL) as websocket:
            # Creating the message to be sent
            if BotName == 'jeriffli':
                message = {
                    'gender': 'female',
                    'user_id': open_id,
                    "instruction": query
                }
            elif BotName == 'kuma':
                message = {
                    'gender': 'male',
                    'user_id': open_id,
                    "instruction": query
                }
            # Converting the message to a JSON string
            message_str = json.dumps(message, ensure_ascii=False)
            print("\nSEND to LLMs Model {}".format(message_str))
            # Sending the message to the server
            await websocket.send(message_str)

            # Receiving the response from the server
            response = await websocket.recv()
            print("\nRECEIVED from LLMs Model {}".format(response))
            return response, None

    async def send_text_with_open_id(self, open_id, content, message_id):
        query = json.loads(content)["text"]
        name = self._get_user_info("open_id", open_id)['user']['name']
        rsp, status = await self.get_rsp_from_query(open_id, query, name)
        # rsp = f"Hello, I am a chatbot. I am still under development. Please come back later. {query}"   
        sentenses = self.cut_sent(rsp)
        for index, sentence in enumerate(sentenses):
            if sentence == "":
                continue
            time.sleep(len(sentence) / 10)
            rsp_content = json.dumps({"text": sentence})
            self.send("open_id", open_id, "text", rsp_content, f"{message_id}_{index}")

    async def send_text_with_chat_id(self, chat_id, open_id, content, message_id):
        query = json.loads(content)["text"]
        name = self._get_user_info("open_id", open_id)['user']['name']
        rsp, status = await self.get_rsp_from_query(open_id, query, name)
        # rsp = f"Hello, I am a chatbot. I am still under development. Please come back later. {query}"
        sentences = self.cut_sent(rsp)
        for index, sentence in enumerate(sentences):
            if sentence == "":
                continue
            time.sleep(len(sentence) / 10)
            rsp_content = json.dumps({"text": f"<at user_id=\"{open_id}\"></at> \n" + sentence})
            self.send("chat_id", chat_id, "text", rsp_content, f"{message_id}_{index}")
        
    async def reply_message_p2p(self, open_id, content, message_id):
        query = json.loads(content)["text"]
        name = self._get_user_info("open_id", open_id)['user']['name']
        rsp, status = await self.get_rsp_from_query(open_id, query, name)
        # rsp = f"Hello, I am a chatbot. I am still under development. Please come back later. {query}"
        sentences = self.cut_sent(rsp)
        for index, sentence in enumerate(sentences):
            if sentence == "":
                continue
            if index == 0:
                rsp_content = json.dumps({"text": sentence})
                self.reply("text", rsp_content, message_id, f"{message_id}_{index}")
            else:
                time.sleep(len(sentence) / 10)
                rsp_content = json.dumps({"text": sentence})
                self.send("open_id", open_id, "text", rsp_content, f"{message_id}_{index}")

    async def proactivate_send_story(self, receive_id_type, receive_id, open_id, content, message_id):
        name = self._get_user_info("open_id", open_id)['user']['name']
        if content.count('*') == 1:
            await self.get_rsp_from_query(receive_id, "", name, action_type='step')
        else:
            await self.get_rsp_from_query(receive_id, "", name, action_type='new_scenario')
        rsp, status = await self.get_rsp_from_query(receive_id, "", name, action_type='ask')
        # rsp = f"Hello, I am a chatbot. I am still under development. Please come back later. {query}"
        sentences = self.cut_sent(rsp)
        for index, sentence in enumerate(sentences):
            if sentence == "":
                continue
            if index == 0:
                sentence = status + '\n' + sentence
            time.sleep(len(sentence) / 10)
            rsp_content = json.dumps({"text": sentence}) 
            self.send(receive_id_type, receive_id, "text", rsp_content, f"{message_id}_{index}")

    async def reply_message_group(self, chat_id, open_id, content, message_id):
        query = json.loads(content)["text"]
        name = self._get_user_info("open_id", open_id)['user']['name']
        rsp, status = await self.get_rsp_from_query(chat_id, query, name)
        # rsp = f"Hello, I am a chatbot. I am still under development. Please come back later. {query}"
        sentences = self.cut_sent(rsp)
        for index, sentence in enumerate(sentences):
            if sentence == "":
                continue
            if index == 0:
                rsp_content = json.dumps({"text": f"<at user_id=\"{open_id}\"></at> \n" + sentence})
                self.reply("text", rsp_content, message_id, f"{message_id}_{index}")
            else:
                rsp_content = json.dumps({sentence})
                self.send("chat_id", chat_id, "text", rsp_content, f"{message_id}_{index}")
       
    
    async def send_message_group(self, chat_id, event_id):
        group_info = self._get_group_info(chat_id)
        group_name, group_description = group_info['name'], group_info['description']
        rsp, status = await self.get_rsp_from_query(chat_id, f"你新加入了一个群，群的信息如下：群名称 {group_name}\n 群描述 {group_description}\n 请你给大家做一个自我介绍，打一个招呼。", name=group_name)
        sentences = self.cut_sent(rsp)
        for index, sentence in enumerate(sentences):
            if sentence == "":
                continue
            if index == 0:
                rsp_content = json.dumps({"text": f"<at user_id=\"all\"></at> " + sentence})
                self.send("chat_id", chat_id, "text", rsp_content, f"{event_id}_{index}")
            else:
                rsp_content = json.dumps({"text": sentence})
                self.send("chat_id", chat_id, "text", rsp_content, f"{event_id}_{index}")

    def send(self, receive_id_type, receive_id, msg_type, content, message_id):
        # send message to user, implemented based on Feishu open api capability. doc link: https://open.feishu.cn/document/uAjLw4CM/ukTMukTMukTM/reference/im-v1/message/create
        self._authorize_tenant_access_token()
        url = "{}{}?receive_id_type={}".format(
            self._lark_host, MESSAGE_URI, receive_id_type
        )
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + self.tenant_access_token,
        }
        req_body = {
            "receive_id": receive_id,
            "content": content,
            "msg_type": msg_type,
            "uuid": str(uuid.uuid5(uuid.NAMESPACE_OID, message_id))
        }
        resp = requests.post(url=url, headers=headers, json=req_body)
        MessageApiClient._check_error_response(resp)

    def reply(self, msg_type, content, message_id, message_idx):
        # reply message to user, implemented based on Feishu open api capability. doc link: https://open.feishu.cn/document/server-docs/im-v1/message/reply
        self._authorize_tenant_access_token()
        url = "{}{}/{}/reply".format(
            self._lark_host, MESSAGE_URI, message_id
        )
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + self.tenant_access_token,
        }
        req_body = {
            "content": content,
            "msg_type": msg_type,
            "uuid": str(uuid.uuid5(uuid.NAMESPACE_OID, message_id))
        }
        resp = requests.post(url=url, headers=headers, json=req_body)
        MessageApiClient._check_error_response(resp)

    def _get_user_info(self, user_id_type, id):
        # get user information by user_id, implemented based on Feishu open api capability. doc link:https://open.feishu.cn/document/server-docs/contact-v3/user/get?appId=cli_a58bccc50c30d00c
        self._authorize_tenant_access_token()
        url = "{}{}".format(self._lark_host, "/open-apis/contact/v3/users/" + id)
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + self.tenant_access_token,
        }
        print(id, headers)
        params = {"user_id_type": user_id_type}
        resp = requests.get(url=url, headers=headers, params=params)
        MessageApiClient._check_error_response(resp)
        return resp.json()['data']
    
    def _get_group_info(self, chat_id):
    # get group information by chat_id, implemented based on Feishu open api capability. doc link:https://open.feishu.cn/document/server-docs/group/chat/get-2?appId=cli_a58bccc50c30d00c
        self._authorize_tenant_access_token()
        url = "{}{}".format(self._lark_host, "/open-apis/im/v1/chats/" + chat_id)
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + self.tenant_access_token,
        } 
        resp = requests.get(url=url, headers=headers)
        MessageApiClient._check_error_response(resp) 
        return resp.json()['data']

    def _authorize_tenant_access_token(self):
        # get tenant_access_token and set, implemented based on Feishu open api capability. doc link: https://open.feishu.cn/document/ukTMukTMukTM/ukDNz4SO0MjL5QzM/auth-v3/auth/tenant_access_token_internal
        url = "{}{}".format(self._lark_host, TENANT_ACCESS_TOKEN_URI)
        req_body = {"app_id": self._app_id, "app_secret": self._app_secret}
        response = requests.post(url, req_body)
        MessageApiClient._check_error_response(response)
        self._tenant_access_token = response.json().get("tenant_access_token")

    @staticmethod
    def _check_error_response(resp):
        # check if the response contains error information
        if resp.status_code != 200:
            resp.raise_for_status()
        response_dict = resp.json()
        code = response_dict.get("code", -1)
        if code != 0:
            logging.error(response_dict)
            raise LarkException(code=code, msg=response_dict.get("msg"))


class LarkException(Exception):
    def __init__(self, code=0, msg=None):
        self.code = code
        self.msg = msg

    def __str__(self) -> str:
        return "{}:{}".format(self.code, self.msg)

    __repr__ = __str__

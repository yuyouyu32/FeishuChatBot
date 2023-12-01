# bot_config.py
import yaml
import config

def load_bot_config(bot_name):
    yaml_file = f"./bots_yaml/{bot_name}.yaml"
    with open(yaml_file, "r") as file:
        selected_bot = yaml.safe_load(file)

    config.APP_ID = selected_bot["APP_ID"]
    config.APP_SECRET = selected_bot["APP_SECRET"]
    config.VERIFICATION_TOKEN = selected_bot["VERIFICATION_TOKEN"]
    config.ENCRYPT_KEY = selected_bot["ENCRYPT_KEY"]
    config.LARK_HOST = selected_bot["LARK_HOST"]
    config.BotOpenID = selected_bot["BotOpenID"]
    config.PORT = selected_bot["PORT"]
    config.BotName = selected_bot["BotName"]
#!/usr/bin/env python3.8
from event_cache import *
import argparse
from bot_config import load_bot_config



if __name__ == "__main__":
    # init()
    parser = argparse.ArgumentParser(description="Start a specific bot")
    parser.add_argument("bot_name", help="The name of the bot to start")
    args = parser.parse_args()
    # Load bot configuration and set global variables
    load_bot_config(args.bot_name)
    from config import PORT
    from app import *
    cleanup_thread.start()
    app.run(host="0.0.0.0", port=PORT, debug=False)

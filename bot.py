#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Authors:      MaanuelMM, CoreDumped-ETSISI
# Credits:      python-telegram-bot, CoreDumped-ETSISI, Eldinnie
# Created:      2019/02/14
# Last update:  2019/02/18

import telegram
import logger
import datetime

from data_loader import DataLoader
from logger import get_logger
from telegram.ext import Updater, CommandHandler
from telegram.error import TelegramError, Unauthorized, BadRequest, TimedOut, ChatMigrated, NetworkError


def error_callback(bot, update, error):
    try:
        raise error
    except Unauthorized:
        logger.exception("Remove update.message.chat_id from conversation list.")
    except BadRequest as e:
        if update.message.chat_id < 0 and e == "Message can't be deleted.":  # This pre-check is necessary if we do not want to spam the logs with "BadRequest: Message can't be deleted" as this bot has no power to remove user messages in private chats.
            logger.exception("Handle malformed requests - read more below!")
    except TimedOut:
        logger.exception("Handle slow connection problems.")
    except NetworkError:
        logger.exception("Handle other connection problems.")
    except ChatMigrated as e:
        logger.exception("The chat_id of a group has changed, use " + e.new_chat_id + " instead.")
    except TelegramError:
        logger.exception("There is some error with Telegram.")

def load_settings():
    global settings
    global last_function_calls
    settings = DataLoader()
    last_function_calls = {}

def log_message(update):
    try:
        username = update.message.from_user.username
    except:
        username = "Unknown"
    try:
        text = update.message.text
    except:
        text = "something"
    logger.info("Received: \"" + text + "\" from " + username + " [Chat ID: " + str(update.message.chat_id) + "].")

def hola_command(bot, update):
    update.effective_message.reply_text(settings.hola_command)


if __name__ == "__main__":
    # Enable logging
    logger = get_logger("bot_starter", True)
    logger.info("Starting...")
    try:
        # Load data and settings
        load_settings()
        # Set up the Updater
        logger.info("Connecting to the Telegram API...")
        updater = Updater(settings.telegram_token)
        # Add handlers
        dispatcher = updater.dispatcher
        dispatcher.add_handler(CommandHandler('hola', hola_command))
        dispatcher.add_error_handler(error_callback)
        # Start the webhook
        updater.start_webhook(listen="0.0.0.0", port=int(settings.server_port), url_path=settings.telegram_token)
        updater.bot.setWebhook("{}{}".format(settings.server_url, settings.server_port))
    except:
        # Shut down
        logger.info("ERROR making connection to the Telegram API. Shutting down...")
        quit()
    else:
        # Successful start
        logger.info("Listening...")
        updater.idle()
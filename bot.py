#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Authors:      CoreDumped-ETSISI, MaanuelMM
# Credits:      CoreDumped-ETSISI, python-telegram-bot, MaanuelMM
# Created:      2019/02/14
# Last update:  2019/02/16

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
        logger.exception("remove update.message.chat_id from conversation list")
    except BadRequest as e:
        if update.message.chat_id < 0 and e == "Message can't be deleted":  # This pre-check is necessary if we do not want to spam the logs with "BadRequest: Message can't be deleted" as this bot has no power to remove user messages in private chats.
            logger.exception("handle malformed requests - read more below!")
    except TimedOut:
        logger.exception("handle slow connection problems")
    except NetworkError:
        logger.exception("handle other connection problems")
    except ChatMigrated as e:
        logger.exception("the chat_id of a group has changed, use " + e.new_chat_id + " instead")
    except TelegramError:
        logger.exception("There is some error with Telegram")

def load_settings():
    global settings
    global last_function_calls
    settings = DataLoader()
    last_function_calls = {}

def is_call_available(name, chat_id, cooldown):
    global last_function_calls
    now = datetime.datetime.now()
    cooldown_time = datetime.datetime.now() - datetime.timedelta(minutes=cooldown)
    if name in last_function_calls.keys():
        if chat_id in last_function_calls[name].keys():
            if last_function_calls[name][chat_id] > cooldown_time:
                last_function_calls[name][chat_id] = now
                return False
            else:
                last_function_calls[name][chat_id] = now
                return True
        else:
            last_function_calls[name][chat_id] = now
            return True
    else:
        last_function_calls[name] = {chat_id: now}
        return True

def log_message(update):
    try:
        username = update.message.from_user.username
    except:
        username = "desconocido"
    try:
        text = update.message.text
    except:
        text = "algo"
    logger.info("He recibido: \"" + text + "\" de " + username + " [ID: " + str(update.message.chat_id) + "]")

def hola_command(bot, update):
    if is_call_available("hola_mundo", update.message.chat_id, 180):
        log_message(update)
        bot.sendMessage(update.message.chat_id, settings.hola_mundo, parse_mode=telegram.ParseMode.HTML)

if __name__ == "__main__":
    print("Bollín Tenorio Bot: Starting...")
    
    logger = get_logger("bot_starter", True)
    load_settings()

    try:
        logger.info("Realizando conexión con la API de Telegram.")
        updater = Updater(settings.telegram_token)
        dispatcher = updater.dispatcher
        dispatcher.add_handler(CommandHandler('hola', hola_command))
        dispatcher.add_error_handler(error_callback)
    except:
        logger.info("Error al realizar la conexión con la API de Telegram.")
        quit()
    updater.start_polling()
    logger.info("Bollín Tenorio Bot: Listening...")
    updater.idle()
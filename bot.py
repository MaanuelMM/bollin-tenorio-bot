#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Authors:      MaanuelMM
# Credits:      eternnoir, atlink, CoreDumped-ETSISI, Eldinnie
# Created:      2019/02/14
# Last update:  2019/02/18

import os
import telebot
import datetime
import logger

from flask import Flask, request
from logger import get_logger


# Enable logger
logger = get_logger("bot_starter", True)
logger.info("Starting...")
# Get Congif Vars
TOKEN = os.environ.get('TOKEN')
URL = os.environ.get('URL')
PORT = os.environ.get('PORT', 5000)
try:
    # Telegram API connection
    logger.info("Connecting to the Telegram API...")
    bot = telebot.TeleBot(token=TOKEN)
    logger.info("Successfully connected to the Telegram API.")
except:
    logger.info("Error connecting to the Telegram API. Shutting down...")
    quit()
else:
    # Start Flask app
    server = Flask(__name__)


@bot.message_handler(commands=['start']) # welcome message handler
def send_welcome(message):
    bot.reply_to(message, "Hola a todos, mis papirrines <3")

@bot.message_handler(commands=['help']) # help message handler
def send_help(message):
    bot.reply_to(message, "Lo siento si funciono mal o estoy muy limitado en funciones, pero estoy trabajando para mejorar día a día :)")


@server.route('/' + TOKEN, methods=['POST'])
def getMessage():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "!", 200

@server.route("/")
def webhook():
    bot.remove_webhook()
    bot.set_webhook(url=URL+TOKEN)
    return "!", 200


if __name__ == "__main__":
    try:
        # run server
        logger.info("Starting running server...")
        server.run(host="0.0.0.0", port=int(PORT))
        logger.info("Listening...")
    except:
        logger.info("Error starting running server. Shutting down...")
        quit()
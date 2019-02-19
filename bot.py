#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Authors:      MaanuelMM
# Credits:      eternnoir, atlink, CoreDumped-ETSISI, Eldinnie
# Created:      2019/02/14
# Last update:  2019/02/19

import os
import telebot
import logger

from flask import Flask, request
from logger import get_logger


# Enable logger
logger = get_logger("bot_starter", True)
logger.info("Starting bot...")
# Get Config Vars
logger.info("Getting Config Vars...")
TOKEN = os.environ.get('TOKEN')
URL = os.environ.get('URL')
PORT = os.environ.get('PORT', 5000)
logger.info("Successfully gotten Config Vars.")
# Telegram API connection
logger.info("Connecting to the Telegram API...")
bot = telebot.TeleBot(token=TOKEN)
logger.info("Successfully connected to the Telegram API.")
# Start Flask server app
server = Flask(__name__)


def log_message(message, chat_id):
    logger.info("Received: \"" + message.text + "\" from " + message.from_user.username + " [Chat ID: " + str(chat_id) + "].")


@bot.message_handler(commands=['start']) # Start message handler
def send_start(message, chat_id):
    log_message(message, chat_id)
    bot.reply_to(message, "Hola a todos, mis papirrines <3")

@bot.message_handler(commands=['hola']) # Hola message handler
def send_hola(message, chat_id):
    log_message(message, chat_id)
    bot.reply_to(message, "Hola, " + message.from_user.first_name)

@bot.message_handler(commands=['help']) # Help message handler
def send_help(message, chat_id):
    log_message(message, chat_id)
    bot.reply_to(message, "Lo siento si funciono mal o estoy muy limitado en funciones, pero estoy trabajando para mejorar día a día :)")


@server.route('/' + TOKEN, methods=['POST'])
def getMessage():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "!", 200

@server.route("/")
def webhook():
    # Remove current webhook
    logger.info("Removing current webhook...")
    bot.remove_webhook()
    logger.info("Successfully removed current webhook.")
    # Create new webhook
    logger.info("Creating new webhook...")
    bot.set_webhook(url=URL+TOKEN)
    logger.info("Successfully created new webhook.")
    return "!", 200


if __name__ == "__main__":
    # Run server
    logger.info("Starting running server...")
    server.run(host="0.0.0.0", port=int(PORT))
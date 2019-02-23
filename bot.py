#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Authors:      MaanuelMM
# Credits:      eternnoir, atlink, CoreDumped-ETSISI, Eldinnie
# Created:      2019/02/14
# Last update:  2019/02/23

import os
import telebot
import logger

from emt_madrid import get_arrive_stop
from data_loader import DataLoader
from flask import Flask, request
from logger import get_logger


# Enable logger
logger = get_logger("bot_starter", True)
logger.info("Starting bot...")
# Get data vars
logger.info("Getting data vars...")
data = DataLoader()
# Create TeleBot
logger.info("Creating TeleBot...")
bot = telebot.TeleBot(token=data.TOKEN)
# Create Flask server
logger.info("Creating Flask server...")
server = Flask(__name__)


def log_message(message):
    logger.info("Received: \"" + message.text + "\" from " + message.from_user.first_name +
            "(ID: " + str(message.from_user.id) + ") " + "[Chat ID: " + str(message.chat.id) + "].")

def log_emt_error(response):
    logger.info("Error in EMT API request. Return code: " + response["ReturnCode"] + ". Description: " +
            response["Description"] + ".")

def remove_command(text):
    # '/command' and 'the rest of the message'
    text.split(' ', 1)
    return text[1] # the rest of the message

# https://stackoverflow.com/questions/3501382/checking-whether-a-variable-is-an-integer-or-not
def letter_or_space_in_text(text):
    # Check for space, letter or if is an integer value
    return ' ' in text or not text.isdecimal() or not float(text).is_integer()

def process_time_left(time_left):
    if(time_left == 0):
        return "En parada"
    elif(time_left > 1200):
        return ">20:00min"
    else:
        return str(int(time_left / 60)).zfill(2) + ":" + str(int(time_left % 60)).zfill(2) + "min"

def make_arrival_line(arrive):
    return "\n\nLínea " + arrive["lineId"] + " (" + arrive["destination"] + "):\n    " + arrive["busTimeLeft"]

def int_or_decimal_str(data):
    return isinstance(data, int) or isinstance(data, str) or data.isdecimal()

def sort_arrivals(arrives):
    arrives_sorted = []
    lines_list = []
    for arrive in arrives:
        if(int_or_decimal_str(arrive["busTimeLeft"])):
            arrives["busTimeLeft"] = process_time_left(int(arrives["busTimeLeft"]))
            if(lines_list and arrive["lineId"] in lines_list):
                i = 0
                while arrive["lineId"] != arrives_sorted[i]["lineId"]:
                    i += 1
                arrives_sorted[i]["busTimeLeft"] += "    " + str(arrive["busTimeLeft"])
                del i
            else:
                lines_list.append(arrive["lineId"])
                arrive["busTimeLeft"] = str(arrive["busTimeLeft"])
                arrives_sorted.append(arrive)
    del lines_list
    return arrives_sorted

def process_response(arrives):
    result = ""
    if(isinstance(arrives, dict)):
        if(int_or_decimal_str(arrives["busTimeLeft"])):
            arrives["busTimeLeft"] = process_time_left(int(arrives["busTimeLeft"]))
            result += make_arrival_line(arrives)
    else:
        arrives_sorted = sort_arrivals(sorted(arrives, key=lambda d: (d["busTimeLeft"])))
        for arrive in arrives_sorted:
            result += make_arrival_line(arrive)
        del arrives_sorted
    return result + "\n\n"


# Start command handler
@bot.message_handler(commands=['start'])
def send_start(message):
    log_message(message)
    bot.reply_to(message, data.START)

# Hola command handler
@bot.message_handler(commands=['hola'])
def send_hola(message):
    log_message(message)
    bot.reply_to(message, data.HOLA + message.from_user.first_name)

# Parada command handler
@bot.message_handler(commands=['parada'])
def send_parada(message):
    log_message(message)
    text_with_no_command = remove_command(message.text)
    if(text_with_no_command == '' or letter_or_space_in_text(text_with_no_command)):
            bot.reply_to(message, data.PARADA_BAD_SPECIFIED)
    else:
        response = get_arrive_stop(data.EMTMADRID_BASEURL, data.EMTMADRID_GETARRIVESTOP_RELATIVEURL,
                data.EMTMADRID_GETARRIVESTOP_REQUESTDATA, data.EMTMADRID_IDCLIENT, data.EMTMADRID_PASSKEY,
                text_with_no_command)
        if("arrives" in response):
            reply = data.PARADA_SUCCESSFUL + process_response(response["arrives"]) + data.PARADA_SUCCESSFUL_DISCLAMER
            bot.reply_to(message, reply)
            del reply
        elif("ReturnCode" in response):
            bot.reply_to(message, data.PARADA_FAIL)
        else:
            bot.reply_to(message, data.PARADA_NO_ESTIMATION)
        del response

# Help command handler
@bot.message_handler(commands=['help'])
def send_help(message):
    log_message(message)
    bot.reply_to(message, data.HELP)


@server.route('/' + data.TOKEN, methods=['POST'])
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
    bot.set_webhook(url=data.URL+data.TOKEN)
    logger.info("Successfully created new webhook.")
    return "!", 200


if __name__ == "__main__":
    # Run server
    logger.info("Starting running server...")
    server.run(host="0.0.0.0", port=int(data.PORT))
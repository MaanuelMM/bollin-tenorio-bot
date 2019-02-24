#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Authors:      MaanuelMM
# Credits:      eternnoir, atlink, CoreDumped-ETSISI, Eldinnie
# Created:      2019/02/14
# Last update:  2019/02/24

import os
import telebot
import logger

from emt_madrid import get_arrive_stop
from data_loader import DataLoader
from flask import Flask, request
from logger import get_logger


# Enable logger
logger = get_logger("bot", True)
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
            " (ID: " + str(message.from_user.id) + ") " + "[Chat ID: " + str(message.chat.id) + "].")

def log_emt_error(response):
    logger.info("Error in EMT Madrid API request. Return code: " + response["ReturnCode"] + ". Description: " +
            response["Description"] + ".")

def make_arrival_line(arrival):
    return "\n\nLínea " + arrival["lineId"] + " (" + arrival["destination"] + "):\n    " + arrival["busTimeLeft"]

def remove_command(text):
    # '/command' and 'the rest of the message'
    if(len(text.split(" ", 1)) == 1):
        return ""
    else:
        return text.split(" ", 1)[1]

def process_time_left(time_left):
    if(str(time_left).isdecimal()):
        time_left = int(time_left)
        if(time_left == 0):
            return "En parada"
        elif(time_left > 1200):
            return ">20:00min"
        else:
            return str(int(time_left / 60)).zfill(2) + ":" + str(int(time_left % 60)).zfill(2) + "min"
    else:
        return "--:--min"

def sort_arrivals(arrivals):
    arrivals_sorted = []
    lines_list = []
    for arrival in arrivals:
        arrival["busTimeLeft"] = process_time_left(arrival["busTimeLeft"])
        if(lines_list and str(arrival["lineId"]) in lines_list):
            i = 0
            while arrival["lineId"] != arrivals_sorted[i]["lineId"]:
                i += 1
            arrivals_sorted[i]["busTimeLeft"] += "    " + str(arrival["busTimeLeft"])
            del i
        else:
            lines_list.append(str(arrival["lineId"]))
            arrival["busTimeLeft"] = str(arrival["busTimeLeft"])
            arrivals_sorted.append(arrival)
    del lines_list
    return arrivals_sorted

def process_response(arrivals):
    result = ""
    if(isinstance(arrivals, dict)):
        arrivals["busTimeLeft"] = process_time_left(arrivals["busTimeLeft"])
        result += make_arrival_line(arrivals)
    else:
        arrivals_sorted = sort_arrivals(sorted(arrivals, key=lambda d: (d["busTimeLeft"])))
        for arrival in arrivals_sorted:
            result += make_arrival_line(arrival)
        del arrivals_sorted
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
    if(text_with_no_command == "" or not text_with_no_command.isdecimal()):
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
            log_emt_error(response)
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
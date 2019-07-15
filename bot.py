#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Authors:      MaanuelMM
# Credits:      eternnoir, atlink, CoreDumped-ETSISI, Eldinnie
# Created:      2019/02/14
# Last update:  2019/07/15

import os
import telebot
import logger
import more_itertools

from emt_madrid import get_token, get_arrive_stop, get_bicimad, get_parkings
from data_loader import DataLoader
from flask import Flask, request
from flask_sslify import SSLify
from logger import get_logger


# Enable logger
logger = get_logger("bot", True)
logger.info("Starting bot...")

try:
    # Get data vars
    logger.info("Getting data and config vars...")
    data = DataLoader()

    # Create TeleBot
    logger.info("Creating TeleBot...")
    bot = telebot.TeleBot(token=data.TOKEN)

    # Create Flask server
    logger.info("Creating Flask server...")
    server = Flask(__name__)

    if 'DYNO' in os.environ:  # only trigger SSLify if the app is running on Heroku
        sslify = SSLify(server)

except Exception as e:
    logger.info("Error creating Bot. Shutting down...")
    logger.error(e, exc_info=True)
    exit()


def log_message(message):
    logger.info("Received: \"" + message.text + "\" from " + message.from_user.first_name +
                " (ID: " + str(message.from_user.id) + ") " + "[Chat ID: " + str(message.chat.id) + "].")


def log_emt_error(response):
    logger.info("Error in EMT Madrid API request:\n" + response)


def get_text(text):
    # '/command' and 'the rest of the message'
    if(len(text.split(" ", 1)) == 1):
        return ""
    else:
        return text.split(" ", 1)[1]


def is_integer(string):
    try:
        return int(string)
    except:
        return False


def make_arrival_line(arrival):
    return "\n\nLínea " + arrival["line"] + " (" + arrival["destination"] + "):\n    " + arrival["estimateArrive"]


def process_time_left(time_left):
    if(str(time_left).isdecimal()):
        time_left = int(time_left)
        if(time_left == 0):
            return "En parada"
        elif(time_left > 1200):
            return ">20:00min"
        else:
            return "  " + str(int(time_left / 60)).zfill(2) + ":" + str(int(time_left % 60)).zfill(2) + "min"
    else:
        return "  --:--min"


def sort_arrivals(arrivals):
    # https://stackoverflow.com/questions/4391697/find-the-index-of-a-dict-within-a-list-by-matching-the-dicts-value
    arrivals_sorted = []
    for arrival in arrivals:
        index_list = list(more_itertools.locate(
            arrivals_sorted, pred=lambda d: d["line"] == arrival["line"]))
        arrival["estimateArrive"] = process_time_left(
            arrival["estimateArrive"])
        if(index_list):  # False if empty
            arrivals_sorted[index_list[0]
                            ]["estimateArrive"] += "    " + arrival["estimateArrive"]
        else:
            arrivals_sorted.append(arrival)
        del index_list
    return arrivals_sorted


def process_arrival_response(arrivals):
    result = ""
    arrivals = sort_arrivals(
        sorted(arrivals, key=lambda d: (d["estimateArrive"])))
    for arrival in arrivals:
        result += make_arrival_line(arrival)
    return result + "\n\n"


def process_bicimad_response(bicimad):
    line = "\n"
    line += "Estación BiciMAD: " + \
        bicimad["name"] + " (#" + str(bicimad["id"]) + ")"
    if bool(bicimad["activate"]):
        line += "  \U0001F7E2OPERATIVA\U0001F7E2"
        line += "\n"
        line += "\n  Huecos disponibles: " + str(bicimad["free_bases"])
        line += "\n  Bicicletas disponibles: " + str(bicimad["dock_bikes"])
        line += "\n  Nivel de ocupación: "
        if(bicimad["light"] > 1):
            line += "\U0001F7E5ALTA\U0001F7E5"
        elif(bicimad["light"] > 0):
            line += "\U0001F7E7MEDIA\U0001F7E7"
        else:
            line += "\U0001F7E9BAJA\U0001F7E9"
    else:
        line += "  \U0001F534INOPERATIVA\U0001F534"
    line += "\n"
    line += "\n\U0001F4CDUbicación: https://google.com/maps/search/?api=1&query=" + \
        str(bicimad["geometry"]["coordinates"][1]) + "," + \
        str(bicimad["geometry"]["coordinates"][0])
    line += "\n"
    return line


def make_parking_line(parking):
    line = "\n"
    line += parking["name"] + " (#" + str(parking["id"]) + ")"
    line += "\n\tPlazas libres: "
    if parking["freeParking"] is None:
        line += "None"
    else:
        line += str(parking["freeParking"])
    line += "\n"
    return line


def process_parkings_response(parkings):
    result = "\n"
    for parking in parkings:
        result += make_parking_line(parking)
    return result


def message_sender(message, reply):
    if(len(reply) > 3000):
        splitted_reply = reply.split("\n\n")
        new_reply = ""
        for fragment in splitted_reply:
            if not new_reply:
                new_reply = fragment
            elif(len(new_reply + "\n\n" + fragment) > 3000):
                bot.reply_to(message, new_reply)
                new_reply = fragment
            else:
                new_reply += "\n\n" + fragment
        del new_reply
    else:
        bot.reply_to(message, reply)


def get_token_clean():
    try:
        token_response = get_token(
            data.EMTMADRID_GETTOKENSESSIONURL, data.EMTMADRID_EMAIL, data.EMTMADRID_PASSWORD)
        token = token_response["data"][0]["accessToken"]
        del token_response
    except:
        try:
            log_emt_error(token_response)
        except:
            log_emt_error("Unable to get API response.")
        raise
    return token


def get_arrive_stop_clean(stop_id):
    try:
        arrive_stop_response = get_arrive_stop(
            data.EMTMADRID_GETARRIVESTOPURL, get_token_clean(), stop_id, data.EMTMADRID_GETARRIVESTOPJSON)
        arrive_stop = arrive_stop_response["data"][0]["Arrive"]
        del arrive_stop_response
    except:
        try:
            log_emt_error(arrive_stop_response)
        except:
            log_emt_error("Unable to get API response.")
        raise
    return arrive_stop


def get_bicimad_clean(station_id):
    try:
        bicimad_response = get_bicimad(
            data.EMTMADRID_GETBICIMADSTATIONSURL, get_token_clean(), station_id)
        bicimad = bicimad_response["data"]
        del bicimad_response
    except:
        try:
            log_emt_error(bicimad_response)
        except:
            log_emt_error("Unable to get API response.")
        raise
    return bicimad


def get_parkings_clean():
    try:
        parkings_response = get_parkings(
            data.EMTMADRID_GETPARKINGSSTATUSURL, get_token_clean())
        parkings = parkings_response["data"]
        del parkings_response
    except:
        try:
            log_emt_error(parkings_response)
        except:
            log_emt_error("Unable to get API response.")
        raise
    return parkings

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
    text = get_text(message.text)
    if(str(message.chat.id) in data.EMTMADRID_ARRIVE_LIST and text.upper() in
            data.EMTMADRID_ARRIVE_LIST[str(message.chat.id)]):
        text = data.EMTMADRID_ARRIVE_LIST[str(message.chat.id)][text.upper()]
    if is_integer(text):
        try:
            arrive_stop = get_arrive_stop_clean(text)
            if arrive_stop:
                message_sender(message, data.PARADA_SUCCESSFUL.replace(
                    "<stopId>", text) + process_arrival_response(arrive_stop) + data.PARADA_SUCCESSFUL_DISCLAIMER)
            else:
                bot.reply_to(message, data.PARADA_NO_ESTIMATION)
            del arrive_stop
        except Exception as e:
            logger.error(e, exc_info=True)
    else:
        bot.reply_to(message, data.PARADA_BAD_SPECIFIED)
    del text

# Bicimad command handler
@bot.message_handler(commands=['bicimad'])
def send_bicimad(message):
    log_message(message)
    text = get_text(message.text)
    if is_integer(text):
        try:
            bicimad = get_bicimad_clean(text)
            if bicimad:
                message_sender(message, process_bicimad_response(bicimad[0]))
            else:
                bot.reply_to(message, data.BICIMAD_NO_INFO)
            del bicimad
        except Exception as e:
            logger.error(e, exc_info=True)
    else:
        bot.reply_to(message, data.BICIMAD_BAD_SPECIFIED)
    del text

# Parkings command handler
@bot.message_handler(commands=['parkings'])
def send_parkings(message):
    log_message(message)
    try:
        message_sender(message, data.PARKINGS +
                       process_parkings_response(get_parkings_clean()))
    except Exception as e:
        logger.error(e, exc_info=True)


# Help command handler
@bot.message_handler(commands=['help'])
def send_help(message):
    log_message(message)
    bot.reply_to(message, data.HELP)


@server.route('/' + data.TOKEN, methods=['POST'])
def getMessage():
    bot.process_new_updates(
        [telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
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
    try:
        # Run server
        logger.info("Starting running server...")
        server.run(host="0.0.0.0", port=int(data.PORT))
    except Exception as e:
        logger.info("Error starting server. Shutting down...")
        logger.error(e, exc_info=True)
        exit()

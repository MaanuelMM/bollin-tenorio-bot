#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Authors:      MaanuelMM
# Credits:      eternnoir, atlink, CoreDumped-ETSISI, Eldinnie
# Created:      2019/02/14
# Last update:  2019/05/20

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
# Get data vars
logger.info("Getting data vars...")
data = DataLoader()
# Create TeleBot
logger.info("Creating TeleBot...")
bot = telebot.TeleBot(token=data.TOKEN)
# Create Flask server
logger.info("Creating Flask server...")
server = Flask(__name__)

if 'DYNO' in os.environ:  # only trigger SSLify if the app is running on Heroku
    sslify = SSLify(server)


def log_message(message):
    logger.info("Received: \"" + message.text + "\" from " + message.from_user.first_name +
                " (ID: " + str(message.from_user.id) + ") " + "[Chat ID: " + str(message.chat.id) + "].")


def log_emt_error(response):
    logger.info("Error in EMT Madrid API request:\n" + response)


def remove_command(text):
    # '/command' and 'the rest of the message'
    if(len(text.split(" ", 1)) == 1):
        return ""
    else:
        return text.split(" ", 1)[1]


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
    line += bicimad["name"] + " (#" + str(bicimad["id"]) + ")"
    if bool(bicimad["activate"]):
        line += ":  🟢OPERATIVA🟢"
        line += "\n"
        line += "\n  Huecos disponibles: " + str(bicimad["free_bases"])
        line += "\n  BicMad disponibles: " + str(bicimad["dock_bikes"])
        line += "\n  Nivel de ocupación: "
        if(bicimad["light"] >= 2):
            line += "🟩ALTA🟩"
        elif(bicimad["light"] > 1):
            line += "🟧MEDIA🟧"
        else:
            line += "🟩BAJA🟩"
    else:
        line += ":  🔴INOPERATIVA🔴"
    line += "\n"
    line += "\n  🗺Ubicación: " + "https://google.com/maps/search/?api=1&query=" + \
        bicimad["geometry"]["coordinates"][1] + "," + \
            bicimad["geometry"]["coordinates"][0]
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
    text = remove_command(message.text)
    if(str(message.chat.id) in data.EMTMADRID_ARRIVE_LIST and text.upper() in
            data.EMTMADRID_ARRIVE_LIST[str(message.chat.id)]):
        text = data.EMTMADRID_ARRIVE_LIST[str(message.chat.id)][text.upper()]
    if(text == "" or not text.isdecimal()):
        bot.reply_to(message, data.PARADA_BAD_SPECIFIED)
    else:
        try:
            token_response = get_token(
                data.EMTMADRID_GETTOKENSESSIONURL, data.EMTMADRID_EMAIL, data.EMTMADRID_PASSWORD)
            token = token_response["data"][0]["accessToken"]
            arrive_stop_response = get_arrive_stop(
                data.EMTMADRID_GETARRIVESTOPURL, token, text, data.EMTMADRID_GETARRIVESTOPJSON)
            arrive_stop = arrive_stop_response["data"][0]["Arrive"]
            if arrive_stop:
                reply = data.PARADA_SUCCESSFUL.replace(
                    "<stopId>", text) + process_arrival_response(arrive_stop) + data.PARADA_SUCCESSFUL_DISCLAIMER
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
                del reply
            else:
                bot.reply_to(message, data.PARADA_NO_ESTIMATION)
            del token_response, token, arrive_stop_response, arrive_stop
        except:
            log = ""
            try:
                log += (str(token_response))
                log += (str(arrive_stop_response))
            except:
                log += "\nSome data is missing."
            log_emt_error(log)
            bot.reply_to(message, data.REQUEST_FAIL)
            try:
                del log, token_response, token, arrive_stop_response, arrive_stop, reply, new_reply
            except:
                pass

# Bicimad command handler
@bot.message_handler(commands=['bicimad'])
def send_bicimad(message):
    log_message(message)
    text = remove_command(message.text)
    if(text == "" or not text.isdecimal()):
        bot.reply_to(message, data.BICIMAD_BAD_SPECIFIED)
    else:
        try:
            token_response = get_token(
                data.EMTMADRID_GETTOKENSESSIONURL, data.EMTMADRID_EMAIL, data.EMTMADRID_PASSWORD)
            token = token_response["data"][0]["accessToken"]
            bicimad_response = get_bicimad(
                data.EMTMADRID_GETBICIMADSTATIONSURL, token, text)
            bicimad = bicimad_response["data"]
            if bicimad:
                reply = data.BICIMAD + process_bicimad_response(bicimad)
                bot.reply_to(message, reply)
                del reply
            else:
                bot.reply_to(message, data.BICIMAD_NO_INFO)
            del token_response, token, bicimad_response, bicimad
        except:
            log = ""
            try:
                log += (str(token_response))
                log += (str(bicimad_response))
            except:
                log += "\nSome data is missing."
            log_emt_error(log)
            bot.reply_to(message, data.REQUEST_FAIL)
            try:
                del log, token_response, token, bicimad_response, bicimad, reply
            except:
                pass

# Parkings command handler
@bot.message_handler(commands=['parkings'])
def send_parkings(message):
    log_message(message)
    try:
        token_response = get_token(
            data.EMTMADRID_GETTOKENSESSIONURL, data.EMTMADRID_EMAIL, data.EMTMADRID_PASSWORD)
        token = token_response["data"][0]["accessToken"]
        parkings_response = get_parkings(
            data.EMTMADRID_GETPARKINGSSTATUSURL, token)
        parkings = parkings_response["data"]
        reply = data.PARKINGS + process_parkings_response(parkings)
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
        del reply, token_response, token, parkings_response, parkings
    except:
        log = ""
        try:
            log += (str(token_response))
            log += (str(parkings_response))
        except:
            log += "\nSome data is missing."
        log_emt_error(log)
        bot.reply_to(message, data.REQUEST_FAIL)
        try:
            del log, token_response, token, parkings_response, parkings, reply, new_reply
        except:
            pass

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
    # Run server
    logger.info("Starting running server...")
    server.run(host="0.0.0.0", port=int(data.PORT))

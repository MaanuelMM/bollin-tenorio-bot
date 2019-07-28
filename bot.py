#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Authors:      MaanuelMM
# Credits:      eternnoir, atlink, CoreDumped-ETSISI, Eldinnie
# Created:      2019/02/14
# Last update:  2019/07/28

import os
import re
import logger
import telebot
import more_itertools

from bot_requests import get_token, get_arrive_stop, get_bicimad, get_parkings, get_generic_request
from data_loader import DataLoader
from flask import Flask, request
from flask_sslify import SSLify
from bs4 import BeautifulSoup
from logger import get_logger


logger = get_logger("bot", True)
logger.info("Starting bot...")

try:
    logger.info("Getting data and config vars...")
    data = DataLoader()

    logger.info("Creating TeleBot...")
    bot = telebot.TeleBot(token=data.TOKEN)

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


def log_api_error(response):
    logger.info("Error in API request:\n" + response)


def get_text_with_no_command(text):
    try:
        return text.split(" ", 1)[1]
    except:
        return ""


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


# https://stackoverflow.com/questions/4391697/find-the-index-of-a-dict-within-a-list-by-matching-the-dicts-value
def sort_arrivals(arrivals):
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


def map_link_maker(coordX, coordY):
    return "https://google.com/maps/search/?api=1&query=" + str(coordX) + "," + str(coordY)


def bicimad_light(light):
    switcher_light = {
        0: "\U0001F7E9BAJA\U0001F7E9",
        1: "\U0001F7E7MEDIA\U0001F7E7",
        2: "\U0001F7E5ALTA\U0001F7E5"
    }
    return switcher_light.get(light, "Indefinido")


def process_bicimad_response(bicimad):
    line = "\n"
    line += "Estación BiciMAD: " + \
        bicimad["name"] + " (#" + str(bicimad["id"]) + ")"
    if bool(bicimad["activate"]):
        line += "  \U0001F7E2OPERATIVA\U0001F7E2"
        line += "\n"
        line += "\n  Huecos disponibles: " + str(bicimad["free_bases"])
        line += "\n  Bicicletas disponibles: " + str(bicimad["dock_bikes"])
        line += "\n  Nivel de ocupación: " + bicimad_light(bicimad["light"])
    else:
        line += "  \U0001F534INOPERATIVA\U0001F534"
    line += "\n"
    line += "\n\U0001F4CDUbicación: " + map_link_maker(bicimad["geometry"]["coordinates"][1], bicimad["geometry"]["coordinates"][0])
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


def generate_metro_data_response(metro_data):
    response = {}
    soup = BeautifulSoup(metro_data, "html.parser")
    for img in soup.find_all("img"):
        line = img.get('class')[0].replace("-", " ").capitalize()
        estimations = re.sub(r'\s\s+', r'\n    ', img.parent.next_sibling.next_sibling.text).strip()
        if line not in response:
            response[line] = []
        response[line].append(estimations)
    return response


def process_metro_response(metro_data):
    result = ""
    for k, v in generate_metro_data_response(metro_data).items():
        result += "\n"
        result += k
        for item in v:
            result += "\n  "
            result += item
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
        token_response = get_token(data.EMTMADRID_GETTOKENSESSIONURL, data.EMTMADRID_EMAIL, data.EMTMADRID_PASSWORD)
        token = token_response["data"][0]["accessToken"]
        del token_response
    except:
        try:
            log_api_error(token_response)
        except:
            log_api_error("Unable to get API response.")
        raise
    return token


def get_arrive_stop_clean(stop_id):
    try:
        arrive_stop_response = get_arrive_stop(data.EMTMADRID_GETARRIVESTOPURL, get_token_clean(), stop_id, data.EMTMADRID_GETARRIVESTOPJSON)
        try:
            arrive_stop = arrive_stop_response["data"][0]["Arrive"]
        except:
            arrive_stop = ""
        del arrive_stop_response
    except:
        try:
            log_api_error(arrive_stop_response)
        except:
            log_api_error("Unable to get API response.")
        raise
    return arrive_stop


def get_bicimad_clean(station_id):
    try:
        bicimad_response = get_bicimad(data.EMTMADRID_GETBICIMADSTATIONSURL, get_token_clean(), station_id)
        try:
            bicimad = bicimad_response["data"]
        except:
            bicimad = ""
        del bicimad_response
    except:
        try:
            log_api_error(bicimad_response)
        except:
            log_api_error("Unable to get API response.")
        raise
    return bicimad


def get_parkings_clean():
    try:
        parkings_response = get_parkings(data.EMTMADRID_GETPARKINGSSTATUSURL, get_token_clean())
        try:
            parkings = parkings_response["data"]
        except:
            parkings = ""
        del parkings_response
    except:
        try:
            log_api_error(parkings_response)
        except:
            log_api_error("Unable to get API response.")
        raise
    return parkings


def get_metro_arrival_clean(station_id):
    try:
        metro_response = get_generic_request(data.METROMADRID_GETARRIVESTATIONURL + station_id).json()
        try:
            metro = metro_response[0]["data"]
        except:
            metro = ""
        del metro_response
    except:
        log_api_error("Unable to get API response due to unauthorized access.")
        raise
    return metro


def get_metro_stations_clean():
    try:
        return get_generic_request(data.METROMADRID_GETSTATIONSLISTURL).json()
    except:
        log_api_error("Unable to get Metro Madrid stations from GitHub.")
        raise



@bot.message_handler(commands=['start'])
def send_start(message):
    log_message(message)
    bot.reply_to(message, data.START)


@bot.message_handler(commands=['hola'])
def send_hola(message):
    log_message(message)
    bot.reply_to(message, data.HOLA + message.from_user.first_name)


@bot.message_handler(commands=['parada'])
def send_parada(message):
    log_message(message)
    text = get_text_with_no_command(message.text)
    if(str(message.chat.id) in data.PARADA_CHAT_LIST and text.upper() in data.PARADA_CHAT_LIST[str(message.chat.id)]):
        text = data.PARADA_CHAT_LIST[str(message.chat.id)][text.upper()]
    if is_integer(text):
        try:
            arrive_stop = get_arrive_stop_clean(text)
            if arrive_stop:
                message_sender(message, data.PARADA_SUCCESSFUL.replace("<stopId>", text) + process_arrival_response(arrive_stop) + data.PARADA_SUCCESSFUL_DISCLAIMER)
            else:
                bot.reply_to(message, data.PARADA_NO_ESTIMATION)
            del arrive_stop
        except Exception as e:
            logger.error(e, exc_info=True)
            bot.reply_to(message, data.REQUEST_FAIL)
    else:
        bot.reply_to(message, data.PARADA_BAD_SPECIFIED)
    del text


@bot.message_handler(commands=['bicimad'])
def send_bicimad(message):
    log_message(message)
    text = get_text_with_no_command(message.text)
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
            bot.reply_to(message, data.REQUEST_FAIL)
    else:
        bot.reply_to(message, data.BICIMAD_BAD_SPECIFIED)
    del text


@bot.message_handler(commands=['parkings'])
def send_parkings(message):
    log_message(message)
    try:
        message_sender(message, data.PARKINGS + process_parkings_response(get_parkings_clean()))
    except Exception as e:
        logger.error(e, exc_info=True)
        bot.reply_to(message, data.REQUEST_FAIL)


@bot.message_handler(commands=['metro'])
def send_metro(message):
    log_message(message)
    text = get_text_with_no_command(message.text)
    if text:
        try:
            stations = get_metro_stations_clean()
            if text in stations:
                response = get_metro_arrival_clean(stations[text])
                if response:
                    message_sender(message, process_metro_response(data))
                else:
                    bot.reply_to(message, data.METRO_NO_ESTIMATION)
                del response
            else:
                bot.reply_to(message, data.METRO_DOES_NOT_EXIST)
            del stations
        except Exception as e:
            logger.error(e, exc_info=True)
            bot.reply_to(message, data.REQUEST_FAIL)
    else:
        bot.reply_to(message, data.METRO_BAD_SPECIFIED)
    del text


@bot.message_handler(commands=['help'])
def send_help(message):
    log_message(message)
    bot.reply_to(message, data.HELP)


@server.route("/" + data.TOKEN, methods=['POST'])
def getMessage():
    bot.process_new_updates(
        [telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "!", 200


@server.route("/")
def webhook():
    logger.info("Removing current webhook...")
    bot.remove_webhook()
    logger.info("Successfully removed current webhook.")
    logger.info("Creating new webhook...")
    bot.set_webhook(url=data.URL+data.TOKEN)
    logger.info("Successfully created new webhook.")
    return "!", 200


if __name__ == "__main__":
    try:
        logger.info("Starting running server...")
        server.run(host="0.0.0.0", port=int(data.PORT))
    except Exception as e:
        logger.info("Error starting server. Shutting down...")
        logger.error(e, exc_info=True)
        exit()

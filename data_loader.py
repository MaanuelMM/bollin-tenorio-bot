#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Authors:      CoreDumped-ETSISI, MaanuelMM
# Credits:      CoreDumped-ETSISI
# Created:      2019/02/14
# Last update:  2019/05/20

import json
import os

from logger import get_logger
from ast import literal_eval


logger = get_logger("data_loader")


class DataLoader:

    def __init__(self):
        try:
            # Get Config Vars from server
            logger.info("Getting Config Vars from server...")
            self.TOKEN = os.environ.get('TOKEN')
            self.PORT = os.environ.get('PORT', '5000')
            self.URL = os.environ.get('URL')
            self.EMTMADRID_EMAIL = os.environ.get('EMTMADRID_EMAIL')
            self.EMTMADRID_PASSWORD = os.environ.get('EMTMADRID_PASSWORD')
            self.EMTMADRID_ARRIVE_LIST = literal_eval(
                os.environ.get('EMTMADRID_ARRIVE_LIST'))
            with open('data/data.json', encoding="utf-8") as data:
                loaded_data = json.load(data)
        except:
            logger.exception("Failed to load the data from the JSON file.")
        else:
            logger.info("Successfully loaded the data from the JSON file.")
            # Get Bot Strings
            logger.info("Getting Bot Strings...")
            self.START = loaded_data["Bot"]["start"]
            self.HOLA = loaded_data["Bot"]["hola"]
            self.HELP = loaded_data["Bot"]["help"]
            self.PARADA_SUCCESSFUL = loaded_data["Bot"]["parada_successful"]
            self.PARADA_SUCCESSFUL_DISCLAIMER = loaded_data["Bot"]["parada_successful_disclaimer"]
            self.PARADA_BAD_SPECIFIED = loaded_data["Bot"]["parada_bad_specified"]
            self.PARADA_NO_ESTIMATION = loaded_data["Bot"]["parada_no_estimation"]
            self.BICIMAD = loaded_data["Bot"]["bicimad"]
            self.PARKINGS = loaded_data["Bot"]["parkings"]
            self.REQUEST_FAIL = loaded_data["Bot"]["request_fail"]
            # Get EMT Madrid API Data
            logger.info("Getting EMT Madrid API Data...")
            self.EMTMADRID_GETTOKENSESSIONURL = loaded_data["EMTMadrid"]["GetTokenSessionURL"]
            self.EMTMADRID_GETARRIVESTOPURL = loaded_data["EMTMadrid"]["GetArriveStopURL"]
            self.EMTMADRID_GETARRIVESTOPJSON = loaded_data["EMTMadrid"]["GetArriveStopJSON"]
            self.EMTMADRID_GETBICIMADSTATIONSURL = loaded_data["EMTMadrid"]["GetBicimadStationsURL"]
            self.EMTMADRID_GETPARKINGSSTATUSURL = loaded_data["EMTMadrid"]["GetParkingsStatusURL"]

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Authors:      CoreDumped-ETSISI, MaanuelMM
# Credits:      CoreDumped-ETSISI
# Created:      2019/02/14
# Last update:  2019/02/23

import json
import os

from logger import get_logger


logger = get_logger("data_loader")

class DataLoader:

    def __init__(self):
        global data
        try:
            data = json.load(open('data/data.json'), encoding="utf-8")
        except:
            logger.exception("Failed to load the data from the JSON file.")
        else:
            logger.info("Successfully loaded the data from the JSON file.")
            # Get Config Vars from server
            logger.info("Getting Config Vars from server...")
            self.TOKEN = os.environ.get('TOKEN')
            self.PORT = os.environ.get('PORT', '5000')
            self.URL = os.environ.get('URL')
            self.EMTMADRID_IDCLIENT = os.environ.get('EMTMADRID_IDCLIENT')
            self.EMTMADRID_PASSKEY = os.environ.get('EMTMADRID_PASSKEY')
            # Get Bot Strings
            logger.info("Getting Bot Strings...")
            self.START = data["Bot"]["start"]
            self.HOLA = data["Bot"]["hola"]
            self.HELP = data["Bot"]["help"]
            self.PARADA_SUCCESSFUL = data["Bot"]["parada_successful"]
            self.PARADA_SUCCESSFUL_DISCLAMER = data["Bot"]["parada_successful_disclamer"]
            self.PARADA_BAD_SPECIFIED = data["Bot"]["parada_bad_specified"]
            self.PARADA_NO_ESTIMATION = data["Bot"]["parada_no_estimation"]
            self.PARADA_FAIL = data["Bot"]["parada_fail"]
            # Get EMT Madrid API Data
            logger.info("Getting EMT Madrid API Data...")
            self.EMTMADRID_BASEURL = data["EMTMadrid"]["BaseURL"]
            self.EMTMADRID_GETARRIVESTOP_RELATIVEURL = data["EMTMadrid"]["GetArriveStop"]["RelativeURL"]
            self.EMTMADRID_GETARRIVESTOP_REQUESTDATA = data["EMTMadrid"]["GetArriveStop"]["RequestData"]
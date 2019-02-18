#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Authors:      MaanuelMM, CoreDumped-ETSISI
# Credits:      CoreDumped-ETSISI
# Created:      2019/02/14
# Last update:  2019/02/18

import json
import os

from logger import get_logger


logger = get_logger("data_loader")

class DataLoader:

    def __init__(self):
        global data_and_settings
        try:
            data = json.load(open('data/data.json'), encoding="utf-8")
            data_and_settings = data.copy()
        except:
            logger.exception("Failed to load the configuration JSON file.")
        else:
            logger.info("Successfully loaded the configuration JSON file.")
            self.telegram_token = os.environ.get('TOKEN') # Getting the token variable directly asking to the server
            self.server_port = os.environ.get('PORT', '8443') # Getting the port number directly asking to the server
            self.server_url = os.environ.get('URL') # Getting the server URL directly asking to the server
            self.hola_command = data_and_settings["hola_command"]
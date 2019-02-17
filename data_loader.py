#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Authors:      MaanuelMM, CoreDumped-ETSISI
# Credits:      CoreDumped-ETSISI
# Created:      2019/02/14
# Last update:  2019/02/17

from logger import get_logger
import json
import os

logger = get_logger("data_loader")


class DataLoader:

    def __init__(self):
        global data_and_settings
        try:
            private_data = json.load(open('data/private-data.json'), encoding="utf-8")
            data = json.load(open('data/data.json'), encoding="utf-8")
            data_and_settings = private_data.copy()
            data_and_settings.update(data)
        except:
            logger.exception("Failed to load the configuration JSON file.")
        else:
            logger.info("Successfully loaded the configuration JSON file.")
            self.telegram_token = data_and_settings["telegram_token"]
            self.server_url = data_and_settings["server_url"]
            self.server_port = os.environ.get('PORT') # Getting the port number directly asking to the server
            self.hola_command = data_and_settings["hola_command"]
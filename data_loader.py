#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Authors:      CoreDumped-ETSISI, MaanuelMM
# Credits:      CoreDumped-ETSISI, MaanuelMM
# Created:      2019/02/14
# Last update:  2019/02/14

from logger import get_logger
import json

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
            logger.exception("Error al cargar el JSON de configuración")
        else:
            logger.info("JSON cargado con éxito")
            self.telegram_token = data_and_settings["telegram_token"]
            self.hola_mundo = data_and_settings["hola_mundo"]
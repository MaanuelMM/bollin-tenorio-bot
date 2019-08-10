#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Authors:      I don't know :(
# Credits:      CoreDumped-ETSISI
# Created:      2019/02/14
# Last update:  2019/08/10

import logging


def get_logger(name=__name__, stream=False):
    formatter = logging.Formatter(
        '[%(levelname)s]  %(asctime)s  %(filename)s:\t %(message)s\n')
    logger = logging.getLogger(name)

    file_handler = logging.FileHandler(
        name + '.log')  # Instantiate the file handler
    file_handler.setFormatter(formatter)
    # only logs warnings level or higher
    file_handler.setLevel(logging.WARNING)
    logger.addHandler(file_handler)

    if stream:
        # Instantiate the stream handler AKA the console
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        stream_handler.setLevel(logging.DEBUG)  # shows everything on console
        logger.addHandler(stream_handler)

    # We add both handlers to the logger

    logger.setLevel(logging.DEBUG)  # Logger registers all logs

    return logger

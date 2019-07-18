#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Authors:      MaanuelMM
# Credits:      EMT-Madrid, alvaroreig
# Created:      2019/02/22
# Last update:  2019/07/18

import requests


def get_token(url, email, password):
    return requests.get(url, headers={"email": email, "password": password}, timeout=10).json()


def get_arrive_stop(url, token, stop_id, json):
    return requests.post(url.replace("<stopId>", stop_id), headers={"accessToken": token}, json=json, timeout=10).json()


def get_bicimad(url, token, station_id):
    return requests.get(url.replace("<idStation>", station_id), headers={"accessToken": token}, timeout=10).json()


def get_parkings(url, token):
    return requests.get(url, headers={"accessToken": token}, timeout=10).json()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Authors:      MaanuelMM
# Credits:      EMT-Madrid, alvaroreig
# Created:      2019/02/22
# Last update:  2019/05/16

import requests


def get_token(url, email, password):
    return requests.get(url, headers={"email": email, "password": password}).json()

def get_arrive_stop(url, token, id_stop, json):
    return requests.post(url.replace("<stopId>", id_stop), headers={"accessToken": token}, json=json).json()
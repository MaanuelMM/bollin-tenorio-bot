#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Authors:      MaanuelMM
# Credits:      EMT-Madrid, alvaroreig
# Created:      2019/02/22
# Last update:  2019/02/23

import requests


def get_response(url, request_data):
    return requests.request("POST", url, data=request_data).json() # Return in JSON format

def get_arrive_stop(base_url, relative_url, request_data, id_client, pass_key, id_stop):
    url = base_url + relative_url
    request_data["idClient"] = id_client
    request_data["passKey"] = pass_key
    request_data["idStop"] = id_stop
    return get_response(url, request_data)
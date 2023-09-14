# Python wrapper for the Open Exchange Rates API
# From https://github.com/massakai/pyoxr
# Edited for relevant functions only

# -*- coding: utf-8 -*-

"""
Open Exchange Rates API for Python
"""

import requests


class OXRClient(object):
    def __init__(self,
                 app_id,
                 api_base="https://openexchangerates.org/api/"):
        self.api_base = api_base.rstrip("/")
        self.app_id = app_id
        self.session = requests.Session()

    def get_currencies(self):
        """
        Get a JSON list of all currency symbols available from the Open
        Exchange Rates API, along with their full names.
        ref. https://oxr.readme.io/docs/currencies-json
        """
        return self.__request("currencies.json")

    def get_latest(self,
                   base=None,
                   symbols=None):
        """
        Get latest data.
        ref. https://oxr.readme.io/docs/latest-json
        """
        return self.__get_exchange_rates("latest.json", base, symbols)

    def __request(self, endpoint, payload=None):
        url = self.api_base + "/" + endpoint
        request = requests.Request("GET", url, params=payload)
        prepared = request.prepare()

        response = self.session.send(prepared)
        if response.status_code != requests.codes.ok:
            raise OXRStatusError(request, response)
        json = response.json()
        if json is None:
            raise OXRDecodeError(request, response)
        return json

    def __get_exchange_rates(self, endpoint, base, symbols, payload=None):
        if payload is None:
            payload = dict()
        payload["app_id"] = self.app_id
        if base is not None:
            payload["base"] = base
        if isinstance(symbols, list) or isinstance(symbols, tuple):
            symbols = ",".join(symbols)
        if symbols is not None:
            payload["symbols"] = symbols
        return self.__request(endpoint, payload)


class OXRError(Exception):
    """Open Exchange Rates Error"""
    def __init__(self, req, resp):
        super(OXRError, self).__init__()
        self.request = req
        self.response = resp


class OXRStatusError(OXRError):
    """API status code error"""
    pass


class OXRDecodeError(OXRError):
    """JSON decode error"""
    pass

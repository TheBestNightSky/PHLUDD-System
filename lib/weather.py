import requests
import json
from lib.location import Location
from lib.exceptions import apiException
import traceback

import lib.logging as Logging

Log = Logging.Log("logs/phludd_log.log")

class Weather:
    def __init__(self, api_key):
        self.weather_key = api_key
        self.lat = 0
        self.lon = 0
        self.Current = _Current(self)
        self.Forcast = _Forcast(self)
        self._lastException = None
        
    def setLoc(self, lat, lon):
        self.lat = lat
        self.lon = lon

    def getLastException(self):
        return self._lastException()

class _Current:
    parent = None
    id = 0
    condition = ""
    description = ""
    temp = 0
    chill = 0
    humid = 0
    city = ""

    def __init__(self, parent : 'Weather'):
        self.parent = parent
    
    def update(self):

        try:
            url = f"https://api.openweathermap.org/data/2.5/weather?lat={self.parent.lat}&lon={self.parent.lon}&appid={self.parent.weather_key}&units=metric"
            
            req = requests.get(url)
            response = req.json()
            req.close()
            
            if int(response['cod']) == 200:
                weather = response['weather'][0]
                self.id = weather['id']
                self.condition = weather['main']
                self.description = weather['description']

                info = response['main']
                self.temp = info['temp']
                self.chill = info['feels_like']
                self.humid = info['humidity']

                self.city = response['name']

                success = True
            else:
                raise apiException(response['cod'], response['message'])
        except requests.exceptions.RequestException as error:
            Log.log(Log.ERROR, F'An error occurred in weather.py: {type(error)} | {error}')
            Log.log(Log.ERROR, ''.join(traceback.format_tb(error.__traceback__)))
            self.parent._lastException = error
            success = False
        except apiException as error:
            Log.log(Log.ERROR, F'An error occurred in weather.py: {type(error)} {error.cod} | {error}')
            Log.log(Log.ERROR, ''.join(traceback.format_tb(error.__traceback__)))
            self.parent._lastException = error
            success = False
        return success


class _Forcast:
    parent = None
    
    def __init__(self, parent : 'Weather'):
        self.parent = parent

    def update(self):
        try:
            url = f"https://api.openweathermap.org/data/2.5/forecast?lat={self.parent.lat}&lon={self.parent.lon}&appid={self.parent.weather_key}&units=metric"

            req = requests.get(url)
            response = req.json()
            req.close()

            if int(response['cod']) == 200:
                success = True
                for i in response['list']:
                    if i['dt_txt'][:10] == '2023-03-08':
                        Log.log(Log.DEBUG, i)
            else:
                raise apiException(response['cod'], response['message'])
        except requests.exceptions.RequestException as error:
            Log.log(Log.ERROR, F'An error occurred in weather.py: {type(error)} | {error}')
            Log.log(Log.ERROR, ''.join(traceback.format_tb(error.__traceback__)))
            self.parent._lastException = error
            success = False
        except apiException as error:
            Log.log(Log.ERROR, F'An error occurred in weather.py: {type(error)} {error.cod} | {error}')
            Log.log(Log.ERROR, ''.join(traceback.format_tb(error.__traceback__)))
            self.parent._lastException = error
            success = False
        return success

    
    

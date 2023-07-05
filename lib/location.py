import requests
import subprocess
import platform
from lib.exceptions import apiException
import traceback

import lib.logging as Logging

Log = Logging.Log("logs/phludd_log.log")

class Location:
    def __init__(self, api_key):
        self.maps_key = api_key
        self._lastException = None


    def getLastError(self):
        return self._lastException
        
    # windows netsh method
    def netsh(self):
        form = {
            "considerIp" : True,
            "wifiAccessPoints" : []
            }

        template = {
            "macAddress" : "",
            "signalStrength" : 0,
            "age" : 0,
            "channel" : 0,
            "signalToNoiseRatio" : 0
            }
        
        raw, error = subprocess.Popen(['netsh', 'wlan', 'show', 'networks', 'bssid'], stdout=subprocess.PIPE, text=True).communicate()

        parsable = raw.split(' ')[11:]
        while '' in parsable:
            parsable.remove('')
        while '\n' in parsable:
            parsable.remove('\n')
        for i in range(0, len(parsable)):
            parsable[i] = parsable[i].strip()


        for i in range(0, len(parsable)):
            if "BSSID" in parsable[i]:
                form["wifiAccessPoints"].append(template.copy())
                form["wifiAccessPoints"][-1]["macAddress"] = parsable[i+3]
            elif "Channel" in parsable[i]:
                form["wifiAccessPoints"][-1]["channel"] = int(parsable[i+2])
            elif "Signal" in parsable[i]:
                percent = int(parsable[i+2].replace('%', ''))/100
                val = (percent * (118 - 0) + 0) - 128
                form["wifiAccessPoints"][-1]["signalStrength"] = int(val)
        return form

    # to-do linux method
    def iwlist(self):
        return None
    
    def generate_dict(self):
        sys = platform.system()
        if sys == "Windows":
            return self.netsh()
        elif sys == "Linux":
            return self.iwlist()

    def Get(self):
        lat, lon = None, None
        try:
            url = "https://www.googleapis.com/geolocation/v1/geolocate?key="
            data = self.generate_dict()
            req = requests.post(url+self.maps_key, json=data)
            response = req.json()
            
            req.close()
            first = list(response.keys())[0]
            if first != "error":
                lat, lon, success = response['location']['lat'], response['location']['lng'], True
            else:
                raise apiException(response['error']['code'], response['error']['message'])
        except requests.exceptions.RequestException as error:
            Log.log(Log.ERROR, F'An error occured in location.py: {type(error)} | {error}')
            Log.log(Log.ERROR, ''.join(traceback.format_tb(error.__traceback__)))
            self._lastException = error
            success = False
        except apiException as error:
            Log.log(Log.ERROR, F'An error occured in location.py: {type(error)} {error.cod} | {error}')
            Log.log(Log.ERROR, ''.join(traceback.format_tb(error.__traceback__)))
            self._lastException = error
            success = False
        return lat, lon, success

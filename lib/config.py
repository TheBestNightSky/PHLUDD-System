import json
import os
from lib.util import Dict2Class

#Settings and Keys
class Configuration:
    apikeys_template = {
        "googleMaps" : "",
        "openWeather" : ""
        }
    
    settings_template = {
        "Sensors" : {
            "S0": {
                "enable" : True,
                "pos" : {
                    "x" : 0,
                    "y" : 0
                    }
                },
            "S1": {
                "enable" : True,
                "pos" : {
                    "x" : 0,
                    "y" : 0
                    }
                },
            "S2": {
                "enable" : True,
                "pos" : {
                    "x" : 0,
                    "y" : 0
                    }
                },
            "S3": {
                "enable" : True,
                "pos" : {
                    "x" : 0,
                    "y" : 0
                    }
                },
            "S4": {
                "enable" : True,
                "pos" : {
                    "x" : 0,
                    "y" : 0
                    }
                },
            "S5": {
                "enable" : True,
                "pos" : {
                    "x" : 0,
                    "y" : 0
                    }
                },
            "S6": {
                "enable" : True,
                "pos" : {
                    "x" : 0,
                    "y" : 0
                    }
                },
            "poll_rate": 600,
            "voltage_threshold": 0.5
            },
        "Email" : {
            "enable": False,
            "Recipients": []
        },
        "Display" : {
            "width" : 1280,
            "height" : 720
        }
    }

    def __init__(self):
        #config file
        if os.path.exists('config.json'):
            file = open('config.json', 'r')
            self.PHLUDD = Dict2Class(json.load(file))
            file.close()
        else:
            json_object = json.dumps(type(self).settings_template, indent=4)
            with open("config.json", "w") as outfile:
                outfile.write(json_object)
                outfile.close()

            self.PHLUDD = Dict2Class(type(self).settings_template)

        #key file
        if os.path.exists('credentials/api_keys.json'):
            file = open('credentials/api_keys.json', 'r')
            self.apikeys = Dict2Class(json.load(file))
            file.close()
        else:
            json_object = json.dumps(type(self).apikeys_template, indent=4)
            with open("credentials/api_keys.json", "w") as outfile:
                outfile.write(json_object)
                outfile.close()

            self.apikeys = Dict2Class(type(self).apikeys_template)

        # email
        if self.PHLUDD.Email.enable:
            recipients = ""
            for i in self.PHLUDD.Email.Recipients:
                recipients = recipients + i + ", "
            self.PHLUDD.Email.recipient_string = recipients[:len(recipients)-2]

        # display
        self.PHLUDD.Display.resolution = (self.PHLUDD.Display.width, self.PHLUDD.Display.height)

        #debug
        self.stream_mode = False
        self.fullscreen = True

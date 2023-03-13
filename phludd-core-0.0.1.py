from types import MappingProxyType
import tkinter as tk
from PIL import Image, ImageTk
import os
import numpy
import math
import random
import time
from gmail_handle import Gmail
import json
import threading
import platform
from weather import *
from location import *

lt = time.time()
api_retry = 60000

class Spinner:
    def __init__(self, canvas, filename, x, y):
        self.canvas = canvas
        im = Image.open(filename)
        seq = []
        try:
            while 1:
                seq.append(im.copy())
                im.seek(len(seq))
        except EOFError:
            pass
        try:
            self.delay = im.info['duration']
        except KeyError:
            self.delay = 100

        first = seq[0].convert('RGBA')
        self.frames = [ImageTk.PhotoImage(first)]

        self.spinner = canvas.create_image(x,y, anchor=tk.NW, image=self.frames[0])

        temp = seq[0]
        for image in seq[1:]:
            temp = image
            frame = temp.convert('RGBA')
            self.frames.append(ImageTk.PhotoImage(frame))

        self.idx = 0

        self.cancel = self.canvas.after(self.delay, self.play)

    def play(self):
        self.canvas.itemconfigure(self.spinner, image=self.frames[self.idx])
        self.idx += 1
        if self.idx == len(self.frames):
            self.idx = 0
        self.cancel = self.canvas.after(self.delay, self.play)

class Weather_Widget():
    global weather
    icon_map = MappingProxyType(
        {
            0 : 5,
            200 : 12,
            201 : 12,
            202 : 12,
            210 : 12,
            211 : 12,
            212 : 13,
            221 : 14,
            230 : 12,
            231 : 12,
            232 : 12,
            300 : 9,
            301 : 9,
            302 : 10,
            310 : 9,
            311 : 9,
            312 : 10,
            313 : 10,
            313 : 11,
            321 : 10,
            500 : 6,
            501 : 6,
            502 : 7,
            503 : 8,
            504 : 8,
            511 : 19,
            520 : 9,
            521 : 9,
            522 : 10,
            531 : 11,
            600 : 15,
            601 : 16,
            602 : 17,
            611 : 15,
            612 : 15,
            613 : 16,
            615 : 18,
            616 : 19,
            620 : 15,
            621 : 16,
            622 : 17,
            701 : 5,
            711 : 5,
            721 : 5,
            731 : 5,
            741 : 5,
            751 : 5,
            761 : 5,
            762 : 5,
            771 : 5,
            781 : 5,
            800 : 0,
            801 : 1,
            802 : 2,
            803 : 3,
            804 : 4
        }
    )
    def __init__(self, canvas, x, y):
        #weather.Current.city = "<City Name>"
        self.canvas = canvas
        self.border = canvas.create_rectangle(x-10, y-50, x+256, y+128, outline='gray')
        self.icon = canvas.create_image(x, y, anchor=tk.NW, image=img_weatherIcons[ type(self).icon_map[ weather.Current.id ] ])
        self.temp = canvas.create_text(x+133, y, anchor=tk.NW, fill="white", font=('Helvetica 40'), text=str(int(weather.Current.temp))+"°ᶜ")
        self.chill = canvas.create_text(x+133, y+50, anchor=tk.NW, fill="white", font=('Helvetica 10 bold'), text="feels like: " + str(int(weather.Current.chill))+"°ᶜ")
        self.cond = canvas.create_text(x+133, y+65, anchor=tk.NW, fill= "white", font=('Helvetica 20 bold'), text=weather.Current.condition)
        self.desc = canvas.create_text(x+133, y+90, anchor=tk.NW, fill="white", font=('Helvetica 10 bold'), text=weather.Current.description)
        self.city = canvas.create_text(x+128, y-30, anchor=tk.CENTER, fill="white", font=('Helvetica 20 bold'), text=weather.Current.city)

    def update(self):
        success = weather.Current.update()
        if success:
            #weather.Current.city = "<City Name>"
            self.canvas.itemconfigure(self.border, outline='gray')
            self.canvas.itemconfigure(self.icon, image=img_weatherIcons[ type(self).icon_map[ weather.Current.id ] ])
            self.canvas.itemconfigure(self.temp, text=str(int(weather.Current.temp))+"°ᶜ")
            self.canvas.itemconfigure(self.chill, text="feels like: " + str(int(weather.Current.chill))+"°ᶜ")
            self.canvas.itemconfigure(self.cond, text=weather.Current.condition)
            self.canvas.itemconfigure(self.desc, text=weather.Current.description)
            self.canvas.itemconfigure(self.city, fill='white', text=weather.Current.city)
        else:
            self.canvas.itemconfigure(self.border, outline='red')
            self.canvas.itemconfigure(self.city, fill='red', text="<An Error Occured>")
            
        canvas.after(300000, self.update)
        
def gmail_setup():
    global smtp
    if not isinstance(smtp, Gmail):
        smtp = Gmail()
    if not smtp.authorized:
        smtp.authorize()
    if smtp.service == None:
        smtp.build_service()

    if not smtp.isReady():
        print("Gmail Setup did not complete successfuly, trying again in 5min")
        root.after(api_retry, gmail_setup)
        
def location_update():
    lat, lon, success = loc.Get()
    if success:
        weather.setLoc(lat, lon)
        weatherWidget.update()
    else:
        canvas.after(api_retry, location_update)
    
def initialize():
    global smtp
    global settings
    global loading
    global canvas
    global img_fg
    global img_iris
    global img_weatherIcons
    global iris
    global fg
    global readout
    global root
    global recipients
    global apikeys
    global loc
    global weather
    global weatherWidget

    start = time.time()
    target_time = 15
    tasks = 36

    loadscreen.itemconfigure(status, text="Verifying Gmail Api authorization...")
    time.sleep((target_time - 3)/tasks)
    smtp = None
    gmail_setup()
    apikeys = {
        "googleMaps" : "",
        "openWeather" : ""
        }
    
    settings = {
        "Sensors" : {
            "S0": [True, 0, 0],
            "S1": [True, 0, 0],
            "S2": [True, 0, 0],
            "S3": [True, 0, 0],
            "S4": [True, 0, 0],
            "S5": [True, 0, 0],
            "S6": [True, 0, 0]
            },
        "SenseRate": 600,
        "TrigerThreshold": 0.5,
        "Email-Enable": False,
        "Email-Recipients": []
        }

    loadscreen.itemconfigure(status, text="Looking for file config.json...")
    time.sleep((target_time - 3)/tasks)
    if os.path.exists('config.json'):
        loadscreen.itemconfigure(status, text="Loading configuration from config.json...")
        time.sleep((target_time - 3)/tasks)
        file = open('config.json', 'r')
        settings = json.load(file)
    else:
        loadscreen.itemconfigure(status, text="NOT FOUND, creating configuration from defaults...")
        time.sleep((target_time - 3)/tasks)
        json_object = json.dumps(settings, indent=4)
        with open("config.json", "w") as outfile:
            outfile.write(json_object)

    loadscreen.itemconfigure(status, text="Looking for file api_keys.json...")
    time.sleep((target_time - 3)/tasks)
    if os.path.exists('credentials/api_keys.json'):
        loadscreen.itemconfigure(status, text="Loading API keys from api_keys.json...")
        time.sleep((target_time - 3)/tasks)
        file = open('credentials/api_keys.json', 'r')
        apikeys = json.load(file)
    else:
        loadscreen.itemconfigure(status, text="NOT FOUND, creating api_keys.json (weather features will be disabled)...")
        time.sleep((target_time - 3)/tasks)
        json_object = json.dumps(apikeys, indent=4)
        with open("credentials/api_keys.json", "w") as outfile:
            outfile.write(json_object)

    if settings["Email-Enable"]:
        loadscreen.itemconfigure(status, text="Generating Gmail recipient string...")
        time.sleep((target_time - 3)/tasks)
        recipients = ""
        for i in settings["Email-Recipients"]:
            recipients = recipients + i + ", "
        recipients = recipients[:len(recipients)-2]
        
    loadscreen.itemconfigure(status, text="Loading image ('assets/UI-Main.png')...")
    time.sleep((target_time - 3)/tasks)
    img_fg = ImageTk.PhotoImage(Image.open('assets/UI-Main.png'))
    loadscreen.itemconfigure(status, text="Loading image ('assets/iris.png')...")
    time.sleep((target_time - 3)/tasks)
    img_iris = ImageTk.PhotoImage(Image.open('assets/iris.png'))

    img_weatherIcons = []
    for i in range(1, 21):
        loadscreen.itemconfigure(status, text=f"Loading image ('assets/weather/{i:02d}.png')...")
        time.sleep((target_time - 3)/tasks)
        img_weatherIcons.append(ImageTk.PhotoImage(Image.open(f'assets/weather/{i:02d}.png')))

    loadscreen.itemconfigure(status, text="Building main system UI...")
    time.sleep((target_time - 3)/tasks)
    canvas = tk.Canvas(root, width=1920, height=1080, borderwidth=0, highlightthickness=0)
    
    iris = canvas.create_image(0,0, anchor=tk.NW, image=img_iris)
    fg = canvas.create_image(0,0, anchor=tk.NW, image=img_fg)
    readout = canvas.create_text(250,30, text="Status:  IDLE", anchor=tk.NW, fill="white", font=('Helvetica 40 bold'))

    loadscreen.itemconfigure(status, text="Initializing Location Services...")
    time.sleep((target_time - 3)/tasks)
    loc = Location(apikeys['googleMaps'])
    loadscreen.itemconfigure(status, text="Getting device current location...")
    time.sleep((target_time - 3)/tasks)
    lat, lon, success = loc.Get()
    
    loadscreen.itemconfigure(status, text="Initializing Weather Services...")
    time.sleep((target_time - 3)/tasks)
    weather = Weather(apikeys['openWeather'])
    loadscreen.itemconfigure(status, text="Updating local weather condition data...")
    time.sleep((target_time - 3)/tasks)
    
    weatherWidget = Weather_Widget(canvas, 10, 942)

    if success:
        weather.setLoc(lat, lon)
    else:
        canvas.after(api_retry, location_update)

    weatherWidget.update()

    while time.time() - start < target_time:
        loadscreen.itemconfigure(status, text=f"Looking cool ;D (Initialization will complete in {(target_time - (time.time() - start)):.2f}s )...")

    loadscreen.itemconfigure(status, text=f"Initializing Complete! ({(time.time() - start):.2f}s)...")
    time.sleep(1)
    loading = False
    root.quit()
    
#### Tkinter Setup ####
root = tk.Tk()
root.attributes("-fullscreen", True)
root.attributes("-topmost", True)
root.config(cursor="none")
loading = True
loadscreen = tk.Canvas(root, width=1920, height=1080, borderwidth=0, highlightthickness=0)
loadscreen.pack()

img_loading = ImageTk.PhotoImage(Image.open('assets/phludd.png'))
loading = loadscreen.create_image(0,0, anchor=tk.NW, image=img_loading)
status = loadscreen.create_text(960, 700, anchor=tk.CENTER, fill="gray", font=('Helvetica 20 bold'), text="Begining Initialization")

lspin = Spinner(loadscreen, 'assets/807.gif', 832, 750)

threading.Thread(target=initialize).start()
while loading: # unnecessary loop to make reading easier
    root.mainloop() # main thread enters Tk().mainloop() so that initializing thread can access Tk concurently

loadscreen.destroy()
canvas.pack()

#### Iris Idle Look ####
lookat = [0,0]
hold_time = random.randint(0,10)
start_time = time.time()
def idle_look(maxhold, speed):
    global hold_time
    global start_time
    pos = canvas.coords(iris)
    if lookat == pos:
        hold_time = random.uniform(0,maxhold)
        start_time = time.time()
        speed = random.randint(2,5)
        return True
    if (time.time() - start_time) < hold_time:
        return False
    mx = -((lookat[0] - pos[0]) // -speed) if (lookat[0] - pos[0]) > 0 else (lookat[0] - pos[0]) // speed
    my = -((lookat[1] - pos[1]) // -speed) if (lookat[1] - pos[1]) > 0 else (lookat[1] - pos[1]) // speed
    canvas.move(iris, (pos[0] + mx)-pos[0], (pos[1] + my)-pos[1])
    return False

def strhex(num):
    hx = str(hex(num))[2:]
    return hx if len(hx) > 1 else '0'+hx

def readSensors():
    global state
    global hold_time
    if state == 0:
        state = 1
        canvas.after(10000, readSensors)
    elif state == 1:
        select = random.randint(0,100)
        if select <= -1:
            state = 3
            alarm(1000, 1000)
            hold_time = 0
            if settings["Email-Enable"] == True:
                smtp.send_message("WARNING! Water level rising above acceptable boundary at sensor " + str(random.randint(0,6)), recipients)
        else:
            state = 0
            canvas.after((settings["SenseRate"]*1000), readSensors)

alarm_state = False
cycle = 0
def alarm(high_interval, low_interval, cycles=0):
    global alarm_state
    global cycle
    global cancel
    if state == 3 or state == 2:
        if not alarm_state:
            if state == 3: canvas.configure(bg='#FF0000')
            alarm_state = True
            print("Beep!")
            cancel = canvas.after(high_interval, alarm, high_interval, low_interval, cycles)
        else:
            if state == 3: canvas.configure(bg='#1E0000')
            alarm_state = False
            cycle += 1
            print("silent beep...")
            cancel = canvas.after(low_interval, alarm, high_interval, low_interval, cycles)
        if cycles != 0 and cycle == cycles:
            canvas.after_cancel(cancel)
            cycle = 0
    elif state == 0:
        canvas.after_cancel(cancel)
        cycle = 0
        alarm_state = False
        
def lbat_alarm():
    interval = int((1/6)*1000)
    alarm(interval, interval, 3)
    if state == 2:
        canvas.after(300000, lbat_alarm)
        
def silence(e):
    global state
    global hold_time
    if state == 3:
        state = 0
        canvas.after((settings["SenseRate"]*1000), readSensors)
    elif state == 0:
        hold_time = 0
        state = 3
        alarm(1000, 1000)
        canvas.after(6000, silence, None)
        if settings["Email-Enable"] == True:
            pass
            smtp.send_message("This is a test of the PHLUDD emergency notification system, if you are reading this everything is working as intended :)", recipients)

def t_topmost(e):
    root.attributes("-topmost", not root.attributes("-topmost"))
    print(root.attributes("-topmost"))

def low_bat_test(e):
    global state
    global hold_time
    if state == 0:
        state = 2
        hold_time = 0
        lbat_alarm()
    elif state == 2:
        state = 0

#### Key Binds ####
canvas.bind_all("<Double-1>", silence)
canvas.bind_all("<F12>", t_topmost)
canvas.bind_all("<F11>", low_bat_test)

canvas.after((settings["SenseRate"]*1000), readSensors)

#### Main Loop ####
state = 0
while True:
    if state == 0:
        canvas.configure(bg='#1E1E1E')
        canvas.itemconfigure(readout, text="Status:  IDLE")
        if idle_look(10, random.randint(2,5)):
            lookat = [random.randint(-200, 200), random.randint(-150,150)]
    elif state == 1:
        val = ((math.cos((time.time() - lt)*4)+1) / 2) * (255 - 30) + 30
        canvas.configure(bg='#1E1E'+strhex(int(val)))
        canvas.itemconfigure(readout, text="Status:  SENSING")
        if idle_look(10, random.randint(2,5)):
            lookat = [random.randint(-200, 200), random.randint(-150,150)]
    elif state == 2:
        val = ((math.cos((time.time() - lt)*4)+1) / 2) * (255 - 30) + 30
        canvas.configure(bg='#' + strhex(int(val)) + strhex(int(val)) + '1E')
        canvas.itemconfigure(readout, text="Status:  Battery Low")
        if idle_look(0.1, 2):
            lookat = [random.randint(-6, 6), random.randint(-6,6)]
    elif state == 3:
        canvas.itemconfigure(readout, text="Status:  !!ALERT!!")
        if idle_look(0.1, 2):
            lookat = [random.randint(-6, 6), random.randint(-6,6)]
    root.update()

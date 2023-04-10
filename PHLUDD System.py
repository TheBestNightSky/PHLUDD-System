import math
import pygame, sys
import time
import threading

pygame.init()

from lib.config import *
import lib.hardware as hardware
import lib.user_interface as ui
import lib.util as util
import lib.gmail_handle
import web.server as Server


def debug(config : Configuration):
    config.stream_mode = True
    config.fullscreen = False


# load Settings and API Keys
config = Configuration()
debug(config)

#server command registration for configuration commands
usage = "setConfig <json_string>"
description = "Loads new json object into phludd configuration and saves configuration to config.json"
Server.Command.register("setConfig", 10, config.update_from_string, usage, description)

usage = "getConfig"
description = "Requests the server to send the current configuration to the client"
Server.Command.register("getConfig", 10, config.get_json_string, usage, description)

#Create Screen
if config.fullscreen:
    screen = pygame.display.set_mode(config.PHLUDD.Display.resolution, pygame.FULLSCREEN)
else:
    screen = pygame.display.set_mode(config.PHLUDD.Display.resolution)

#Title and Icon
pygame.display.set_caption("PHLUDD System")
icon = pygame.image.load('assets/eye.png')
pygame.display.set_icon(icon)

#Loading Screen Assests
loading_bg = pygame.image.load('assets/phludd.png')
loading_bg = pygame.transform.scale(loading_bg, config.PHLUDD.Display.resolution)

spinner = util.GIF(screen, 555, 540, "assets/807.gif")
spinner.transform.scale(170,170)

running = False

def gmail_setup():
        global SMTP
        if not isinstance(SMTP, lib.gmail_handle.Gmail):
            SMTP = lib.gmail_handle.Gmail()
        if not SMTP.authorized:
            SMTP.authorize()
        if SMTP.service == None:
            SMTP.build_service()

        ready = SMTP.isReady()
        if not ready:
            print("Gmail Setup did not complete successfuly, trying again in 5min")
            pygame.time.set_timer(pygame.event.Event(api_retry, callback=gmail_setup), 300000)
        return ready


def initialize():
    global api_retry
    global SMTP
    global iris
    global main_ui_bg
    global weather
    global status
    global SettingsButton
    global SensorToggleButtons
    global EmailToggleButton
    global MapButton
    global ExitButton
    global sensor_array
    global sensor_icons
    global map_img
    global phludd
    global running

    sensors = config.PHLUDD.Sensors
    sensor_array = [sensors.S0, sensors.S1, sensors.S2, sensors.S3, sensors.S4, sensors.S5, sensors.S6]

    ## Gmail ##
    api_retry = pygame.event.custom_type()
    SMTP = None
    if config.PHLUDD.Email.enable:
        gmail_setup()

    ###### UI ######

    #### MAIN MENU ####

    # Iris
    iris = ui.Iris(screen, config)

    # BackGround
    bgImg = pygame.image.load('assets/UI-Main.png')
    bgImg = pygame.transform.scale(bgImg, config.PHLUDD.Display.resolution)
    main_ui_bg = ui.BackGround(screen, bgImg, (32,32,32))

    ## Weather Widget ##
    weather = ui.Weather_Widget(screen, 10, 532, config)
    weather.update()

    ## Status Display ##
    status = util.Text(screen, 120,30, font=pygame.font.Font("assets/fonts/Rounded Elegance.ttf", 30), text="Status:    Idle")

    #### SETTINGS MENU ####

    ## Setings Icon ##
    settings_icon = pygame.image.load('assets/settings_icon.png')
    SettingsButton = util.Button(screen, 1120, 10, settings_icon)

    ## Toggle Buttons ##
    SensorToggleButtons = []
    y = 100
    for sensor in sensor_array:
        SensorToggleButtons.append(util.SliderToggle(screen, 100,y, 46, 'assets/toggle-button.gif', config=sensor_array[sensor_array.index(sensor)], text=f"Sensor {sensor_array.index(sensor)}: "))
        y += 50

    EmailToggleButton = util.SliderToggle(screen, 500, 100, 46, 'assets/toggle-button.gif', config=config.PHLUDD.Email, text=f"Enabled Email Notifications: ")

    #### MAP MENU ####

    ## Map Icon ##
    map_icon = pygame.image.load('assets/map_icon.png')
    MapButton = util.Button(screen, 1120, 170, map_icon)

    ## Exit Icon ##
    exit_icon = pygame.image.load('assets/x.png')
    ExitButton = util.Button(screen, 1206, 10, exit_icon)

    ## Sensor Icons ##
    sensor_icon = pygame.image.load('assets/target.png')
    sensor_icons = []
    for sensor in sensor_array:
        sensor_icons.append(ui.Sensor_Icon(screen, sensor.pos.x, sensor.pos.y, sensor_icon, f"Sensor {sensor_array.index(sensor)}", sensor_array[sensor_array.index(sensor)]))

    ## Map ##
    map_img = pygame.image.load('assets/map/map.png')
    ###### END UI #######


    ###### PHLUDD Hardware ######
    phludd = hardware.Phludd(screen, main_ui_bg, iris, config)
    phludd.init()

    running = True

def ExitCleanup():
    global running
    running = False
    pygame.quit()
    hardware.GPIO.cleanup()
    Server.server_stop()

def loading():
    while not running:
        for event in pygame.event.get():
            ## System Events ##
            if event.type == pygame.QUIT:
                ExitCleanup()
                return

            ## Keyboard Events ##
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F4 and bool(event.mod & pygame.KMOD_ALT):
                    ExitCleanup()
                    return

            elif hasattr(event, "msg"):
                if event.msg == 'gif_update' or event.msg == "weather_update":
                    event.callback()


        screen.fill((0,0,0))
        screen.blit(loading_bg, (0,0))
        spinner.draw()

        pygame.display.update()

def map():
    click_start = 0
    click_target = None
    map_changed = False
    while running:
        
        for event in pygame.event.get():
            
            ## System Events ##
            if event.type == pygame.QUIT:
                ExitCleanup()
                return

            ## Keyboard Events ##
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F4 and bool(event.mod & pygame.KMOD_ALT):
                    ExitCleanup()
                    return

            ## Mouse / Touch Events ##
            elif event.type == pygame.MOUSEBUTTONUP:
                if ExitButton.clicked(event.pos):
                    if map_changed:
                        config.save()
                    iris.idle_look()
                    return
                elif click_target != None:
                    if time.time() - click_start >= 1 and click_target.move == False:
                        click_target.move = True
                        map_changed = True
                    else:
                        click_target.move = False
                        click_target = None

            elif event.type == pygame.MOUSEMOTION:
                for sensor in sensor_icons:
                    if sensor.move:
                        sensor.setPos(event.pos)

            elif event.type == pygame.MOUSEBUTTONDOWN:
                clicked = None
                for sensor in sensor_icons:
                    if sensor.clicked(event.pos):
                        clicked = sensor

                if click_target == None:
                    click_start = time.time()
                    click_target = clicked
            
            # UI events
            elif hasattr(event, "msg"):
                if event.msg == 'gif_update' or event.msg == "weather_update":
                    event.callback()

            ## Phludd hardware events ##
            elif event.type in phludd.events:
                phludd.event_handle(event)
                if event.type == phludd.phludd_sensor_read_event:
                    status.setText("Status:    Scanning...")
                elif event.type == phludd.phludd_alarm_clear_event:
                    for sensor in sensor_icons:
                        sensor.reset()
                elif event.type == phludd.phludd_idle_event:
                    status.setText("Status:    Idle")
                elif event.type == phludd.phludd_alarm_trigger_event:
                    for sensor in event.sensor_ids:
                        sensor_icons[sensor].trigger()

                    status.setText("Status:    !Flood Detected!")
                elif event.type == phludd.phludd_lbat_trigger_event:
                    status.setText("Status:    Battery Low!")

            ## API events ##
            elif event.type == api_retry:
                event.callback()

        screen.fill((0,0,0,0))
        screen.blit(map_img, (0,0))

        for sensor in sensor_array:
            if sensor.enable:
                sensor_icons[sensor_array.index(sensor)].draw()

        ExitButton.draw()

        pygame.display.update()


def settings():
    settings_changed = False
    while running:
        # Event Processing
        for event in pygame.event.get():
            ## System Events ##
            if event.type == pygame.QUIT:
                ExitCleanup()
                return

            ## Keyboard Events ##
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F4 and bool(event.mod & pygame.KMOD_ALT):
                    ExitCleanup()
                    return

            ## Mouse / Touch Events ##
            elif event.type == pygame.MOUSEBUTTONUP:
                if ExitButton.clicked(event.pos):
                    iris.idle_look()
                    if settings_changed:
                        if config.PHLUDD.Email.enable:
                            gmail_setup()
                        config.save()
                        settings_changed = False
                    return

                elif EmailToggleButton.clicked(event.pos):
                    EmailToggleButton.Toggle()
                    settings_changed = True

                else:
                    for Toggle in SensorToggleButtons:
                        if Toggle.clicked(event.pos):
                            Toggle.Toggle()
                            settings_changed = True
                            break


            elif hasattr(event, "msg"):
                if event.msg == 'gif_update' or event.msg == "weather_update":
                    event.callback()

            ## Phludd hardware events ##
            elif event.type in phludd.events:
                phludd.event_handle(event)
                if event.type == phludd.phludd_sensor_read_event:
                    status.setText("Status:    Scanning...")
                elif event.type == phludd.phludd_alarm_clear_event:
                    for sensor in sensor_icons:
                        sensor.reset()
                elif event.type == phludd.phludd_idle_event:
                    status.setText("Status:    Idle")
                    Server.alert_all("PHLUDD device has returned to an IDLE state")
                elif event.type == phludd.phludd_alarm_trigger_event:
                    for sensor in event.sensor_ids:
                        sensor_icons[sensor].trigger()
                    Server.alert_all("PHLUDD device has entered an ALARM state")

                    status.setText("Status:    !Flood Detected!")
                elif event.type == phludd.phludd_lbat_trigger_event:
                    status.setText("Status:    Battery Low!")
                    Server.alert_all("PHLUDD device has entered a LOW_BATTERY state")

            ## API events ##
            elif event.type == api_retry:
                event.callback()

        screen.fill((0,0,0))

        for Toggle in SensorToggleButtons:
            Toggle.draw()

        EmailToggleButton.draw()

        ExitButton.draw()
        pygame.display.update()


def main():
    while running:

        # Event Processing
        for event in pygame.event.get():

            ## System Events ##
            if event.type == pygame.QUIT:
                ExitCleanup()

            ## Keyboard Events ##
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F4 and bool(event.mod & pygame.KMOD_ALT):
                    ExitCleanup()

                elif event.key == pygame.K_F12:
                    phludd.alarm_test()

                elif event.key == pygame.K_F11:
                    e = pygame.event.post(pygame.event.Event(phludd.phludd_lbat_trigger_event))

                elif event.key == pygame.K_F10:
                    phludd.alarm_silence()

                elif event.key == pygame.K_m:
                    map()

            ## Mouse / Touch Events ##
            elif event.type == pygame.MOUSEBUTTONUP:
                if MapButton.clicked(event.pos):
                    map()
                elif SettingsButton.clicked(event.pos):
                    settings()
            
            ## UI Events ##
            elif event.type == iris.idle_look_event:
                iris.idle_look()

            elif hasattr(event, "msg"):
                if event.msg == 'gif_update' or event.msg == "weather_update":
                    event.callback()

            ## Phludd hardware events ##
            elif event.type in phludd.events:
                phludd.event_handle(event)
                if event.type == phludd.phludd_sensor_read_event:
                    status.setText("Status:    Scanning...")
                    Server.alert_all("PHLUDD device is polling water sensors for data")
                elif event.type == phludd.phludd_alarm_clear_event:
                    for sensor in sensor_icons:
                        sensor.reset()
                elif event.type == phludd.phludd_idle_event:
                    main_ui_bg.setColor((32, 32, 32))
                    status.setText("Status:    Idle")
                    Server.alert_all("PHLUDD device has returned to an IDLE state")
                elif event.type == phludd.phludd_alarm_trigger_event:
                    sensor_string = "        "
                    for sensor in event.sensor_ids:
                        sensor_icons[sensor].trigger()
                        sensor_string = sensor_string + "id: " + str(sensor) + " | lable: " + sensor_icons[sensor].lable.text + ",\n        "
                    sensor_string = sensor_string[:-10]
                    Server.alert_all("PHLUDD device has entered an ALARM state")
                    if config.PHLUDD.Email.enable and SMTP is not None:
                        if SMTP.isReady():
                            msg = f"PHLUDD System automated alert!\n\nWARNING!:\n        Water level rising above acceptable boundary!\n\nAlarm triggered by sensor(s):\n{sensor_string}"
                            SMTP.send_message(msg, config.PHLUDD.Email.recipient_string)

                    status.setText("Status:    !Flood Detected!")
                elif event.type == phludd.phludd_lbat_trigger_event:
                    status.setText("Status:    Battery Low!")
                    Server.alert_all("PHLUDD device has entered a LOW_BATTERY state")

            ## API events ##
            elif event.type == api_retry:
                event.callback()

        
        if not running:
            break

        ## BackGround Fill Fade for phludd hardware sensing/low bat states
        if phludd.state == phludd.STATE_SENSING:
            val = ((math.cos(run_timer.Peak()*4)+1) / 2) * (255 - 32) + 32
            main_ui_bg.setColor((32, 32, val))
        elif phludd.state == phludd.STATE_LOW_BAT:
            val = ((math.cos(run_timer.Peak()*4)+1) / 2) * (255 - 32) + 32
            main_ui_bg.setColor((val, val, 32))
        
        # Draw #
        main_ui_bg.clear()
        iris.draw()
        main_ui_bg.draw()
        status.draw()
        SettingsButton.draw()
        MapButton.draw()
        weather.draw()
        pygame.display.update()

run_timer = util.Timer()

spinner.init()
#initialize()
threading.Thread(target=initialize).start()
loading()

if running:
    spinner.halt()
    iris.idle_look()
    main()
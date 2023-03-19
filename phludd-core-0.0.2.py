import math
import pygame, sys
import time

pygame.init()

from lib.config import *
import lib.hardware as hardware
import lib.user_interface as ui
import lib.util as util



def debug(config : Configuration):
    config.stream_mode = True
    config.fullscreen = False


# load Settings and API Keys
config = Configuration()
debug(config)

## Gmail ##
api_retry = pygame.event.custom_type()
SMTP = None
def gmail_setup():
    global SMTP
    if not isinstance(SMTP, lib.gmail_handle.Gmail):
        SMTP = lib.gmail_handle.Gmail()
    if not SMTP.authorized:
        SMTP.authorize()
    if SMTP.service == None:
        SMTP.build_service()

    if not SMTP.isReady():
        print("Gmail Setup did not complete successfuly, trying again in 5min")
        pygame.time.set_timer(pygame.event.Event(api_retry, callback=gmail_setup), 300000)

gmail_setup()

#Create Screen
if config.fullscreen:
    screen = pygame.display.set_mode(config.PHLUDD.Display.resolution, pygame.FULLSCREEN)
else:
    screen = pygame.display.set_mode(config.PHLUDD.Display.resolution)

#Title and Icon
pygame.display.set_caption("PHLUDD System")
icon = pygame.image.load('assets/eye.png')
pygame.display.set_icon(icon)


###### UI ######
# Iris
iris = ui.Iris(screen, config)
iris.idle_look()

# BackGround
bgImg = pygame.image.load('assets/UI-Main.png')
bgImg = pygame.transform.scale(bgImg, config.PHLUDD.Display.resolution)
main_ui_bg = ui.BackGround(screen, bgImg, (32,32,32))

## Weather Widget ##
weather = ui.Weather_Widget(screen, 10, 532, config)
weather.update()

## Status Display ##
status = util.Text(screen, 120,30, font=pygame.font.Font("assets/fonts/Rounded Elegance.ttf", 30), text="Status:    Idle")

## Setings Icon ##
settings_icon = pygame.image.load('assets/settings_icon.png')
SettingsButton = util.Button(screen, 1120, 10, settings_icon)

## Map Icon ##
map_icon = pygame.image.load('assets/map_icon.png')
MapButton = util.Button(screen, 1120, 170, map_icon)

## Exit Icon ##
exit_icon = pygame.image.load('assets/x.png')
ExitButton = util.Button(screen, 1206, 10, exit_icon)

## Sensor Icons ##
sensors = config.PHLUDD.Sensors
sensor_array = [sensors.S0, sensors.S1, sensors.S2, sensors.S3, sensors.S4, sensors.S5, sensors.S6]
sensor_icon = pygame.image.load('assets/target.png')
sensor_icons = []
for sensor in sensor_array:
    if sensor.enable:
        sensor_icons.append(ui.Sensor_Icon(screen, sensor.pos.x, sensor.pos.y, sensor_icon, f"Sensor {sensor_array.index(sensor)}", sensor_array[sensor_array.index(sensor)]))

## Map ##
map_img = pygame.image.load('assets/map/map.png')
###### END UI #######


###### PHLUDD Hardware ######
phludd = hardware.Phludd(screen, main_ui_bg, iris, config)
phludd.init()


#Main Loop
running = True

run_timer = util.Timer()

def ExitCleanup():
    global running
    running = False
    pygame.quit()
    hardware.GPIO.cleanup()


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

            elif hasattr(event, "msg"):
                if event.msg == 'gif_update' or event.msg == "weather_update":
                    event.callback()

        screen.fill((0,0,0,0))
        screen.blit(map_img, (0,0))

        for icon in sensor_icons:
            icon.draw()

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
                    e = pygame.event.post(pygame.event.Event(phludd.phludd_alarm_trigger_event))
                    print("Post Alarm Norm Event: ", e)

                elif event.key == pygame.K_F11:
                    e = pygame.event.post(pygame.event.Event(phludd.phludd_lbat_trigger_event))
                    print("Post Alarm Lbat Event: ", e)

                elif event.key == pygame.K_F10:
                    phludd.alarm_silence()

                elif event.key == pygame.K_m:
                    map()

            ## Mouse / Touch Events ##
            elif event.type == pygame.MOUSEBUTTONUP:
                if MapButton.clicked(event.pos):
                    map()
                elif SettingsButton.clicked(event.pos):
                    pass

            ## Phludd hardware events ##
            elif event.type in phludd.events:
                phludd.event_handle(event)
                if event.type == phludd.phludd_sensor_read_event:
                    status.setText("Status:    Scanning...")
                elif event.type == phludd.phludd_alarm_clear_event:
                    for sensor in sensor_icons:
                        sensor.reset()
                elif event.type == phludd.phludd_idle_event:
                    main_ui_bg.setColor((32, 32, 32))
                    status.setText("Status:    Idle")
                elif event.type == phludd.phludd_alarm_trigger_event:
                    sensor_string = "        "
                    for sensor in event.sensor_ids:
                        sensor_icons[sensor].trigger()
                        sensor_string = sensor_string + "id: " + str(sensor) + " | lable: " + sensor_icons[sensor].lable.text + ",\n        "
                    sensor_string = sensor_string[:-10]
                    if config.PHLUDD.Email.enable and SMTP.isReady():
                        msg = f"PHLUDD System automated alert!\n\nWARNING!:\n        Water level rising above acceptable boundary!\n\nAlarm triggered by sensor(s):\n{sensor_string}"
                        SMTP.send_message(msg, config.PHLUDD.Email.recipient_string)

                    status.setText("Status:    !Flood Detected!")
                elif event.type == phludd.phludd_lbat_trigger_event:
                    status.setText("Status:    Battery Low!")
            

            
            ## UI Events ##
            elif event.type == iris.idle_look_event:
                iris.idle_look()

            elif hasattr(event, "msg"):
                if event.msg == 'gif_update' or event.msg == "weather_update":
                    event.callback()

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

main()
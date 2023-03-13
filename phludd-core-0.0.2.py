import math
import pygame, sys
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

spinner = util.GIF(screen, 832, 400, 'assets/807.gif')
spinner.init()
###### END UI #######


###### PHLUDD Hardware ######
phludd = hardware.Phludd(screen, main_ui_bg, iris, config)
phludd.init()


#Main Loop
running = True
state = 0
run_timer = util.Timer()
while running:

    # Event Processing
    for event in pygame.event.get():

        ## System Events ##
        if event.type == pygame.QUIT:
            running = False

        ## Keyboard Events ##
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_F4 and bool(event.mod & pygame.KMOD_ALT):
                pygame.quit()
                sys.exit()

            elif event.key == pygame.K_F12:
                e = pygame.event.post(pygame.event.Event(phludd.phludd_alarm_trigger_event))
                print("Post Alarm Norm Event: ", e)

            elif event.key == pygame.K_F11:
                e = pygame.event.post(pygame.event.Event(phludd.phludd_lbat_trigger_event))
                print("Post Alarm Lbat Event: ", e)

            elif event.key == pygame.K_F10:
                phludd.alarm_silence()

        ## Phludd hardware events ##
        elif event.type in phludd.events:
            phludd.event_handle(event)
            
        ## UI Events ##
        elif event.type == iris.idle_look_event:
            iris.idle_look()

        elif hasattr(event, "msg"):
            if event.msg == 'gif_update' or event.msg == "weather_update":
                event.callback()

        

    ## BackGround Fill Fade for phludd hardware sensing/low bat states
    if phludd.state == 1:
        val = ((math.cos(run_timer.Peak()*4)+1) / 2) * (255 - 32) + 32
        main_ui_bg.setColor((32, 32, val))
    elif phludd.state == 2:
        val = ((math.cos(run_timer.Peak()*4)+1) / 2) * (255 - 32) + 32
        main_ui_bg.setColor((val, val, 32))
        
    # Draw #
    main_ui_bg.clear()
    iris.draw()
    main_ui_bg.draw()
    weather.draw()
    spinner.draw()
    pygame.display.update()

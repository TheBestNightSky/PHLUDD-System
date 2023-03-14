from types import MappingProxyType
from urllib import request
import pygame
import random
import requests.exceptions

from lib.location import Location
from lib.weather import Weather
from lib.config import Configuration

from lib.util import Coords, Rect, Text


# Iris
class Iris:
    def __init__(self, surface, config):
        global screen_res
        self.idle_look_event = pygame.event.custom_type()
        self.Img = pygame.image.load('assets/iris.png')
        self.Img = pygame.transform.scale(self.Img, config.PHLUDD.Display.resolution)
        self.X = 0
        self.Y = 0
        self.surface = surface
        self.looklimit = Coords(200, 150)
        self.hold_time_range = [3000,5000]
        self.path = []
        
    def draw(self):
        self.surface.blit(self.Img, (self.X, self.Y))

    def calc_idle_look(self, speed, limitX, limitY):
        tx, ty = random.randint(-self.looklimit.x, self.looklimit.x), random.randint(-self.looklimit.y, self.looklimit.y)
        x, y = self.X, self.Y

        while (x, y) != (tx, ty):
            vx, vy = (tx - x), (ty - y)
            mx = -(vx // -speed) if vx > 0 else vx // speed
            my = -(vy // -speed) if vy > 0 else vy // speed 
            self.path.append((int(x+mx) , int(y+my)))
            x, y = self.path[-1]

    def idle_look(self):
        if not self.path:
            self.calc_idle_look(random.randint(2,5), 200, 150)
            pygame.time.set_timer(self.idle_look_event, random.randint(self.hold_time_range[0]+1, self.hold_time_range[1]), 1)
        else:
            self.X, self.Y = self.path.pop(0)
            pygame.time.set_timer(self.idle_look_event, 33, 1)



## BackGrounds ##
class BackGround:
    def __init__(self, surface, img, rgb=(0,0,0)):
        self.surface = surface
        self.img = img
        self.rgb = rgb

    def setColor(self, rgb):
        self.rgb = rgb

    def clear(self):
        self.surface.fill(self.rgb)
        
    def draw(self):
        self.surface.blit(self.img, (0,0))



## Weather Widget ##
class Weather_Widget():
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

    def __init__(self, surface : pygame.Surface, x : int, y : int, config : Configuration):
        self.update_event = pygame.event.custom_type()

        self.config = config

        self.img_weatherIcons = []
        for i in range(1, 21):
            self.img_weatherIcons.append(pygame.image.load(f'assets/weather/{i:02d}.png'))
            
        self.Loc = Location(config.apikeys.googleMaps)
        self.Weather = Weather(config.apikeys.openWeather)
        lat, lon, success = self.Loc.Get()
        if success:
            self.loc_valid = True
            self.Weather.setLoc(lat, lon)
        else:
            self.loc_valid = False

        self.surface = surface
        self.x = x
        self.y = y
        self.img = pygame.Surface((266, 178))
        self.border = Rect(self.img, 0, 0, 266, 178, color=(255,0,0), border_width=2)
        self.icon_pos = (3,40)
        self.icon = None

        self.city = Text(self.img, 20, 5, color=(255,0,0), font=pygame.font.Font("assets/fonts/DejaVuSerifCondensed-Bold.ttf", 31), text="<Error>")
        self.temp = Text(self.img, 131, 35, font=pygame.font.Font("assets/fonts/DejaVuSerifCondensed-Bold.ttf", 50), text="<Error>°ᶜ")
        self.chill = Text(self.img, 131, 85, font=pygame.font.Font("assets/fonts/DejaVuSerifCondensed-Bold.ttf", 16), text="feels like: <Error>°ᶜ")
        self.cond = Text(self.img, 131, 105, font=pygame.font.Font("assets/fonts/DejaVuSerifCondensed-Bold.ttf", 35), text="<Error>")
        self.desc = Text(self.img, 131, 137, font=pygame.font.Font("assets/fonts/DejaVuSerifCondensed-Bold.ttf", 20), text="<Error>")
        

    def update(self):
        if self.loc_valid:
            success = self.Weather.Current.update()
            if success:
                self.border.setColor((100, 100, 100))
                self.city.setColor((255,255,255))
                self.icon = self.img_weatherIcons[ type(self).icon_map[self.Weather.Current.id] ]
                
                if self.config.stream_mode:
                    self.city.setText("<City Hidden>")
                else:
                    self.city.setText(self.Weather.Current.city)
                self.temp.setText(str(int(self.Weather.Current.temp))+"°ᶜ")
                self.chill.setText("feels like: " + str(int(self.Weather.Current.chill))+"°ᶜ")
                self.cond.setText(self.Weather.Current.condition)
                self.desc.setText(self.Weather.Current.description)

            else:
                self.icon = self.img_weatherIcons[5]

                self.border.setColor((255, 0, 0))
                self.city.setColor((255,0,0))

                self.city.setText("<Error>")

        else:
            self.icon = self.img_weatherIcons[5]
            lat, lon, success = self.Loc.Get()
            if success:
                self.loc_valid = True
                self.Weather.setLoc(lat, lon)
                self.update()
                return
            else:
                self.loc_valid = False

        self.img.fill((0,0,0,0))

        self.img.blit(self.icon, self.icon_pos)
        self.temp.draw()
        self.chill.draw()
        self.cond.draw()
        self.desc.draw()
        self.city.draw()

        self.border.draw()
                
        pygame.time.set_timer(pygame.event.Event(self.update_event, msg="weather_update", callback=self.update), 300000)

        if not success:
            e = self.Loc.getLastError()
            if type(e) == requests.exceptions.ConnectionError:
                pygame.time.set_timer(pygame.event.Event(self.update_event, msg="weather_update", callback=self.update), 5000)

    def draw(self):
        self.surface.blit(self.img, (self.x, self.y))

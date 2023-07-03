from types import MappingProxyType
import pygame
import random
import requests.exceptions

from lib.location import Location
from lib.weather import Weather
from lib.config import Configuration

from lib.util import Coords, Rect, Text, GIF

# Map Sensor Icon
class Sensor_Icon:
    def __init__(self, surface, x, y, image, lable, config):
        self.surface = surface
        self.x = x
        self.y = y
        self.img = image
        self.lable = Text(self.surface, x+32, y, font=pygame.font.Font("assets/fonts/DejaVuSerifCondensed-Bold.ttf", 18), text=lable)
        self.triggered_animation = GIF(self.surface, self.x-16, self.y-16, 'assets/square-spinner.gif')
        self.highlight = Rect(self.surface, x, y, 32, 32, color=(0,10,255), border_width=2)
        self.config = config
        self.move = False
        self.triggered = False

    def draw(self):
        if self.move:
            self.highlight.draw()
        elif self.triggered:
            self.triggered_animation.draw()
        self.surface.blit(self.img, (self.x, self.y))
        self.lable.draw()

    def trigger(self):
        self.triggered = True
        self.triggered_animation.init()

    def reset(self):
        if self.triggered:
            self.triggered = False
            self.triggered_animation.halt()

    def clicked(self, pos):
        x, y = pos
        if self.x < x < self.x + self.img.get_width() and self.y < y < self.y + self.img.get_height():
            return True
        return False

    def setPos(self, pos):
        x, y = pos
        self.x, self.y = pos
        self.triggered_animation.x, self.triggered_animation.y = x-16, y-16
        self.highlight.x, self.highlight.y = pos
        self.lable.x, self.lable.y = x+32, y
        self.config.pos.x, self.config.pos.y = pos

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
        self.looklimit = Coords(
            int(config.PHLUDD.Display.resolution[0] * 0.10390625),
            int(config.PHLUDD.Display.resolution[1] * 0.13888889)
        )
        self.hold_time_range = [3000,5000]
        self.path = []
        
    def draw(self):
        self.surface.blit(self.Img, (self.X, self.Y))

    def calc_idle_look(self, speed):
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
            self.calc_idle_look(random.randint(2,5))
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
        self.buffer = pygame.Surface((300, 178))
        self.scale = (int(self.config.PHLUDD.Display.resolution[0] * 0.234375), int(self.config.PHLUDD.Display.resolution[1] * 0.24722222))
        self.border = Rect(self.buffer, 0, 0, 300, 178, color=(255,0,0), border_width=2)
        self.icon_pos = (3,40)
        self.icon = None

        self.city = Text(self.buffer, 20, 5, color=(255,0,0), font=pygame.font.Font("assets/fonts/DejaVuSerifCondensed-Bold.ttf", 31), text="<Error>")
        self.temp = Text(self.buffer, 131, 35, font=pygame.font.Font("assets/fonts/DejaVuSerifCondensed-Bold.ttf", 50), text="<Error>°ᶜ")
        self.chill = Text(self.buffer, 131, 85, font=pygame.font.Font("assets/fonts/DejaVuSerifCondensed-Bold.ttf", 16), text="feels like: <Error>°ᶜ")
        self.cond = Text(self.buffer, 131, 105, font=pygame.font.Font("assets/fonts/DejaVuSerifCondensed-Bold.ttf", 35), text="<Error>")
        self.desc = Text(self.buffer, 131, 137, font=pygame.font.Font("assets/fonts/DejaVuSerifCondensed-Bold.ttf", 20), text="<Error>")
        

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

        self.buffer.fill((0,0,0,0))

        self.buffer.blit(self.icon, self.icon_pos)
        self.temp.draw()
        self.chill.draw()
        self.cond.draw()
        self.desc.draw()
        self.city.draw()

        self.border.draw()

        self.img = pygame.transform.scale(self.buffer, self.scale)

        pygame.time.set_timer(pygame.event.Event(self.update_event, msg="weather_update", callback=self.update), 300000)

        if not success:
            e = self.Loc.getLastError()
            if type(e) == requests.exceptions.ConnectionError:
                pygame.time.set_timer(pygame.event.Event(self.update_event, msg="weather_update", callback=self.update), 5000)

    def clicked(self, pos):
        x, y = pos
        if self.x < x < self.x + self.img.get_width() and self.y < y < self.y + self.img.get_height():
            return True
        return False

    def draw(self):
        self.surface.blit(self.img, (self.x, self.y))

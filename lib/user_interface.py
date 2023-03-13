from types import MappingProxyType
import pygame
import random

from lib.util import Coords, Rect

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

    def __init__(self, surface, x, y):
        self.img_weatherIcons = []
        for i in range(1, 21):
            self.img_weatherIcons.append(pygame.image.load(f'assets/weather/{i:02d}.png'))
            
        self.surface = surface
        self.x = x
        self.y = y
        self.img = pygame.Surface((266, 178))
        self.border = Rect(self.img, 0, 0, 266, 178, color=(100,100,100), border_width=2)

    def update(self):
        self.img.fill((0,0,0,0))
        self.border.draw()

    def draw(self):
        self.surface.blit(self.img, (self.x, self.y))

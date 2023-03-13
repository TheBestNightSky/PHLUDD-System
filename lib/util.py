import pygame
import time
from PIL import Image
## Util ##

class Dict2Class(object):
    def __init__(self, dict_obj):

        
        for key in dict_obj:
            if type(dict_obj[key]) == dict:
                atr = Dict2Class(dict_obj[key])
            else:
                atr = dict_obj[key]
            setattr(self, key, atr)
            
class Coords:
    def __init__(self, x, y, z=0):
        self.x = x
        self.y = y
        self.z = z

class Timer:
    def __init__(self):
        self.time = time.time()

    def Mark(self):
        delta = time.time() - self.time
        self.time = time.time()
        return delta

    def Peak(self):
        delta = time.time() - self.time
        return delta

class Text:
    def __init__(self, surface, x, y, color=(255,255,255), font=pygame.font.SysFont(None, 48), text="<Text>"):
        self.surface = surface
        self.x = x
        self.y = y
        self.color = color
        self.font = font
        self.text = text
        self.img = self.font.render(self.text, True, self.color)

    def setText(self, text):
        self.text = text
        self.img = self.font.render(self.text, True, self.color)

    def setColor(self, color):
        self.color = color
        self.img = self.font.render(self.text, True, self.color)

    def setFont(self, font):
        self.font = font
        self.img = self.font.render(self.text, True, self.color)

    def draw(self):
        self.surface.blit(self.img, (self.x, self.y))

class Rect:
    def __init__(self, surface, x, y, width, height, color=(0,0,0), border_width=5, fill=False):
        self.surface = surface
        self.img = pygame.Surface((width, height), pygame.SRCALPHA)
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.color = color
        self.border_width = border_width
        self.fill = fill
        self._update()

    def setColor(color):
        self.color = color
        self._update()

    def _update(self):
        self.img.fill(self.color)

        if not self.fill:
            self.img.fill((0,0,0,0), rect=(self.border_width, self.border_width, self.width-(self.border_width * 2), self.height-(self.border_width * 2)))

    def draw(self):
        self.surface.blit(self.img, (self.x, self.y))

class GIF:
    recycle = {}
    def __init__(self, surface, x, y, filename):
        self.surface = surface
        self.x = x
        self.y = y

        im = Image.open(filename)
        seq = []
        try:
            while 1:
                seq.append(im.copy().convert('RGBA'))
                im.seek(len(seq))
        except EOFError:
            pass
        try:
            self.delay = im.info['duration']
        except KeyError:
            self.delay = 100


        self.frames = []

        for image in seq:
            self.frames.append(pygame.image.fromstring(image.tobytes(), image.size, image.mode))

        self.Img = self.frames[0]
        self.idx = 0

    def reserve_id(self):
        found = False
        for key in type(self).recycle:
            if type(self).recycle[key] == False:
                self.update_event = key
                type(self).recycle[key] = True
                found = True
                break
        if not found:
            self.update_event = pygame.event.custom_type()
            type(self).recycle[self.update_event] = True

    def release_id(self):
        type(self).recycle[self.update_event] = False
        
    def init(self):
        self.reserve_id()
        pygame.time.set_timer(pygame.event.Event(self.update_event, msg="gif_update", callback=self.next_frame), self.delay)

    def halt(self):
        pygame.time.set_timer(pygame.event.Event(self.update_event, msg="gif_update", callback=self.play), 0)
        self.release_id()

    def next_frame(self):
        self.Img = self.frames[self.idx]
        self.idx += 1
        if self.idx == len(self.frames):
            self.idx = 0
        pygame.time.set_timer(pygame.event.Event(self.update_event, msg="gif_update", callback=self.next_frame), self.delay)

    def draw(self):
        self.surface.blit(self.Img, (self.x, self.y))
        













from re import L
import pygame
import time
from PIL import Image
import threading
import psutil
import subprocess
## Util ##


## Utility used to define class instance functions inside a seperate namespace
## while maintaining access to parent methods/atributes
##
## Usage:
##     Define the desired namespace as a nested class that inherits from namespace
##     Define functions inside that namespace
##     In parent class __init__ call NameSpace(self)
class NameSpace:
    def __init__(self, parent):
        if type(self) != NameSpace:
            #this makes is so that functions defined in the nested class
            #will get passed a referance to the parent class in the self argument
            #instead of a pointer to itself when called
            self.__dict__ = parent.__dict__
        else:
            atrs = vars(type(parent))
            for obj in atrs:
                if type(atrs[obj]) == type and issubclass(atrs[obj], NameSpace):
                    ## asigns nested classes that inherit from namespace as
                    ## class atributes to the parent class and instanciates them with parent obj
                    setattr(parent, atrs[obj].__name__, atrs[obj](parent))
        

## Makes things ugly on the inside so they can be pretty on the outside :3 
##########################################

def Is_Process(processName):
    '''
    Check if there is any running process that contains the given name processName.
    '''
    #Iterate over the all the running process
    for proc in psutil.process_iter():
        try:
            # Check if process name contains the given name string.
            if processName.lower() in proc.name().lower():
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return False;

def Watchdog():
    if not Is_Process("phludd-watchdog"):
        subprocess.run("python", "watchdog.py")
    else:
        pass


class Dict2Class(object):
    def __init__(self, dict_obj):

        
        for key in dict_obj:
            if type(dict_obj[key]) == dict:
                atr = Dict2Class(dict_obj[key])
            else:
                atr = dict_obj[key]
            setattr(self, key, atr)

    def ToDict(self):
        node_dict = vars(self).copy()
        
        for key in node_dict:
            if type(node_dict[key]) == type(self):
                node_dict[key] = node_dict[key].ToDict()

        return node_dict

    def reset(self, dict_obj):
        self.__init__(dict_obj)
            
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

    def setColor(self, color):
        self.color = color
        self._update()

    def _update(self):
        self.img.fill(self.color)

        if not self.fill:
            self.img.fill((0,0,0,0), rect=(self.border_width, self.border_width, self.width-(self.border_width * 2), self.height-(self.border_width * 2)))

    def draw(self):
        self.surface.blit(self.img, (self.x, self.y))


class Button:
    def __init__(self, surface, x, y, image):
        self.surface = surface
        self.x = x
        self.y = y
        self.img = image

    def draw(self):
        self.surface.blit(self.img, (self.x, self.y))

    def clicked(self, pos):
        x, y = pos
        if self.x < x < self.x + self.img.get_width() and self.y < y < self.y + self.img.get_height():
            return True
        return False


class SliderToggle(Button):
    def __init__(self, surface, x, y, true_frame, file, start_state=False, text="<Text>", config=None, active=False):
        self.surface = surface
        self.x = x
        self.y = y
        self.true_frame = true_frame
        self.lable = Text(self.surface, self.x, self.y, text=text)
        self.gif = GIF(self.surface, 0, 0, file)
        self.gif.x, self.gif.y = self.x + self.lable.img.get_width(), self.y - (self.gif.Img.get_height() // 2.5)

        self.active = active
        
        if config == None:
            self.state = start_state
        else:
            self.state = config.enable
            
        self.config = config

        if self.state:
            self.gif.set_frame(self.true_frame)
        

    def Toggle(self):
        if self.gif.update_event is None:
            self.state = not self.state
            if self.config is not None:
                self.config.enable = self.state
            self.gif.init()
            self.gif.next_frame()

    def setState(self, state: bool):
        if self.state != state:
            if self.active == True:
                self.Toggle()
            else:
                self.state = state
                if self.state:
                    self.gif.set_frame(self.true_frame)
                else:
                    self.gif.set_frame(0)

    def draw(self):
        self.lable.draw()
        self.gif.draw()
        if self.gif.idx == self.true_frame or self.gif.idx == 0 and self.gif.update_event is not None:
            self.gif.halt()

    def clicked(self, pos):
        x, y = pos
        if self.gif.x < x < self.gif.x + self.gif.Img.get_width() and self.lable.y < y < self.lable.y + self.lable.img.get_height():
            return True
        return False



class GIF:
    recycle = {}
    cache = {}
    gif_lock = threading.Lock()

    def __init__(self, surface, x, y, filename):
        self.surface = surface
        self.update_event = None
        self.x = x
        self.y = y
        self.filename = filename
        self.cache_id = filename
        
        if self.filename not in GIF.cache:
            self._load(self.filename)

        self.Img, self.delay = GIF.cache[self.cache_id][0]
        self.idx = 0

        ## namespace stuff
        #self.transform = GIF.transform(self)
        NameSpace(self)

    ## Internal Functions ##
    def _load(self, filename):
        ## Hacky BS to get information from gif file that PIL dosnt read >:C ##
        ## NOTE: turns out it does read it, the methods to get the info are just completely undocumented >:C
        frame_data = []
        with open(filename, "rb") as file:
            if file.read(3).decode('ISO 8859-1') != "GIF":
                raise Exception("File is not a GIF!")

            while (byte := file.read(1)):
                if ord(byte) == 0x21: #If byte is Extension Introducer
                    if ord(file.read(1)) == 0xf9: #And next byte marks block as Graphic Control Label
                        if ord(file.read(1)) == 0x04: #And block size is 4
                            packed = ord(file.read(1)) #get packed fields (Reserved: 3bits, Disposal Method: 3bits, User Input Flag: 1bit, Transparent Color Flag: 1bit)
                            replace = not bool(packed & 0b00000100) #Mask least significant bit of Disposal Method as no one uses methods other than 1 and 2 (replace or combine)
                            transparent = bool(packed & 0b00000001) #Unused for now but may be usefull to know
                            frame_data.append({"is_replace": replace, "is_transparent": transparent, "delay": file.read(2), "transparency_index" : ord(file.read(1))})
            file.close()
        ## End of stuff you shouldnt even try to read

        im = Image.open(filename)
        seq = []
        try:
            while 1:
                seq.append(im.copy().convert("RGBA"))
                im.seek(len(seq))
        except EOFError:
            pass

        GIF.cache[filename] = []
        buffer = pygame.Surface(seq[0].size, pygame.SRCALPHA)
        for image in seq:
            dispose = frame_data[seq.index(image)]["is_replace"]
            if dispose:
                buffer.fill((0,0,0,0))
            buffer.blit(pygame.image.fromstring(image.tobytes(), image.size, image.mode), (0,0))
            GIF.cache[filename].append((buffer.copy(), ord(frame_data[seq.index(image)]["delay"][:1]) * 10))


    def _reserve_id(self):
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

    def _release_id(self):
        type(self).recycle[self.update_event] = False
        self.update_event = None
    
    ## External Functions ##
    def init(self):
        with GIF.gif_lock:
            self._reserve_id()
            pygame.time.set_timer(pygame.event.Event(self.update_event, msg="gif_update", callback=self.next_frame), GIF.cache[self.filename][self.idx][1])

    def halt(self):
        with GIF.gif_lock:
            if self.update_event is not None:
                pygame.time.set_timer(pygame.event.Event(self.update_event, msg="gif_update", callback=self.next_frame), 0)
                self._release_id()

    def set_frame(self, index):
        with GIF.gif_lock:
            self.idx = index
            self.Img = GIF.cache[self.cache_id][self.idx][0]

    def next_frame(self):
        with GIF.gif_lock:
            if self.update_event != None:
                self.Img, delay = GIF.cache[self.cache_id][self.idx]
                self.idx += 1
                if self.idx == len(GIF.cache[self.cache_id]):
                    self.idx = 0
                pygame.time.set_timer(pygame.event.Event(self.update_event, msg="gif_update", callback=self.next_frame), delay)
            else:
                print("Tried to update halted gif!")


    class transform(NameSpace):

        def scale(self, newX, newY):
            with GIF.gif_lock:
                self.cache_id = self.filename + f" Scaled: {newX}x{newY}"
                if self.cache_id not in GIF.cache:
                    GIF.cache[self.filename + f" Scaled: {newX}x{newY}"] = []

                    for i in range(0, len(GIF.cache[self.filename])):
                        GIF.cache[self.filename + f" Scaled: {newX}x{newY}"].append( (pygame.transform.scale(GIF.cache[self.filename][i][0], (newX, newY)), GIF.cache[self.filename][i][1]))
            

    def draw(self):
        self.surface.blit(self.Img, (self.x, self.y))
        













import random
import pygame

###### PHLUDD HARDWARE ######
class Phludd:
    def __init__(self, surface, ui_bg, iris, config):
        # event stuff
        self.phludd_alarm_event = pygame.event.custom_type()
        self.phludd_alarm_trigger_event = pygame.event.custom_type()
        self.phludd_lbat_trigger_event = pygame.event.custom_type()
        self.phludd_alarm_clear_event = pygame.event.custom_type()
        self.phludd_sensor_read_event = pygame.event.custom_type()

        self.events = [
            self.phludd_alarm_event,
            self.phludd_alarm_trigger_event,
            self.phludd_lbat_trigger_event,
            self.phludd_alarm_clear_event,
            self.phludd_sensor_read_event
        ]

            
        # local stuff
        self.state = 0
        self.alarm_state = False
        self.cycle = 0
        self.ui_bg = ui_bg
        self.iris = iris
        self.poll_rate = config.PHLUDD.Sensors.poll_rate * 1000

    def event_handle(self, event):
        ## Phludd Hardware Events ##
        if event.type == self.phludd_alarm_event:
            if self.state == 3:
                self.alarm_norm()
            elif self.state == 2:
                self.alarm_lbat()

        elif event.type == self.phludd_sensor_read_event:
            self.read_sensors()

        elif event.type == self.phludd_alarm_trigger_event:
            self.iris.looklimit.x, self.iris.looklimit.y = 6, 6
            self.iris.hold_time_range = [0,100]
            self.iris.path = []
            self.iris.idle_look()
            self.state = 3
            self.alarm_norm()

        elif event.type == self.phludd_lbat_trigger_event:
            if self.state == 0:
                self.iris.looklimit.x, self.iris.looklimit.y = 6, 6
                self.iris.hold_time_range = [0,100]
                self.iris.idle_look()
            self.state = 2
            self.alarm_lbat()

        elif event.type == self.phludd_alarm_clear_event:
            self.iris.looklimit.x, self.iris.looklimit.y = 200, 150
            self.iris.hold_time_range = [3000,5000]
            self.iris.path = []
            self.iris.idle_look()
            self.ui_bg.setColor((32,32,32))

    def init(self):
        pygame.time.set_timer(self.phludd_sensor_read_event, self.poll_rate)
        
    def alarm_handle(self, high_interval, low_interval, cycles=0):
        if self.state == 3 or self.state == 2:
            if not self.alarm_state:
                self.alarm_state = True
                if self.state == 3: self.ui_bg.setColor((255, 0, 0))
                print("Beep!")
                pygame.time.set_timer(self.phludd_alarm_event, high_interval, 1)
            else:
                self.alarm_state = False
                if self.state == 3: self.ui_bg.setColor((32, 32, 32))
                self.cycle += 1
                print("not Beep!")
                pygame.time.set_timer(self.phludd_alarm_event, low_interval, 1)
            if cycles != 0 and self.cycle == cycles:
                print("Alarm Cycle End")
                pygame.time.set_timer(self.phludd_alarm_event, 0)
                self.alarm_state = False
                self.cycle = 0

    def alarm_silence(self):
        pygame.time.set_timer(self.phludd_alarm_event, 0)
        pygame.time.set_timer(self.phludd_lbat_trigger_event, 0)
        e = pygame.event.post(pygame.event.Event(self.phludd_alarm_clear_event))
        self.cycle = 0
        self.state = 0
        self.alarm_state = False

    def alarm_test(self):
        self.state = 3
        self.cycle = 0
        self.alarm_handle(1, 1)

    def alarm_lbat(self):
        interval = int((1/6)*1000)
        self.alarm_handle(interval, interval, 3)
        if self.state == 2:
            pygame.time.set_timer(self.phludd_lbat_trigger_event, 300000)

    def alarm_norm(self):
        self.alarm_handle(1000, 1000)

    def read_sensors(self):
        if self.state == 0:
            self.state = 1
            pygame.time.set_timer(self.phludd_sensor_read_event, 10000)
        elif self.state == 1:
            select = random.randint(0,100)
            if select <= 10:
                e = pygame.event.post(pygame.event.Event(self.phludd_alarm_trigger_event))
            else:
                self.state = 0
                self.ui_bg.setColor((32, 32, 32))
                pygame.time.set_timer(self.phludd_sensor_read_event, self.poll_rate)
        else:
            pygame.time.set_timer(self.phludd_sensor_read_event, self.poll_rate)

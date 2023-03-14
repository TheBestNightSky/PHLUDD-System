import random
import pygame
import collections
from lib.RPi import GPIO
from lib.ADC import MCP

## GPIO / ADC setup ##
GPIO_ALARM = 18
GPIO_SENSOR_ENABLE = 17

GPIO.setmode(GPIO.BCM)

GPIO.setup(GPIO_ALARM, GPIO.OUT)
GPIO.setup(GPIO_SENSOR_ENABLE, GPIO.OUT)

MCP.newADC()

###### PHLUDD HARDWARE ######
class Phludd:
    def __init__(self, surface, ui_bg, iris, config):
        # event stuff
        self.phludd_idle_event = pygame.event.custom_type()
        self.phludd_alarm_event = pygame.event.custom_type()
        self.phludd_alarm_trigger_event = pygame.event.custom_type()
        self.phludd_bat_check_event = pygame.event.custom_type()
        self.phludd_lbat_trigger_event = pygame.event.custom_type()
        self.phludd_alarm_clear_event = pygame.event.custom_type()
        self.phludd_sensor_read_event = pygame.event.custom_type()
        self.phludd_sensor_finish_event = pygame.event.custom_type()

        self.events = [
            self.phludd_idle_event,
            self.phludd_alarm_event,
            self.phludd_alarm_trigger_event,
            self.phludd_lbat_trigger_event,
            self.phludd_bat_check_event,
            self.phludd_alarm_clear_event,
            self.phludd_sensor_read_event,
            self.phludd_sensor_finish_event
        ]

        ## State Constants ##
        self.STATE_IDLE = 0
        self.STATE_SENSING = 1
        self.STATE_LOW_BAT = 2
        self.STATE_ALARM = 3

        # local stuff
        self.state = self.STATE_IDLE
        self.prev_state = self.STATE_IDLE
        self.alarm_state = False
        self.cycle = 0
        self.ui_bg = ui_bg
        self.iris = iris
        self.config = config
        self.poll_rate = config.PHLUDD.Sensors.poll_rate * 1000

        self.bat_data = collections.deque(maxlen=200)


    def event_handle(self, event):
        ## Phludd Hardware Events ##
        if event.type == self.phludd_alarm_event:
            if self.state == self.STATE_ALARM:
                self.alarm_norm()
            elif self.state == self.STATE_LOW_BAT:
                self.alarm_lbat()

        elif event.type == self.phludd_sensor_read_event:
            self.read_sensors()

        elif event.type == self.phludd_sensor_finish_event:
            if self.prev_state == self.STATE_IDLE:
                self.state = self.STATE_IDLE
                pygame.event.post(pygame.event.Event(self.phludd_idle_event))
            elif self.prev_state == self.STATE_LOW_BAT:
                pygame.event.post(pygame.event.Event(self.phludd_lbat_trigger_event))

        elif event.type == self.phludd_idle_event:
            pygame.time.set_timer(self.phludd_sensor_read_event, self.poll_rate)

        elif event.type == self.phludd_alarm_trigger_event:
            if self.state == self.STATE_LOW_BAT:
                self.alarm_silence()
            self.iris.looklimit.x, self.iris.looklimit.y = 6, 6
            self.iris.hold_time_range = [0,100]
            self.iris.path = []
            self.iris.idle_look()
            self.state = self.STATE_ALARM
            self.alarm_norm()

        elif event.type == self.phludd_bat_check_event:
            self.bat_data.append((MCP.read_voltage(7)/(5.9/(10+5.9)))/0.43)
            if self.state != self.STATE_LOW_BAT and self.state != self.STATE_SENSING:
                if len(self.bat_data) == 200 and sum(self.bat_data)/len(self.bat_data) <= 7:
                    pygame.event.post(pygame.event.Event(self.phludd_lbat_trigger_event))

        elif event.type == self.phludd_lbat_trigger_event:
            if self.state == self.STATE_IDLE:
                self.iris.looklimit.x, self.iris.looklimit.y = 6, 6
                self.iris.hold_time_range = [0,100]
                self.iris.idle_look()
            self.state = self.STATE_LOW_BAT
            self.alarm_lbat()

        elif event.type == self.phludd_alarm_clear_event:
            self.iris.looklimit.x, self.iris.looklimit.y = 200, 150
            self.iris.hold_time_range = [3000,5000]
            self.iris.path = []
            self.iris.idle_look()
            self.ui_bg.setColor((32,32,32))
            pygame.event.post(pygame.event.Event(self.phludd_idle_event))


    def init(self):
        pygame.time.set_timer(self.phludd_sensor_read_event, self.poll_rate)
        pygame.time.set_timer(self.phludd_bat_check_event, 500)

        
    def alarm_handle(self, high_interval, low_interval, cycles=0):
        if self.state == self.STATE_ALARM or self.state == self.STATE_LOW_BAT:
            if not self.alarm_state:
                self.alarm_state = True
                if self.state == self.STATE_ALARM: self.ui_bg.setColor((255, 0, 0))
                GPIO.output(GPIO_ALARM, GPIO.HIGH)
                print("Beep!")
                pygame.time.set_timer(self.phludd_alarm_event, high_interval, 1)
            else:
                self.alarm_state = False
                if self.state == self.STATE_ALARM: self.ui_bg.setColor((32, 32, 32))
                self.cycle += 1
                GPIO.output(GPIO_ALARM, GPIO.LOW)
                print("not Beep!")
                pygame.time.set_timer(self.phludd_alarm_event, low_interval, 1)
            if cycles != 0 and self.cycle == cycles:
                print("Alarm Cycle End")
                pygame.time.set_timer(self.phludd_alarm_event, 0)
                self.alarm_state = False
                GPIO.output(GPIO_ALARM, GPIO.LOW)
                self.cycle = 0


    def alarm_silence(self):
        if self.state == self.STATE_LOW_BAT or self.state == self.STATE_ALARM:
            pygame.time.set_timer(self.phludd_alarm_event, 0)
            pygame.time.set_timer(self.phludd_lbat_trigger_event, 0)
            self.bat_data.clear()
            e = pygame.event.post(pygame.event.Event(self.phludd_alarm_clear_event))
            self.cycle = 0
            self.state = self.STATE_IDLE
            self.prev_state = 0
            self.alarm_state = False
            GPIO.output(GPIO_ALARM, GPIO.LOW)


    def alarm_test(self):
        self.state = self.STATE_ALARM
        self.cycle = 0
        self.alarm_handle(1, 1)


    def alarm_lbat(self):
        interval = int((1/6)*1000)
        self.alarm_handle(interval, interval, 3)

        if self.state == self.STATE_LOW_BAT:
            pygame.time.set_timer(self.phludd_lbat_trigger_event, 300000)


    def alarm_norm(self):
        self.alarm_handle(1000, 1000)

    def setState(self, state : int):
        self.prev_state = self.state + 0
        self.state = state

    def read_sensors(self):
        if self.state == self.STATE_IDLE or self.state == self.STATE_LOW_BAT:
            self.setState(self.STATE_SENSING)
            GPIO.output(GPIO_SENSOR_ENABLE, GPIO.HIGH)
            pygame.time.set_timer(self.phludd_sensor_read_event, 10000, 1)
        
        elif self.state == self.STATE_SENSING:
            #select = random.randint(0,100)
            #if select <= 10:
            #    e = pygame.event.post(pygame.event.Event(self.phludd_alarm_trigger_event))
            #else:
            #    pygame.time.set_timer(self.phludd_sensor_read_event, self.poll_rate)
            #    pygame.event.post(pygame.event.Event(self.phludd_sensor_finish_event))
            sens_map = [self.config.PHLUDD.Sensors.S0, self.config.PHLUDD.Sensors.S1, self.config.PHLUDD.Sensors.S2, self.config.PHLUDD.Sensors.S3, self.config.PHLUDD.Sensors.S4, self.config.PHLUDD.Sensors.S5, self.config.PHLUDD.Sensors.S6]
            trig = []
            for i in range(0, 7):
                voltage = MCP.read_voltage(i)
                if sens_map[i].enable and voltage >= self.config.PHLUDD.Sensors.voltage_threshold:
                    trig.append(True)
                else:
                    trig.append(False)

            if any(trig):
                e = pygame.event.post(pygame.event.Event(self.phludd_alarm_trigger_event))
            else:
                pygame.time.set_timer(self.phludd_sensor_read_event, self.poll_rate)
                pygame.event.post(pygame.event.Event(self.phludd_sensor_finish_event))

            GPIO.output(GPIO_SENSOR_ENABLE, GPIO.LOW)

        else:
            pygame.time.set_timer(self.phludd_sensor_read_event, self.poll_rate)

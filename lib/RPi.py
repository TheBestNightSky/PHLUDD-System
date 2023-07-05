## Development Wrapper for RPi.GPIO
## Simulate GPIO interaction when running outside of Rasberry Pi

import lib.logging as Logging

Log = Logging.Log("logs/phludd_log.log")

try:
    import RPi.GPIO as _GPIO
    sim = False

except ImportError as e:
    import random
    Log.log(Log.DEBUG, "RPI.GPIO is missing!! Running in simulation mode!")
    sim = True


if not sim:
    GPIO = _GPIO

else:
    class GPIO:
        BCM = 11
        BOARD = 10
        BOTH = 33
        FALLING = 32
        HARD_PWM = 43
        HIGH = 1
        I2C = 42
        IN = 1
        LOW = 0
        OUT = 0
        PUD_DOWN = 21
        PUD_OFF = 20
        PUD_UP = 22
        RISING = 31
        SERIAL = 40
        SPI = 41
        UNKNOWN = -1

        def setmode(a):
            return None

        def setup(channel : int, direction : bool, pull_up_down:int=PUD_OFF, initial:bool=LOW):
            return None

        def output(channel : int, value : bool):
            if value:
                Log.log(Log.DEBUG, f"GPIO Pin {channel} set HIGH")
            else:
                Log.log(Log.DEBUG, f"GPIO Pin {channel} set LOW")
            return None

        def input(channel : int):
            return random.randint(0,1)
        
        def cleanup():
            return None

        def setwarnings(flag):
            return None



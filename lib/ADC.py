## Development Wrapper for mcp3008
## Simulate GPIO interaction when running outside of Rasberry Pi

try:
    import busio
    import digitalio
    import board
    import adafruit_mcp3xxx.mcp3008 as _MCP
    from adafruit_mcp3xxx.analog_in import AnalogIn
    sim = False

except ImportError as e:
    import random
    sim = True



if not sim:
    spi = busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)
    class _ADC:
        def __init__(self, gpio_pin):
            self.cs = digitalio.DigitalInOut(gpio_pin)
            self.mcp = _MCP.MCP3008(spi, self.cs)

            self.channel = [AnalogIn(self.mcp, _MCP.P0), AnalogIn(self.mcp, _MCP.P1), AnalogIn(self.mcp, _MCP.P2), AnalogIn(self.mcp, _MCP.P3), AnalogIn(self.mcp, _MCP.P4), AnalogIn(self.mcp, _MCP.P5), AnalogIn(self.mcp, _MCP.P6), AnalogIn(self.mcp, _MCP.P7)]

    class MCP:
        _chips = []
        
        def newADC(gpio_pin=board.D22):
            MCP._chips.append(_ADC(gpio_pin))
            return len(MCP._chips)-1

        def id_read_voltage(ident, channel):
            return MCP._chips[ident].channel[channel].voltage

        def id_read_value(ident, channel):
            return MCP._chips[ident].channel[channel].value

        def read_voltage(channel):
            return MCP.id_read_voltage(int(channel // 8), channel % 8)

        def read_value(channel):
            return MCP.id_read_value(int(channel // 8), channel % 8)

else:
    class MCP:
        _chips = []
        bat = 9
        
        def newADC(gpio_pin=22):
            MCP._chips.append(None)
            return len(MCP._chips)-1

        def id_read_voltage(ident, channel):
            if channel == 7:
                MCP.bat -= 0.0000001
                return MCP.bat
            else:
                return random.uniform(0.00, 0.55)

        def id_read_value(ident, channel):
            return MCP._chips[ident].channel[channel].value

        def read_voltage(channel):
            return MCP.id_read_voltage(int(channel // 8), channel % 8)

        def read_value(channel):
            return MCP.id_read_value(int(channel // 8), channel % 8)
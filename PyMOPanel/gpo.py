from enum import Enum

class LedStatus(Enum):
    YELLOW = b'\0\0'
    GREEN  = b'\0\1'
    RED    = b'\1\0'
    OFF    = b'\1\1'

class GPO:
    def __init__(self, panel, led0 = LedStatus.OFF, led1 = LedStatus.OFF, led2 = LedStatus.OFF):
        self._panel = panel
        self._ledRegisters = [ (2,1), (4,3), (6,5) ] # (msb, lsb) tuples per each led
        self._leds = [None, None, None]
        self.setLed(0, led0)
        self.setLed(1, led1)
        self.setLed(2, led2)

    def setGPOState(self, gpo, value):
        self._panel.writeBytes([0xfe, 0x56 if value == 0 else 0x57, gpo])

    def setLed(self, led, state):
        self._leds[led] = state
        gpoMsb,gpoLsb = self._ledRegisters[led]
        self.setGPOState(gpoMsb, state.value[0])
        self.setGPOState(gpoLsb, state.value[1])
    

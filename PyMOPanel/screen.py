from time import sleep
from .helpers import sanitizeUint8

class Screen:
    def __init__(self, panel, initBrightness = 200, initContrast = 128):
        self._panel = panel
        self._brightness = None
        self._contrast   = None
        self.clear()
        self.setBrightness(initBrightness)
        self.setContrast(initContrast)
        self.enable(True)

    def clear(self):
        self._panel.writeBytes([0xfe, 0x58])

    def enable(self, value, minsToEnable = 0):
        value = bool(value)
        self._status = value
        if value:
            self._panel.writeBytes([0xfe, 0x42, int(minsToEnable)])
        else:
            self._panel.writeBytes([0xfe, 0x46])

    def setBrightness(self, brightness):
        sanitizedValue = sanitizeUint8(brightness)
        if sanitizedValue == self._brightness:
            return
        self._brightness = sanitizedValue
        self._panel.writeBytes([0xfe, 0x99, 
                         sanitizedValue])

    def incBrightness(self, increment):
        self.setBrightness(self._brightness + increment)

    def setContrast(self, contrast):
        sanitizedValue = sanitizeUint8(contrast)
        if sanitizedValue == self._contrast:
            return
        self._contrast = sanitizedValue
        self._panel.writeBytes([0xfe, 0x50,
                         sanitizedValue])

    def incContrast(self, increment):
        self.setContrast(self._contrast + increment)

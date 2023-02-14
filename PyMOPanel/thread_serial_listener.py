#!/usr/bin/env python3
import serial.threaded
import traceback
from .helpers import *

# class for handling threaded serial input. Note that (static) attributes need to be set. _panel is mandatory, _customCallbackForDataReceived is optional. brightnessAndContrastControlCallback is provided as an example of default behavior. Thread can be started and stopped
class ThreadSerialListener(serial.threaded.Protocol):
    _panel = None
    _customCallbackForDataReceived = None

    def brightnessAndContrastControlCallback(self, data):
        for currentByte in bytearray(data):
            if currentByte == UP_KEY:
                self._panel.setBrightness(sanitizeUint8(self._panel._brightness + 20))
            elif currentByte == DOWN_KEY:
                self._panel.setBrightness(sanitizeUint8(self._panel._brightness - 20))
            elif currentByte == LEFT_KEY:
                self._panel.setContrast(sanitizeUint8(self._panel._contrast - 5))
            elif currentByte == RIGHT_KEY:
                self._panel.setContrast(sanitizeUint8(self._panel._contrast + 5))

    def connection_made(self, transport):
        print('port connected')

    def data_received(self, data):
        if not self._customCallbackForDataReceived:
            print("Data received but no callback defined")
            return
        self._customCallbackForDataReceived(data)

    def connection_lost(self, exc):
        if exc:
            traceback.print_exc(exc)
        print('port closed\n')

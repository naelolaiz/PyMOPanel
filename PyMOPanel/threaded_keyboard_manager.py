import serial.threaded
import traceback
from .helpers import *
from .constants import Constants


class KeyboardManager:
    # class for handling threaded serial input. Note that (static) attributes need to be set. _panel is mandatory, _customCallbackForDataReceived is optional. brightnessAndContrastControlCallback is provided as an example of default behavior. Thread can be started and stopped
    class ThreadSerialListener(serial.threaded.Protocol):
        _panel = None
        _customCallbackForDataReceived = None
    
        def brightnessAndContrastControlCallback(self, data):
            for currentByte in bytearray(data):
                if currentByte == Constants.UP_KEY:
                    self._panel.incBrightness(20)
                elif currentByte == Constants.DOWN_KEY:
                    self._panel.incBrightness(-20)
                elif currentByte == Constants.LEFT_KEY:
                    self._panel.incContrast(-5)
                elif currentByte == Constants.RIGHT_KEY:
                    self._panel.incContrast(5)
    
        def connection_made(self, transport):
            print('port connected')
    
        def data_received(self, data):
            if not self._customCallbackForDataReceived:
                print("Data received but no callback defined")
                return
            self._customCallbackForDataReceived(data)
    
        def connection_lost(self, exc):
            if exc:
                print(str(exc))
                traceback.print_exc(exc)
            print('port closed\n')

    def __init__(self, panel, serialHandler):
        self.ThreadSerialListener._panel = panel
        self._serialHandler = serialHandler
        self._threadedSerialListener = None

    def enableKeyboardControllingContrastAndBrightness(self):
        self.ThreadSerialListener._customCallbackForDataReceived = self.ThreadSerialListener.brightnessAndContrastControlCallback
        self._threadedSerialListener = serial.threaded.ReaderThread(self._serialHandler, self.ThreadSerialListener)
        self._threadedSerialListener.start()

    def disableKeyboardControllingContrastAndBrightness(self):
        self._threadedSerialListener.stop()
        self.ThreadSerialListener._customCallbackForDataReceived = None

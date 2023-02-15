import serial.threaded
import traceback
from .helpers import *
from .constants import Constants
from enum import Enum

class AutoRepeatKeyMode(Enum):
    RESEND_KEY  = 0,
    KEY_UP_DOWN = 1,
    OFF = 3

class KeyboardManager:
    # class for handling threaded serial input. Note that (static) attributes need to be set. _panel is mandatory, _customCallbackForDataReceived is optional. brightnessAndContrastControlCallback is provided as an example of default behavior. Thread can be started and stopped
    class ThreadSerialListener(serial.threaded.Protocol):
        _panel = None
        _customCallbackForDataReceived = None
        _saveIgnoredKeys = False
        _ignoredKeysBuffer = bytearray()
    
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
                elif self._saveIgnoredKeys:
                    self._ignoredKeysBuffer.append(currentByte)
    
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

    def __init__(self, panel, serialHandler, autoTransmitKeyPressed = True, autoRepeatKeyMode = AutoRepeatKeyMode.OFF, debounceTimeInTicksOf6_554ms = 8):
        self._panel = panel
        self.ThreadSerialListener._panel = panel
        self._serialHandler = serialHandler
        self._threadedSerialListener = None
        self._autoTrasmitKeyPressed = None
        self._autoRepeatKeyMode = None
        self._debounceTime = None
        self.setAutoTransmitKeyPressed(autoTransmitKeyPressed)
        self.setAutoRepeatKeyMode(autoRepeatKeyMode)
        self.setDebounceTime(debounceTimeInTicksOf6_554ms)

    def enableKeyboardControllingContrastAndBrightness(self):
        self.ThreadSerialListener._customCallbackForDataReceived = self.ThreadSerialListener.brightnessAndContrastControlCallback
        self.ThreadSerialListener._saveIgnoredKeys = True
        self._threadedSerialListener = serial.threaded.ReaderThread(self._serialHandler, self.ThreadSerialListener)
        self._threadedSerialListener.start()

    def disableKeyboardControllingContrastAndBrightness(self):
        self._threadedSerialListener.stop()
        self.ThreadSerialListener._customCallbackForDataReceived = None

    # keypad methods
    def setAutoTransmitKeyPressed(self, state):
        self._autoTrasmitKeyPressed = bool(state)
        keyword = 0x41 if state else 0x4f
        self._panel.writeBytes([0xfe, keyword])

    def setAutoRepeatKeyMode(self, mode):
        self._autoRepeatKeyMode = mode
        if mode == AutoRepeatKeyMode.OFF:
            command_list = [0xfe, 0x60]
        else:
            command_list = [0xfe, 0x7e, mode.value]
        self._panel.writeBytes(command_list)

    def pollKeyPressed(self) :
        self._panel.writeBytes([0xfe, 0x26])
        return self.readBytes(self._serialHandler.in_waiting)

    def clearKeyBuffer(self):
        self._panel.writeBytes([0xfe, 0x45])

    def setDebounceTime(self, time):
        self._debounceTime = sanitizeUint8(time)
        self._panel.writeBytes([0xfe, 0x55, self._debounceTime])

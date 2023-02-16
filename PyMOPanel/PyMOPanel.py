import serial
from threading import Lock 
from .keyboard import KeyboardManager
from .bar_graph import BarGraphManager
from .screen import Screen
from .text import Text
from .graphics import Graphics
from .gpo import LedStatus, GPO
from .filesystem import Filesystem
from time import sleep

class PyMOPanel:
    def __init__(self, port = '/dev/ttyUSB0', baudrate = 19200):
        self._port = port
        self._baudrate = baudrate
        self._serialSendLock = Lock()
        self._serialReceiveLock = Lock()
        self._serialHandler = serial.Serial(port=port, baudrate=baudrate)
        if not self._serialHandler.is_open:
            raise Exception("MatrixOrbital device not found")
        self.screen = Screen(self)
        self.text   = Text(panel       = self,
                           fontRefId   = 0,
                           autoScroll  = True,
                           leftMargin  = 0,
                           topMargin   = 0,
                           charSpacing = 1,
                           lineSpacing = 1,
                           lastYRow    = 64)
        self.fs = Filesystem(self)
        self.graphics   = Graphics(self)
        self.gpo        = GPO(self)
        self.keyboard   = KeyboardManager(self, self._serialHandler)
        self.barGraphs  = BarGraphManager(self)
        
    # serial write and read functions
    def writeBytes(self, buffer):
        with self._serialSendLock:
            self._serialHandler.write(buffer)

    def readBytes(self, requestedBytesCount):
        return self._serialHandler.read(requestedBytesCount)

    def resetInputState(self):
        self.clearKeyBuffer()
        self._serialHandler.reset_input_buffer()
        
    # setup
    def setBaudRate(self, baudrate):
        speed={9600:   0xCF,
               14400:  0x8A,
               19200:  0x67,
               28800:  0x44,
               38400:  0x33,
               57600:  0x22,
               76800:  0x19,
               115200: 0x10}[baudrate]
        self.writeBytes([0xfe, 0x39, speed])
        sleep(0.1)
        self._serialHandler.baudrate = baudrate

    def getBaudRate(self):
        return self._serialHandler.baudrate

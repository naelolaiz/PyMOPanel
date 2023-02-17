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
    def __init__(self, port = '/dev/ttyUSB0', baudrate = 19200, timeout = 1):
        self._port = port
        self._baudrate = baudrate
        self._serialSendLock = Lock()
        self._serialReceiveLock = Lock()
        self._serialHandler = serial.Serial(port=port, baudrate=baudrate, timeout = timeout)
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
        self.keyboard.clearKeyBuffer()
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

    def getVersionNumber(self):
        self.writeBytes([0xfe, 0x36])
        version = self.readBytes(1)
        return "{}.{}".format(version[0]&0xf, (version[0]>>4)&0xf) if version else ""

    def getModuleType(self):
        self.writeBytes([0xfe, 0x37])
        module = self.readBytes(1)
        if not module:
            return ""
        return  {0x01: "LCD0821",            0x02: "LCD2021",
                 0x05: "LCD2041",            0x06: "LCD4021",
                 0x07: "LCD4041",            0x08: "LK202-25",
                 0x09: "LK204-25",           0x0A: "LK404-55",
                 0x0B: "VFD2021",            0x0C: "VFD2041",
                 0x0D: "VFD4021",            0x0E: "VK202-25",
                 0x0F: "VK204-25",           0x10: "GLC12232",
                 0x13: "GLC24064",           0x15: "GLK24064-25",
                 0x22: "GLK12232-25",        0x24: "GLK12232-25-SM",
                 0x25: "GLK24064-16-1U-USB", 0x26: "GLK24064-16-1U",
                 0x27: "GLK19264-7T-1U-USB", 0x28: "GLK12232-16",
                 0x29: "GLK12232-16-SM",     0x2A: "GLK19264-7T-1U",
                 0x2B: "LK204-7T-1U",        0x2C: "LK204-7T-1U-USB",
                 0x31: "LK404-AT",           0x32: "MOS-AV-162A",
                 0x33: "LK402-12",           0x34: "LK162-12",
                 0x35: "LK204-25PC",         0x36: "LK202-24-USB",
                 0x37: "VK202-24-USB",       0x38: "LK204-24-USB",
                 0x39: "VK204-24-USB",       0x3A: "PK162-12",
                 0x3B: "VK162-12",           0x3C: "MOS-AP-162A",
                 0x3D: "PK202-25",           0x3E: "MOS-AL-162A",
                 0x3F: "MOS-AL-202A",        0x40: "MOS-AV-202A",
                 0x41: "MOS-AP-202A",        0x42: "PK202-24-USB",
                 0x43: "MOS-AL-082",         0x44: "MOS-AL-204",
                 0x45: "MOS-AV-204",         0x46: "MOS-AL-402",
                 0x47: "MOS-AV-402",         0x48: "LK082-12",
                 0x49: "VK402-12",           0x4A: "VK404-55",
                 0x4B: "LK402-25",           0x4C: "VK402-25",
                 0x4D: "PK204-25",           0x4F: "MOS",
                 0x50: "MOI",                0x51: "XBoard-S",
                 0x52: "XBoard-I",           0x53: "MOU",
                 0x54: "XBoard-U",           0x55: "LK202-25-USB",
                 0x56: "VK202-25-USB",       0x57: "LK204-25-USB",
                 0x58: "VK204-25-USB",       0x5B: "LK162-12-TC",
                 0x72: "GLK240128-25",       0x73: "LK404-25",
                 0x74: "VK404-25",           0x78: "GLT320240",
                 0x79: "GLT480282",          0x7A: "GLT240128"}[module]

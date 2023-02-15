import serial
import time
from threading import Lock 
from .constants import *
from .helpers import *
from .threaded_keyboard_manager import KeyboardManager
from .bar_graph import *
from .screen import Screen
from .text import Text
from .graphics import Graphics

class MatrixOrbital:
    def __init__(self, port = '/dev/ttyUSB0', baudrate = 19200):
        self._port = port
        self._baudrate = baudrate
        self._serialSendLock = Lock()
        self._serialReceiveLock = Lock()
        self._serialHandler = serial.Serial(port=port, baudrate=baudrate)
        if not self._serialHandler.is_open:
            raise Exception("MatrixOrbital device not found")
        self._screen = Screen(self)
        self._text   = Text(panel       = self,
                            fontRefId   = 0,
                            autoScroll  = True,
                            leftMargin  = 0,
                            topMargin   = 0,
                            charSpacing = 1,
                            lineSpacing = 1,
                            lastYRow    = 64)
        self._graphics = Graphics(self)
        self._keyboard = KeyboardManager(self, self._serialHandler)
        self._barGraph = BarGraphManager(self)
        
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
    def setBaudRate(self, baud_rate) :
        speed={9600:   0xCF,
               14400:  0x8A,
               19200:  0x67,
               28800:  0x44,
               38400:  0x33,
               57600:  0x22,
               76800:  0x19,
               115200: 0x10}[baud_rate]
        self.writeBytes([0xfe, 0x39, speed])

    # Enable or disable contrast and brightness control by the keypad
    def enableKeyboardControllingContrastAndBrightness(self):
        self._keyboard.enableKeyboardControllingContrastAndBrightness()

    def disableKeyboardControllingContrastAndBrightness(self):
        self._keyboard.disableKeyboardControllingContrastAndBrightness()

    # screen methods
    def clearScreen(self):
        self._screen.clearScreen()

    def setScreen(self, value):
        self._screen.setScreen(value)

    def setBrightness(self, brightness):
        self._screen.setBrightness(brightness)

    def incBrightness(self, increment):
        self._screen.incBrightness(increment)

    def setContrast(self, contrast):
        self._screen.setContrast(contrast)

    def incContrast(self, increment):
        self._screen.incContrast(increment)

    # LEDs control
    def setGPOState(self, gpio, value):
        self.writeBytes([0xfe, 0x56 if value == 0 else 0x57, gpio])
    def setLedState(self, led, state):
        gpoMsb = 2 if led == 0 else 4 if led == 1 else 6
        gpoLsb = 1 if led == 0 else 3 if led == 1 else 5
        self.setGPOState(gpoMsb, state[0])
        self.setGPOState(gpoLsb, state[1])
    def setLedYellow(self, led):
        self.setLedState(led, [0, 0])
    def setLedGreen(self, led):
        self.setLedState(led, [0,1])
    def setLedRed(self, led):
        self.setLedState(led, [1, 0])
    def setLedOff(self, led):
        self.setLedState(led, [1,1])

    # keypad methods
    def setAutoTransmitKeyPressed(self, state) :
        keyword = 0x41 if state else 0x4f
        self.writeBytes([0xfe,keyword])
    def setAutoRepeatKeyModeResend(self, state) :
        command_list = [0xfe, 0x60] # autorepeat off
        if state:
            command_list = [0xfe, 0x7e, 0x00]
        self.writeBytes(command_list)
    def setAutoRepeatKeyModeUpDown(self, state) :
        command_list = [0xfe, 0x60] # autorepeat off
        if state:
            command_list = [0xfe, 0x7e, 0x01]
        self.writeBytes(command_list)
    def pollKeyPressed(self) :
        self.writeBytes([0xfe, 0x26])
        return self.readBytes(self._serialHandler.in_waiting)
    def clearKeyBuffer(self) :
        self.writeBytes([0xfe, 0x45])
    def setDebounceTime(self, time) :
        self.writeBytes([0xfe, 0x55,
                         sanitizeUint8(time)])

    # text methods
    def print(self, text, x0=None, y0=None, font_ref_id=None):
        self._text.print(text, x0, y0, font_ref_id)

    def setFontMetrics(self,
                       leftMargin=0,
                       topMargin=0,
                       charSpacing=1,
                       lineSpacing=1,
                       lastYRow=64):
        self._text.setFontMetrics(leftMargin,
                                  topMargin,
                                  charSpacing,
                                  lineSpacing,
                                  lastYRow) 
     
    def selectCurrentFont(self, font_ref_id):
        self._text.selectCurrentFont(font_ref_id)

    def cursorMoveHome(self): 
        self._text.cursorMoveHome()

    def setCursorMoveToPos(self, col, row):
        self._text.setCursorMoveToPos(col, row)

    def setCursorCoordinate(self, x, y) :
        self._text.setCursorCoordinate(x, y)

    def setAutoScroll(self, state) :
        self._text.setAutoScroll(state)

    # graphics methods
    def setDrawingColor(self, color):
        self._graphics.setDrawingColor(color)

    def drawPixel(self, x, y):
        self._graphics.drawPixel(x, y)

    def drawLine(self, x0, y0, x1, y1):
        self._graphics.drawLine(x0, y0, x1, y1)

    def continueLine(self, x, y):
        self._graphics.continueLine(x, y)

    def drawRectangle(self, color, x0, y0, x1, y1, solid=False):
        self._graphics.drawRectangle(color, x0, y0, x1, y1, solid)
        
    # show a bitmap. It could be an animated gif
    def uploadAndShowBitmap(self, inputFilename, x0=0, y0=0, thresholdForBW=50, inverted = False):
        self._graphics.uploadAndShowBitmap(inputFilename, x0, y0, thresholdForBW, inverted)

    # add Bar graphs
    def addBarGraph(self, x0, y0, x1, y1, direction):
        self._barGraph.addBarGraph(x0, y0, x1, y1, direction)

    def setBarGraphValue(self, index, value):
        self._barGraph.setBarGraphValue(index, value)


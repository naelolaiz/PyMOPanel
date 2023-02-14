import serial
import time
from threading import Lock 
from PIL import Image

from .constants import *
from .helpers import *
from .threaded_keyboard_manager import KeyboardManager
from .bar_graph import *
from .screen import Screen
from .text import Text

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
        self._textControl = Text(panel       = self,
                                 fontRefId   = 0,
                                 autoScroll  = True,
                                 leftMargin  = 0,
                                 topMargin   = 0,
                                 charSpacing = 1,
                                 lineSpacing = 1,
                                 lastYRow    = 64)
        self._keyboardManager = KeyboardManager(self, self._serialHandler)
        self._barGraphManager = BarGraphManager(self)
        
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
        self._keyboardManager.enableKeyboardControllingContrastAndBrightness()

    def disableKeyboardControllingContrastAndBrightness(self):
        self._keyboardManager.disableKeyboardControllingContrastAndBrightness()

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
    def print(self,
              text,
              x0=None,
              y0=None,
              font_ref_id=None):
        self._textControl.print(text,
                                x0,
                                y0,
                                font_ref_id)

    def setFontMetrics(self,
                       leftMargin=0,
                       topMargin=0,
                       charSpacing=1,
                       lineSpacing=1,
                       lastYRow=64):
        self._textControl.setFontMetrics(leftMargin,
                                         topMargin,
                                         charSpacing,
                                         lineSpacing,
                                         lastYRow) 
     
    def selectCurrentFont(self, font_ref_id):
        self._textControl.selectCurrentFont(font_ref_id)

    def cursorMoveHome(self): 
        self._textControl.cursorMoveHome()

    def setCursorMoveToPos(self, col, row):
        self._textControl.setCursorMoveToPos(col, row)

    def setCursorCoordinate(self, x, y) :
        self._textControl.setCursorCoordinate(x, y)

    def setAutoScroll(self, state) :
        self._textControl.setAutoScroll(state)

    # graphics methods
    def setDrawingColor(self, color):
        self.writeBytes([0xfe, 0x63,
                         sanitizeUint8(color)])
    def drawPixel(self, x, y):
        self.writeBytes([0xfe, 0x70,
                         sanitizeUint8(x),
                         sanitizeUint8(y)])
    def drawLine(self, x0,y0,x1,y1):
        self.writeBytes([0xfe, 0x6c,
                         sanitizeUint8(x0),
                         sanitizeUint8(y0),
                         sanitizeUint8(x1),
                         sanitizeUint8(y1)])
    def continueLine(self, x,y):
        self.writeBytes([0xfe, 0x65,
                         sanitizeUint8(x),
                         sanitizeUint8(y)])
    def drawRectangle(self, color, x0, y0, x1, y1, solid=False) :
        keyword=0x78 if solid else 0x72
        self.writeBytes([0xfe, keyword, 
                         sanitizeUint8(color),
                         sanitizeUint8(x0),
                         sanitizeUint8(y0),
                         sanitizeUint8(x1),
                         sanitizeUint8(y1)])
    # show a bitmap. It could be an animated gif
    def uploadAndShowBitmap(self, inputFilename, x0=0, y0=0, thresholdForBW=50, inverted = False):
        time.sleep(0.2) # otherwise transfer may fail
        img = Image.open(inputFilename)
        width = img.width
        height = img.height
        isAnimation = hasattr(img,"n_frames")
        frames = img.n_frames if isAnimation else 2
        def getValueForAboveThreshold(bitIndex, inverted):
            return 1<<(7-bitIndex) if inverted else 0
        def getValueForBelowThreshold(bitIndex, inverted):
            return getValueForAboveThreshold(bitIndex, not inverted)

        for frame in range(1,frames):
            if isAnimation: 
                img.seek(frame)
            bitDepth = {'1':1, 'L':8, 'P':8, 'RGB':24, 'RGBA':32, 'CMYK':32, 'YCbCr':24, 'I':32, 'F':32}[img.mode]
            bytesPerPixel = bitDepth / 8

            buffer = img.tobytes()
            if len(buffer) % bitDepth != 0:
                raise Exception('bitmap size should be a multiple of the used depth')

            # init array with header
            outputArray = bytearray(b'\xfe\x64')
            outputArray += x0.to_bytes(1,'little')
            outputArray += y0.to_bytes(1,'little')
            outputArray += width.to_bytes(1,'little')
            outputArray += height.to_bytes(1,'little')

            # pack input 8 bit image to 1 bit monocromatic pixels
            for pixelNr in range(0, width*height, 8):
                baseAddrForByte = pixelNr
                outputArray += sum([getValueForAboveThreshold(bitIndex,inverted) if sumChannels(buffer, pixelNr+bitIndex, bytesPerPixel)>=thresholdForBW else getValueForBelowThreshold(bitIndex,inverted) for bitIndex in range(8)]).to_bytes(1,'little')

            # send data
            self.writeBytes(bytes(outputArray))

    # add Bar graphs
    def addBarGraph(self, x0, y0, x1, y1, direction):
        self._barGraphManager.addBarGraph(x0, y0, x1, y1, direction)

    def setBarGraphValue(self, index, value):
        self._barGraphManager.setBarGraphValue(index, value)


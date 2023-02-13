#!/usr/bin/env python3
import serial
import serial.threaded
import time
from threading import Lock 
import traceback
from PIL import Image

class MatrixOrbital:
# panel constants
    class Constants:
        PANEL_WIDTH        = 192
        CENTER_X           = int(PANEL_WIDTH/2)
        PANEL_HEIGHT       = 64
        CENTER_Y           = int(PANEL_HEIGHT/2)
        MAX_NUMBER_OF_BARS = 16
        UP_KEY             = 0x42
        DOWN_KEY           = 0x48
        LEFT_KEY           = 0x44
        RIGHT_KEY          = 0x43
        CENTER_KEY         = 0x45
        TOP_LEFT_KEY       = 0x41
        BOTTOM_LEFT_KEY    = 0x47

# class for handling threaded serial input. Note that (static) attributes need to be set. _panel is mandatory, _customCallbackForDataReceived is optional. brightnessAndContrastControlCallback is provided as an example of default behavior. Thread can be started and stopped
    class ThreadSerialListener(serial.threaded.Protocol):
        _panel = None
        _customCallbackForDataReceived = None

        def brightnessAndContrastControlCallback(self, data):
            for currentByte in bytearray(data):
                if currentByte == MatrixOrbital.Constants.UP_KEY:
                    self._panel.setBrightness(MatrixOrbital.Helpers.sanitizeUint8(self._panel._brightness + 20))
                elif currentByte == MatrixOrbital.Constants.DOWN_KEY:
                    self._panel.setBrightness(MatrixOrbital.Helpers.sanitizeUint8(self._panel._brightness - 20))
                elif currentByte == MatrixOrbital.Constants.LEFT_KEY:
                    self._panel.setContrast(MatrixOrbital.Helpers.sanitizeUint8(self._panel._contrast - 5))
                elif currentByte == MatrixOrbital.Constants.RIGHT_KEY:
                    self._panel.setContrast(MatrixOrbital.Helpers.sanitizeUint8(self._panel._contrast + 5))

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

# misc helpers
    class Helpers:
        def sanitizeUint8(value):
            return max(0,int(value)) & 0xFF
        def sumChannels(inputByteArray, offset, dataSize):
            dataSize=int(dataSize)
            sum=0
            base = offset*dataSize
            for i in range(dataSize):
                sum += inputByteArray[base+i]
            return sum/dataSize
    class BarGraph:
        def __init__(self, x0, y0, x1, y1, direction):
            self._x0 = x0
            self._y0 = y0
            self._x1 = x1
            self._y1 = y1
            self._direction = direction
            self._delta = abs(x0-x1) if direction == 'HorizontalLeft' or direction == 'HorizontalRight' else abs(y0-y1)
            self._value = 0.
        def setValue(self, value):
            self._value = value
        def getValueInPixels(self):
            return int(self._value * self._delta)

    def __init__(self, port = '/dev/ttyUSB0', baudrate = 19200):
        self._port = port
        self._baudrate = baudrate
        self._serialSendLock = Lock()
        self._serialReceiveLock = Lock()
        self._serialDriver = serial.Serial(port=port, baudrate=baudrate)
        if not self._serialDriver.is_open:
            raise Exception("MatrixOrbital device not found")
        self._barGraphs = []
        self.setBrightness(200)
        self.setContrast(128)

    # serial write and read functions
    def writeBytes(self, buffer):
        with self._serialSendLock:
            self._serialDriver.write(buffer)
    def readBytes(self, requestedBytesCount):
        return self._serialDriver.read(requestedBytesCount)

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

    # Enable or disable contrast and brigness control by the keypad
    def enableKeyboardControllingContrastAndBrightness(self):
        self.ThreadSerialListener._customCallbackForDataReceived = self.ThreadSerialListener.brightnessAndContrastControlCallback
        self.ThreadSerialListener._panel = self
        self._serialListener = serial.threaded.ReaderThread(self._serialDriver, self.ThreadSerialListener)
        self._serialListener.start()
    def disableKeyboardControllingContrastAndBrightness(self):
        self.ThreadSerialListener._customCallbackForDataReceived = None
        self._serialListener.stop()

    # screen methods
    def clearScreen(self):
        self.writeBytes([0xfe, 0x58])
        time.sleep(0.1)
    def setScreen(self, value):
        self.writeBytes([0xfe, 0x42 if value else 0x46])
        time.sleep(0.1)
    def setBrightness(self, brightness):
        self._brightness = brightness
        self.writeBytes([0xfe, 0x99, 
                         MatrixOrbital.Helpers.sanitizeUint8(brightness)])
    def setContrast(self, contrast):
        self._contrast = contrast
        self.writeBytes([0xfe, 0x50,
                         MatrixOrbital.Helpers.sanitizeUint8(contrast)])

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
        return self.readBytes(self._serialDriver.in_waiting)
    def clearKeyBuffer(self) :
        self.writeBytes([0xfe, 0x45])
    def setDebounceTime(self, time) :
        self.writeBytes([0xfe, 0x55,
                         MatrixOrbital.Helpers.sanitizeUint8(time)])

    # text methods
    def print(self, text, x0=None, y0=None, font_ref_id=None) :
        if font_ref_id:
            self.selectCurrentFont(font_ref_id)
        if x0 != None and y0 != None:
            self.setCursorMoveToPos(x0,y0)
        self.writeBytes(bytes(text, 'UTF-8') if type(text) == str else text)
    def setFontMetrics(self, leftMargin=0, topMargin=0, charSpacing=1, lineSpacing=1, lastYRow=64) :
        self.writeBytes([0xfe, 0x32,
                         MatrixOrbital.Helpers.sanitizeUint8(leftMargin),
                         MatrixOrbital.Helpers.sanitizeUint8(topMargin),
                         MatrixOrbital.Helpers.sanitizeUint8(charSpacing),
                         MatrixOrbital.Helpers.sanitizeUint8(lineSpacing),
                         MatrixOrbital.Helpers.sanitizeUint8(lastYRow)])
    def selectCurrentFont(self, font_ref_id) :
        self.writeBytes([0xfe, 0x31,
                         MatrixOrbital.Helpers.sanitizeUint8(font_ref_id)])
    def cursorMoveHome(self) : 
        self.writeBytes([0xfe, 0x48])
    def setCursorMoveToPos(self, col, row) :
        self.writeBytes([0xfe, 0x47,
                         MatrixOrbital.Helpers.sanitizeUint8(col),
                         MatrixOrbital.Helpers.sanitizeUint8(row)])
    def setCursorCoordinate(self, x, y) :
        self.writeBytes([0xfe, 0x79,
                         MatrixOrbital.Helpers.sanitizeUint8(x),
                         MatrixOrbital.Helpers.sanitizeUint8(y)]) 
    def setAutoScroll(self, state) :
        keyword = 0x51 if state else 0x52
        self.writeBytes([0xfe, keyword])

    # graphics methods
    def setDrawingColor(self, color):
        self.writeBytes([0xfe, 0x63,
                         MatrixOrbital.Helpers.sanitizeUint8(color)])
    def drawPixel(self, x, y):
        self.writeBytes([0xfe, 0x70,
                         MatrixOrbital.Helpers.sanitizeUint8(x),
                         MatrixOrbital.Helpers.sanitizeUint8(y)])
    def drawLine(self, x0,y0,x1,y1):
        self.writeBytes([0xfe, 0x6c,
                         MatrixOrbital.Helpers.sanitizeUint8(x0),
                         MatrixOrbital.Helpers.sanitizeUint8(y0),
                         MatrixOrbital.Helpers.sanitizeUint8(x1),
                         MatrixOrbital.Helpers.sanitizeUint8(y1)])
    def continueLine(self, x,y):
        self.writeBytes([0xfe, 0x65,
                         MatrixOrbital.Helpers.sanitizeUint8(x),
                         MatrixOrbital.Helpers.sanitizeUint8(y)])
    def drawRectangle(self, color, x0, y0, x1, y1, solid=False) :
        keyword=0x78 if solid else 0x72
        self.writeBytes([0xfe, keyword, 
                         MatrixOrbital.Helpers.sanitizeUint8(color),
                         MatrixOrbital.Helpers.sanitizeUint8(x0),
                         MatrixOrbital.Helpers.sanitizeUint8(y0),
                         MatrixOrbital.Helpers.sanitizeUint8(x1),
                         MatrixOrbital.Helpers.sanitizeUint8(y1)])
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
                outputArray += sum([getValueForAboveThreshold(bitIndex,inverted) if MatrixOrbital.Helpers.sumChannels(buffer, pixelNr+bitIndex, bytesPerPixel)>=thresholdForBW else getValueForBelowThreshold(bitIndex,inverted) for bitIndex in range(8)]).to_bytes(1,'little')

            # send data
            self.writeBytes(bytes(outputArray))

    # add Bar graphs
    # direction: Vertical{Left|Right}, Horizontal{Bottom|Top}
    def addBarGraph(self, x0, y0, x1, y1, direction):
        if len(self._barGraphs) == MatrixOrbital.Constants.MAX_NUMBER_OF_BARS:
            raise Exception("Cannot have more than {} bars".format(MatrixOrbital.Constants.MAX_NUMBER_OF_BARS))
        self._barGraphs.append(MatrixOrbital.BarGraph(x0,y0,x1,y1,direction))

        index = len(self._barGraphs)-1
        directionEnumValue = 0 if direction == "VerticalBottom" else 1 if direction == "HorizontalLeft" else 2 if direction == "VerticalTop" else 3

        # init bar graph
        self.writeBytes([0xfe, 0x67, index, directionEnumValue, x0, y0, x1, y1])
        return index
    def setBarGraphValue(self, index, value):
        self._barGraphs[index].setValue(value)
        self.writeBytes([0xfe, 0x69, index, self._barGraphs[index].getValueInPixels()])


    # filesystem
    def getFilesystemSpace(self):
        self._serialDriver.reset_input_buffer()
        self.writeBytes([0xfe, 0xaf])
        return int.from_bytes(self.readBytes(4), byteorder='little', signed=False)

    def getFilesystemDirectory(self):
        self.writeBytes([0xfe, 0xb3])
        entriesCount = self.readBytes(1)[0]
        unused_entries = []
        used_entries = []
        for entryNumber in range(entriesCount):
            used = self.readBytes(1)[0] != 0
            # bit0: type (0 is font, 1 bitmap), bit1..bit7: fileId
            typeAndFileId = self.readBytes(1)[0]
            isBitmapNotIcon = bool(typeAndFileId & 1)
            fileId = typeAndFileId >> 1
            fileSize = int.from_bytes(self.readBytes(2), byteorder='little', signed=False)
            container = used_entries if used else unused_entries
            container += [("bitmap" if isBitmapNotIcon else "icon", fileId, fileSize)]
        return (used_entries, unused_entries)
        
    def downloadFile(self, fontNoBitmap, fileId, outputFilename):
        self._serialDriver.reset_input_buffer()
        self.writeBytes([0xfe, 0xb2, 0 if fontNoBitmap else 1, fileId])
        fileSizeInBytes = int.from_bytes(self.readBytes(4), byteorder='little', signed=False) - 2
        width  = self.readBytes(1)[0]
        height = self.readBytes(1)[0]
        print('Downloading {} {} from panel filesystem to {}...'.format('font' if fontNoBitmap else 'bitmap', fileId, outputFilename))
        open(outputFilename+'.info', 'w').writelines(['width: {}\n'.format(width), 'height: {}\n'.format(height)])
        open(outputFilename, 'wb').write(self.readBytes(fileSizeInBytes))
        print('done!')

    def dumpCompleteFilesystem(self, outputFilename):
        self._serialDriver.reset_input_buffer()
        self.writeBytes([0xfe, 0x30])
        filesystemSize = int.from_bytes(self.readBytes(4), byteorder='little', signed=False)
        print('Dumping panel filesystem to {}...'.format(outputFilename))
        open(outputFilename, 'wb').write(self.readBytes(filesystemSize))
        print('done!')

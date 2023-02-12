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
            return max(0,value) & 0xFF
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
        self._barGraphs = []
        self.setBrightness(200)
        self.setContrast(128)

    def enableKeyboardControllingContrastAndBrightness(self):
        self.ThreadSerialListener._customCallbackForDataReceived = self.ThreadSerialListener.brightnessAndContrastControlCallback
        self.ThreadSerialListener._panel = self
        self._serialListener = serial.threaded.ReaderThread(self._serialDriver, self.ThreadSerialListener)
        self._serialListener.start()

    def disableKeyboardControllingContrastAndBrightness(self):
        self.ThreadSerialListener._customCallbackForDataReceived = None
        self._serialListener.stop()

    def sendBytes(self, buffer):
        with self._serialSendLock:
            self._serialDriver.write(buffer)

    def read(self, requestedBytesCount):
        return self._serialDriver.read(requestedBytesCount)

    def dumpFileFromFilesystem(self, fontNoBitmap, fileId, outputFilename):
        self._serialDriver.reset_input_buffer()
        self.sendBytes([0xfe,0xb2, 0 if fontNoBitmap else 1, fileId])
        fileSizeInBytes = int.from_bytes(self.read(4), byteorder='little', signed=False) - 2
        width  = int.from_bytes(self.read(1), byteorder='little', signed=False)
        height = int.from_bytes(self.read(1), byteorder='little', signed=False)
        print('Downloading {} {} from panel filesystem to {}...'.format('font' if fontNoBitmap else 'bitmap', fileId, outputFilename))
        open(outputFilename+'.info', 'w').writelines(['width: {}\n'.format(width), 'height: {}\n'.format(height)])
        open(outputFilename, 'wb').write(self.read(fileSizeInBytes))
        print('done!')

    def dumpCompleteFilesystem(self, outputFilename):
        self._serialDriver.reset_input_buffer()
        self.sendBytes([0xfe, 0x30])
        filesystemSize = int.from_bytes(self.read(4), byteorder='little', signed=False)
        print('Dumping panel filesystem to {}...'.format(outputFilename))
        open(outputFilename, 'wb').write(self.read(filesystemSize))
        print('done!')

    
    # direction: Vertical{Left|Right}, Horizontal{Bottom|Top}
    def addBarGraph(self, x0, y0, x1, y1, direction):
        if len(self._barGraphs) == MatrixOrbital.Constants.MAX_NUMBER_OF_BARS:
            raise Exception("Cannot have more than {} bars".format(MatrixOrbital.Constants.MAX_NUMBER_OF_BARS))
        self._barGraphs.append(MatrixOrbital.BarGraph(x0,y0,x1,y1,direction))

        index = len(self._barGraphs)-1
        directionEnumValue = 0 if direction == "VerticalBottom" else 1 if direction == "HorizontalLeft" else 2 if direction == "VerticalTop" else 3

        # init bar graph
        self.sendBytes([0xfe, 0x67, index, directionEnumValue, x0, y0, x1, y1])
        return index

    def setBarGraphValue(self, index, value):
        self._barGraphs[index].setValue(value)
        self.sendBytes([0xfe, 0x69, index, self._barGraphs[index].getValueInPixels()])

    def drawBMP(self, inputFilename, x0=0, y0=0, thresholdForBW=50, inverted = False):
        time.sleep(0.2) # otherwise transfer may fail
        img = Image.open(inputFilename)
        width = img.width
        height = img.height
        isAnimation = hasattr(img,"n_frames")
        frames = img.n_frames if isAnimation else 2
        def getValueForAboveThreshold(bit, inverted):
            return 1<<(7-bit) if inverted else 0
        def getValueForBelowThreshold(bit, inverted):
            return getValueForAboveThreshold(bit, not inverted)

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
                outputArray += sum([getValueForAboveThreshold(bit,inverted) if MatrixOrbital.Helpers.sumChannels(buffer, pixelNr+bit, bytesPerPixel)>=thresholdForBW else getValueForBelowThreshold(bit,inverted) for bit in range(8)]).to_bytes(1,'little')

            # send data
            #print(str(outputArray))
            self.sendBytes(bytes(outputArray))

    def setGPOState(self, gpio, value):
        self.sendBytes([0xfe, 0x56 if value == 0 else 0x57, gpio])

    def setLedState(self, led, state):
        gpoMsb = 2 if led == 0 else 4 if led == 1 else 6
        gpoLsb = 1 if led == 0 else 3 if led == 1 else 5
        self.setGPOState(gpoMsb, state[0])
        self.setGPOState(gpoLsb, state[1])

    def setLedYellow(self, led):
        self.setLedState(led, [0,0])

    def setLedGreen(self, led):
        self.setLedState(led, [0,1])

    def setLedRed(self, led):
        self.setLedState(led, [1,0])

    def setLedOff(self, led):
        self.setLedState(led, [1,1])

    def setDisplayOn(self):
        self.sendBytes([0xfe, 0x42, 0x10])

    def setDisplayOff(self):
        self.sendBytes([0xfe, 0x46, 0x10])

    def moveCursorHome(self):
        self.sendBytes([0xfe, 0x48, 0x10])

    def clearScreen(self):
        self.sendBytes([0xfe, 0x58, 0x10])

    def setDrawingColor(self, color):
        self.sendBytes([0xfe, 0x63, color, 0x10])

    def drawPixel(self, x, y):
        self.sendBytes([0xfe, 0x70, MatrixOrbital.Helpers.sanitizeUint8(x), MatrixOrbital.Helpers.sanitizeUint8(y), 0x10])

    def drawSolidRectangle(self, color, x0, y0, x1, y1):
        self.sendBytes([0xfe, 0x78, color, x0, y0, x1, y1])

    def drawLine(self, x0,y0,x1,y1):
        self.sendBytes([0xfe,0x6c,x0,y0,x1,y1])

    def setCursorPos(self, col, row):
        self.sendBytes([0xfe,0x47,col,row])

    def writeText(self, text):
        self.sendBytes(bytes(text, 'UTF-8'))

    def setSendAllKeyPresses(self):
        self.sendBytes([0xfe, 0x41])

    def setBrightness(self, brightness):
        self._brightness = brightness
        self.sendBytes([0xfe, 0x99, brightness])

    def setContrast(self, contrast):
        self._contrast = contrast
        self.sendBytes([0xfe, 0x50, contrast])


#!/usr/bin/env python3
import serial
import serial.threaded
import time
from math import pi, sin, cos
from threading import Thread, Lock, current_thread
from sys import argv,stdout
import traceback
from PIL import Image
from random import random

class MatrixOrbital:
    class Constants:
        PANEL_WIDTH  = 192
        PANEL_HEIGHT = 64
        UP_KEY          = 0x42
        DOWN_KEY        = 0x48
        LEFT_KEY        = 0x44
        RIGHT_KEY       = 0x43
        CENTER_KEY      = 0x45
        TOP_LEFT_KEY    = 0x41
        BOTTOM_LEFT_KEY = 0x47

    class Helpers:
        def sanitizeUint8(value):
            return max(0,value) & 0xFF

    def __init__(self, port = '/dev/ttyUSB0', baudrate = 19200):
        self._port = port
        self._baudrate = baudrate
        self._serialSendLock = Lock()
        self._serialDriver = serial.Serial(port=port, baudrate=baudrate)
        self.setBrightness(200)
        self.setContrast(128)

    def sendBytes(self, buffer):
        with self._serialSendLock:
            self._serialDriver.write(buffer)

    def dumpFileFromFilesystem(self, fontNoBitmap, fileId, outputFilename):
        self._serialDriver.reset_input_buffer()
        self.sendBytes([0xfe,0xb2, 0 if fontNoBitmap else 1, fileId])
        fileSizeInBytes = int.from_bytes(self._serialDriver.read(4), byteorder='little', signed=False) - 2
        width  = int.from_bytes(self._serialDriver.read(1), byteorder='little', signed=False)
        height = int.from_bytes(self._serialDriver.read(1), byteorder='little', signed=False)
        print('Downloading {} {} from panel filesystem to {}...'.format('font' if fontNoBitmap else 'bitmap', fileId, outputFilename))
        open(outputFilename+'.info', 'w').writelines(['width: {}\n'.format(width), 'height: {}\n'.format(height)])
        open(outputFilename, 'wb').write(self._serialDriver.read(fileSizeInBytes))
        print('done!')

    def dumpCompleteFilesystem(self, outputFilename):
        self._serialDriver.reset_input_buffer()
        self.sendBytes([0xfe, 0x30])
        filesystemSize = int.from_bytes(self._serialDriver.read(4), byteorder='little', signed=False)
        print('Dumping panel filesystem to {}...'.format(outputFilename))
        open(outputFilename, 'wb').write(self._serialDriver.read(filesystemSize))
        print('done!')

    def drawBMP(self, inputFilename, x0=0, y0=0):
        time.sleep(0.3) # otherwise transfer may fail
        img = Image.open(inputFilename)
        width = img.width
        height = img.height
        for frame in range(img.n_frames):
            img.seek(frame)
            bitDepth = {'1':1, 'L':8, 'P':8, 'RGB':24, 'RGBA':32, 'CMYK':32, 'YCbCr':24, 'I':32, 'F':32}[img.mode]
            threshold = 100

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
            for byteNr in range(int(len(buffer)/bitDepth)):
                outputArray += ((128 if buffer[byteNr*bitDepth]>threshold else 0) +
                                (64  if buffer[byteNr*bitDepth+1]>threshold else 0) +
                                (32  if buffer[byteNr*bitDepth+2]>threshold else 0) +
                                (16  if buffer[byteNr*bitDepth+3]>threshold else 0) +
                                (8   if buffer[byteNr*bitDepth+4]>threshold else 0) +
                                (4   if buffer[byteNr*bitDepth+5]>threshold else 0) +
                                (2   if buffer[byteNr*bitDepth+6]>threshold else 0) +
                                (1   if buffer[byteNr*bitDepth+7]>threshold else 0)).to_bytes(1,'little')
            # send data
            #print(str(outputArray))
            self.sendBytes(bytes(outputArray))
            time.sleep(0.2) 

    def setGPOState(self, gpio, value):
        self.sendBytes([0xfe, 0x56 if value == 0 else 0x57, gpio])

    def setLedState(self, led, state):
        gpoMsb = 0 if led == 1 else 4 if led == 2 else 6
        gpoLsb = 1 if led == 1 else 3 if led == 2 else 5
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
        self.sendBytes([0xfe, 0x70, x, y, 0x10])

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

    def drawSpiral(self, color, centerPos, maxRadius, incRadius = 0.03, incAngle = pi/100, startingAngle =0):
        self.setDrawingColor(color)
        angle = startingAngle
        radius = 0
        while radius < maxRadius:
            x = int(centerPos[0] + cos(angle) * radius)
            y = int(centerPos[1] + sin(angle) * radius)
            if x<0 or x>self.Constants.PANEL_WIDTH or y <0 or y > self.Constants.PANEL_HEIGHT:
                break
            self.drawPixel(x,y)
            radius += incRadius
            angle +=incAngle


class Demo:
    class ThreadSerialListener(serial.threaded.Protocol):
        _panel = None
        def connection_made(self, transport):
            print('port connected')
        def data_received(self, data):
            for currentByte in bytearray(data):
                if currentByte == MatrixOrbital.Constants.UP_KEY:
                    self._panel.setBrightness(MatrixOrbital.Helpers.sanitizeUint8(self._panel._brightness + 20))
                elif currentByte == MatrixOrbital.Constants.DOWN_KEY:
                    self._panel.setBrightness(MatrixOrbital.Helpers.sanitizeUint8(self._panel._brightness - 20))
                elif currentByte == MatrixOrbital.Constants.LEFT_KEY:
                    self._panel.setContrast(MatrixOrbital.Helpers.sanitizeUint8(self._panel._contrast - 5))
                elif currentByte == MatrixOrbital.Constants.RIGHT_KEY:
                    self._panel.setContrast(MatrixOrbital.Helpers.sanitizeUint8(self._panel._contrast + 5))
        def connection_lost(self, exc):
            if exc:
                print(str(exc))
                traceback.print_exc(exc)
            print('port closed\n')

    def demoThreadedLedChanges(self):
        while self._ledsDemoRunning:
            for led in range(1,4):
                self._panel.setLedOff(led)
                time.sleep(0.3)
                self._panel.setLedYellow(led)
                time.sleep(0.3)
                self._panel.setLedRed(led)
                time.sleep(0.3)
                self._panel.setLedGreen(led)
                time.sleep(0.3)

    def __init__(self, panel):
        self._panel = panel
        self.ThreadSerialListener._panel = self._panel
        self._listener = serial.threaded.ReaderThread(panel._serialDriver, self.ThreadSerialListener)
        self._ledsDemoRunning = False

    def enableKeyboardControllingContrastAndBrightness(self):
        self._listener.start()

    def disableKeyboardControllingContrastAndBrightness(self):
        self._listener.stop()

    def startLedsDemoThread(self):
        self._ledsDemoRunning = True
        self._threadLedsDemo = Thread(target=self.demoThreadedLedChanges)
        self._threadLedsDemo.start()

    def stopLedsDemoThread(self):
        self._ledsDemoRunning = False

    def runDemoPressedKeys(self, charsCount):
        self._panel.clearScreen()
        self._panel.writeText('Press {} keys to finish'.format(charsCount))
        self._panel.setSendAllKeyPresses()
        for i in range(charsCount):
            char = self._panel._serialDriver.read(1)
            print(char)
            self._panel.setCursorPos(7, 0)
            self._panel.writeText(str(charsCount-i-1))
            self._panel.setCursorPos(i+1, 3)
            self._panel.sendBytes(char)
    def runDemoSpirals(self):
        self._panel.clearScreen()
        self._panel.drawSpiral(200, [int(MatrixOrbital.Constants.PANEL_WIDTH/2), int(MatrixOrbital.Constants.PANEL_HEIGHT/2)], MatrixOrbital.Constants.PANEL_HEIGHT)
        sign = 1
        for i in range(20):
            offsetX = (random()*150)-75
            self._panel.drawSpiral(200, 
                                   [int(MatrixOrbital.Constants.PANEL_WIDTH/2) + offsetX, int(MatrixOrbital.Constants.PANEL_HEIGHT/2)],
                                   MatrixOrbital.Constants.PANEL_HEIGHT,
                                   incAngle = sign * pi / (50 + random() * 100),
                                   incRadius = 0.02 + random()/5)
            sign = sign * -1


def main(port):
    myPanel = MatrixOrbital(port=port)
    demo = Demo(myPanel)

    # dump complete filesystem to a file
    #myPanel.dumpCompleteFilesystem('filesystem.data')

    # dump bitmap 1 to a file
    #myPanel.dumpFileFromFilesystem(0, 1, 'bitmap1_output.data')

    # enable controlling brightness and contrast by the keyboard
    demo.enableKeyboardControllingContrastAndBrightness()

    myPanel.setDisplayOn()
    myPanel.clearScreen()
    
    # simple text
    myPanel.writeText('hello world!\n')
    time.sleep(1)
    myPanel.drawBMP('./animation.gif')
    myPanel.drawBMP('./animation.gif')
    myPanel.drawBMP('./animation.gif')
    time.sleep(1)

    # start blinking leds on the background
    demo.startLedsDemoThread()

    # draw some spirals
    demo.runDemoSpirals()
    
    # stop leds blinking
    demo.stopLedsDemoThread()

    # stop keyboard thread 
    demo.disableKeyboardControllingContrastAndBrightness()

    # start keyboard demo
    demo.runDemoPressedKeys(8)

    # show a BMP and exit
    myPanel.clearScreen()
    demo.startLedsDemoThread()
    myPanel.drawBMP('./goodbye.bmp')

    time.sleep(2)

    demo.stopLedsDemoThread()
    myPanel.setDisplayOff()

if __name__ == '__main__':
    port = argv[1] if len(argv) == 2 else '/dev/ttyUSB0'
    main(port=port)


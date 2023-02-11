#!/usr/bin/env python3
import serial
import serial.threaded
import time
from math import pi, sin, cos
from threading import Thread, Lock
from sys import argv,stdout
import traceback

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

    class State:
        def __init__(self):
            self._serialSendLock = Lock()
            self._ledsDemoRunning = False

    class ThreadSerialListener(serial.threaded.Protocol):
        _panel = None
        def connection_made(self, transport):
            print("port connected")
        def data_received(self, data):
            for currentByte in bytearray(data):
                if currentByte == MatrixOrbital.Constants.UP_KEY:
                    self._panel.setBrightness((self._panel._brightness + 20) & 0xFF)
                elif currentByte == MatrixOrbital.Constants.DOWN_KEY:
                    self._panel.setBrightness(max((self._panel._brightness - 20),0))
                elif currentByte == MatrixOrbital.Constants.LEFT_KEY:
                    self._panel.setContrast(max((self._panel._contrast - 5),0))
                elif currentByte == MatrixOrbital.Constants.RIGHT_KEY:
                    self._panel.setContrast((self._panel._contrast + 5) & 0xFF)
        def connection_lost(self, exc):
            if exc:
                print(str(exc))
                traceback.print_exc(exc)
            print('port closed\n')

    def demoThreadedLedChanges(self):
        while self._state._ledsDemoRunning:
            for led in range(1,4):
                self.setLedOff(led)
                time.sleep(0.3)
                self.setLedYellow(led)
                time.sleep(0.3)
                self.setLedRed(led)
                time.sleep(0.3)
                self.setLedGreen(led)
                time.sleep(0.3)

    def __init__(self, port = '/dev/ttyUSB0', baudrate = 19200):
        self._port = port
        self._baudrate = baudrate
        self._serialDriver = serial.Serial(port=port, baudrate=baudrate)
        self._state = MatrixOrbital.State()
        self.ThreadSerialListener._panel = self
        self._listener = serial.threaded.ReaderThread(self._serialDriver, self.ThreadSerialListener)
        self.setBrightness(200)
        self.setContrast(128)

    def sendBytes(self, buffer):
        with self._state._serialSendLock:
            self._serialDriver.write(buffer)

    def dumpFileFromFilesystem(self, fontNoBitmap, fileId, outputFilename):
        self._serialDriver.reset_input_buffer()
        self.sendBytes([0xfe,0xb2, 0 if fontNoBitmap else 1, fileId])
        fileSizeInBytes = int.from_bytes(self._serialDriver.read(4), byteorder="little", signed=False) - 2
        width  = int.from_bytes(self._serialDriver.read(1), byteorder="little", signed=False)
        height = int.from_bytes(self._serialDriver.read(1), byteorder="little", signed=False)
        print("Downloading {} {} from panel filesystem to {}...".format("font" if fontNoBitmap else "bitmap", fileId, outputFilename))
        open(outputFilename+".info", "w").writelines(["width: {}\n".format(width), "height: {}\n".format(height)])
        open(outputFilename, "wb").write(self._serialDriver.read(fileSizeInBytes))
        print("done!")

    def startKeyboardControlThread(self):
        self._listener.start()

    def stopKeyboardControlThread(self):
        self._listener.stop()

    def startLedsDemoThread(self):
        self._state._ledsDemoRunning = True
        self._threadLedsDemo = Thread(target=self.demoThreadedLedChanges)
        self._threadLedsDemo.start()

    def stopLedsDemoThread(self):
        self._state._ledsDemoRunning = False

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
        self.sendBytes(bytes(text, "UTF-8"))

    def setSendAllKeyPresses(self):
        self.sendBytes([0xfe, 0x41])

    def setBrightness(self, brightness):
        self._brightness = brightness
        self.sendBytes([0xfe, 0x99, brightness])

    def setContrast(self, contrast):
        self._contrast = contrast
        self.sendBytes([0xfe, 0x50, contrast])

    def drawSpiral(self, color, centerPos, maxRadius, incRadius = 0.03, incAngle = pi/180, startingAngle =0):
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

    def dumpInput(self, charsCount):
        self.writeText("Press {} keys to finish".format(charsCount))
        self.setSendAllKeyPresses()
        for i in range(charsCount):
            char = self._serialDriver.read(1)
            print(char)
            self.setCursorPos(7, 0)
            self.writeText(str(charsCount-i-1))
            self.setCursorPos(i+1, 3)
            self.sendBytes(char)


def main(port):
    myPanel = MatrixOrbital(port=port)


    # dump bitmap 1 to a file
    myPanel.dumpFileFromFilesystem(0, 1, "bitmap1_output.data")

    # listen to the keyboard for contrast and brightness controls
    myPanel.startKeyboardControlThread()
    myPanel.setDisplayOn()
    myPanel.clearScreen()
    
    # simple text
    myPanel.writeText("hello world!")
    time.sleep(1)
    myPanel.startLedsDemoThread()
    
    myPanel.clearScreen()
    myPanel.drawSpiral(200, [int(myPanel.Constants.PANEL_WIDTH/2), int(myPanel.Constants.PANEL_HEIGHT/2)], myPanel.Constants.PANEL_HEIGHT)
    sign = 1
    for offsetX in [25,50]:
        myPanel.drawSpiral(200, [int(myPanel.Constants.PANEL_WIDTH/2) + offsetX, int(myPanel.Constants.PANEL_HEIGHT/2)], myPanel.Constants.PANEL_HEIGHT, incAngle = sign * pi/180)
        sign = sign * -1
        myPanel.drawSpiral(200, [int(myPanel.Constants.PANEL_WIDTH/2) - offsetX, int(myPanel.Constants.PANEL_HEIGHT/2)], myPanel.Constants.PANEL_HEIGHT, incAngle = sign * pi/180)
        sign = sign * -1
    #leds
    #for i in range(0,4):


    #stop keyboard thread and start keyboard demo
    myPanel.stopKeyboardControlThread()
    myPanel.stopLedsDemoThread()
    myPanel.clearScreen()
    myPanel.dumpInput(8)

if __name__ == "__main__":
    port = argv[1] if len(argv) == 2 else "/dev/ttyUSB0"
    main(port=port)


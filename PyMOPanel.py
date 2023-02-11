#!/usr/bin/env python3
import serial
import time
import math
import threading
from sys import argv

class MatrixOrbital:
    PANEL_WIDTH  = 192
    PANEL_HEIGHT = 64
    UP_KEY          = chr(0x42)
    DOWN_KEY        = chr(0x48)
    LEFT_KEY        = chr(0x44)
    RIGHT_KEY       = chr(0x43)
    CENTER_KEY      = chr(0x45)
    TOP_LEFT_KEY    = chr(0x41)
    BOTTOM_LEFT_KEY = chr(0x47)
    def read_from_port(matrixOrbitalInstance):
        while matrixOrbitalInstance._threadKeyboardRunning:
           if matrixOrbitalInstance._serialDriver.in_waiting  == 0:
               continue
           reading = matrixOrbitalInstance._serialDriver.read()
           if reading == MatrixOrbital.UP_KEY:
               matrixOrbitalInstance.setBrightness((matrixOrbitalInstance._brightness + 20) & 0xFF)
           elif reading == MatrixOrbital.DOWN_KEY:
               matrixOrbitalInstance.setBrightness(max((matrixOrbitalInstance._brightness - 20),0))
           elif reading == MatrixOrbital.LEFT_KEY:
               matrixOrbitalInstance.setContrast(max((matrixOrbitalInstance._contrast - 5),0))
           elif reading == MatrixOrbital.RIGHT_KEY:
               matrixOrbitalInstance.setContrast((matrixOrbitalInstance._contrast + 5) & 0xFF)
           else:
               matrixOrbitalInstance._dumpBuffer += reading 
    def __init__(self, port = '/dev/ttyUSB0', baudrate = 19200):
        self._port = port
        self._baudrate = baudrate
        self._serialDriver = serial.Serial(port=port, baudrate=baudrate)
        self._threadKeyboardRunning = False
        self.setBrightness(200)
        self.setContrast(128)

    def startThreadKeyoard(self):
        self._threadKeyboard = threading.Thread(target=MatrixOrbital.read_from_port, args=(self,))
        self._threadKeyboardRunning = True
        self._threadKeyboard.start()

    def stopThreadKeyboard(self):
        self._threadKeyboardRunning = False
        self._threadKeyboard.join()

    def dumpFileFromFilesystem(self, fontNoBitmap, fileId, outputFilename):
        self._serialDriver.reset_input_buffer()
        self._serialDriver.write([0xfe,0xb2, 0 if fontNoBitmap else 1, fileId])
        fileSizeInBytes = int.from_bytes(self._serialDriver.read(4), byteorder="little", signed=False) - 2
        width  = int.from_bytes(self._serialDriver.read(1), byteorder="little", signed=False)
        height = int.from_bytes(self._serialDriver.read(1), byteorder="little", signed=False)
        print("Downloading {} {} from panel filesystem to {}...".format("font" if fontNoBitmap else "bitmap", fileId, outputFilename))
        open(outputFilename+".info", "w").writelines(["width: {}\n".format(width), "height: {}\n".format(height)])
        open(outputFilename, "wb").write(self._serialDriver.read(fileSizeInBytes))
        print("done!")


    def setGPOState(self, gpio, value):
        self._serialDriver.write([0xfe, 0x56 if value == 0 else 0x57, gpio])

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
        self._serialDriver.write([0xfe, 0x42, 0x10])

    def setDisplayOff(self):
        self._serialDriver.write([0xfe, 0x46, 0x10])

    def moveCursorHome(self):
        self._serialDriver.write([0xfe, 0x48, 0x10])

    def clearScreen(self):
        self._serialDriver.write([0xfe, 0x58, 0x10])

    def setDrawingColor(self, color):
        self._serialDriver.write([0xfe, 0x63, color, 0x10])

    def drawPixel(self, x, y):
        self._serialDriver.write([0xfe, 0x70, x, y, 0x10])

    def drawSolidRectangle(self, color, x0, y0, x1, y1):
        self._serialDriver.write([0xfe, 0x78, color, x0, y0, x1, y1])

    def drawLine(self, x0,y0,x1,y1):
        self._serialDriver.write([0xfe,0x6c,x0,y0,x1,y1])

    def setCursorPos(self, col, row):
        self._serialDriver.write([0xfe,0x47,col,row])

    def writeText(self, text):
        self._serialDriver.write(bytes(text, "UTF-8"))

    def setSendAllKeyPresses(self):
        self._serialDriver.write([0xfe, 0x41])

    def setBrightness(self, brightness):
        self._brightness = brightness
        self._serialDriver.write([0xfe, 0x99, brightness])

    def setContrast(self, contrast):
        self._contrast = contrast
        self._serialDriver.write([0xfe, 0x50, contrast])

    def drawSpiral(self, color, centerPos, maxRadius, incRadius = 0.03, incAngle = math.pi/180, startingAngle =0):
        self.setDrawingColor(color)
        angle = startingAngle
        radius = 0
        while radius < maxRadius:
            x = int(centerPos[0] + math.cos(angle) * radius)
            y = int(centerPos[1] + math.sin(angle) * radius)
            if x<0 or x>self.PANEL_WIDTH or y <0 or y > self.PANEL_HEIGHT:
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
            self._serialDriver.write(char)


def main(port):
    myPanel = MatrixOrbital(port=port)


    # dump bitmap 1 to a file
    myPanel.dumpFileFromFilesystem(0, 1, "bitmap1_output.data")

    # listen to the keyboard for contrast and brightness controls
    myPanel.startThreadKeyoard()
    myPanel.setDisplayOn()
    myPanel.clearScreen()
    
    # simple text
    myPanel.writeText("hello world!")
    time.sleep(1)
    
    myPanel.clearScreen()
    myPanel.drawSpiral(200, [int(myPanel.PANEL_WIDTH/2), int(myPanel.PANEL_HEIGHT/2)], myPanel.PANEL_HEIGHT)
    sign = 1
    for offsetX in [10,30,50]:
        myPanel.drawSpiral(200, [int(myPanel.PANEL_WIDTH/2) + offsetX, int(myPanel.PANEL_HEIGHT/2)], myPanel.PANEL_HEIGHT, incAngle = sign * math.pi/180)
        sign = sign * -1
        myPanel.drawSpiral(200, [int(myPanel.PANEL_WIDTH/2) - offsetX, int(myPanel.PANEL_HEIGHT/2)], myPanel.PANEL_HEIGHT, incAngle = sign * math.pi/180)
        sign = sign * -1
    #leds
    for i in range(0,4):
        for led in range(1,4):
            myPanel.setLedOff(led)
            time.sleep(0.3)
            myPanel.setLedYellow(led)
            time.sleep(0.3)
            myPanel.setLedRed(led)
            time.sleep(0.3)
            myPanel.setLedGreen(led)
            time.sleep(0.3)


    #stop keyboard thread and start keyboard demo
    myPanel.stopThreadKeyboard()
    myPanel.clearScreen()
    myPanel.dumpInput(8)

if __name__ == "__main__":
    port = argv[1] if len(argv) == 2 else "/dev/ttyUSB0"
    main(port=port)


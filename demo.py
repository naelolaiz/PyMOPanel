#!/usr/bin/env python3
import serial.threaded
import time
from math import pi, sin, cos 
from threading import Thread 
from sys import argv
import traceback
from random import random,randint

from PyMOPanel import MatrixOrbital

class Demo:
    def demoThreadedLedChanges(self):
        while self._ledsDemoRunning:
            for led in range(3):
                self._panel.setLedOff(led)
                time.sleep(0.2)
                self._panel.setLedYellow(led)
                time.sleep(0.1)
                self._panel.setLedRed(led)
                time.sleep(0.1)
                self._panel.setLedGreen(led)
                time.sleep(0.1)

    def __init__(self, panel):
        self._panel = panel
        self._ledsDemoRunning = False

    def drawSpiral(self, color, centerPos, maxRadius, incRadius = 0.03, incAngle = pi/100, startingAngle =0):
        self._panel.setDrawingColor(color)
        angle = startingAngle
        radius = 0
        while radius < maxRadius:
            x = int(centerPos[0] + cos(angle) * radius)
            y = int(centerPos[1] + sin(angle) * radius)
            if x<0 or x>MatrixOrbital.Constants.PANEL_WIDTH or y <0 or y > MatrixOrbital.Constants.PANEL_HEIGHT:
                break
            self._panel.drawPixel(x,y)
            radius += incRadius
            angle +=incAngle

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
        self.drawSpiral(200, [MatrixOrbital.Constants.CENTER_X, MatrixOrbital.Constants.CENTER_Y], MatrixOrbital.Constants.PANEL_HEIGHT)
        sign = 1
        for i in range(22):
            offsetX = randint(-75,75)
            offsetY = randint(-20,20)
            self.drawSpiral(200, 
                                   [MatrixOrbital.Constants.CENTER_X + offsetX, MatrixOrbital.Constants.CENTER_Y + offsetY],
                                   randint(10,MatrixOrbital.Constants.PANEL_HEIGHT),
                                   incAngle = sign * pi / randint(10,60),
                                   incRadius = 0.02 + 0.25 * random())
            sign = sign * -1

    def runDemoBarGraphs(self):
        self._panel.clearScreen()
        time.sleep(0.2)
        numberOfBars = MatrixOrbital.Constants.MAX_NUMBER_OF_BARS
        deltaX = int(MatrixOrbital.Constants.PANEL_WIDTH / numberOfBars)
        for i in range(0, MatrixOrbital.Constants.PANEL_WIDTH, deltaX):
            index = self._panel.addBarGraph(i,          0,
                                            i+deltaX-1, MatrixOrbital.Constants.PANEL_HEIGHT,
                                            "VerticalBottom")

        scaler = 1/1.3
        for i in range(400):
            bar = randint(0,numberOfBars-1)
            self._panel.setBarGraphValue(bar, random()*scaler)
            time.sleep(0.03)

    def runDemoLissajous(self, cycles):
        self._panel.clearScreen()
        for i in range(cycles):
            self._panel.clearScreen()
            time.sleep(0.2)
            phaseX=0
            phaseY=0
            incPhaseX = random()*pi/60
            incPhaseY = random()*pi/60
            for frame in range(700):
                x = MatrixOrbital.Constants.CENTER_X + int(MatrixOrbital.Constants.CENTER_X * cos(phaseX))
                y = MatrixOrbital.Constants.CENTER_Y + int(MatrixOrbital.Constants.CENTER_Y * sin(phaseY))
                self._panel.drawPixel(x,y)
                phaseX += incPhaseX
                phaseY += incPhaseY
                time.sleep(0.003)


def main(port):
    myPanel = MatrixOrbital(port=port)
    demo = Demo(myPanel)

    # dump complete filesystem to a file
    #myPanel.dumpCompleteFilesystem('filesystem.data')

    # dump bitmap 1 to a file
    #myPanel.dumpFileFromFilesystem(0, 1, 'bitmap1_output.data')

    # enable controlling brightness and contrast by the keyboard
    myPanel.enableKeyboardControllingContrastAndBrightness()

    myPanel.setDisplayOn()
    myPanel.clearScreen()

    # simple text
    myPanel.writeText('hello world!\n')
    time.sleep(2)
    myPanel.clearScreen()

    # start blinking leds on the background
    demo.startLedsDemoThread()
    time.sleep(1)

    # stop leds blinking before the animation
    demo.stopLedsDemoThread()
    myPanel.drawBMP('gif/resized_scissors.gif', x0=40)
    demo.startLedsDemoThread()
    time.sleep(1)

    # bar graphs
    demo.runDemoBarGraphs()

    time.sleep(1)

    # draw 10 Lissajous curves
    demo.runDemoLissajous(10)

    time.sleep(1)

    # draw some spirals
    demo.runDemoSpirals()
    
    # stop keyboard thread 
    myPanel.disableKeyboardControllingContrastAndBrightness()

    # start keyboard demo
    demo.runDemoPressedKeys(8)

    # show a BMP and exit
    demo.stopLedsDemoThread()
    myPanel.clearScreen()
    time.sleep(1)
    myPanel.drawBMP('gif/resized_corridor.gif', x0=40)
    myPanel.drawBMP('gif/resized_corridor.gif', x0=40, inverted=True)
    time.sleep(0.2)
    myPanel.drawBMP('gif/resized_line.gif', x0=50, thresholdForBW=128)
    myPanel.drawBMP('gif/resized_line.gif', x0=50)
    time.sleep(0.5)

    demo.startLedsDemoThread()
    myPanel.drawBMP('bmp/goodbye.bmp')
    time.sleep(2)
    demo.stopLedsDemoThread()
    myPanel.setDisplayOff()
    time.sleep(1)
    for i in range(3):
        myPanel.setLedOff(i)

if __name__ == '__main__':
    port = argv[1] if len(argv) == 2 else '/dev/ttyUSB0'
    main(port=port)


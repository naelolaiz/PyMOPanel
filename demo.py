#!/usr/bin/env python3
import time
from math import pi, sin, cos 
from threading import Thread 
from sys import argv
from random import random,randint

from PyMOPanel import PyMOPanel
from PyMOPanel.constants import Constants
from PyMOPanel.bar_graph import Direction
from PyMOPanel.gpo import LedStatus

class Demo:
    def demoThreadedLedChanges(self):
        while self._ledsDemoRunning:
            for led in range(3):
                self._panel.setLed(led, LedStatus.OFF)
                time.sleep(0.2)
                self._panel.setLed(led, LedStatus.YELLOW)
                time.sleep(0.1)
                self._panel.setLed(led, LedStatus.RED)
                time.sleep(0.1)
                self._panel.setLed(led, LedStatus.GREEN)
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
            if x<0 or x>Constants.PANEL_WIDTH or y <0 or y > Constants.PANEL_HEIGHT:
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
        self._panel.print('Press {} keys to finish'.format(charsCount))
        self._panel.setAutoTransmitKeyPressed(True)
        for i in range(charsCount):
            char = self._panel.readBytes(1)
            self._panel.print(str(charsCount-i-1), x0=7, y0=0)
            self._panel.print(char, x0=i+1, y0=3)

    def runDemoSpirals(self, spiralsCount):
        self._panel.clearScreen()
        self.drawSpiral(200, [Constants.CENTER_X, Constants.CENTER_Y], Constants.PANEL_HEIGHT)
        sign = 1
        for i in range(spiralsCount-1):
            offsetX = randint(-75,75)
            offsetY = randint(-20,20)
            self.drawSpiral(200, 
                                   [Constants.CENTER_X + offsetX, Constants.CENTER_Y + offsetY],
                                   randint(10,Constants.PANEL_HEIGHT),
                                   incAngle = sign * pi / randint(10,60),
                                   incRadius = 0.02 + 0.25 * random())
            sign = sign * -1

    def runDemoBarGraphs(self, changesCount, sleepTimeBetweenChange = 0.03):
        self._panel.clearScreen()
        time.sleep(0.2)
        numberOfBars = Constants.MAX_NUMBER_OF_BARS
        deltaX = int(Constants.PANEL_WIDTH / numberOfBars)
        for i in range(0, Constants.PANEL_WIDTH, deltaX):
            index = self._panel.addBarGraph(i, 0,
                                            i+deltaX-1, Constants.PANEL_HEIGHT,
                                            Direction(Direction.VERTICAL_BOTTOM_TO_TOP))
        scaler = 1/1.3
        for i in range(changesCount):
            bar = randint(0,numberOfBars-1)
            self._panel.setBarGraphValue(bar, random()*scaler)
            time.sleep(sleepTimeBetweenChange)

    def runDemoLissajous(self, cycles):
        self._panel.clearScreen()
        for i in range(cycles):
            self._panel.clearScreen()
            time.sleep(0.2)
            phaseX=0
            phaseY=0
            incPhaseX = random()*pi/60
            incPhaseY = random()*pi/60
            for frame in range(1500):
                x = Constants.CENTER_X + int(Constants.CENTER_X * cos(phaseX))
                y = Constants.CENTER_Y + int(Constants.CENTER_Y * sin(phaseY))
                self._panel.drawPixel(x,y)
                phaseX += incPhaseX
                phaseY += incPhaseY
                time.sleep(0.003)

def main(port):
    myPanel = PyMOPanel(port=port)
    demo = Demo(myPanel)

    # enable controlling brightness and contrast by the keyboard
    myPanel.enableKeyboardControllingContrastAndBrightness()

    # turn screen on
    myPanel.clearScreen()
    myPanel.setScreen(True)

    # simple text
    myPanel.print('hello world!\n')
    time.sleep(2)
    myPanel.clearScreen()

    # start blinking leds on the background
    demo.startLedsDemoThread()
    time.sleep(1)

    # stop leds blinking before the animation
    demo.stopLedsDemoThread()
    myPanel.uploadAndShowBitmap('gif/resized_scissors.gif', x0=40)
    demo.startLedsDemoThread()
    time.sleep(1)

    # bar graphs
    demo.runDemoBarGraphs(350)

    time.sleep(1)

    # draw 10 Lissajous curves
    demo.runDemoLissajous(10)

    time.sleep(1)

    # draw 10 spirals
    demo.runDemoSpirals(10)
    
    # stop keyboard thread 
    myPanel.disableKeyboardControllingContrastAndBrightness()

    # start keyboard demo
    demo.runDemoPressedKeys(8)

    # show a BMP and exit
    demo.stopLedsDemoThread()
    myPanel.clearScreen()
    time.sleep(1)
    myPanel.uploadAndShowBitmap('gif/resized_corridor.gif', x0=40)
    myPanel.uploadAndShowBitmap('gif/resized_corridor.gif', x0=40, inverted=True)
    time.sleep(0.2)
    myPanel.uploadAndShowBitmap('gif/resized_line.gif', x0=50, thresholdForBW=128)
    myPanel.uploadAndShowBitmap('gif/resized_line.gif', x0=50)
    time.sleep(0.5)

    demo.startLedsDemoThread()
    myPanel.uploadAndShowBitmap('bmp/goodbye.bmp')
    time.sleep(2)
    demo.stopLedsDemoThread()

    # turn screen off
    myPanel.setScreen(False)
    time.sleep(1)
    for i in range(3):
        myPanel.setLed(i, LedStatus.OFF)

if __name__ == '__main__':
    port = argv[1] if len(argv) == 2 else '/dev/ttyUSB0'
    main(port=port)


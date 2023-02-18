#!/usr/bin/env python3
import time
from math import pi, sin, cos 
from threading import Thread 
from random import random,randint
from sys import argv, path

path.append("..")
from PyMOPanel import PyMOPanel
from PyMOPanel.graphics import Graphics
from PyMOPanel.bar_graph import Direction, BarGraphManager
from PyMOPanel.gpo import LedStatus

class Demo:
    def demoThreadedLedChanges(self):
        while self._ledsDemoRunning:
            for led in range(3):
                self._panel.gpo.setLed(led, LedStatus.OFF)
                time.sleep(0.2)
                self._panel.gpo.setLed(led, LedStatus.YELLOW)
                time.sleep(0.1)
                self._panel.gpo.setLed(led, LedStatus.RED)
                time.sleep(0.1)
                self._panel.gpo.setLed(led, LedStatus.GREEN)
                time.sleep(0.1)

    def __init__(self, panel):
        self._panel = panel
        self._ledsDemoRunning = False

    def drawSpiral(self, color, centerPos, maxRadius, incRadius = 0.03, incAngle = pi/100, startingAngle =0):
        self._panel.graphics.setDrawingColor(color)
        angle = startingAngle
        radius = 0
        while radius < maxRadius:
            x = int(centerPos[0] + cos(angle) * radius)
            y = int(centerPos[1] + sin(angle) * radius)
            if x<0 or x>Graphics.PANEL_WIDTH or y <0 or y > Graphics.PANEL_HEIGHT:
                break
            self._panel.graphics.drawPixel(x,y)
            radius += incRadius
            angle +=incAngle
            time.sleep(0.00003)

    def startLedsDemoThread(self):
        self._ledsDemoRunning = True
        self._threadLedsDemo = Thread(target=self.demoThreadedLedChanges)
        self._threadLedsDemo.start()

    def stopLedsDemoThread(self):
        self._ledsDemoRunning = False

    def runDemoPressedKeys(self, charsCount):
        self._panel.screen.clear()
        self._panel.text.print('Press {} keys to finish'.format(charsCount))
        self._panel.keyboard.setAutoTransmitKeyPressed(True)
        for i in range(charsCount):
            char = self._panel.readBytes(1)
            self._panel.text.print(str(charsCount-i-1), x0=7, y0=0)
            self._panel.text.print(char, x0=i+1, y0=3)

    def runDemoSpirals(self, spiralsCount):
        self._panel.screen.clear()
        self.drawSpiral(200, [Graphics.CENTER_X, Graphics.CENTER_Y], Graphics.PANEL_HEIGHT)
        sign = 1
        for i in range(spiralsCount-1):
            offsetX = randint(-75,75)
            offsetY = randint(-20,20)
            self.drawSpiral(200, 
                                   [Graphics.CENTER_X + offsetX, Graphics.CENTER_Y + offsetY],
                                   randint(10,Graphics.PANEL_HEIGHT),
                                   incAngle = sign * pi / randint(10,60),
                                   incRadius = 0.02 + 0.25 * random())
            sign = sign * -1

    def runDemoBarGraphs(self, changesCount, sleepTimeBetweenChange = 0.03):
        self._panel.screen.clear()
        time.sleep(0.2)
        numberOfBars = BarGraphManager.MAX_NUMBER_OF_BARS
        deltaX = int(Graphics.PANEL_WIDTH / numberOfBars)
        for i in range(0, Graphics.PANEL_WIDTH, deltaX):
            index = self._panel.barGraphs.addBarGraph(i, 0,
                                                      deltaX-1, Graphics.PANEL_HEIGHT,
                                                      Direction(Direction.VERTICAL_BOTTOM_TO_TOP))
        scaler = 1/1.3
        for i in range(changesCount):
            bar = randint(0,numberOfBars-1)
            self._panel.barGraphs.setBarGraphValue(bar, random()*scaler)
            time.sleep(sleepTimeBetweenChange)

    def runDemoLissajous(self, cycles):
        for i in range(cycles):
            self._panel.screen.clear()
            #time.sleep(0.1)
            phaseX=0
            phaseY=0
            incPhaseX = random()*pi/60
            incPhaseY = random()*pi/60
            for frame in range(1500):
                x = Graphics.CENTER_X + int(Graphics.CENTER_X * cos(phaseX))
                y = Graphics.CENTER_Y + int(Graphics.CENTER_Y * sin(phaseY))
                self._panel.graphics.drawPixel(x,y)
                phaseX += incPhaseX
                phaseY += incPhaseY
                time.sleep(0.00003)

def main(port):
    myPanel = PyMOPanel(port=port)
    myPanel.setBaudRate(19200)
    myPanel.setBaudRate(115200)
    demo = Demo(myPanel)

    # in my panel neither of these work
    print("Version number: {}. Module type: {}".format(myPanel.getVersionNumber(), myPanel.getModuleType()))

    # enable controlling brightness and contrast by the keyboard
    myPanel.keyboard.controlBrighnessAndContrastByKeypad(True)

    # turn screen on
    myPanel.screen.clear()
    myPanel.screen.enable(True)

    # simple text
    myPanel.text.print('hello world!\n')
    time.sleep(2)
    myPanel.screen.clear()

    # start blinking leds on the background
    demo.startLedsDemoThread()
    time.sleep(1)

    # stop leds blinking before the animation
    demo.stopLedsDemoThread()
    myPanel.graphics.uploadAndShowBitmap('resources/gif/resized_scissors.gif', x0=40, framesPerSecond = 3)
    demo.startLedsDemoThread()
    time.sleep(1)

    # bar graphs
    demo.runDemoBarGraphs(350)

    time.sleep(1)

    # draw Lissajous curves
    demo.runDemoLissajous(5)

    time.sleep(1)

    # draw spirals
    demo.runDemoSpirals(40)
    
    # stop keyboard thread 
    myPanel.keyboard.controlBrighnessAndContrastByKeypad(False)

    # start keyboard demo
    demo.runDemoPressedKeys(5)

    # show a BMP and exit
    demo.stopLedsDemoThread()
    myPanel.screen.clear()
    time.sleep(1)
    myPanel.graphics.uploadAndShowBitmap('resources/gif/resized_corridor.gif', x0=40, framesPerSecond = 10)
    myPanel.graphics.uploadAndShowBitmap('resources/gif/resized_corridor.gif', x0=40, inverted=True, framesPerSecond = 6)
    time.sleep(0.2)
    myPanel.graphics.uploadAndShowBitmap('resources/gif/resized_line.gif', x0=50, thresholdForBW=128)
    myPanel.graphics.uploadAndShowBitmap('resources/gif/resized_line.gif', x0=50)
    time.sleep(0.5)

    demo.startLedsDemoThread()
    myPanel.graphics.uploadAndShowBitmap('resources/bmp/goodbye.bmp')
    time.sleep(2)
    demo.stopLedsDemoThread()

    # turn screen off
    myPanel.screen.enable(False)
    time.sleep(1)
    for i in range(3):
        myPanel.gpo.setLed(i, LedStatus.OFF)
    myPanel.setBaudRate(19200)

if __name__ == '__main__':
    port = argv[1] if len(argv) == 2 else '/dev/ttyUSB0'
    main(port=port)


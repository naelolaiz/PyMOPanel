#!/usr/bin/env python3

import psutil
import time
from sys import path, argv

path.append("..")
from PyMOPanel import PyMOPanel
from PyMOPanel.bar_graph import Direction, BarGraphManager
from PyMOPanel.filesystem import FileType
from PyMOPanel.graphics import Graphics
from PyMOPanel.font import Font

def main(port):
    myPanel = PyMOPanel(port=port)
    myPanel.setBaudRate(19200)
    myPanel.setBaudRate(115200)
    myPanel.setBaudRate(19200)

    cpuCount = psutil.cpu_count()

    myPanel.screen.clear()
    myPanel.screen.enable(True)

    # TODO: upload font.
    fontIdToUse = 1
    myPanel.text.selectCurrentFont(fontIdToUse)
    fontToUse = Font.fromBuffer(myPanel.fs.downloadFile(FileType.FONT, fontIdToUse))
    numberOfLines = int(Graphics.PANEL_HEIGHT / fontToUse.getHeight())

    # show layout for up to lines-1 cpus
    cpuToShowCount = min(numberOfLines-1, cpuCount)

    heightBars = int(Graphics.PANEL_HEIGHT / numberOfLines)


    leftMargin = myPanel.text.getLeftMargin()
    topMargin = myPanel.text.getTopMargin()
    charSpacing = myPanel.text.getCharSpacing()
    lineSpacing = myPanel.text.getLineSpacing()

    templateForCPUCaption = "cpu{}:     %"
    textLengthInChars = len(templateForCPUCaption.format(1))
    textWidthInPixels = fontToUse.getNominalWidth() * textLengthInChars + charSpacing * (textLengthInChars-1)

    widthBars = Graphics.CENTER_X - textWidthInPixels

    xOffset = leftMargin + textWidthInPixels + 4
    yOffset = topMargin
    for cpuNr in range(cpuToShowCount):
        myPanel.text.print(templateForCPUCaption.format(cpuNr), col=0, row=cpuNr+1)
        myPanel.barGraphs.addBarGraph(xOffset,  yOffset,
                                      widthBars, heightBars,
                                      Direction(Direction.HORIZONTAL_LEFT_TO_RIGHT))
        yOffset += lineSpacing + heightBars

                                      
    # last line show mem usage
    myPanel.text.print("mem.:     %", col=0, row=cpuToShowCount+1)
    myPanel.barGraphs.addBarGraph(xOffset,  yOffset,
                                  widthBars, heightBars,
                                  Direction(Direction.HORIZONTAL_LEFT_TO_RIGHT))

    while True:
        cpu_percentage_per_cpu = psutil.cpu_percent(1, percpu=True)
        total_percentage_cpu = sum(cpu_percentage_per_cpu) / len(cpu_percentage_per_cpu)
        memory_percentage_usage = psutil.virtual_memory().percent
        for cpuNr in range(cpuToShowCount):
            myPanel.barGraphs.setBarGraphValue(cpuNr, cpu_percentage_per_cpu[cpuNr] / 100)
            myPanel.text.print("{:5.1f}".format(cpu_percentage_per_cpu[cpuNr]), col= 5, row=cpuNr+1)
        
        myPanel.barGraphs.setBarGraphValue(cpuToShowCount,  memory_percentage_usage/ 100)
        myPanel.text.print("{:5.1f}".format(memory_percentage_usage), col=5, row=cpuToShowCount+1)
            
        time.sleep(1)

if __name__ == '__main__':
    port = argv[1] if len(argv) == 2 else '/dev/ttyUSB0'
    main(port=port)

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
    panel = PyMOPanel(port=port)

    # To prevent baudrate mismatches between the host and the panel, since using in the code both 19200 (default) and 115200 and 
    # a program may be stopped when using 115200, here we first set the baud rate to 115200. So if the panel is at 19200 it will 
    # effectively change both the host and the panel to 115200. But if the panel was at 115200, the command (sent at 19200) won't
    # be a valid command and will be ignored by the panel -or print just garbage-, but the serial connection would be set at 115200,
    # matching the panel. Then we just set our desired baudrate to work: 19200

    panel.setBaudRate(115200)
    panel.setBaudRate(19200)

    panel.screen.clear()
    panel.screen.enable(True)

    # check available fonts, and select first one available. TODO: upload custom font?
    available_font_ids = ([file['file_index'] for file in panel.fs.ls() if file['file_type'] == FileType.FONT])
    for font_id_to_use in available_font_ids:
        font_to_use = Font.fromBuffer(panel.fs.downloadFile(FileType.FONT, font_id_to_use))
        if font_to_use:
            break
    assert font_to_use
    print ("Using font id {}".format(font_id_to_use))
    panel.text.selectCurrentFont(font_id_to_use)

    panel.keyboard.enableKeyboardControllingContrastAndBrightness()
    numberOfLines = int(Graphics.PANEL_HEIGHT / font_to_use.getHeight())

    # show layout for up to lines-1 cpus
    cpuCount = psutil.cpu_count()
    cpuToShowCount = min(numberOfLines-1, cpuCount)

    heightBars = int(Graphics.PANEL_HEIGHT / numberOfLines)


    leftMargin = panel.text.getLeftMargin()
    topMargin = panel.text.getTopMargin()
    charSpacing = panel.text.getCharSpacing()
    lineSpacing = panel.text.getLineSpacing()

    templateForCPUCaption = "cpu{}:     %"
    textLengthInChars = len(templateForCPUCaption.format(1))
    textWidthInPixels = font_to_use.getNominalWidth() * textLengthInChars + charSpacing * (textLengthInChars-1)

    widthBars = Graphics.CENTER_X - textWidthInPixels

    xOffset = leftMargin + textWidthInPixels + 4
    yOffset = topMargin
    for cpuNr in range(cpuToShowCount):
        panel.text.print(templateForCPUCaption.format(cpuNr), col=0, row=cpuNr+1)
        panel.barGraphs.addBarGraph(xOffset,  yOffset,
                                      widthBars, heightBars,
                                      Direction(Direction.HORIZONTAL_LEFT_TO_RIGHT))
        yOffset += lineSpacing + heightBars

    # last line show mem usage
    panel.text.print("mem.:     %", col=0, row=cpuToShowCount+1)
    panel.barGraphs.addBarGraph(xOffset,  yOffset,
                                  widthBars, heightBars,
                                  Direction(Direction.HORIZONTAL_LEFT_TO_RIGHT))

    while True:
        cpu_percentage_per_cpu = psutil.cpu_percent(0.3, percpu=True)
        memory_percentage_usage = psutil.virtual_memory().percent
        for cpuNr in range(cpuToShowCount):
            panel.barGraphs.setBarGraphValue(cpuNr, cpu_percentage_per_cpu[cpuNr] / 100)
            panel.text.print("{:5.1f}".format(cpu_percentage_per_cpu[cpuNr]), col= 5, row=cpuNr+1)
        
        panel.barGraphs.setBarGraphValue(cpuToShowCount,  memory_percentage_usage/ 100)
        panel.text.print("{:5.1f}".format(memory_percentage_usage), col=5, row=cpuToShowCount+1)
            
        time.sleep(0.3)

if __name__ == '__main__':
    port = argv[1] if len(argv) == 2 else '/dev/ttyUSB0'
    main(port=port)

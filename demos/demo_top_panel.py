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

    panel.keyboard.controlBrighnessAndContrastByKeypad(True)
    number_of_lines = int(Graphics.PANEL_HEIGHT / font_to_use.getHeight())

    # show layout for up to lines-1 cpus
    cpu_count = psutil.cpu_count()
    cpu_to_show_count = min(number_of_lines-1, cpu_count)

    bar_height = int(Graphics.PANEL_HEIGHT / number_of_lines)


    left_margin = panel.text.getLeftMargin()
    top_margin = panel.text.getTopMargin()
    char_spacing = panel.text.getCharSpacing()
    line_spacing = panel.text.getLineSpacing()

    template_for_cpu_caption = "cpu{}:     %"
    text_length_in_chars = len(template_for_cpu_caption.format(1))
    text_width_in_pixels = font_to_use.getNominalWidth() * text_length_in_chars + char_spacing * (text_length_in_chars-1)

    bar_width = Graphics.CENTER_X - text_width_in_pixels

    offset_x = left_margin + text_width_in_pixels + 4
    offset_y = top_margin
    for cpu_number in range(cpu_to_show_count):
        panel.text.print(template_for_cpu_caption.format(cpu_number), col=0, row=cpu_number+1)
        panel.barGraphs.addBarGraph(offset_x,  offset_y,
                                      bar_width, bar_height,
                                      Direction(Direction.HORIZONTAL_LEFT_TO_RIGHT))
        offset_y += line_spacing + bar_height

    # last line show mem usage
    panel.text.print("mem.:     %", col=0, row=cpu_to_show_count+1)
    panel.barGraphs.addBarGraph(offset_x,  offset_y,
                                  bar_width, bar_height,
                                  Direction(Direction.HORIZONTAL_LEFT_TO_RIGHT))

    while True:
        cpu_percentage_per_cpu = psutil.cpu_percent(0.3, percpu=True)
        memory_percentage_usage = psutil.virtual_memory().percent
        for cpu_number in range(cpu_to_show_count):
            panel.barGraphs.setBarGraphValue(cpu_number, cpu_percentage_per_cpu[cpu_number] / 100)
            panel.text.print("{:5.1f}".format(cpu_percentage_per_cpu[cpu_number]), col= 5, row=cpu_number+1)
        
        panel.barGraphs.setBarGraphValue(cpu_to_show_count,  memory_percentage_usage/ 100)
        panel.text.print("{:5.1f}".format(memory_percentage_usage), col=5, row=cpu_to_show_count+1)
            
        time.sleep(0.3)

if __name__ == '__main__':
    port = argv[1] if len(argv) == 2 else '/dev/ttyUSB0'
    main(port=port)

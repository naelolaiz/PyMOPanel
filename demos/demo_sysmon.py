#!/usr/bin/env python3
"""System monitor demo: CPU per-core and memory usage on the panel."""

import sys
import time
import platform
import psutil
import serial.tools.list_ports

from PyMOPanel import PyMOPanel
from PyMOPanel.bar_graph import Direction
from PyMOPanel.filesystem import FileType
from PyMOPanel.font import Font
from PyMOPanel.graphics import Graphics
from PyMOPanel.gpo import LedStatus


def detect_port():
    """Return the serial port for the panel, or None to use direct USB.

    On macOS the panel may not enumerate as a serial port (vendor-specific USB
    class, no built-in driver). In that case we return None and PyMOPanel will
    talk to the USB bulk endpoints directly via pyusb.

    On Linux the panel appears as /dev/ttyUSB* or /dev/ttyACM*.
    """
    ports = serial.tools.list_ports.comports()

    os_name = platform.system()
    if os_name == "Darwin":
        prefixes = ("cu.usbserial", "cu.usbmodem")
    else:  # Linux and others
        prefixes = ("ttyUSB", "ttyACM")

    for port in ports:
        device = port.device.split("/")[-1]
        if any(device.startswith(p) for p in prefixes):
            return port.device

    return None  # fall back to direct USB


class BuiltinFontMetrics:
    """Approximate metrics for the panel's built-in font (ref ID 0).
    The GLK19264 built-in font is a 5x7 glyph with 1px descent = 8px tall,
    nominally 6px wide (5 + 1px spacing).
    """
    def getHeight(self):        return 8
    def getNominalWidth(self): return 6


def load_first_font(panel):
    """Return (font_id, font_metrics) for the first usable font.
    Falls back to built-in font (ref ID 0) if none are uploaded.
    """
    for entry in panel.fs.ls():
        if entry["file_type"] != FileType.FONT:
            continue
        font_id = entry["file_index"]
        font = Font.fromBuffer(panel.fs.downloadFile(FileType.FONT, font_id))
        if font:
            return font_id, font
    print("No uploaded fonts found; using built-in font 0.")
    return 0, BuiltinFontMetrics()


def main(port=None):
    if port is None:
        port = detect_port()
    print(f"Connecting {'via USB' if port is None else f'on {port}'}")

    panel = PyMOPanel(port=port)

    # Recover from any baud-rate mismatch (see demo_top_panel.py for explanation)
    panel.setBaudRate(115200)
    panel.setBaudRate(19200)

    panel.screen.clear()
    panel.screen.enable(True)
    panel.gpo.setLed(0, LedStatus.OFF)
    panel.gpo.setLed(1, LedStatus.OFF)
    panel.gpo.setLed(2, LedStatus.OFF)

    font_id, font = load_first_font(panel)
    print(f"Using font id {font_id}  ({font.getHeight()}px tall)")
    panel.text.selectCurrentFont(font_id)

    char_spacing = panel.text.getCharSpacing()
    line_spacing  = panel.text.getLineSpacing()
    font_h = font.getHeight()
    font_w = font.getNominalWidth()
    row_h  = font_h + line_spacing

    max_rows    = Graphics.PANEL_HEIGHT // row_h
    cpu_count   = psutil.cpu_count(logical=True)
    # reserve one row for memory; show as many CPU cores as fit
    cpu_rows    = min(cpu_count, max_rows - 1)
    mem_row_idx = cpu_rows  # 0-based row index for memory

    # Label width: "cpu0: 100.0%" — we fix it to "cXX:100.0%" width
    label_tmpl  = "c{:02d}:100.0%"
    label_chars = len(label_tmpl.format(0))
    label_px    = font_w * label_chars + char_spacing * (label_chars - 1)

    bar_x0    = label_px + 4
    bar_width = Graphics.PANEL_WIDTH - bar_x0 - 1

    # Register bar graphs
    for i in range(cpu_rows):
        y0 = i * row_h
        panel.barGraphs.addBarGraph(bar_x0, y0, bar_width, font_h,
                                    Direction(Direction.HORIZONTAL_LEFT_TO_RIGHT))

    mem_y0 = mem_row_idx * row_h
    panel.barGraphs.addBarGraph(bar_x0, mem_y0, bar_width, font_h,
                                Direction(Direction.HORIZONTAL_LEFT_TO_RIGHT))

    print(f"Showing {cpu_rows} CPU core(s) + memory. Ctrl-C to exit.")

    # Prime psutil so the first reading is non-zero
    psutil.cpu_percent(interval=None, percpu=True)

    try:
        while True:
            cpu_pcts = psutil.cpu_percent(interval=0.5, percpu=True)
            mem_pct  = psutil.virtual_memory().percent

            for i in range(cpu_rows):
                pct = cpu_pcts[i]
                label = f"c{i:02d}:{pct:5.1f}%"
                panel.text.print(label, col=0, row=i + 1)
                panel.barGraphs.setBarGraphValue(i, pct / 100.0)

            mem_label = f"mem:{mem_pct:5.1f}%"
            panel.text.print(mem_label, col=0, row=mem_row_idx + 1)
            panel.barGraphs.setBarGraphValue(cpu_rows, mem_pct / 100.0)

    except KeyboardInterrupt:
        print("\nExiting.")
        panel.screen.clear()


if __name__ == "__main__":
    port_arg = sys.argv[1] if len(sys.argv) == 2 else None
    main(port=port_arg)

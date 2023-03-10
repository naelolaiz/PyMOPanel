from enum import Enum
from typing import Final

class Direction(Enum):
    VERTICAL_BOTTOM_TO_TOP   = 0
    HORIZONTAL_LEFT_TO_RIGHT = 1
    VERTICAL_TOP_TO_BOTTOM   = 2
    HORIZONTAL_RIGHT_TO_LEFT = 3

class BarGraph:
    def __init__(self, x0, y0, x1, y1, direction):
        self._x0 = x0
        self._y0 = y0
        self._x1 = x1
        self._y1 = y1
        self._direction = direction
        self._delta = abs(x0-x1) if direction.name.startswith('HORIZONTAL') else abs(y0-y1)
        self._value = 0.
    def setValue(self, value):
        self._value = value
    def getValueInPixels(self):
        return int(self._value * self._delta)

class BarGraphManager:
    MAX_NUMBER_OF_BARS: Final[int] = 16
    def __init__(self, panel):
        self._barGraphs = []
        self._panel = panel
    # add bar graph. Returns index, or raise exception if full
    def addBarGraph(self, x0, y0, width, height, direction):
        if len(self._barGraphs) == BarGraphManager.MAX_NUMBER_OF_BARS:
            raise Exception("Cannot have more than {} bars".format(BarGraphManager.MAX_NUMBER_OF_BARS))
        self._barGraphs.append(BarGraph(x0,
                                        y0,
                                        x0+width,
                                        y0+height,
                                        direction))
        index = len(self._barGraphs)-1
        # init bar graph
        self._panel.writeBytes([0xfe, 0x67,
                         index,
                         direction.value,
                         self._barGraphs[-1]._x0,
                         self._barGraphs[-1]._y0,
                         self._barGraphs[-1]._x1,
                         self._barGraphs[-1]._y1])
        return index
    
    def setBarGraphValue(self, index, value):
        self._barGraphs[index].setValue(value)
        self._panel.writeBytes([0xfe, 0x69,
                               index,
                               self._barGraphs[index].getValueInPixels()])



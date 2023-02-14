from .helpers import sanitizeUint8
class Text:
    def __init__(self,
                 panel,
                 fontRefId = 0,
                 autoScroll = True,
                 leftMargin = 0,
                 topMargin = 0,
                 charSpacing = 1,
                 lineSpacing = 1,
                 lastYRow = 64):
        self._panel = panel
        self._currentFont = None
        self._autoScroll = None
        self._leftMargin = leftMargin
        self._topMargin = topMargin
        self._charSpacing = charSpacing
        self._lineSpacing = lineSpacing
        self._lastYRow = lastYRow
        self.selectCurrentFont(fontRefId)
        self.setAutoScroll(autoScroll)
        self.setFontMetrics(leftMargin,
                            topMargin,
                            charSpacing,
                            lineSpacing,
                            lastYRow)
        
    # text methods
    def print(self,
              text,
              x0=None,
              y0=None,
              font_ref_id=None):
        if font_ref_id:
            self.selectCurrentFont(font_ref_id)
        if x0 != None and y0 != None:
            self.setCursorMoveToPos(x0,y0)
        self._panel.writeBytes(bytes(text, 'UTF-8') if type(text) == str else text)

    def setFontMetrics(self,
                       leftMargin=0,
                       topMargin=0,
                       charSpacing=1,
                       lineSpacing=1,
                       lastYRow=64):
        self._leftMargin  = sanitizeUint8(leftMargin)
        self._topMargin   = sanitizeUint8(topMargin)
        self._charSpacing = sanitizeUint8(charSpacing)
        self._lineSpacing = sanitizeUint8(lineSpacing)
        self._lastYRow    = sanitizeUint8(lastYRow)
        self._panel.writeBytes([0xfe, 0x32,
                                self._leftMargin,
                                self._topMargin,
                                self._charSpacing,
                                self._lineSpacing,
                                self._lastYRow])

    def selectCurrentFont(self, font_ref_id) :
        self._currentFont = sanitizeUint8(font_ref_id)
        self._panel.writeBytes([0xfe, 0x31,
                                self._currentFont])

    def cursorMoveHome(self) : 
        self._panel.writeBytes([0xfe, 0x48])

    def setCursorMoveToPos(self, col, row) :
        self._panel.writeBytes([0xfe, 0x47,
                         sanitizeUint8(col),
                         sanitizeUint8(row)])

    def setCursorCoordinate(self, x, y) :
        self._panel.writeBytes([0xfe, 0x79,
                         sanitizeUint8(x),
                         sanitizeUint8(y)]) 

    def setAutoScroll(self, state):
        self._autoScroll = bool(state)
        keyword = 0x51 if state else 0x52
        self._panel.writeBytes([0xfe, keyword])

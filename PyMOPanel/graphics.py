from PIL import Image
from typing import Final
from .helpers import sanitizeUint8

class Graphics:
    PANEL_WIDTH:  Final[int] = 192
    CENTER_X:     Final[int] = int(PANEL_WIDTH/2)
    PANEL_HEIGHT: Final[int] = 64
    CENTER_Y:     Final[int] = int(PANEL_HEIGHT/2)
    def __init__(self, panel):
        self._panel = panel

    def setDrawingColor(self, color):
        self._panel.writeBytes([0xfe, 0x63,
                         sanitizeUint8(color)])
    def drawPixel(self, x, y):
        self._panel.writeBytes([0xfe, 0x70,
                         sanitizeUint8(x),
                         sanitizeUint8(y)])

    def drawLine(self, x0,y0,x1,y1):
        self._panel.writeBytes([0xfe, 0x6c,
                         sanitizeUint8(x0),
                         sanitizeUint8(y0),
                         sanitizeUint8(x1),
                         sanitizeUint8(y1)])

    def continueLine(self, x,y):
        self._panel.writeBytes([0xfe, 0x65,
                         sanitizeUint8(x),
                         sanitizeUint8(y)])

    def drawRectangle(self, color, x0, y0, x1, y1, solid=False) :
        keyword=0x78 if solid else 0x72
        self._panel.writeBytes([0xfe, keyword, 
                         sanitizeUint8(color),
                         sanitizeUint8(x0),
                         sanitizeUint8(y0),
                         sanitizeUint8(x1),
                         sanitizeUint8(y1)])

    # show a bitmap. It could be an animated gif
    def uploadAndShowBitmap(self, inputFilename, x0=0, y0=0, thresholdForBW=50, inverted = False):
        img = Image.open(inputFilename)
        width = img.width
        height = img.height
        isAnimation = hasattr(img,"n_frames")
        frames = img.n_frames if isAnimation else 2

        def getValueForAboveThreshold(bitIndex, inverted):
            return 1<<(7-bitIndex) if inverted else 0
        def getValueForBelowThreshold(bitIndex, inverted):
            return getValueForAboveThreshold(bitIndex, not inverted)

        def sumChannels(inputByteArray, offset, dataSize):
            dataSize=int(dataSize)
            sum=0
            base = offset*dataSize
            for i in range(dataSize):
                sum += inputByteArray[base+i]
            return sum/dataSize

        for frame in range(1,frames):
            if isAnimation: 
                img.seek(frame)
            bitDepth = {'1':1, 'L':8, 'P':8, 'RGB':24, 'RGBA':32, 'CMYK':32, 'YCbCr':24, 'I':32, 'F':32}[img.mode]
            bytesPerPixel = bitDepth / 8

            buffer = img.tobytes()
            if len(buffer) % bitDepth != 0:
                raise Exception('bitmap size should be a multiple of the used depth')

            # init array with header
            outputArray = bytearray(b'\xfe\x64')
            outputArray += x0.to_bytes(1,'little')
            outputArray += y0.to_bytes(1,'little')
            outputArray += width.to_bytes(1,'little')
            outputArray += height.to_bytes(1,'little')

            # pack input 8 bit image to 1 bit monocromatic pixels
            for pixelNr in range(0, width*height, 8):
                baseAddrForByte = pixelNr
                outputArray += sum([getValueForAboveThreshold(bitIndex,inverted) if sumChannels(buffer, pixelNr+bitIndex, bytesPerPixel)>=thresholdForBW else getValueForBelowThreshold(bitIndex,inverted) for bitIndex in range(8)]).to_bytes(1,'little')

            # send data
            self._panel.writeBytes(bytes(outputArray))

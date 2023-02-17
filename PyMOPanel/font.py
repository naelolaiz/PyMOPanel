import numpy as np
from math import ceil
import pprint

class Font:
    class Char:
        def __init__(self, width, data):
            self._width = width
            self._data  = data

    def __init__(self):
        self._nominal_width = 0
        self._height        = 0
        self._ascii_range   = [None, None]
        self._chars         = []

    def getNominalWidth(self):
        return self._nominal_width

    def getHeight(self):
        return self._height

    def getCharsCount(self):
        assert len(self._chars) == 1 + self._ascii_range[1] - self._ascii_range[0]
        return len(self._chars)

    def getChar(self, charIndex):
        assert charIndex < len(self._chars)
        return self._chars[charIndex]

    def getHeaderSize(self):
        return 4

    def getCharTableSize(self):
        return self.getCharsCount() * 3

    def getBufferSize(self):
        return self.getHeaderSize() + self.getCharTableSize() + sum([len(char._data) for char in self._chars])

    def toBuffer(self):
        outputBuffer = bytearray(self.getBufferSize())
        bufferIndex = 0
        # header
        outputBuffer[bufferIndex] = self._nominal_width 
        bufferIndex += 1
        outputBuffer[bufferIndex] = self._height
        bufferIndex += 1
        outputBuffer[bufferIndex] = self._ascii_range[0] 
        bufferIndex += 1
        outputBuffer[bufferIndex] = self._ascii_range[1] 
        bufferIndex += 1

        # now populate both the chars data and tables
        char_table_offset = bufferIndex
        char_data_offset  = bufferIndex + self.getCharTableSize()
        for char in self._chars:
            outputBuffer[char_table_offset:char_table_offset+2] = int(char_data_offset).to_bytes(length=2, byteorder='big')
            char_table_offset += 2
            outputBuffer[char_table_offset] = char._width
            char_table_offset += 1
            data_size = len(char._data)
            outputBuffer[char_data_offset:char_data_offset+data_size] = char._data
            char_data_offset += data_size
        return bytes(outputBuffer)
        
    def toDictOfUnpackedNumpyArray(self):
        myChars = { 'nominal_width': self._nominal_width,
                    'height': self._height,
                    'ascii_start_value': self._ascii_range[0],
                    'ascii_end_value': self._ascii_range[1],
                    'chars': {}
                    }

        for i,char in enumerate(self._chars):
            if not char._width: 
                return
            bitsPerChar =int(self._height * char._width)
            # decode char
            rawBitsIncludingZeroPadding = np.unpackbits(np.frombuffer(char._data, dtype=np.uint8), axis=0)
            myChars['chars'][chr(self._ascii_range[0] + i)] = rawBitsIncludingZeroPadding[:bitsPerChar].reshape(-1, char._width)
        return myChars

    def saveDictOfUnpackedNumpyArray(self, outputFilename):
        open(outputFilename, 'w').write(pprint.pformat(self.toDictOfUnpackedNumpyArray()).replace(" array", "\narray"))

    def fromBuffer(inputBuffer):
        print(len(inputBuffer))
        if not inputBuffer or len(inputBuffer) == 0:
            print("Aborting font import of empty buffer")
            return 
        font = Font()
        bufferIndex = 0
        font._nominal_width  = inputBuffer[bufferIndex]
        bufferIndex += 1
        font._height         = inputBuffer[bufferIndex]
        bufferIndex += 1
        font._ascii_range[0] = inputBuffer[bufferIndex]
        bufferIndex += 1
        font._ascii_range[1] = inputBuffer[bufferIndex]
        bufferIndex += 1
        font._chars = []
        for ch in range(font._ascii_range[0], font._ascii_range[1]+1):
            offset = int.from_bytes(inputBuffer[bufferIndex:bufferIndex+2], byteorder='big')
            bufferIndex += 2
            char_width = inputBuffer[bufferIndex]
            bufferIndex += 1
            bitsPerChar =int(font._height * char_width)
            bytesPerChar = ceil(bitsPerChar / 8.)
            thisCharData = inputBuffer[offset:offset+bytesPerChar] 
            font._chars += [ font.Char(char_width, thisCharData) ]
        return font

    def fromDictOfUnpackedNumpyArray(dictOfNpArrays):
        font = Font()
        font._nominal_width = dictOfNpArrays['nominal_width']
        font._height = dictOfNpArrays['height']
        font._ascii_range = [dictOfNpArrays['ascii_start_value'], dictOfNpArrays['ascii_end_value']]
        font._chars = []
        for npChar in dictOfNpArrays['chars'].values():
           font._chars += [ font.Char(npChar.shape[1], bytes(np.packbits(npChar))) ]
        return font
            
    def fromRawDataFile(inputFilename):
        buffer = open(inputFilename, 'rb').read()
        return Font.fromBuffer(buffer)

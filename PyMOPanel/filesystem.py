from PIL import Image
from enum import Enum
from math import ceil

import numpy as np
import pprint
from .MatrixOrbital import *

class FileType(Enum):
    FONT   = 0
    BITMAP = 1

# filesystem
def getFreeSpaceInBytes(panel):
    panel.writeBytes([0xfe, 0xaf])
    return int.from_bytes(panel.readBytes(4), byteorder='little', signed=False)

def getDirectory(panel):
    panel.setAutoTransmitKeyPressed(False)
    panel.resetInputState()
    panel.writeBytes([0xfe, 0xb3])
    entriesCount = panel.readBytes(1)[0]
    buffer = panel.readBytes(4 * entriesCount)
    panel.setAutoTransmitKeyPressed(True)
    entries = []
    for entryNumber in range(entriesCount):
        offset = entryNumber * 4
        used = buffer[offset] != 0
        offset += 1
        if not used:
            # ignore the remaining bytes
            continue
        # bit0: type (0 is font, 1 bitmap), bit1..bit7: fileId
        typeAndFileId = buffer[offset]
        offset += 1
        fileType = FileType(typeAndFileId & 1)
        fileId = typeAndFileId >> 1
        fileSize = int.from_bytes(buffer[offset:offset+2], byteorder='little', signed=False)
        offset += 2 
        entries += [(fileType, fileId, fileSize)]
    return entries
    
def download(panel, fileType, fileId, outputFilename):
    panel.setAutoTransmitKeyPressed(False)
    panel.resetInputState()
    panel.writeBytes([0xfe, 0xb2, fileType.value, fileId])
    fileSizeInBytes = int.from_bytes(panel.readBytes(4), byteorder='little', signed=False)
    if fileSizeInBytes == 0:
        print("File size == 0! Aborting download")
        panel.setAutoTransmitKeyPressed(True)
        return
    buffer = panel.readBytes(fileSizeInBytes)
    panel.setAutoTransmitKeyPressed(True)
    bufferIndex = 0
    header = {}
    header['fileSizeIncludingHeader'] = fileSizeInBytes
    header['width'] = buffer[bufferIndex]
    bufferIndex += 1
    header['height'] = buffer[bufferIndex]
    bufferIndex += 1
    if fileType == FileType.FONT:
        header['ascii_start_value'] = buffer[bufferIndex]
        bufferIndex += 1
        header['ascii_end_value'] = buffer[bufferIndex]
        bufferIndex += 1
        charTable = []
        charData = []
        myChars = {}
        for ch in range(header['ascii_start_value'], header['ascii_end_value']+1):
            thisTable = {}
            offsetValue = buffer[bufferIndex:bufferIndex+2]
            bufferIndex += 2
            thisTable['offset'] = int.from_bytes(offsetValue, byteorder='big')
            thisTable['char_width'] = buffer[bufferIndex]
            bufferIndex += 1
            bitsPerChar =int(header['height'] * thisTable['char_width'])
            bytesPerChar = ceil(bitsPerChar / 8.)
            thisCharData = buffer[thisTable['offset']:thisTable['offset']+bytesPerChar+1] 
            # decode char
            rawBitsIncludingZeroPadding=np.unpackbits(np.frombuffer(thisCharData, dtype=np.uint8), axis=0)
            myChars[chr(ch)] = rawBitsIncludingZeroPadding[:bitsPerChar].reshape(-1,thisTable['char_width'])
            charData += [thisCharData]
            charTable += [thisTable]
        header['charTable'] = charTable
        header['charData'] = charData
        with open(outputFilename+'.chars', 'w') as charsFile:
            charsFile.write(pprint.pformat(myChars))
    print('Downloading {} {} from panel filesystem to {}...'.format(fileType.name, fileId, outputFilename))
    open(outputFilename+'.info', 'w').write("{}\n".format(str(header)))
    open(outputFilename, 'wb').write(buffer)
    print('done!')

def dumpAll(panel, outputFilename):
    panel.setAutoTransmitKeyPressed(False)
    panel.resetInputState()
    panel.writeBytes([0xfe, 0x30])
    filesystemSize = int.from_bytes(panel.readBytes(4), byteorder='little', signed=False)
    print('Dumping panel filesystem to {}...'.format(outputFilename))
    open(outputFilename, 'wb').write(panel.readBytes(filesystemSize))
    panel.setAutoTransmitKeyPressed(True)
    print('done!')

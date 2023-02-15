from PIL import Image
from enum import Enum
from math import ceil

import numpy as np
import pprint

class FileType(Enum):
    FONT   = 0
    BITMAP = 1

# filesystem
def getFreeSpaceInBytes(panel):
    panel.writeBytes([0xfe, 0xaf])
    return int.from_bytes(panel.readBytes(4), byteorder='little', signed=False)

def ls(panel):
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
        entries += [{'file_type' : fileType, 
                     'file_index': fileId,
                     'file_size' : fileSize}]
    return entries
    
def download(panel, fileType, fileId, outputFilename = None):
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
    #if fileType == FileType.FONT:
    #    print(str(fontDictToUnpackedNumpyArray(fontBuffer2Dict((buffer)))))
    if outputFilename:
        print('Downloading {} {} from panel filesystem to {}...'.format(fileType.name, fileId, outputFilename))
        open(outputFilename, 'wb').write(buffer)
        print('done!')
    return buffer

def upload(panel, inputFilename, fileType, fileId):
    # TODO. Font: [0xfe, 0x24, refId, size, data] ; bitmap: [0xfe, 0x54, refId, size, data]
    return 

def dumpAll(panel, outputFilename):
    panel.setAutoTransmitKeyPressed(False)
    panel.resetInputState()
    panel.writeBytes([0xfe, 0x30])
    filesystemSize = int.from_bytes(panel.readBytes(4), byteorder='little', signed=False)
    print('Dumping panel filesystem to {}...'.format(outputFilename))
    open(outputFilename, 'wb').write(panel.readBytes(filesystemSize))
    panel.setAutoTransmitKeyPressed(True)
    print('done!')

# file formats helpers
def fontBuffer2Dict(inputBuffer):
    bufferIndex = 0
    myFont = {}
    myFont['fileSizeIncludingHeader'] = len(inputBuffer)
    myFont['nominal_width'] = inputBuffer[bufferIndex]
    bufferIndex += 1
    myFont['height'] = inputBuffer[bufferIndex]
    bufferIndex += 1
    myFont['ascii_start_value'] = inputBuffer[bufferIndex]
    bufferIndex += 1
    myFont['ascii_end_value'] = inputBuffer[bufferIndex]
    bufferIndex += 1
    chars = []
    for ch in range(myFont['ascii_start_value'], myFont['ascii_end_value']+1):
        thisTable = {}
        offsetValue = inputBuffer[bufferIndex:bufferIndex+2]
        bufferIndex += 2
        thisTable['offset'] = int.from_bytes(offsetValue, byteorder='big')
        thisTable['char_width'] = inputBuffer[bufferIndex]
        bufferIndex += 1
        bitsPerChar =int(myFont['height'] * thisTable['char_width'])
        bytesPerChar = ceil(bitsPerChar / 8.)
        thisCharData = inputBuffer[thisTable['offset']:thisTable['offset']+bytesPerChar+1] 
        chars += [ { 'char_table': thisTable, 'char_data': thisCharData } ]
    myFont['chars']  = chars
    return myFont

def fontDict2UnpackedNumpyArray(inputDict):
    myChars = {}
    height = inputDict['height']
    if not height:
        return
    for i,char in enumerate(inputDict['chars']):
        char_width = char['char_table']['char_width']
        if not char_width: 
            return
        bitsPerChar =int(height * char_width)
        # decode char
        rawBitsIncludingZeroPadding = np.unpackbits(np.frombuffer(char['char_data'], dtype=np.uint8), axis=0)
        myChars[chr(inputDict['ascii_start_value'] + i)] = rawBitsIncludingZeroPadding[:bitsPerChar].reshape(-1, char_width)
    return pprint.pformat(myChars)

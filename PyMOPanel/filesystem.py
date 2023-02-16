from enum import Enum
from .font import Font

class FileType(Enum):
    FONT   = 0
    BITMAP = 1

# filesystem
def free(panel):
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
    error = False
    panel.setAutoTransmitKeyPressed(False)
    panel.resetInputState()
    panel.setBaudRate(115200)
    panel.writeBytes([0xfe, 0xb2, fileType.value, fileId])
    fileSizeInBytes = int.from_bytes(panel.readBytes(4), byteorder='little', signed=False)
    if fileSizeInBytes == 0:
        print("File size == 0! Aborting download")
        panel.setAutoTransmitKeyPressed(True)
        error = True
    else: 
        buffer = panel.readBytes(fileSizeInBytes)
        panel.setAutoTransmitKeyPressed(True)
        if outputFilename:
            print('Downloading {} {} from panel filesystem to {}...'.format(fileType.name, fileId, outputFilename))
            open(outputFilename, 'wb').write(buffer)
            print('done!')
    panel.setBaudRate(19200)
    return None if error else buffer

def move(panel, oldType, oldId, newType, newId):
    panel.writeBytes([0xfe, 0xb4, oldType.value, oldId, newType.value, newId])

def rm(panel, fileType, refId):
    panel.writeBytes([0xfe, 0xad, fileType.value, refId])
    
def upload(panel, inputFilename, fileType, fileId):
    panel.resetInputState()
    error = False
    panel.setBaudRate(115200)
    # TODO: add timeout
    def expectKey(panel, expectedKey):
        readKey = panel.readBytes(1)
        #print("{} : {}".format(readKey,expectedKey))
        return readKey == expectedKey
    if fileType == FileType.BITMAP:
        print("bitmap uploading not supported yet")
        return

    # TODO. Font: [0xfe, 0x24, refId, size, data] ; bitmap: [0xfe, 0x54, refId, size, data]

    fileBuffer = open(inputFilename,'rb').read()
    font = Font.fromBuffer(fileBuffer)
    bufferToWrite=font.toBuffer()
    #print (len(fileBuffer))
    assert bufferToWrite == fileBuffer
    assert font.getBufferSize() == len(fileBuffer)
    #print (bytes([0xfe, 0x24]) +int(fileId).to_bytes(length=1,byteorder='little') + len(fileBuffer).to_bytes(length=2, byteorder='little'))
    panel.writeBytes(bytes([0xfe, 0x24]) +int(fileId).to_bytes(length=1,byteorder='little') + len(fileBuffer).to_bytes(length=2, byteorder='little'))
    if not expectKey(panel, b'\x01'):
        print("Panel aborted uploading")
        error = True
    else:
        # here the manual says to send a 0x01, but it gets echoed by the panel, and then a byte is missing at the end, so apparently it is an error.

        for i,b in enumerate(bufferToWrite):
            #print(i)
            panel.writeBytes(b.to_bytes(length=1, byteorder='little'))
            if not expectKey(panel, b.to_bytes(length=1, byteorder='little')):
                print("error uploading file")
                error = True
            panel.writeBytes(b'\x01')
    panel.setBaudRate(19200)
    return not error

def dumpAll(panel, outputFilename):
    panel.setAutoTransmitKeyPressed(False)
    panel.resetInputState()
    panel.setBaudRate(115200)
    panel.writeBytes([0xfe, 0x30])
    filesystemSize = int.from_bytes(panel.readBytes(4), byteorder='little', signed=False)
    print('Dumping panel filesystem to {}...'.format(outputFilename))
    open(outputFilename, 'wb').write(panel.readBytes(filesystemSize))
    panel.setBaudRate(19200)
    panel.setAutoTransmitKeyPressed(True)
    print('done!')

def wipe(panel):
    panel.writeBytes([0xfe, 0x21, 0x59, 0x21])

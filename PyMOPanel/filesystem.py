from enum import Enum

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


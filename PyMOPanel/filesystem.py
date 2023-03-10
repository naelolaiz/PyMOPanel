from enum import Enum
from sys import stdout
from .font import Font
from .helpers import useHighSpeedDecorator

class FileType(Enum):
    FONT   = 0
    BITMAP = 1

class Filesystem:
    def __init__(self, panel):
        self._panel = panel

    def free(self):
        self._panel.writeBytes([0xfe, 0xaf])
        return int.from_bytes(self._panel.readBytes(4), byteorder='little', signed=False)
    
    def ls(self):
        self._panel.writeBytes([0xfe, 0xb3])
        entriesCount = self._panel.readBytes(1)[0]
        buffer = self._panel.readBytes(4 * entriesCount)
        entries = []
        for entryNumber in range(entriesCount):
            offset = entryNumber * 4
            used = buffer[offset] != 0
            offset += 1
            if not used:
                # ignore the remaining bytes
                #print("ignoring unused file {}".format(entryNumber))
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
        
    @useHighSpeedDecorator 
    def downloadFile(self, fileType, fileId, outputFilename = None):
        self._panel.writeBytes([0xfe, 0xb2, fileType.value, fileId])
        fileSizeInBytes = int.from_bytes(self._panel.readBytes(4), byteorder='little', signed=False)
        if fileSizeInBytes == 0:
            print("File size == 0! Aborting download")
            return

        buffer = self._panel.readBytes(fileSizeInBytes)
        if outputFilename:
            print('Downloading {} {} from panel filesystem to {}...'.format(fileType.name, fileId, outputFilename))
            open(outputFilename, 'wb').write(buffer)
            print('done!')
        return  buffer

    @useHighSpeedDecorator 
    def _upload(self, header, data):
        self._panel.resetInputState()
        if len(header) == 0 or len(data) == 0:
            print("empty header or data. aborting upload")
            return
        #print("header: {} . len(data): {}".format(header, len(data)))
        def expectKey(panel, expectedKey):
            readKey = panel.readBytes(1)
            #print("{} {}".format(readKey,expectedKey))
            return readKey == expectedKey

        # send header and expect the confirmation byte
        self._panel.writeBytes(header)
        if not expectKey(self._panel, b'\x01'):
            print("Panel aborted uploading")
            return False

        # here the manual says to send a 0x01, but it gets echoed by the panel, and then a byte is missing at the end, so apparently it is an error.
    
        # send data byte per byte, check the echoed byte from the panel, and send a confirmation byte before sending the next one from the buffer
        for i,b in enumerate(data):
            #print(i)
            # each 10 bytes update progress bar
            if i%10 == 0:
                 stdout.write('.')
            #    stdout.write("[{:{}}] {:.1f}%".format("="*i, 10, (100/10)*i))
                 stdout.flush()
            self._panel.writeBytes(b.to_bytes(length=1, byteorder='little'))
            if not expectKey(self._panel, b.to_bytes(length=1, byteorder='little')):
                print("error uploading file")
                return False
            self._panel.writeBytes(b'\x01')
        print("")
        return True

    def uploadFont(self, inputFilename, fileId):
        # TODO bitmap: [0xfe, 0x54, refId, size, data]
        #if fileType == FileType.BITMAP:
        #    print("bitmap uploading not supported yet")
        #    return
        fileBuffer = open(inputFilename,'rb').read()
        font = Font.fromBuffer(fileBuffer)
        bufferToWrite=font.toBuffer()
        #print (len(fileBuffer))
        assert bufferToWrite == fileBuffer
        assert font.getBufferSize() == len(fileBuffer)
        header = bytes([0xfe, 0x24]) +int(fileId).to_bytes(length=1,byteorder='little') + len(fileBuffer).to_bytes(length=2, byteorder='little')
        return self._upload(header, bufferToWrite)
    
    def mv(self, oldType, oldId, newType, newId):
        self._panel.writeBytes([0xfe, 0xb4, oldType.value, oldId, newType.value, newId])
    
    def rm(self, fileType, refId):
        self._panel.writeBytes([0xfe, 0xad, fileType.value, refId])

    @useHighSpeedDecorator 
    def downloadFS(self, outputFilename):
        self._panel.resetInputState()
        self._panel.writeBytes([0xfe, 0x30])
        filesystemSize = int.from_bytes(self._panel.readBytes(4), byteorder='little', signed=False)
        print('Dumping panel filesystem to {}...'.format(outputFilename))
        open(outputFilename, 'wb').write(self._panel.readBytes(filesystemSize))
        print('done!')

    def uploadFS(self, inputFilename):
        bufferToWrite = open(inputFilename, 'rb').read()
        bufferSize = len(bufferToWrite)
        print( bufferSize)
        assert bufferSize <= 16384
        header = bytes([0xfe, 0xb0]) + bufferSize.to_bytes(length=4, byteorder='little')
        return self._upload(header, bufferToWrite)
    
    def wipeFS(self):
        self._panel.writeBytes([0xfe, 0x21, 0x59, 0x21])
    
    def writeCustomerData(self, data):
        expectedLength = 16
        dataLength = len(data)
        assert dataLength <= expectedLength
        # padding bytes
        if len(data) < expectedLength:
            padding = (' ' if type(data) == str else b'\x20') * (expectedLength - dataLength)
            data += padding
        if type(data) == str:
            data = bytes(data, 'UTF-8')
        self._panel.writeBytes(bytes([0xfe, 0x34]) + data)

    def readCustomerData(self):
        expectedLength = 16
        self._panel.writeBytes([0xfe, 0x35])
        return self._panel.readBytes(16)

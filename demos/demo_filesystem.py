#!/usr/bin/env python3
from time import sleep
from sys import argv, path
import pprint
path.append("..")
from PyMOPanel import PyMOPanel as Panel, filesystem as fs
from PyMOPanel.font import *


def main(port):
    myPanel = Panel(port=port)

    print("Customer data: {}".format(str(myPanel.fs.readCustomerData())))
    # uncomment if you want to ovewrite the customer data
    #myPanel.fs.writeCustomerData("Up to 16 chars")

    # dump complete filesystem to a file
    myPanel.fs.downloadFS('filesystem.data')

    print("filesystem free space: {} bytes".format(myPanel.fs.free()))

    filesystemContent = myPanel.fs.ls()
    print("filesystem content: {}".format(pprint.pformat(filesystemContent)))


    # TODO
    #print(myPanel.fs.uploadFont("myFont.data", 1))
    
    print("Downloading all files:")
    for file in filesystemContent:
        file_type  = file['file_type']
        file_index = file['file_index']
        file_size  = file['file_size']
        if file_size == 0:
            print("File {} is empty! Skipping it".format(file_index))
            continue
        outputFilename = '{}_{}.data'.format(file_type.name, str(file_index))
        print("Downloading {} with size {}.".format(outputFilename, file_size))
        fileContentBuffer = myPanel.fs.downloadFile(file_type, file_index, outputFilename)
        if fileContentBuffer and file_type == fs.FileType.FONT: 
            # testing roundtrip conversion
            assert Font.fromRawDataFile(outputFilename).toBuffer() == fileContentBuffer
            # write the data in a file with numpy array
            Font.fromBuffer(fileContentBuffer).saveDictOfUnpackedNumpyArray("{}.npArrayDict".format(outputFilename))
            myDict = Font.fromBuffer(fileContentBuffer).toDictOfUnpackedNumpyArray()
            #assert myDict == Font.fromDictOfUnpackedNumpyArray(myDict).toDictOfUnpackedNumpyArray()
            #open("a", "wb").write(Font.fromDictOfUnpackedNumpyArray(myDict).toBuffer())
            #open("b", "wb").write(fileContentBuffer)
            # this comparison fails on the padded bits. Is my FS corrupted? (the padded bits are read as 1, but regenerated as 0)
            #assert Font.fromDictOfUnpackedNumpyArray(myDict).toBuffer() == fileContentBuffer
            

if __name__ == '__main__':
    port = argv[1] if len(argv) == 2 else '/dev/ttyUSB0'
    main(port=port)

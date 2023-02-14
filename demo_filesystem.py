#!/usr/bin/env python3
from time import sleep
from sys import argv
from PyMOPanel import MatrixOrbital

def main(port):
    myPanel = MatrixOrbital(port=port)

    # dump complete filesystem to a file
    myPanel.dumpCompleteFilesystem('filesystem.data')

    print("filesystem free space: {} bytes".format(myPanel.getFilesystemFreeSpaceInBytes()))

    filesystemContent = myPanel.getFilesystemDirectory()
    print("filesystem content: {}".format(str(filesystemContent)))
    
    print("Downloading all files:")
    for (fileType, fileId, fileSize) in filesystemContent:
        if fileSize == 0:
            print("File {} is empty! Skipping it".format(fileId))
            continue
        outputFilename = '{}_{}.data'.format(fileType.name, str(fileId))
        print("Writting {} with size {}.".format(outputFilename, fileSize))
        myPanel.downloadFile(fileType, fileId, outputFilename)

if __name__ == '__main__':
    port = argv[1] if len(argv) == 2 else '/dev/ttyUSB0'
    main(port=port)

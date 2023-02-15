#!/usr/bin/env python3
from time import sleep
from sys import argv, path
import pprint
path.append("..")
from PyMOPanel import PyMOPanel as Panel, filesystem as fs

def main(port):
    myPanel = Panel(port=port)

    # dump complete filesystem to a file
    fs.dumpAll(myPanel, 'filesystem.data')

    print("filesystem free space: {} bytes".format(fs.getFreeSpaceInBytes(myPanel)))

    filesystemContent = fs.ls(myPanel)
    print("filesystem content: {}".format(pprint.pformat(filesystemContent)))
    
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
        fontBuffer = fs.download(myPanel, file_type, file_index, outputFilename)
        if fontBuffer: 
            fontDict   = fs.fontBuffer2Dict(fontBuffer)
            fontUnpackedNumpyArray = fs.fontDict2UnpackedNumpyArray(fontDict) 
            open('{}.dict'.format(outputFilename), 'w').write(pprint.pformat(fontDict))
            if fontUnpackedNumpyArray:
                open('{}.np'.format(outputFilename), 'w').write(fontUnpackedNumpyArray)


if __name__ == '__main__':
    port = argv[1] if len(argv) == 2 else '/dev/ttyUSB0'
    main(port=port)

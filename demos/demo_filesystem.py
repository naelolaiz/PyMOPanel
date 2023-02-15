#!/usr/bin/env python3
from time import sleep
from sys import argv, path
path.append("..")
from PyMOPanel import PyMOPanel as Panel, filesystem as fs

def main(port):
    myPanel = Panel(port=port)

    # dump complete filesystem to a file
    fs.dumpAll(myPanel, 'filesystem.data')

    print("filesystem free space: {} bytes".format(fs.getFreeSpaceInBytes(myPanel)))

    filesystemContent = fs.ls(myPanel)
    print("filesystem content: {}".format(str(filesystemContent)))
    
    print("Downloading all files:")
    for file in filesystemContent:
        file_type  = file['file_type']
        file_index = file['file_index']
        file_size  = file['file_size']
        if file_size == 0:
            print("File {} is empty! Skipping it".format(file_index))
            continue
        outputFilename = '{}_{}.data'.format(file_type.name, str(file_index))
        print("Writting {} with size {}.".format(outputFilename, file_size))
        fs.download(myPanel, file_type, file_index, outputFilename)

if __name__ == '__main__':
    port = argv[1] if len(argv) == 2 else '/dev/ttyUSB0'
    main(port=port)

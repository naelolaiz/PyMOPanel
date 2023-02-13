#!/usr/bin/env python3
import time
from sys import argv
from PyMOPanel import MatrixOrbital

def main(port):
    myPanel = MatrixOrbital(port=port)

    # dump complete filesystem to a file
    #myPanel.dumpCompleteFilesystem('filesystem.data')

    time.sleep(0.2)

    print("filesystem space: {}".format(myPanel.getFilesystemSpace()))

    (used,unused) = myPanel.getFilesystemDirectory()
    print("used: {}".format(str(used)))
    print("unused: {}".format(str(unused)))

    # dump bitmap 1 to a file
    #myPanel.downloadFile(0, 1, 'bitmap1_output.data')

if __name__ == '__main__':
    port = argv[1] if len(argv) == 2 else '/dev/ttyUSB0'
    main(port=port)

# misc helpers
def sanitizeUint8(value):
    return max(0,int(value)) & 0xFF
def sumChannels(inputByteArray, offset, dataSize):
    dataSize=int(dataSize)
    sum=0
    base = offset*dataSize
    for i in range(dataSize):
        sum += inputByteArray[base+i]
    return sum/dataSize

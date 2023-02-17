# misc helpers
def sanitizeUint8(value):
    return max(0,int(value)) & 0xFF

# decorator to switch temporarly to high speed. IT REQUIRES self._panel!
def useHighSpeedDecorator(func):
    def wrapperFunction(*args, **kwargs):
        self = args[0]
        previousBaudRate = self._panel.getBaudRate()
        if previousBaudRate != 115200:
            self._panel.setBaudRate(115200)
        retValue = func(*args, **kwargs)
        if previousBaudRate != 115200:
            self._panel.setBaudRate(previousBaudRate)
        return retValue
    return wrapperFunction

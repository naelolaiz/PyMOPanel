# misc helpers
def sanitizeUint8(value):
    return max(0,int(value)) & 0xFF

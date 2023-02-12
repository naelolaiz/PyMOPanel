#!/usr/bin/python
# class to manage MatrixOrbital GLK19264 (not finished yet)
# Depend on python-ftdi (debian) libftdi (use +python - gentoo)
# need permissions on device (groups uucp, plugdev and usb, probably)
# License: GPL
# Copyright: Natanael Olaiz 01/2010
# 

# Matrix Orbital GLK19264-7T-1U Technical Manual: http://www.tri-m.com/products/matrix/files/manual/bgk24064_man.pdf
# libftdi api doc: http://www.intra2net.com/en/developer/libftdi/documentation/group__libftdi.html



#TODO: check idVendor and idProduct, flush buffers where apply


#import fcntl, termios
import serial

class MatrixOrbital :
	PORT = "/dev/ttyUSB0"
	BAUDRATE = 19200
	def __init__(self, port=PORT, baudrate=BAUDRATE) :
		self._port = port
		self._baudrate = baudrate
		self._handler = serial.Serial(port=port, baudrate=baudrate)
		# if the device is not here. Serial(...) will fail with AttributeError
		if not self._handler.isOpen():
			raise Exception("MatrixOrbital device not found")

	def __del__(self):
		self._handler.close()

	def sendRawCommand(self, command):
		return self._handler.write(command)

	def read(self):
		return list(self._handler.read(self._handler.inWaiting()))
	
	def sendCommand(self, command, one_byte=False, send_confirmation=False):
		def listToChars(input_list):
			return "".join([chr(i&0xff) for i in input_list])
		def checkAndSendConfirmation():
		# confirmations. TODO: check and use properly!
			while self.read():
				self.sendRawCommand(chr(1))
		def send_raw(chars, confirmation):
			if confirmation: checkAndSendConfirmation()
			ret=self.sendRawCommand(chars)
			if confirmation: checkAndSendConfirmation()
			return ret
		# here is the action :
		command_in_chars=listToChars(command)
		if one_byte:
			written_bytes = sum([send_raw(character, send_confirmation) for character in command_in_chars])
		else:
			written_bytes = send_raw(command_in_chars, send_confirmation)
		return written_bytes
	# setup
	def setBaudRate(self, baud_rate) :
		speed={9600:    0xCF,
			14400:  0x8A,
			19200:  0x67,
			28800:  0x44,
			38400:  0x33,
			57600:  0x22,
			76800:  0x19,
			115200: 0x10}[baud_rate]
		self.sendCommand([0xfe,0x39,speed])

	# screen methods
	def clearScreen(self) :
		self.sendCommand([0xfe, 0x58])
	def setScreen(self, state) :
		keyword=0x42 if state else 0x46
		self.sendCommand([0xfe,keyword])
	def setBrightness(self, value, save_as_default=False) :
		keyword = 0x98 if save_as_default else 0x99
		self.sendCommand([0xfe, keyword, value & 0xff])
	def setContrast(self, value, save_as_default=False) :
		keyword = 0x91 if save_as_default else 0x50
		self.sendCommand([0xfe, keyword, value & 0xff])
	# led methods
	def setGPO(self, gpo_nr, state, save_as_default=False) :
		if not save_as_default :
			keyword=0x57 if state else 0x56
			self.sendCommand([0xfe, keyword, gpo_nr & 7])
		else:
			self.sendCommand([0xfe, 0xc3, gpo_nr & 7, int(state)])
	#keypad methods
	def setAutoTransmitKeyPressed(self, state) :
		keyword = 0x41 if state else 0x4f
		self.sendCommand([0xfe,keyword])
	def setAutoRepeatKeyModeResend(self, state) :
		command_list = [0xfe, 0x60] # autorepeat off
		if state:
			command_list = [0xfe, 0x7e, 0x00]
		self.sendCommand(command_list)
	def setAutoRepeatKeyModeUpDown(self, state) :
		command_list = [0xfe, 0x60] # autorepeat off
		if state:
			command_list = [0xfe, 0x7e, 0x01]
		self.sendCommand(command_list)
	def pollKeyPressed(self) :
		self.sendCommand([0xfe,0x26])
		#TODO: return the buffer
	def clearKeyBuffer(self) :
		self.sendCommand([0xfe,0x45])
	def setDebounceTime(self, time) :
		self.sendCommand([0xfe, 0x55, time & 0xff])
	# text methods
	def setFontMetrics(self, leftMargin=0, topMargin=0, charSpacing=1, lineSpacing=1, lastYRow=64) :
		self.sendCommand([0xfe, 0x32, leftMargin & 0xff, topMargin & 0xff, charSpacing & 0xff, lineSpacing & 0xff, lastYRow & 0xff])
	def selectCurrentFont(self, font_ref_id) :
		self.sendCommand([0xfe, 0x31, font_ref_id & 0xff])
	def printText(self, text) :
		self.sendRawCommand(text)
	def printLocatedText(self, x, y, text, font_ref_id=None) :
		if font_ref_id : self.selectCurrentFont(font_ref_id)
		self.setCursorMoveToPos(x,y)
		self.printText(text)
	def cursorMoveHome(self) : 
		self.sendCommand([0xfe, 0x48])
	def setCursorMoveToPos(self, col, row) :
		self.sendCommand([0xfe, 0x47, col, row])
	def setCursorCoordinate(self, x, y) :
		self.sendCommand([0xfe,0x79,x,y]) 
	def setScroll(self, state) :
		keyword = 0x51 if state else 0x52
		self.sendCommand([0xfe,keyword])
	# graphics methods
	def uploadAndShowBitmap(self, filename, x=0, y=0, w=192, h=64) : #TODO: remove hardcoded values
		self.sendCommand([0xfe, 0x64, x & 0xff, y & 0xff, w & 0xff, h & 0xff] + ImageHandler(filename).getData())
	def setDrawColor(self, value) :
		self.sendCommand([0xfe, 0x63, value & 0xff])
	def drawPixel(self, x, y) :
		self.sendCommand([0xfe, 0x70, x & 0xff, y & 0xff])
	def drawLine(self, x0, y0, x1, y1):
		self.sendCommand([0xfe, 0x6c, x0 & 0xff, y0 & 0xff, x1 & 0xff, y1 & 0xff])
	def drawRectangle(self, color, x0, y0, x1, y1, solid=False) :
		keyword=0x78 if solid else 0x72
		self.sendCommand([0xfe, keyword, color & 0xff, x0 & 0xff, y0 & 0xff, x1 & 0xff, y1 & 0xff])

import Image
class ImageHandler :
	_image=None
	_chars_data=[]
	def __init__(self, filename) :
		self._image = self.load(filename)
	def load(self, filename) :
		if self._image:
			try: self._image.close()
			except: pass
		self._image = Image.open(filename)
		self._chars_data=[]

		data=list(self._image.getdata())
		if (len(data) % 8) != 0:
			padded_data = data + ((8 - (len(data) % 8)) * [0])
			data=padded_data
		while data:
			newbyte=0
			for i in range(8):
				newbyte = (newbyte<<1) | data.pop(0)
			self._chars_data.append(newbyte & 0xff)
	def getData(self) : return self._chars_data


def main():
	driver=MatrixOrbital()
	driver.clearScreen()
	driver.drawRectangle(255,0,0,191,63)
	driver.cursor_move_to_pos(10,5)
	driver.print_text("hola mundo!")
if __name__=="__main__":
	main()

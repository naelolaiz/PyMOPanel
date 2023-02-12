#!/usr/bin/python2

import time
import sys
import glob
import os
import MatrixOrbital
import subprocess
import shutil
import threading

import imm_box
import imm_upgrade_manager

USE_CURSES = False
DEBUG=False 

# Enable this if we want to use content via sftp:
import imm_content_manager
import curses
import curses.ascii

import preset_manager

HOME = os.getenv("HOME")

PROCESS_TO_KILL = "imm_3d_upmix_slave"

PLAYER_STATUS_FILE = os.path.join(HOME, "PLAYING")
STATUS_MESSAGE_FILE = os.path.join(HOME, "STATUS")

CONTENT_PATH = os.path.join(HOME,"content")
EVENTS_PATH = os.path.join(HOME, ".events")
REBOOT_FILE = os.path.join(EVENTS_PATH, "reboot")

INGEST_CONTENT_SOURCE_PATH = "/media/disk"

#INGEST_CONTENT_SOURCE_PATH = "/home/nael/pendrive_content"

DISABLE_INTERACTIVE_BOOT_FILE = '/tmp/lcd_panel_no_interactive_boot'


def get_process_pid(name_of_process) :
	cmd = "pidof %s" % name_of_process
	pid_list = [line.strip() for line in subprocess.Popen(cmd.split(), stdout=subprocess.PIPE).stdout]
	return None if not pid_list else int(pid_list[0])

def kill_process(name_of_process, signal) :
	pid = -1
	while pid:
		pid = get_process_pid(name_of_process)
		if not pid: return
		try: os.system("kill -%i %i" % (signal, pid))
		except: pass

MENU_STRINGS = preset_manager.getUpmixPlayerPresets() 

if DEBUG: print MENU_STRINGS

STATUS_STRINGS = (
	[
		"Status: 3D Upmix ON",
		"Status: Playing 3D audio demo",
	],
	# notification
	[
		"",
		"Lost internet connection.",
	]
)

class CursesPanel :
	def __init__(self) :
		# init curses
		curses.initscr()
		self.stdscr = curses.newwin(10,70,10,10)
   		curses.noecho()
		curses.cbreak()
		curses.curs_set(0) # make cursor invisible
		self.stdscr.keypad(1)
		self.stdscr.timeout(1) # ms	
		self.clear()
#		pad = curses.newpad(100, 100)
		# styles
		self.BOLD = curses.A_BOLD
		self.REVERSE = curses.A_REVERSE
		self.DIM = curses.A_DIM

	def _located_print(self, y, x, content, style) :
		self.stdscr.addstr(y, x, content, style)
	def located_print(self, y, x, content) :
		self._located_print(y, x, content, self.DIM)
	def print_emphasis(self, y, content, x=0) :
		self._located_print(y, x, content, self.BOLD)
	def getkey(self) :
		return self.stdscr.getch()
	def clear(self) :
		self.stdscr.clear()
		self.stdscr.box()
	def curses_refresh(self) :
		self.stdscr.refresh()
	def curses_tear_down(self) :
		curses.nocbreak() 
		self.stdscr.keypad(0) 
		curses.echo()
		curses.endwin()

class NullDriver() :
	def selectCurrentFont(self,f) : 
		pass
	def setFontMetrics(self,charSpacing=0) :
		pass
	def setScroll(self,_) :
		pass
	def setCursorMoveToPos(self, x,y) :
		pass
	def printText(self,_) :
		pass
	def clearScreen(self) :
		pass
	def clearKeyBuffer(self) :
		pass
	def setAutoRepeatKeyModeResend(self, value) :
		pass
	def read(self) :
		return []

class MatrixOrbitalPanel :
	def __init__(self) :
		# curses styles: temporal
		self.BOLD = curses.A_BOLD
		self.REVERSE = curses.A_REVERSE
		self.DIM = curses.A_DIM
		# init curses as a temporal echo
		if USE_CURSES : self.curses_echo = CursesPanel() 

		self.NO_KEY = -1
		self.KEY_ESC = curses.ascii.ESC
		self.KEY_BACK = 0 # not used in curses
		self.KEY_LEFT = curses.KEY_LEFT
		self.KEY_RIGHT = curses.KEY_RIGHT
		self.KEY_UP = curses.KEY_UP
		self.KEY_DOWN = curses.KEY_DOWN
		self.KEY_ENTER = ord('\n')

		try :
			self._driver = MatrixOrbital.MatrixOrbital("/dev/ttyUSB0", 19200 )
		except Exception, e :
			print "ERROR: Device is not ready, %s"%e
			self._driver = NullDriver()
		self._driver.selectCurrentFont(1)
		self._driver.setFontMetrics(charSpacing=1)
		self._driver.clearScreen()
		self._driver.setScroll(False) # avoid automatic lines scrolling
		self._driver.clearKeyBuffer()
		self._timeout_ms=1.

	def _located_print(self, y, x, content, style) :
		if USE_CURSES : self.curses_echo._located_print(y, x, content, style)
		self._driver.setCursorMoveToPos(x, y)
		self._driver.printText(content)
		time.sleep(0.08) 
	def located_print(self, y, x, content) :
		self._located_print(y, x, content, self.DIM)
	def print_item(self, y, content, is_selected, is_cursor) :
		selected = "[*] " if is_selected else "[ ] "
		if is_selected == None : #special case: no selectable item:
			selected = ''
		cursor = ("<",">") if is_cursor else (" "," ")
		content = content[:(29-len(selected))]
		trailing = " " * (29 - (len(content)+len(selected)))
		formatted = cursor[0] + selected + content + trailing + cursor[1]
		self._located_print(y, 1, formatted, self.DIM)
	def print_emphasis(self, y, content) :
		content = content[:32]
		trailing = " " * (32 - len(content))
		self._located_print(y, 1, content+trailing, self.BOLD)
	def getkey(self) :
		panel_keys = self._driver.read()
		if not panel_keys: 
			time.sleep(self._timeout_ms/1000.)
			return self.curses_echo.getkey() if USE_CURSES else -1
		else : 
			return {
				"B" : self.KEY_UP,
				"H" : self.KEY_DOWN,
				"D" : self.KEY_LEFT,
				"C" : self.KEY_RIGHT,
				"E" : self.KEY_ENTER,
				"A" : self.KEY_BACK,
				"G" : None,
				} [panel_keys[-1]]  
	def clear(self) :
		if USE_CURSES : self.curses_echo.clear()
		self._driver.clearScreen() # produces flickering
	def curses_refresh(self) :
		if USE_CURSES : self.curses_echo.refresh()
	def curses_tear_down(self) :
		if USE_CURSES : self.curses_echo.curses_tear_down()
	def navigation_keys(self) :
		return (
			self.KEY_LEFT,
			self.KEY_RIGHT,
			self.KEY_UP,
			self.KEY_DOWN,
			self.KEY_ENTER, 
			) 

def debug(msg) :
	os.system("echo %s >> /tmp/a" % msg)

class UpgradeWindow : 

	def __init__(self, parent) :
		self._parent = parent
		self._panel = parent._panel
		self._waiting_for_key = False
		self._upgrade_cancelled = False
		self._proposed_version = None

		self._box_info = imm_box.BoxInfo()
		self._current_version = self._box_info.get_version()
		self._serial_number = self._box_info.get_serial_number()
		self._internet_handler = imm_upgrade_manager.InternetUpgradeApiClient()

	def check_for_pendrive_upgrade(self) : 
		event_file = '/home/imm/.events/pendrive_upgrade_available'
		if self._upgrade_cancelled : return False # TODO: remove after menu improvements
		imm_upgrade_manager.check_and_trigger_pendrive_upgrade()
		if not os.path.exists(event_file) : return False
		return open(event_file).read().strip()
		#internet_upgrade_available = os.path.exists( '/home/imm/.events/internet_upgrade_available' )
		#return pendrive_upgrade_available #or internet_upgrade_available

	def check_for_internet_upgrade(self) :
		if self._upgrade_cancelled : return False # TODO: remove after menu improvements
		if not self._internet_handler.is_internet_available() : return False
		server_version = self._internet_handler.call_server_is_new_version(self._serial_number, self._current_version)
		return server_version if server_version else False

	def start_upgrade_process(self) :
		if os.path.exists("/home/imm/.events/pendrive_upgrade_available") : 
			shutil.move("/home/imm/.events/pendrive_upgrade_available","/home/imm/.events/pendrive_upgrade_requested")
		#if os.path.exists("/home/imm/.events/internet_upgrade_available") : 
		#	shutil.move("/home/imm/.events/internet_upgrade_available","/home/imm/.events/internet_upgrade_requested")
		self._panel.clear()
		self._panel.print_emphasis(1, "Starting upgrade process.")
		#print "DO UPGRADE!!!!!"
		#TODO: REMOVEEEEEEEEEEEEEEEE:
		self._upgrade_cancelled = True
		# show info
		# move files
		# reboot

	def run_upgrade_menu(self, version) :
		if self._waiting_for_key : return False
		self._panel.print_emphasis (1, "Upgrade %s available!" % version)
		self._panel.print_emphasis (3, "The upgrade might take long time.")
		self._panel.print_emphasis (4, "The audio will be stopped")
		self._panel.print_emphasis (6,"Do you want to start now?")
		self._panel.print_emphasis (7,"(center: OK ; other: cancel)")
		self._waiting_for_key = True
		self._proposed_version = version

	def process_event(self, key) : 
		if self._waiting_for_key and key != self._panel.NO_KEY :
			self._waiting_for_key = False
			if key == self._panel.KEY_ENTER :
				self.start_upgrade_process()
			#else if key == self._panel.KEY_BACK :
			else :
				self._upgrade_cancelled = True
				#print "UPGRADE_CANCELLED"
				self._panel.clear()
				self._panel.print_emphasis(1, "Upgrade %s available!" % self._proposed_version)
				self._panel.print_emphasis(4, "Upgrade cancelled by user.")
				self._panel.print_emphasis(5, "You'll not be warned again")
				self._panel.print_emphasis(6, "until the next boot.")
				time.sleep(3)
			self._parent.change_to_status()

	def repaint(self) : # TODO
		pass

	def timeout(self) : # TODO
		if not self._waiting_for_key : 
			self._parent.change_to_status()
		return

class ProgressBarThread(threading.Thread) :
	def __init__ (self, panel, max_value, test_to_eval, y, max_x = 32) :
		threading.Thread.__init__(self)
		self._panel = panel
		self.set_max_value(max_value)
		self._test_to_eval = test_to_eval
		self._y = y
		self._usable_chars = max_x - 2

	def set_max_value(self, value) :
		self._max_value = value

	def run(self) :
		percentage_done = 0
		while percentage_done < 100 :
			try: 
				current_value = float(eval(self._test_to_eval))
			except:
				current_value = 0
			percentage_done = 100. * current_value / float(self._max_value) 
			chars_to_print = int(self._usable_chars * 0.01 * percentage_done)
			to_print = "[%s%s]" % ("*" * chars_to_print, " " * (self._usable_chars - chars_to_print) )
			self._panel.print_emphasis(self._y, to_print)
			#print to_print , percentage_done, self._usable_chars, current_value
			time.sleep(0.1)

class IngestWindow:
	def __init__(self, parent) :
		self._ingest_source_path = INGEST_CONTENT_SOURCE_PATH
		self._content_target_path = CONTENT_PATH
		self._parent = parent
		self._panel = parent._panel
		imm_content_manager.create_keyfile(self._content_target_path, "%s/player.key" % self._content_target_path)
		self._waiting_for_key = False
		self._box_info = imm_box.BoxInfo()
		self._waiting_for_suicide = False

	#def check_for_content(self):
	#	if not self.check_content_path_available(): return False
	#	compatible_content, incompatible_content = self.get_new_content_available()
	#	return True if compatible_content['new'] + compatible_content['to_replace'] else False

	def run_ingestion_menu(self, compatible_content, incompatible_content) :
		if self._waiting_for_key : return False
		#compatible_content, incompatible_content = self.get_new_content_available()
		if self._parent._current_context is not self and ((compatible_content['new']+compatible_content['to_replace']) or self.are_volume_files_on_pendrive()) :
			self._parent.change_to_ingestion()
		ingestion_done = self._ingest_menu(compatible_content, incompatible_content)
		return ingestion_done

	def check_content_path_available(self):
		return os.path.exists(self._ingest_source_path) and os.path.isdir(self._ingest_source_path)

	# This expects to have all the content already ingested, so it must be called AFTER audio ingestion
	def get_new_volumes_available(self) :
		ingested_wavs_without_extension = [os.path.splitext(os.path.basename(wav_filename))[0] for wav_filename, _, _, _, _ in imm_content_manager.get_info_list_from_directory(self._content_target_path)]
		new_volume_files = [ volume_filename for volume_filename in imm_content_manager.get_files_from_directory_recursively(self._ingest_source_path, "*.volume") if os.path.splitext(os.path.basename(volume_filename))[0] in ingested_wavs_without_extension ]
		return new_volume_files

	def are_volume_files_on_pendrive(self) :
		return len(imm_content_manager.get_files_from_directory_recursively(self._ingest_source_path, "*.volume")) > 0

	def get_new_content_available(self):
		list_of_wavs_on_ingestion_dir = imm_content_manager.get_wav_files_from_directory_recursively(self._ingest_source_path)

		box_serial_number = self._box_info.get_serial_number()
		box_layout = self._box_info.get_layout()

		compatible_content = dict (new = [], to_replace = [], already_ingested = [])
		incompatible_content = []

		if not self.check_content_path_available(): return (compatible_content,incompatible_content)

		# format: list of tuples: (wav_filename, SN, name)
		ingested_info_by_id = imm_content_manager.get_info_list_from_directory_by_ids(self._content_target_path)
			
		for wavfile in list_of_wavs_on_ingestion_dir :
			if not imm_content_manager.is_normalized_content_filename(wavfile) : continue
			ID, SN, LAYOUT, name = imm_content_manager.get_information_from_content_filename(wavfile)
			pendrive_hash = imm_content_manager.get_hash_from_wavfile(wavfile)

			if (
				( SN and (SN==box_serial_number or SN[2:]=="0000") ) 
			    or
				( LAYOUT and (LAYOUT==box_layout or (LAYOUT[:-3]==box_layout[:-3] and LAYOUT[-3:]=='000')) ) 
			   ) \
			   and pendrive_hash : # TODO: validate hash: "and pendrive_hash == imm_content_manager.get_rsa1_hash_in_base64(wavfile).strip() :"

				id_exists = ID in ingested_info_by_id.keys()
				if not id_exists: 
					keyword = "new"
				else:
					#compare hash
					ingested_hash = imm_content_manager.get_hash_from_wavfile(os.path.join(self._content_target_path, os.path.basename(ingested_info_by_id[ID][0])))
					keyword = "to_replace" if pendrive_hash != ingested_hash else "already_ingested"
				compatible_content[keyword].append((name, wavfile))
			else:
				incompatible_content.append((name, wavfile))
		return (compatible_content,incompatible_content)

	def _is_content_mounted(self) :
		return os.system('mount | grep /home/imm/content') == 0

	def _ingest_menu(self, compatible_content, incompatible_content) :
		# TODO: check for available space / content fits...

		# format: list of tuples: (wav_filename, SN, LAYOUT, name)
		ingested_info_by_id = imm_content_manager.get_info_list_from_directory_by_ids(self._content_target_path)
		y_offset = 1
		self._panel.print_emphasis(y_offset, "New media content found!")
		y_offset += 2

		if not self._is_content_mounted() :
			self._panel.print_emphasis(y_offset, 'ERROR: NO HD DETECTED')
			y_offset+=1
			self._panel.print_emphasis(y_offset, 'Cannot ingest content')
			y_offset+=1
			self._panel.print_emphasis(y_offset, 'Contact imm technical support')
			y_offset+=2
			self._panel.print_emphasis(y_offset, 'Remove pendrive and press a key')
			self._waiting_for_key = True
			return False

		for key, caption in [('new', 'INGESTING'), ('to_replace', 'REPLACING')] :
			for source_number,(source_name, wav_filename) in enumerate(compatible_content[key]) :
				ID, SN, LAYOUT, name = imm_content_manager.get_information_from_content_filename(wav_filename)
				source_name_without_extension = source_name [:-4]
				self._panel.print_emphasis(y_offset, "%s (%i/%i)" % (caption, source_number + 1, len(compatible_content[key])))
				self._panel.print_emphasis(y_offset + 1, "%s" % source_name_without_extension)
				hashfilename = "%s.hash" % os.path.splitext(wav_filename)[0]
				if ID in ingested_info_by_id.keys() : 
					already_ingested_filename = ingested_info_by_id[ID][0]
					already_ingested_hashfilename = "%s.hash" % os.path.splitext(already_ingested_filename)[0]
					if os.path.exists(already_ingested_hashfilename) :
						shutil.move(already_ingested_hashfilename, "%s.replaced" % already_ingested_hashfilename)
					if os.path.exists(already_ingested_filename) : 
						shutil.move(already_ingested_filename, "%s.replaced" % already_ingested_filename)

				shutil.copy(hashfilename, self._content_target_path)
				progress_bar_thread = ProgressBarThread(self._panel, os.path.getsize(wav_filename), 'os.path.getsize("%s")' % os.path.join(self._content_target_path,os.path.basename(wav_filename)), 6)
				progress_bar_thread.start()
				shutil.copy(wav_filename, self._content_target_path)
				if progress_bar_thread.is_alive() : progress_bar_thread.join()
				self._panel.print_emphasis(6, "")
				self._panel.print_emphasis(y_offset + 1, "")
		new_volume_filenames = self.get_new_volumes_available() 
		for volume_filename in new_volume_filenames :
			shutil.copy(volume_filename, self._content_target_path)

		self._panel.print_emphasis(y_offset, "%i files ingested" % len(compatible_content['new']))
		y_offset += 1
		self._panel.print_emphasis(y_offset, "%i files replaced" % len(compatible_content['to_replace']))
		y_offset += 1
		self._panel.print_emphasis(y_offset, "%i volume files ingested" % len(new_volume_filenames))

		imm_content_manager.create_keyfile(self._content_target_path, "%s/player.key" % self._content_target_path)
		os.system("sync")
		kill_process( PROCESS_TO_KILL, 9)
		# end of copy content and kill process

		y_offset += 3
		self._panel.print_emphasis(y_offset, "Remove pendrive and press a key")
		self._waiting_for_key = True
		open(DISABLE_INTERACTIVE_BOOT_FILE,'w').write('')
		self._waiting_for_suicide = True
		return True

	def process_event(self, key) : 
		if self._waiting_for_key and key in self._panel.navigation_keys() :
			if self._waiting_for_suicide : 
				sys.exit(0)
			self._waiting_for_key = False
			self._parent.change_to_status()

	def repaint(self) : # TODO
		pass

	def timeout(self) : # TODO
		if not self._waiting_for_key : 
			self._parent.change_to_status()
		return

class StatusWindow :
	def __init__(self, parent) :
		self._parent = parent
		self._panel = parent._panel
		self._box_info = imm_box.BoxInfo()
		self._channels_number = self._box_info.get_layout_channels_number()
		self.status, self.notification = STATUS_STRINGS 
		
	def repaint(self) :
		self._panel.print_emphasis(1, ":: imm 3D upmix - %i channels ::" % self._channels_number)
		self.displayed_status_index = 1 if os.path.exists(PLAYER_STATUS_FILE) else 0
		self._panel.print_emphasis(4, self.status[self.displayed_status_index]) 
		status_message = file(STATUS_MESSAGE_FILE).readline() if os.path.exists(STATUS_MESSAGE_FILE) else ""
		self._panel.print_emphasis(7, status_message.strip()[:31])
		# TODO: remove when improved menu with status/about item:
		version = self._box_info.get_version()
		self._panel.located_print(8,32-len(version), "v%s" % version)

	def process_event(self, key) :
		if key in self._panel.navigation_keys() :
			self._parent.change_to_menu()
	def timeout(self) :
		# do nothing in this default view
		return

class MenuWindow :
	def __init__(self, parent) :
		self._parent	= parent
		self._panel	= parent._panel
		self.titles	= [ menu['title'] for menu in MENU_STRINGS ] 
		self.items	= [ menu['items_populator']() for menu in MENU_STRINGS ] 
		self.arguments	= [ menu['args_populator']() if menu['args_populator'] is not None else menu['items_populator']() for menu in MENU_STRINGS ] 
		self.actions	= [ menu['change_action'] for menu in MENU_STRINGS ] 
		self.is_selected_function = [ menu['is_selected'] if menu.has_key('is_selected') else None for menu in MENU_STRINGS ] 
		if DEBUG: 
			print self.items
			print self.arguments
			print self.actions

		# Attributes:
		self.displayed_menu_index = 0
		self.first_displayed_item_index = [0] * len(self.titles)
		self.cursor_item_index = [0] * len(self.titles)
		self.selected_item_index = [0] * len(self.titles)
		self.displayed_status_index = 0
		self.displayed_notification_index = 0
		self.LINES = 6	

		# remove status file
		if os.path.exists(STATUS_MESSAGE_FILE) :
			try :
				file(STATUS_MESSAGE_FILE,"w").write("")
			except :
				self._parent._panel.clear()
				self._parent._panel.print_emphasis(3, "ERROR: read-only filesystem")
				self._parent._panel.print_emphasis(4, "Contact technical support")
				time.sleep(60)

		# check for events path, create it if it doesn't 
		if not os.path.exists(EVENTS_PATH) :
			raise NameError (".events path not created!")

	def _items(self) :
		return self.items[self.displayed_menu_index]
	def _first_displayed_item_index(self) :
		return self.first_displayed_item_index[self.displayed_menu_index]
	def _cursor_item_index(self) :
		return self.cursor_item_index[self.displayed_menu_index]
	def _selected_item_index(self) :
		return self.selected_item_index[self.displayed_menu_index]
	def _displayed_item(self) :
		items = self._items()
		return items[ self._first_displayed_item_index() ]
	def _argument(self, item_index) :
		arguments = self.arguments[self.displayed_menu_index]
		return arguments[ item_index ]
	def _displayed_title(self) :
		title = self.titles[self.displayed_menu_index]
		return title
	def _inc_item(self, inc) :
		proposed_value = self._cursor_item_index() + inc
		items = self._items()
		if proposed_value >= 0 and proposed_value < len(items) : 
			self.cursor_item_index[self.displayed_menu_index] = proposed_value
		if self._cursor_item_index() >= self._first_displayed_item_index()+self.LINES :
			self.first_displayed_item_index[self.displayed_menu_index] += 1
		elif self._cursor_item_index() < self._first_displayed_item_index() :
			self.first_displayed_item_index[self.displayed_menu_index] -= 1
			
	def _inc_menu(self, inc) :
		proposed_value = self.displayed_menu_index + inc
		if proposed_value >= 0 and proposed_value < len(self.titles) : self.displayed_menu_index = proposed_value
	def _select_current_item(self) :
		item_index = self._cursor_item_index()
		self.selected_item_index[self.displayed_menu_index] = item_index
		action = self.actions[self.displayed_menu_index]
		if action : action( self._argument(item_index) )
	def _is_item_selected(self, index) :
		f =  self.is_selected_function[self.displayed_menu_index]
		if f != None :
			return f( self._argument(index) )
		else :
		##############################
		# TODO: check this doesn't break anything!!! (NAEL, 12/09/2011)
			return None
		#	return self._selected_item_index() == index
		##############################
	def _is_item_cursor(self, index) :
		return self._cursor_item_index() == index
#	def _is_cursor_item_selected(self) :
#		return self._is_item_selected(self._cursor_item_index())
		
# public:	
	def repaint(self) :
		self._panel.print_emphasis(1, "Menu: "+self._displayed_title())
		items = self._items()
		for i in range(self.LINES) : 
			index = self._first_displayed_item_index()+i
			if index >= len(items) : break
			self._panel.print_item(2+i, items[index], self._is_item_selected(index), self._is_item_cursor(index))
		self._panel.curses_refresh()

	def process_event(self, key) :
		if key == self._panel.KEY_LEFT: 
			self._panel.clear()
			self._inc_menu(-1)
		elif key == self._panel.KEY_RIGHT: 
			self._panel.clear()
			self._inc_menu(1)
		elif key == self._panel.KEY_UP:
			self._inc_item(-1)
		elif key == self._panel.KEY_DOWN: 
			self._inc_item(1)
		elif key == self._panel.KEY_ENTER :
				self._select_current_item()
		elif key == self._panel.KEY_BACK or key == ord('d') :
			self._parent.change_to_status()
		self._parent.set_refresh()

	def timeout(self) :
		self._parent.change_to_status()

class EventHandler :
	def __init__(self) :
		self._panel = MatrixOrbitalPanel()
		self._menu_window = MenuWindow(self)
		self._upgrade_window = UpgradeWindow(self)
		self._status_window = StatusWindow(self)
		self._ingest_window = IngestWindow(self)
		self._current_context = self._status_window
		if os.path.exists(DISABLE_INTERACTIVE_BOOT_FILE) :
			os.remove(DISABLE_INTERACTIVE_BOOT_FILE)
		else : 
			self.interactive_boot_option()
#		self.inactivity_time_ms = 0
		self._needs_refresh = True
		self._time_counter = 0 #time.time()
	def _current_window_is_default(self) :
		return self._current_context is self._status_window
	def change_to_menu(self) :
		self._current_context = self._menu_window
		self._panel.clear()
		self.set_refresh()
	def change_to_status(self) :
		self._current_context = self._status_window
		self._panel.clear()
		self.set_refresh()
	def change_to_ingestion(self) :
		self._current_context = self._ingest_window
		self._panel.clear()
		self.set_refresh()
	def change_to_upgrade(self) :
		self._current_context = self._upgrade_window
		self._panel.clear()
		self.set_refresh()
	def set_refresh(self) :
		self._needs_refresh = True
	def run(self) :
		key = self._panel.NO_KEY
		# event loop
		self._time_counter = time.time()
		while 1:  
                        if self._current_window_is_default() :
				compatible_content, incompatible_content = self._ingest_window.get_new_content_available()
				if compatible_content['new'] or compatible_content['to_replace'] or self._ingest_window.are_volume_files_on_pendrive() :
					#if self._ingest_window.check_for_content() :
	                                self.change_to_ingestion()
        	                        self._ingest_window.run_ingestion_menu(compatible_content, incompatible_content) 
				pendrive_upgrade_version = self._upgrade_window.check_for_pendrive_upgrade() if self._current_window_is_default() else None
				#internet_upgrade_version = self._upgrade_window.check_for_internet_upgrade()
				if pendrive_upgrade_version :
					self.change_to_upgrade()
					self._upgrade_window.run_upgrade_menu(pendrive_upgrade_version)
			# Wait for key till timeout
			key = self._panel.getkey() 
			if key == self._panel.NO_KEY :
				#self.inactivity_time_ms += 1
				#if self.inactivity_time_ms < 4000 and not self._needs_refresh: # keep waiting key in the same mode
				if time.time() - self._time_counter < 4 and not self._needs_refresh : # keep waiting key in the same mode
					continue 
				elif time.time() > 4 : # timeout: change to default mode
					#self.set_refresh()
#					if not self._current_window_is_default() : 
					self._current_context.timeout()
					self.set_refresh()
				#self.inactivity_time_ms = 0
			self._time_counter = time.time()

			self._current_context.process_event(key)
			if self._needs_refresh :
				self._current_context.repaint()
				self._needs_refresh = False

		self._panel.curses_tear_down()

	def interactive_boot_option(self) :
		self._panel._driver.setAutoRepeatKeyModeResend(True)
		self._panel.print_emphasis(4, "Enter boot option")
		time.sleep(3)
		pressed_keys = self._panel._driver.read()
		rescue_boot = True
		for k in pressed_keys : 
			if k is not "E" : 
				rescue_boot = False
				break
		rescue_boot = rescue_boot and len(pressed_keys) > 3
		if rescue_boot : 
			try : 
				open(REBOOT_FILE, "w").write("0") # 0 is rescue partition
			except :
				self._panel.print_emphasis(4, "Error rebooting on rescue...")
			else :	
				self._panel.print_emphasis(4, "Rebooting in rescue mode...")
				time.sleep(20)
		if DEBUG: self._panel.print_emphasis(5, ",".join(pressed_keys))
		self._panel.print_emphasis(4, "Normal boot...")
		time.sleep(1)
		self._panel.clear()
		self._panel._driver.setAutoRepeatKeyModeResend(False)
def main():
	app = EventHandler()
	app.run() 

if __name__ == "__main__" :
	main()

# PyMOPanel
Python module to control Matrix Orbital GLK19264-7T-1U LCD+keyboard USB panels.

Manual: https://www.mouser.com/datasheet/2/255/GLK19264-7T-1U-5080.pdf

**WORK IN PROGRESS**.

![Example](doc/output_lcd.gif? "example")
![Example](doc/output_top.gif? "example of CPU and memory utilization monitor")

### TODO
 - separate Driver from Controller and Demo logic
   - [x] ~classes~
   - [x] files
 - create proper module and python package
 - create menu helper (a la curses) to allow adding items with custom callback functions
 - MIDI / OSC
   - keyboard to OSC example
   - OSC / MIDI monitor with bar graphs
   - custom widgets for controllers / monitors? (knobs, ...)
 - graphics
   - [x] ~.bmp to screen~
   - [x] ~upload animated .gif to screen!~
   - [x] ~download bitmaps~
   - create helper for threaded animations, so several animations on different screen positions are played (to check how serially-interleaved frames work)
   - upload bitmaps
   - save fs image to .bmp
   - implement strip charts
   - allow FM and AM in Lissajous demo
   - optimizations
     - use uploaded bitmaps instead for faster animations
     - use numpy.array's to precalculate trigonometric functions in vectors
 - bar graphs
   - improve code (allow deleting, ...)
 - fonts
   - FontManager (caching the current set font, downloading to cache font attributes)
   - [x] ~font to ascii numpy arrays~
   - [x] ~ascii numpy arrays to font~
   - [x] ~downloader~
   - uploader (WIP)
 - filesystem
   - [x] ~filesystem to .data dump~
   - .data to filesystem
   - decoding filesystem to files
   - [x] ~ls~
   - [x] ~move~
   - [x] ~rm~
   - [x] ~free~
   - implement xmodem?
 - hack for Quake to use the panel as display + input device?     

# PyMOPanel
Python module to control Matrix Orbital GLK19264-7T-1U LCD+keyboard USB panels.

Manual: https://www.mouser.com/datasheet/2/255/GLK19264-7T-1U-5080.pdf

**WORK IN PROGRESS**. It is currently just a basic script where I am testing and adding functionalities.

![Example](doc/output_lcd.gif "example")

### TODO
 - separate Driver from Controller and Demo logic
   - [x] ~classes~
   - files
 - create proper module
 - create menu helper (a la curses) to allow adding items with custom callback functions
 - MIDI / OSC
   - keyboard to OSC example
   - OSC / MIDI monitor with bar graphs
   - custom widgets for controllers / monitors? (knobs, ...)
 - [x] ~.bmp to screen~
 - [x] ~upload animated .gif to screen!~
 - allow FM and AM in Lissajous demo
 - optimizations
   - use uploaded bitmaps instead for faster animations
   - use numpy.array's to precalculate trigonometric functions in vectors  
 - filesystem
   - [x] ~dumpers~
   - "ls"
   - .data to filesystem
   - helpers
     - .data to .bmp?
 - hack for Quake to use the panel as display + input device?     


allow passing cropping option for animation and bitmaps, and FFOA for animations.

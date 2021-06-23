# tkGfx -    Implementation of the Gfx.Driver Interface in a 
#    tkinter enviroment

"""Implementes Gfx.Driver using tkInter. 

Has some flaws! Specifically rotated text is not yet implemented.
"""

import math
from Tkinter import *
import tkFont
import Gfx

from Compatibility import *


driverName = "tkGfx"

########################################################################
#
#   class Driver
#
########################################################################


class Driver(Gfx.Driver):
    """A graphics driver for  Tkinter.
    For an explanation of the inherited methods see GfxDriver.py.
    """

    def __init__(self, tkCanvas):
        """Initialize Driver for a Tkinter Canvas Object."""
        self.canvas = tkCanvas
        self.resizedGfx()
        self.reset()
        self.clear()

    def colorStr(self, rgbTuple):
        """rgbTuple -> string (eg. '#A0A0F3')"""
        def hex2str(c):
            h = hex(int(round(c*255)))[2:]
            if len(h) == 1: return "0"+h
            else: return h
        s = "#" + hex2str(rgbTuple[0]) + hex2str(rgbTuple[1]) + \
                  hex2str(rgbTuple[2])
        return s

    def resizedGfx(self):
        """Take notice if the undelying device has been resized."""
        self.w = int(self.canvas.cget("width"))
        self.h = int(self.canvas.cget("height"))

    def getSize(self):
        return self.w, self.h

        
    def setColor(self, rgbTuple):
        self.color = rgbTuple
        self.fg = self.colorStr(rgbTuple)


    def setLineWidth(self, width):
        self.lineWidth = width
        if width == Gfx.THIN: self.width = "1.0"
        elif width == Gfx.MEDIUM: self.width = "2.0"
        elif width == Gfx.THICK: self.width = "3.0"
        else: raise ValueError, "'thickness' must be THIN, MEDIUM or THICK !"

    def setLinePattern(self, pattern):
        """Set line pattern (CONTINOUS, DASHED or DOTTED)."""
        self.linePattern = pattern
        if pattern == Gfx.CONTINUOUS: self.dash = ""
        elif pattern == Gfx.DASHED: self.dash = "- "
        elif pattern == Gfx.DOTTED: self.dash = ". "
        else: raise ValueError, "'pattern' must be CONTINUOUS, DASHED or DOTTED !"        
        
    def setFillPattern(self, pattern):
        """Set pattern for filled areas (SOLID or PATTERNED)."""
        self.fillPattern = pattern
        if pattern == Gfx.SOLID: self.stipple = ""
        elif pattern == Gfx.PATTERN_A: self.stipple = "" # needs to be updated
        elif pattern == Gfx.PATTERN_B: self.stipple = ""
        elif pattern == Gfx.PATTERN_C: self.stipple = ""
        else: raise ValueError, "'pattern' must be SOLID or PATTERNED !"        


    def setFont(self, ftype, size, weight):
        self.fontType = ftype
        self.fontSize = size
        self.fontWeight = weight
        if ftype == Gfx.SANS: self.family = "Helvetica"
        elif ftype == Gfx.SERIF: self.family = "Times"
        elif ftype == Gfx.FIXED: self.family = "Courier"
        else: raise ValueError, "'type' must be SANS, SERIF or FIXED !"
        if size == Gfx.SMALL: self.size = "8"
        elif size == Gfx.NORMAL: self.size = "12"
        elif size == Gfx.LARGE: self.size = "16"
        else: raise ValueError, "'size' must be SMALL or NORMAL or LARGE !"
        if "i" in weight: self.slant = "italic"
        else: self.slant = "roman"
        if "b" in weight: self.weight = "bold"
        else: self.weight = "bold"
        self.font = tkFont.Font(family = self.family, size = self.size,
                                weight = self.weight, slant=self.slant)
        
    def getTextSize(self, text):
        return (len(text) * int(self.size)*2/3, int(self.size))   # very inexact

        
    def clear(self, rgbTuple = (1.0, 1.0, 1.0)):
        self.canvas.delete("all")
        self.canvas.config(bg = self.colorStr(rgbTuple))

    def drawPoint(self, x, y):
        self.canvas.create_line(x+1, self.h-y, x+2, self.h-y,
                                width=self.width, fill=self.fg)
    
    def drawLine(self, x1, y1, x2, y2):
        self.canvas.create_line(x1+1, self.h-y1, x2+1, self.h-y2,
                                width=self.width, dash=self.dash,
                                fill=self.fg)
    
    def fillPoly(self, array):
        if array:
            coords = ()
            for point in array: coords += (point[0]+1, self.h-point[1])
            self.canvas.create_polygon(coords, fill = self.fg,
                                       stipple = self.stipple)

    def writeStr(self, x, y, str, rotationAngle = 0.0):
        if rotationAngle <> 0.0:
            # very bad workaround:
            w,h = self.getTextSize(str)
            x += w*(math.cos(2.0*math.pi*rotationAngle/360.0)/2.0 - 0.5)
            y += w*(math.sin(2.0*math.pi*rotationAngle/360.0)/2.0)
        self.canvas.create_text(x+1,self.h-y, text=str, anchor="sw",
                                    font = self.font, fill=self.fg)            




########################################################################
#
#   class Window
#
########################################################################


class Window(Driver, Gfx.Window):
    
    def __init__(self, size=(640, 480), title="tkGraph"):
        self.root = Tk()
        self.root.title(title)
        self.root.protocol = ("WM_DELETE_WINDOW", self.quit)
        self.graph = Canvas(self.root, width=size[0], height=size[1])
        self.graph.pack()
        self.root.update()
        Driver.__init__(self, self.graph)

    def refresh(self):
        self.root.update()

    def quit(self):
        self.root.destroy()

    def waitUntilClosed(self):
        self.root.mainloop()

    def dumpPS(self, fileName):
        f = open(fileName, "w")
        f.write(self.graph.postscript())
        f.close()
                
    
########################################################################
#
#   Test
#
########################################################################

if __name__ == "__main__":
    import systemTest
    systemTest.Test_tkGfx()

    


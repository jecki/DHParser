# awtGfx -    Implementation of the Gfx.Driver Interface with the java.awt

"""Implementes Gfx.Driver for the java awt. 
"""

import math
import java, pawt
from java import awt, applet

import Gfx
from Compatibility import *


driverName = "awtGfx"

########################################################################
#
#   class Driver
#
########################################################################

white = pawt.colors.white
black = pawt.colors.black


class Driver(Gfx.Driver):
    """A simple graphics layer on top of teh java awt.
    See GfxInterface.py
    """

    def __init__(self, awtObject):
        """Initialize canvas on an awt component or image.
        """
        self.changeGfx(awtObject)

    def changeGfx(self, awtObject):
        """Change the awt object (either image or awt component)"""
        self.awtObject = awtObject
        self.graphics = self.awtObject.getGraphics()
        self.resizedGfx()
        self.reset()

    def resizedGfx(self):
        self.w = self.awtObject.getWidth()
        self.h = self.awtObject.getHeight()

    def getSize(self):
        return self.w, self.h

    def getResolution(self):
        return 100

    def setColor(self, rgbTuple):
        self.graphics.setColor(awt.Color(*rgbTuple))
        self.color = rgbTuple

    def setLineWidth(self, width):
        self.lineWidth = width
        # not yet implemented

    def setLinePattern(self, pattern):
        self.linePattern = pattern
        # not yet implemented

    def setFillPattern(self, pattern):
        self.fillPattern = pattern
        # not yet implemented
        
    def setFont(self, ftype, size, weight):
        self.fontType = ftype
        self.fontSize = size
        self.fontWeight = weight
        if ftype == Gfx.SANS:  self.ff = "SansSerif"
        elif ftype == Gfx.SERIF:  self.ff = "Serif"
        elif ftype == Gfx.FIXED:  self.ff = "Monospaced"
        else: raise ValueError, \
                    "'type' must be 'sans', 'serif' or 'fixed' !"
        if size == Gfx.SMALL: self.fsize = 10
        elif size == Gfx.NORMAL: self.fsize = 12
        elif size == Gfx.LARGE: self.fsize = 14
        else: raise ValueError, \
                    "'size' must be 'small', 'normal' or 'large' !"
        self.fst = 0
        if "i" in weight: self.fst |= awt.Font.ITALIC
        elif "b" in weight: self.fst |= awt.Font.BOLD
        self.graphics.setFont(awt.Font(self.ff, self.fst, self.fsize))

    def getTextSize(self, text):
        return (len(text) * self.fsize*2/3, self.fsize)
        # very inexact!
       
    def drawLine(self, x1, y1, x2, y2):
        self.graphics.drawLine(x1, self.h-y1-1, x2, self.h-y2-1)

    def drawPoly(self, array):
        xpoints = [x for x,y in array]
        ypoints = [self.h-y-1 for x,y in array]
        self.graphics.drawPolyline(xpoints, ypoints, len(array))        

    def drawRect(self, x, y, w, h):
        self.graphics.drawRect(x,self.h-y-h,w-1,h-1)

    def fillRect(self, x, y, w, h):
        self.graphics.fillRect(x,self.h-y-h,w,h)

    def fillPoly(self, array):
        xpoints = [x for x,y in array]
        ypoints = [self.h-y-1 for x,y in array]
        self.graphics.fillPolygon(xpoints, ypoints, len(array))


    def writeStr(self, x, y, str, rotationAngle=0.0):
        w,h = self.getTextSize(str)        
        if rotationAngle == 0.0:
            self.graphics.drawString(str, x, self.h-y)
        else:
            dcfg = self.graphics.getDeviceConfiguration()
            image = dcfg.createCompatibleImage(w, h)
            g = image.getGraphics()
            g.setFont(awt.Font(self.ff, self.fst, self.fsize))
            g.drawString(str, 0, h*5/6)
            a = rotationAngle / 180.0 * math.pi
            for dy in range(h):
                for dx in range(w):
                    if (image.getRGB(dx, dy) & 0x00FFFFFF) != 0:
                        r = math.sqrt(dx**2+dy**2)
                        da = math.atan2(dy,dx) - a
                        xx = int(r * math.cos(da)+0.5)
                        yy = int(r * math.sin(da)+0.5)
                        self.graphics.drawLine(x+xx, self.h-y-1+yy,
                                               x+xx, self.h-y-1+yy)
                                                 
##~             afTrans = awt.geom.AffineTransform()
##~             theta = rotationAngle*math.pi/180.0
##~             # afTrans.setToRotation(theta, x, y)
##~             # afTrans.setToRotation(math.pi/2.0, 100, 120)
##~             dummyObserver = awt.Canvas()
##~             self.graphics.drawImage(image, afTrans, dummyObserver)
        
##~             # very bad workaround:
##~             x += w*(math.cos(2.0*math.pi*rotationAngle/360.0)/2.0 - 0.5)
##~             y += w*(math.sin(2.0*math.pi*rotationAngle/360.0)/2.0)
##~             self.graphics.drawString(str, x, self.h-y-h)


########################################################################
#
#   class Window
#
########################################################################

myCanvas = None
myApplet = None

class Canvas(awt.Canvas):
    def __init__(self):
        self.win = None
    def setWin(self, win):
        self.win = win
    def paint(self, g):
        if self.win != None:  self.win.refresh()
        
class Applet(applet.Applet):
    def init(self):
        self.setLayout(awt.BorderLayout())
        self.panel = awt.Panel()
        self.panel.setLayout(awt.BorderLayout())
        self.canvas = Canvas()
        self.panel.add(self.canvas)
        self.add(self.panel)

class Window(Driver, Gfx.Window):
    def __init__(self, size=(640,480), title="awtGraph"):
        global myCanvas, myApplet
        if myCanvas == None:
            if myApplet == None:
                myApplet = Applet()
                pawt.test(myApplet, name=title, size=(size[0]+8,size[1]+30))
            myCanvas = myApplet.canvas
        dcfg = myCanvas.getGraphics().getDeviceConfiguration()
        self.image = dcfg.createCompatibleImage(size[0], size[1])
        Driver.__init__(self, self.image)
        if isinstance(myCanvas, Canvas):  myCanvas.setWin(self)

    def refresh(self):
        myCanvas.getGraphics().drawImage(self.image, None, 0, 0)

    def quit(self):
        pass
    
    def waitUntilClosed(self):
        self.refresh()

########################################################################
#
#   Test
#
########################################################################

if __name__ == "__main__":
    import systemTest
    systemTest.Test_awtGfx()


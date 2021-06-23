# Gfx

"""Defines an abstract base class for a (simple) graphics interface.

The purpose of modules 'Plotter.Gfx' is to define a simple graphics
interface that can be implemented for different GUI or printing 
libraries. In order to implement a driver for a certain GUI or
graphics device, the class Driver (and possibly also the class window)
should be derived and (at least) abstract methods should be implemented
for the respective device.

Currently there exist implementations for wxWindows, gtk and tkinter.
"""

from Compatibility import *


########################################################################
#
#   constants
#
########################################################################

THIN="thin"; MEDIUM="medium"; THICK="thick"             # pen size
CONTINUOUS="continuous"; DASHED="dashed"; DOTTED="dotted"# line style
SOLID="solid"; PATTERN_A="patternA";                    # fill style
PATTERN_B="patternB"; PATTERN_C="patternC";
PATTERNED="patternA"
SANS="sans"; SERIF="serif"; FIXED="fixed"               # font style
SMALL="small"; NORMAL="normal"; LARGE="large"           # font size
PLAIN = ""; BOLD = "b"; ITALIC="i"; BOLDITALIC="bi"    # font weight


########################################################################
#
#   colors
#
########################################################################

BLACK  = (0.0, 0.0, 0.0)
WHITE  = (1.0, 1.0, 1.0)
RED    = (1.0, 0.0, 0.0)
GREEN  = (0.0, 1.0, 0.0)
BLUE   = (0.0, 0.0, 1.0)
YELLOW = (1.0, 1.0, 0.0)
TURKEY = (0.0, 1.0, 1.0)
PINK   = (1.0, 0.0, 1.0)


########################################################################
#
#   class Pen
#
#  Pens are sets of graphical atrributes. Thus changeing the font, color,
#  style of a graphics context simplifies to applying a pen that contains
#  the respective attributes.
#
########################################################################

class Pen(object):
    """Record containing the all drawing attributes, namely: color, 
    line width, line style, fill pattern, font type, size and weight.
    """

    __slots__ = ('color', 'lineWidth', 'linePattern', 'fillPattern',
		 'fontType', 'fontSize', 'fontWeight')

    def __repr__(self):
        return "Pen(" + repr(self.color) + "," \
                      + repr(self.lineWidth) + ", " \
                      + repr(self.linePattern) + ", " \
                      + repr(self.fillPattern) + ", " \
                      + repr(self.fontType) + ", " \
                      + repr(self.fontSize) + ", " \
                      + repr(self.fontWeight) + ", " \
                      ")"
    
    def __init__(self, color = (0.0, 0.0, 0.0), lineWidth = THIN, 
                 linePattern = CONTINUOUS, fillPattern = SOLID,
                 ftype = SANS, fsize = NORMAL, fweight = PLAIN):
        self.color = color
        self.lineWidth = lineWidth
        self.linePattern = linePattern
        self.fillPattern = fillPattern
        self.fontType = ftype
        self.fontSize = fsize
        self.fontWeight = fweight
             
COLOR, LINE_WIDTH, LINE_PATTERN, FILL_PATTERN, FONT = \
map(lambda i:2**i, range(5))
MASK_LINE = COLOR|LINE_WIDTH|LINE_PATTERN
MASK_FILL = COLOR|FILL_PATTERN
MASK_FONT = COLOR|FONT
MASK_ALL = COLOR|LINE_WIDTH|LINE_PATTERN|FILL_PATTERN|FONT


########################################################################
#
#  standard pens
#
########################################################################

BLACK_PEN  = Pen(color = BLACK)
WHITE_PEN  = Pen(color = WHITE)
RED_PEN    = Pen(color = RED)
GREEN_PEN  = Pen(color = GREEN) 
BLUE_PEN   = Pen(color = BLUE)
YELLOW_PEN = Pen(color = YELLOW)
TURKEY_PEN = Pen(color = TURKEY)
PINK_PEN   = Pen(color = PINK)



########################################################################
#
#   class Driver
#
########################################################################

class Driver(object):
    """Abstract Graphics Interface class.

    A graphics driver can be implemented by subclassing this interface
    class and overwriting its drawing methods. 
    
    Attributes (read only, use the setXXX methods to change values!):
        color       - pen color (also fill color!)
        lineWidth   - pen width for drawing lines and points
        linePattern - drawing pattern for lines
        fillPattern - drawing pattern for filled areas
        fontType    - font type: sans, serif or fixed
        fontSize    - font size: small, normal or large
        fontWeight  - font wight: "", "b", "i" or "bi"
    
    In order to implement a minimal driver, the following methods must 
    be overriden:
        getSize,
        getTextSize,
        drawLine,
        fillPoly,
        writeStr
    The methods must be aware of the attributes set by the setXXX methods

    Note that canvas size ranges from (0,0) to (width-1, height-1). The
    size of the canvas is predetermined by the driver. The origin
    is always the lower left border.        
    """

    def __init__(self):
        self.color = (0.0, 0.0, 0.0)
        self.lineWidth = THIN
        self.linePattern = CONTINUOUS
        self.fillPattern = SOLID
        self.fontType = SANS
        self.fontSize = NORMAL
        self.fontWeight = PLAIN
    
    def reset(self):
        """Resets the driver to default values."""
        self.setColor((0.0, 0.0, 0.0))
        self.setLineWidth(THIN)
        self.setLinePattern(CONTINUOUS)
        self.setFillPattern(SOLID)
        self.setFont(SANS, NORMAL, PLAIN)

    def resizedGfx(self):
        """Takes notice if the undelying device has been resized."""
        pass

    def getSize(self):
        """Gets canvas size in pixel. Returns a tuple (w,h)."""
        raise NotImplementedError

    def getResolution(self):
        """Returns resolution of graphics device in dots per inch."""
        return 100

        
    def setColor(self, rgbTuple):
        """Sets drawing color. r,g,b range from 0.0 to 1.0"""
        self.color = rgbTuple


    def setLineWidth(self, width):
        """Sets pen thickness (THIN, MEDIUM or THICK)."""
        self.lineWidth = width

    def setLinePattern(self, pattern):
        """Sets line pattern (CONTINOUS, DASHED or DOTTED)."""
        self.linePattern = pattern

    def setFillPattern(self, pattern):
        """Sets pattern for filled areas (SOLID or PATTERNED)."""
        self.fillPattern = pattern


    def setFont(self, ftype, size, weight):
        """Selects a font.
        
        type:  SANS, SERIF or FIXED
        size:  SMALL, NORMAL or LARGE
        weight: '', 'b', 'i', 'bi' for plain, bold, italic, bold+italic
                                    respectively
        """
        self.fontType = ftype
        self.fontSize = size
        self.fontWeight = weight

    def applyPen(self, pen, mask = MASK_ALL):
        """Sets the gfx attributes according to pen"""
        if COLOR & mask and self.color != pen.color:  
            self.setColor(pen.color)
        if LINE_WIDTH & mask and self.lineWidth != pen.lineWidth:  
            self.setLineWidth(pen.lineWidth)
        if LINE_PATTERN & mask and self.linePattern != pen.linePattern: 
            self.setLinePattern(pen.linePattern)
        if FILL_PATTERN & mask and self.fillPattern != pen.fillPattern:
            self.setFillPattern(pen.fillPattern)
        if FONT & mask and (self.fontType != pen.fontType or \
          self.fontSize != pen.fontSize or \
          self.fontWeight != pen.fontWeight):
            self.setFont(pen.fontType, pen.fontSize, pen.fontWeight)
            
    def savePen(self):
        """Returns the gfx attributes as a pen."""
        return Pen(self.color, self.lineWidth, self.linePattern,
                   self.fillPattern, self.fontType, self.fontSize,
                   self.fontWeight)            
        
    def getTextSize(self, text):
        """Returns the size of the bounding box, if 'text' is printed
        with the selected font. Returns a tuple (w,h).
        """
        raise NotImplementedError

##    def selectFontSize(self, text, w,h):
##        """Change the font size, so that the string 'text' will fit
##        the into the bounding box 'w','h'. Returns true if successful.
##        """
##
##        for fs in range(3,0,-1):
##            self.setFont(self, self.fontType, fs, self.fontWeight)
##            sw,sh = self.getTextSize(text)
##            if sw <= w and sh <= h: break
##        else:
##            return 0
##        return 1

        
    def clear(self, rgbTuple = (1.0, 1.0, 1.0)):
        """Clears the painting area using the specified background color.
        """
        w, h = self.getSize()
        self.clearRegion((0, 0, w-1, h-1), rgbTuple)

    def clearRegion(self, region, rgbTuple=(1.0, 1.0, 1.0)):
        """Clears a region (4-tuple: (x1,y1,x2,y2)) of the painting area."""
        saveColor = self.color;
        savePattern = self.fillPattern
        self.setColor(rgbTuple)
        self.setFillPattern(SOLID)
        self.fillRect(region[0], region[1],
                      region[2]-region[0]+1, region[3]-region[1]+1)
        self.setColor(saveColor)
        self.setFillPattern(savePattern)        

    def drawPoint(self, x, y):
        """Draws a point."""
        self.drawLine(x, y, x, y)
    
    def drawLine(self, x1, y1, x2, y2):
        """Draws a line"""
        raise NotImplementedError

    def drawRect(self, x, y, w, h):
        """Draws a rectangle"""
        self.drawPoly([(x,y),(x+w-1,y),(x+w-1,y+h-1),(x,y+h-1),(x,y)])
        
    def drawPoly(self, array):
        """Draws a polygon outline. 'array must be an array of coordinate
        tupels [(x1,y1), (x2,y2), ...]"""
        n = len(array)
        if n == 0: return
        elif n == 1:
            self.drawPoint(array[0][0], array[0][1])
        else:
            p0 = array[0]
            for p1 in array[1:]:
                self.drawLine(p0[0], p0[1], p1[0], p1[1])
                p0 = p1
    
    def fillRect(self, x, y, w, h):
        """Draws a filled rectangle"""
        self.fillPoly([(x,y), (x+w-1,y), (x+w-1,y+h-1), (x, y+h-1)])

    def fillPoly(self, array):
        """Draws a filled polygon. 'array' must be an array of coordinate
        tupels [(x1,y1), (x2,y2), ...]."""
        raise NotImplementedError


    def writeStr(self, x, y, str, rotationAngle=0.0):
        """Writes String str at position (x,y), where (x,y) is the lower
        left corner of the text.
        """
        raise NotImplementedError


    #### helper functions to circumvent limitations of the used toolkit ####

    def _dashedLine(self, x1, y1, x2, y2):
        """Draws a dashed line segment; circumvents the underlying graphics
        toolkit to ensure that really a dashed line is drawn (even for
        short line segments).
        """
        dX = x2-x1;  dY = y2-y1
        if (dX*dX + dY*dY) < 64:
            if (x1 / 7) % 2 == 0:  self.drawLine(x1, y1, x2, y2)
        else:
            self.drawLine(x1, y1, x2, y2)

    def _dottedLine(self, x1, y1, x2, y2):
        """Draws a dotted line segment; circumvents the underlying graphics
        toolkit to ensure that really a dotted line is drawn (even for
        short line segments)."""
        dX = x2-x1;  dY = y2-y1
        if (dX*dX + dY*dY) < 4:
            if (x1 / 3) % 2 == 0:  self.drawLine(x1, y1, x2, y2)
        else:
            self.drawLine(x1, y1, x2, y2)


    def _drawLine(self, x1, y1, x2, y2):
        """Draws a line and ensures that it is really dashed or dotted
        if the line pattern requires it.
        """
        if self.linePattern == DASHED:
            self._dashedLine(x1, y1, x2, y2)
        elif self.linePattern == DOTTED:
            self._dottedLine(x1, y1, x2, y2)
        else: self.drawLine(x1, y1, x2, y2) 

    def _drawPoly(self, array):
        """Draws a polygon and ensures that it is really dashed or
        dotted if the line pattern requires it.
        """
        if self.linePattern == CONTINUOUS:
            self.drawPoly(array)
        else:
            if self.linePattern == DASHED: f = self._dashedLine
            elif self.linePattern == DOTTED: f = self._dottedLine
            for n in xrange(1, len(array)):
                f(array[n-1][0], array[n-1][1],
                  array[n][0], array[n][1])
            


def split(self, x1, y1, x2, y2):
    """-> (xd, yd, xu, yp), the rounded down and rounded up middle point
    of the line (x1, y1, x2, y2)"""
    return (x1 + (x2-x1)/2, y1 + (y2-y1)/2,
            x1 + (x2-x1+1)/2, y1 + (y2-y2+1)/2)
        

########################################################################
#
#   NIL Driver - A dummy driver that outputs nothing
#
########################################################################

class nilDriver(Driver):
    """A dummy Gfx.Driver without output. This is useful for testing
    as well as other purposes such as drawing on a graph and only
    later opening the actual device to be drawn to (and then telling
    the graph that the device context (resp. driver) has changed).
    """
    def __init__(self, w = 1024, h = 768):
        Driver.__init__(self)
        self.w = w
        self.h = h
    
    def reset(self):
        Driver.reset(self)
        
    def resizedGfx(self):
        pass

    def getSize(self):
        return self.w, self.h

    def getResolution(self):
        return 100

    def setColor(self, rgbTuple):
        self.color = rgbTuple

    def setLineWidth(self, width):
        self.lineWidth = width

    def setLinePattern(self, pattern):
        self.linePattern = pattern

    def setFillPattern(self, pattern):
        self.fillPattern = pattern

    def setFont(self, ftype, size, weight):
        Driver.setFont(self, ftype, size, weight)

    def applyPen(self, pen, mask = MASK_ALL):
        Driver.applyPen(self, pen, mask)

    def savePen(self):
        return Driver.savePen(self)           
        
    def getTextSize(self, text):
        if self.fontSize == SMALL:    return (len(text)*8, 16)
        elif self.fontSize == NORMAL: return (len(text)*12, 24)
        elif self.fontSize == LARGE:  return (len(text)*16, 32)
        else: raise ValueError, "Illegal font size %i" % self.fontSize

##    def selectFontSize(self, text, w,h):
##        """Change the font size, so that the string 'text' will fit
##        the into the bounding box 'w','h'. Returns true if successful.
##        """
##
##        for fs in range(3,0,-1):
##            self.setFont(self, self.fontType, fs, self.fontWeight)
##            sw,sh = self.getTextSize(text)
##            if sw <= w and sh <= h: break
##        else:
##            return 0
##        return 1

    def clear(self, rgbTuple = (1.0, 1.0, 1.0)):
        pass
    def clearRegion(self, region, rgbTuple=(1.0, 1.0, 1.0)):
        pass       
    def drawPoint(self, x, y):
        pass
    def drawLine(self, x1, y1, x2, y2):
        pass
    def drawRect(self, x, y, w, h):
        pass
    def drawPoly(self, array):
        pass
    def fillRect(self, x, y, w, h):
        pass
    def fillPoly(self, array):
        pass
    def writeStr(self, x, y, str, rotationAngle=0.0):
        pass   

########################################################################
#
#   class Window
#
########################################################################

class Window(Driver):
    """Opens a window that can be painted into. """

    def __init__(self, size, title):
        pass

    def refresh(self):
        """Refreshes the display."""
        raise NotImplementedError

    def quit(self):
        """Closes the window"""
        raise NotImplementedError

    def waitUntilClosed(self):
        """Waits until the graph window ist closed by the user.
        """
        raise NotImplementedError        
        

########################################################################
#
#   Test
#
########################################################################

if __name__ == "__main__":
    import systemTest
    systemTest.Test_nilDevice()
    print "nilDevice test sucessful"

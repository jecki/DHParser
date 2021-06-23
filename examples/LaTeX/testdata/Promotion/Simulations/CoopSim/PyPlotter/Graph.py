#!/usr/bin/python
# Graph

"""Provides classes for coordinate transformations, management of screen
regions, and drawing graphs onto a cartesian plane.
"""

import math, random, copy
from Compatibility import *

import Gfx, Colors


########################################################################
#
#   class CoordinateTransformer
#
########################################################################
    

class CoordinateTransformer(object):
    """Transforms virtual coordinates to screen (or printer) coordinates

    Attributes (read only!):
        vx1, vy1, vx2, vy1  -   virtual coordinate range
        sx1, sy1, sx2, sy2  -   screen coordinate range
        keepAspect          -   keep aspect ratio (boolean)
    """
    
    def __init__(self, x1,y1,x2,y2, vx1=-1.0, vy1=-1.0,
                 vx2=1.0, vy2=1.0, keepAspectRatio=True):
        """Initialize coordinate transformer with sreen and virtual
        coordinate range.
        """
        self.x1 = vx1;  self.y1 = vy1
        self.x2 = vx2;  self.y2 = vy2
        self.keepAspect = keepAspectRatio
        self.setScreen(x1,y1, x2,y2)

    def setScreen(self, x1,y1, x2,y2):
        """Define the screen coordinates. Note that the direction is
        always from bottom to top and from left to right. So, if the
        origin of the screen is the upper left corner, y1 and y2 have
        to be swapped.
        """
        self.sx1 = x1;  self.sy1 = y1
        self.sx2 = x2;  self.sy2 = y2
        self.sw = x2-x1
        self.sh = y2-y1
        self.setRange(self.x1, self.y1, self.x2, self.y2)

    def setRange(self, x1,y1, x2,y2):
        """Set the virtual coordinate range."""
        self.x1 = float(x1);  self.y1 = float(y1);
        self.x2 = float(x2);  self.y2 = float(y2);
        self.w = self.x2-self.x1
        self.h = self.y2-self.y1
        self.xmult = self.sw / self.w
        self.ymult = self.sh / self.h
        self.dx = 0;  self.dy = 0
        if self.keepAspect:
            sr = float(self.sw) / float(self.sh)
            vr = self.w / self.h
            if sr < vr:
                self.ymult *= sr / vr
                self.dy = round((self.sh - self.h*self.ymult) / 2.0)
            elif sr > vr:
                self.xmult *= vr / sr
                self.dx = round((self.sw - self.w*self.xmult) / 2.0)
        self.dx += (0.0-x1)*self.xmult - (0 - self.sx1)
        self.dy += (0.0-y1)*self.ymult - (0 - self.sy1)

    def keepAspectRatio(self, yesno):
        """boolean: Keep Aspect Ratio?"""
        if yesno != self.keepAspect:
            self.keepAspect = yesno
            self.setRange(self.x1, self.y1, self.x2, self.y2)
    
    def X(self, x):
        """Transform virtual x-coordinate to screen coortinate."""
        return int(x*self.xmult + self.dx +0.5)

    def Y(self, y):
        """Transform virtual y-coordinate to screen coortinate."""
        return int(y*self.ymult + self.dy +0.5)


    def transform(self, pointList):
        """Transform an array of (x,y)-tupels to screen coordinates."""
        return [(self.X(p[0]), self.Y(p[1])) for p in pointList]

    
    def invX(self, sx):
        """Transform a screen x-coordinate to a virtual coordinate."""
        return float(sx-self.dx) / self.xmult

    def invY(self, sy):
        """Transform a screen y-coordinate to a virtual coordinate."""
        return float(sy-self.dy) / self.ymult

    def inverse(self, pointList):
        """Retransform an array of (x,y)-tupels of screen coordinates
        to virtual coordinates.
        """
        return [(self.invX(p[0]), self.invY(p[1])) for p in pointList]



########################################################################
#
#   class VirtualScreen
#
########################################################################        


def screenRegion(gfx, region=(0.0, 0.0, 1.0, 1.0)):
    """(gfx, 4-tuple of floats) -> (4-tuple of ints)
    Determine the absolute coordinates of a screen region from its
    relative coordinates (coordinates from 0.0 to 1.0)
    """
    w,h = gfx.getSize()
    x1 = (w-1)*region[0];  y1 = (h-1)*region[1]
    x2 = (w-1)*region[2];  y2 = (h-1)*region[3]
    if type(w) == type(1):
        x1 = int(x1 + 0.5);  y1 = int(y1 + 0.5)
        x2 = int(x2 + 0.5);  y2 = int(y2 + 0.5)  
    return (x1, y1, x2, y2)

def relativeRegion(region, parentRegion):
    """(region, region) -> (region)
    Create a region as part of another region. => region
    """
    w = parentRegion[2] - parentRegion[0]
    h = parentRegion[3] - parentRegion[1]
    x1 = parentRegion[0] + w*region[0]
    y1 = parentRegion[1] + h*region[1]
    x2 = parentRegion[0] + w*region[2]
    y2 = parentRegion[1] + h*region[3]
    return (x1, y1, x2, y2)


REGION_FULLSCREEN = (0.0, 0.0, 1.0, 1.0)
REGION_FRAMED = (0.05, 0.05, 0.95, 0.95)


class VirtualScreen(object):
    """Uses a region of the graphics area as a virtual screen.
    
    Attributes (read only!):
        gfx        -  the graphics interface
        region     -  4-tuple of floats: the relative coordinates of the
                      screen region Ex: (0.,0.,1.,1.) == full screen
        tr         -  the coordinate transformer
    """
    
    def __init__(self, gfx, x1, y1, x2, y2, region, keepAspectRatio):
        """Occupies a region on gfx using coordinate range x1,y1 to x2,y2
        """
        self.gfx = gfx
        self.region = region
        scr = self.screenRegion()
        self.tr = CoordinateTransformer(scr[0], scr[1], scr[2], scr[3], 
                                        x1, y1, x2, y2,
                                        keepAspectRatio)
                                        
    def screenRegion(self):
        """Retruns the screen coordinates of the virual screen.
        Determines the screen coordinates of the region covered by
        the virtual screen."""
        return screenRegion(self.gfx, self.region)
        
    def adjustRange(self, x1, y1, x2, y2):
        """Adjusts the coordinate range."""
        self.tr.setRange(x1, y1, x2, y2)

    def adjustRegion(self, region):
        """Adjusts the region of the screen that is used."""
        self.region = region
        self.resizedGfx()
        
    def resizedGfx(self):
        """Adjusts attributes after a resize of the graphics interface.
        """
        scr = self.screenRegion()
        self.tr.setScreen(scr[0], scr[1], scr[2], scr[3])
                                                
    def changeGfx(self, gfx):
        """Use a new graphics interface from now on. Returns the old
        graphics interface."""
        oldGfx = self.gfx
        self.gfx = gfx
        self.resizedGfx()
        return oldGfx

##~     def redraw(self):
##~         """Redraw the contents of the virtual screen.
##~         The redraw method must always be called explicitly"""
##~         pass    # this is a dummy!


########################################################################
#
#   class HardFramedScreen
#
######################################################################## 

   
class HardFramedScreen(VirtualScreen):
    """A virtual screen with a hard frame, i.e. a frame of which the 
    size is defined by screen coordinates (instead of region size or
    virtual coordinates).
    
    Attributes:
        top, bottom, left, right    - frame width on the respective side
        sx1, sy1, sx2, sy2          - the screen coordinates of the full
            screen (including the frame).
        overlap                     - 4-tuple of integers, resembling
            z-values of the top, bottom, left and right frame parts.
    """
    
    def __init__(self, gfx, x1, y1, x2, y2, region,  
                 top, bottom, left, right, keepAspect, 
                 overlap = (1, 1, 0, 0)):
        """Initializes a VirtualScreen with a frame defined by 'top',
        'bottom', 'left', 'right'
        """
        self.top = top; self.bottom = bottom
        self.left = left; self.right = right
        self.overlap = overlap
        VirtualScreen.__init__(self, gfx, x1, y1, x2, y2, region, 
                               keepAspect)
                               
    def _setOverlap(self, overlap):
        """Changes the overlapping order of the side frames."""
        self.overlap = overlap
        
    def screenRegion(self):
        scr = VirtualScreen.screenRegion(self)
        self.sx1, self.sy1, self.sx2, self.sy2 = scr
        return (scr[0] + self.left,  scr[1] + self.bottom,
                scr[2] - self.right,  scr[3] - self.top)
                
    def adjustFrame(self, top, bottom, left, right):
        """Changes the frame size."""
        self.top = top; self.bottom = bottom
        self.left = left; self.right = right
        self.resizedGfx()
        
    def innerFrame(self):
        """-> (sx1, sy1, sx2, sy2) screen coordinates of the inner
        frame."""    
        return (self.sx1 + self.left, self.sy1 + self.bottom,
                self.sx2 - self.right, self.sy2 - self.top)

    def topFrame(self):
        """-> (sx1, sy1, sx2, sy2) screen coordinates of the top frame.
        """
        if self.overlap[3] > self.overlap[0]:  sx2 = self.sx2 - self.right
        else:  sx2 = self.sx2
        if self.overlap[2] > self.overlap[0]:  
            sx1 = self.sx1 + self.left - 1
        else:  sx1 = self.sx1
        return (sx1, self.sy2-self.top+1, sx2, self.sy2)        
    
    def bottomFrame(self):
        """-> (sx1, sy1, sx2, sy2) screen coordinates of the bottom
        frame."""
        if self.overlap[3] > self.overlap[1]:  sx2 = self.sx2-self.right
        else:  sx2 = self.sx2
        if self.overlap[2] > self.overlap[1]:  
            sx1 = self.sx1 + self.left - 1
        else:  sx1 = self.sx1
        return (sx1, self.sy1, sx2, self.sy1+self.bottom-1)    

    def leftFrame(self):
        """-> (sx1, sy1, sx2, sy2) screen coordinates of the left frame.
        """
        if self.overlap[0] > self.overlap[2]:  sy2 = self.sy2 - self.top
        else:  sy2 = self.sy2
        if self.overlap[1] > self.overlap[2]:  
            sy1 = self.sy1 + self.bottom - 1
        else:  sy1 = self.sy1
        return (self.sx1, sy1, self.sx1+self.left-1, sy2)
        
    def rightFrame(self):
        """-> (sx1, sy1, sx2, sy2) screen coordinates of the right frame.
        """
        if self.overlap[0] > self.overlap[3]:  sy2 = self.sy2 - self.top
        else:  sy2 = self.sy2
        if self.overlap[1] > self.overlap[3]:  
            sy1 = self.sy1 + self.bottom - 1
        else:  sy1 = self.sy1
        return (self.sx2-self.right+1, sy1, self.sx2, sy2)
        
    
########################################################################
#
#   class Cartesian
#
########################################################################        
    
# Style Flags
    
AXISES, AXIS_DIVISION, FULL_GRID, LABELS, CAPTION, \
TITLE, SHUFFLE_DRAW, EVADE_DRAW, LOG_X, LOG_Y, \
KEEP_ASPECT, AUTO_ADJUST = map(lambda i:2**i, range(12))

DEFAULT_STYLE = TITLE|CAPTION|LABELS|FULL_GRID|AXISES|AUTO_ADJUST

MASK_LAYOUT = LABELS|CAPTION|TITLE
MASK_GRAPHSTYLE = AXISES|AXIS_DIVISION|FULL_GRID|SHUFFLE_DRAW|EVADE_DRAW
MASK_RANGE_TYPE = KEEP_ASPECT|AUTO_ADJUST

MAGIC_TITLESIZE_FACTOR = 3
MAGIC_LABELSIZE_FACTOR = 3
MAGIC_CAPTIONLINE_FACTOR = 1.2
MAGIC_CAPTIONENTRY_EXTEND = 2
MAGIC_CPATIONENTRY_DIV = 6
MAGIC_CAPTIONENTRY_HSPACE = 2
MAGIC_CAPTIONSIZE_ADD = 1 # lines

LOG_BASE = 10

class AutoPen(Gfx.Pen):
    def __init__(self):
        Gfx.Pen.__init__(self)
        self.lineWidth = Gfx.MEDIUM

class DontDrawPen(Gfx.Pen):
    def __init__(self):
        Gfx.Pen.__init__(self)
        self.color = (1.0, 1.0, 1.0)

AUTO_GENERATE_PEN = AutoPen()
DONT_DRAW_PEN = DontDrawPen()
CAPTION_PEN = Gfx.Pen(color = Gfx.BLACK, fsize = Gfx.SMALL)

def bitsum(i):
    """-> cross sum of the bits of integer i"""
    s = 0;  k = 2**int(math.log(i, 2))
    while k > 0:
        s += k & i
        k /= 2
    return s


class Cartesian(HardFramedScreen):
    """Plots function values onto a coordinate plane.
    
    Attributs (read only!):
        x1,y1,x2,y2 - floats: coordinate Range
        xaxis, yaxis- strings: axis descriptions
        
        styleFlags  - integer, interpreted as a bitfield of flags;
            defines style of the graph. Possible flags:
                AXIS, AXIS_DIVISION, FULL_GRID: Draw axises,
                    axis divisions and (or) a full grid,
                LABEL, CAPTION, TITLE: draw axis labels, a
                    a caption with descriptions (generated from the pen
                    names) below the graph, a title above the graph.
                SHUFFLE_DRAW, EVADE_DRAW: two different algorithms to 
                    allow for the visibility of overlapping graphs
                LOG_X, LOG_Y: use a logarithmic scale for the x or y
                    axis respectively.
                KEEP_ASPECT: Keep the aspect ratio of the coordinates
                AUTO_ADJUST: automatically adjust the range of the graph
                    when a point is added that falls outside the current
                    range.

        stretchX, stretchY - stretch factor for lagrithmic scales
                    
        axisPen, labelPen, titlePen, captionPen, backgroundPen - pens 
            (sets of graphical attributes) for the respective elements 
            of the graph
            
        pens        - dictionary (indexed by name strings) of pens (see
            mod. Pens) for graphs to be drawn onto the coordinate plane
        
        values      - dictionary (indexed by name strings) of lists of
            value pairs (x,y) that define the graph associated with the
            respective pen (identified by its name)
        penOrder    - list of pen names in drawing order
        colorIndex  - color index that points to the color to be fetched
            next from Colors.color, when generating the color for an
            AutoPen.
    """

    def __init__(self, gfx, x1, y1, x2, y2, 
                 title = "Graph",  xaxis="X", yaxis="Y", 
                 styleFlags = DEFAULT_STYLE, 
                 axisPen = Gfx.BLACK_PEN, labelPen = Gfx.BLACK_PEN,
                 titlePen = Gfx.BLACK_PEN, captionPen = Gfx.BLACK_PEN,
                 backgroundPen = Gfx.WHITE_PEN, 
                 region = REGION_FULLSCREEN):
        """Initializes the graph using the graphics driver 'gfx'. 
        For the other parameters see doc string of class Cartesian.
        """
        self.x1, self.x2 = x1, x2
        self.y1, self.y2 = y1, y2         
        self.titleStr = title
        self.xaxis, self.yaxis = xaxis, yaxis
        self.styleFlags = styleFlags
        self.axisPen, self.labelPen = axisPen, labelPen
        self.titlePen, self.captionPen = titlePen, captionPen
        self.backgroundPen = backgroundPen
        self.pens = {};  self.values = {};  self.penOrder = []
        self.colorIndex = 2  # set to 2, if you want to skipt that yellow pen!
        self.dpi = gfx.getResolution()
        self.top, self.bottom, self.left, self.right = 0,0,0,0
        self.gfx = gfx;  self.region = region;
        self._assertRangeParameters()
        self._calcStretchFactors()        
        top, bottom, left, right = self._xcalcFrame()
        HardFramedScreen.__init__(self, gfx, self.x1, self.y1,
                                  self.x2, self.y2, region, 
                                  top, bottom, left, right,
                                  styleFlags & KEEP_ASPECT)
        self.redraw()

    def _maxCaptionEntrySize(self):
        """-> (w, h, th) Size of the biggest Caption Entry."""
        sl = [self.gfx.getTextSize(name) for name in self.pens.keys()]
        if sl == []:  sl.append(self.gfx.getTextSize("ABDFGabdfg"))
        wl = [s[0] for s in sl];  hl = [s[1] for s in sl]
        th = max(hl);  w = max(wl)
        w += int(MAGIC_CAPTIONENTRY_EXTEND * th + 0.5)
        w += MAGIC_CAPTIONENTRY_HSPACE * th
        h = int(th * MAGIC_CAPTIONLINE_FACTOR + 0.5)
        self._captionESTuple = (w,h,th)
        return self._captionESTuple
        
    def _captionLinesNColumns(self):
        """-> (l,c) number of caption lines and columns."""
        w, h, th = self._captionESTuple
        scr = screenRegion(self.gfx, self.region)
        sw = scr[2]-scr[0]+1
        c = max(1, min(len(self.pens), sw / w))
        l = max(1, (len(self.pens) + c - 1) / c)
        self._captionLCTuple = (l,c)
        return self._captionLCTuple

    def _xcalcFrame(self):
        """Returns the screen coordinates (top, bottom, left, right) of
        the frame.
        """
        if self.styleFlags & TITLE:
            self.gfx.applyPen(self.titlePen, Gfx.FONT)
            th = self.gfx.getTextSize("0g")[1]
            top = int(th * MAGIC_TITLESIZE_FACTOR + 0.5)
        else: top = 0
        if self.styleFlags & LABELS:
            self.gfx.applyPen(self.labelPen, Gfx.FONT)
            th = self.gfx.getTextSize("Og")[1]
            self.labelSize = int(th * MAGIC_LABELSIZE_FACTOR + 0.5)
        else:  self.labelSize = 0
        left = self.labelSize
        right = 0
        if self.styleFlags & CAPTION:
            self.gfx.applyPen(self.captionPen, Gfx.FONT)
            w, h, th = self._maxCaptionEntrySize()
            l, c = self._captionLinesNColumns()
            bottom = l * h + th * MAGIC_CAPTIONSIZE_ADD + self.labelSize
            sx1, sy1, sx2, sy2 = screenRegion(self.gfx, self.region)
            if (bottom+top) > (sy2-sy1)/2:
                bottom -= (bottom+top) - (sy2-sy1)/2
                if bottom < 0: bottom = 0
        else: bottom = self.labelSize
        return top, bottom, left, right
        
    def _calcFrame(self):
        """Determines the frame size. Returns True if frame size has
        changed.
        """
        top, bottom, left, right = self._xcalcFrame()
        if top != self.top or bottom != self.bottom or \
           left != self.left or right != self.right:
            self.adjustFrame(top, bottom, left, right)
            return True
        else: return False  

    def _calcStretchFactors(self):
        """Determines the stretch factors for logarithmic scales."""
        self.stretchX = math.log10(self.x2 - self.x1 + 1.0)
        self.stretchY = math.log10(self.y2 - self.y1 + 1.0)

    def _scaleX(self, x):
        """Maps the x coordinate onto the screen coordinate range."""
        if LOG_X & self.styleFlags:
            return self.tr.X(math.log10(x) * \
                       (self.x2 - self.x1) / self.stretchX + self.x1)
        else:  return self.tr.X(x)

    def _scaleY(self, y):
        """Maps the x coordinate onto the screen coordinate range."""
        if LOG_Y & self.styleFlags:
            return self.tr.Y(math.log10(y) * \
                       (self.y2 - self.y1) / self.stretchY + self.y1)
        else:  return self.tr.Y(y)

    def _invX(self, x):
        if LOG_X & self.styleFlags:
            r = self.tr.invX(x) - self.x1
            r = r * self.stretchX / (self.x2 - self.x1)
            return  LOG_BASE ** r
        else:  return self.tr.invX(x)

    def _invY(self, y):
        if LOG_Y & self.styleFlags:
            r = self.tr.invY(y) - self.y1
            r = r * self.stretchY / (self.y2 - self.y1)
            return LOG_BASE ** r         
        else:  return self.tr.invY(y)

    def _axisDivision(self, a, b):
        """Divides a coordinate axis between a and b in a suitable
        manner."""
        if b-a <= 1.0: corr = -1.0
        else: corr = 0.0
        steps = 10.0**int(math.log10((b-a)/2.0)+corr)
        m = round(a/steps)*steps
        if m <= a: m += steps
        epsilon = abs(b-a)/1000.0
        l = []
        while m < b-epsilon:
            l.append(m)
            m += steps
        return l

    def _logAxisDivision(self, a, b):
        """Divides a coordinate axis between a and b logarithmically.
        """
        steps = int(math.log10(b-a+1)+ 0.01/b)
        l = []
        for i in xrange(int(a + 0.9999), steps+1):
            l.append(LOG_BASE ** i)
        return l

    def _XaxisDivision(self):
        """Divides the x axis either linearly or logarithmically
        according to the style flags."""
        if LOG_X & self.styleFlags:
            return self._logAxisDivision(self.x1, self.x2)
        else:  return self._axisDivision(self.x1, self.x2)

    def _YaxisDivision(self):
        """Divides the x axis either linearly or logarithmically
        according to the style flags."""
        if LOG_Y & self.styleFlags:
            return self._logAxisDivision(self.y1, self.y2)
        else:  return self._axisDivision(self.y1, self.y2)
            
    def _clear(self, sx1, sy1, sx2, sy2):
        self.gfx.applyPen(self.backgroundPen, Gfx.MASK_FILL)
        self.gfx.fillRect(sx1, sy1, sx2-sx1+1, sy2-sy1+1)

    def _clearTitle(self):
        x1, y1, x2, y2 = self.topFrame()
        y1 += 2 # a little bit of tweaking
        self._clear(x1, y1, x2, y2)        
            
    def _clearGraph(self):
        sx1 = self.tr.X(self.x1);  sy1 = self.tr.Y(self.y1)
        sx2 = self.tr.X(self.x2);  sy2 = self.tr.Y(self.y2) 
        self._clear(sx1, sy1, sx2, sy2+1) # "+1"  is a tweak !  
    
    def _clearFullGraph(self):
        sx1, sy1, sx2, sy2 = self.innerFrame()
        sx1 -= self.labelSize
        sy1 -= self.labelSize
        self._clear(sx1, sy1, sx2, sy2+1) # "+1"  is a tweak !
        
    def _clearLabels(self):
        sx1 = self.tr.X(self.x1)-1;  sy1 = self.tr.Y(self.y1)-1
        sx2 = self.tr.X(self.x2)+1;  sy2 = self.tr.Y(self.y2)+1        
        self.gfx.applyPen(self.backgroundPen, Gfx.MASK_FILL)
        self.gfx.fillRect(sx1-self.labelSize, sy1+1, self.labelSize,
                          sy2-sy1)
        self.gfx.fillRect(sx1+1, sy1-self.labelSize, sx2-sx1, 
                          self.labelSize)
        
    def _clearCaption(self):
        sx1, sy1, sx2, sy2 = self.bottomFrame()
        sy2 -= self.labelSize
        self._clear(sx1, sy1, sx2, sy2)
            
    def _drawGrid(self):
        """Draws the axises of the coordinate system.
        """       
        if self.styleFlags & AXISES:
            sx1 = self.tr.X(self.x1);  sy1 = self.tr.Y(self.y1)
            sx2 = self.tr.X(self.x2);  sy2 = self.tr.Y(self.y2)        
            if self.y1 <= 0.0:  y = self._scaleY(0.0)
            else:  y = self._scaleY(self.y1)
            self.gfx.applyPen(self.axisPen, Gfx.MASK_LINE)
            self.gfx.drawLine(self.tr.X(self.x1), y, self.tr.X(self.x2), y)
            if self.styleFlags & AXIS_DIVISION:
                self.gfx.setLineWidth(Gfx.THIN)
                sy1 = y - self.dpi / 40 - 1
                sy2 = sy1 + self.dpi / 20 + 1
                for x in self._XaxisDivision():
                    sx = self._scaleX(x)
                    self.gfx.drawLine(sx, sy1, sx, sy2)
                self.gfx.setLineWidth(self.axisPen.lineWidth)
                    
            if self.x1 <= 0.0:  x = self._scaleX(0.0)
            else:  x = self._scaleX(self.x1)
            self.gfx.applyPen(self.axisPen, Gfx.MASK_LINE)
            self.gfx.drawLine(x, self.tr.Y(self.y1), x, self.tr.Y(self.y2))
            if self.styleFlags & AXIS_DIVISION:
                self.gfx.setLineWidth(Gfx.THIN)
                sx1 = x - self.dpi / 40 - 1
                sx2 = sx1 + self.dpi / 20 + 1
                for y in self._YaxisDivision():
                    sy = self._scaleY(y)
                    self.gfx.drawLine(sx1, sy, sx2, sy)

        if self.styleFlags & FULL_GRID:
            sx1 = self.tr.X(self.x1);  sy1 = self.tr.Y(self.y1)
            sx2 = self.tr.X(self.x2);  sy2 = self.tr.Y(self.y2)
            self.gfx.setColor(self.axisPen.color)        
            self.gfx.setLineWidth(Gfx.THIN)
            self.gfx.setLinePattern(Gfx.DOTTED)
            for x in self._XaxisDivision():
                sx = self._scaleX(x)
                self.gfx.drawLine(sx, sy1, sx, sy2)
            for y in self._YaxisDivision():
                sy = self._scaleY(y)
                self.gfx.drawLine(sx1, sy, sx2, sy)
            self.gfx.setLineWidth(self.axisPen.lineWidth)
            self.gfx.setLinePattern(Gfx.CONTINUOUS)
            self.gfx.drawRect(sx1, sy1, sx2-sx1+1, sy2-sy1+1)

    def _drawLabels(self):
        """Writes the labels onto the graph.
        """
        def fmtNum(f, df):
            """float -> string (nicely rounded and formatted)."""
            if f <> 0.0: i = int(round(math.log10(abs(df))))-1
            else: i = 0
            if i >= 0: i = 0
            else: i = abs(i)
            return  ("%."+str(i)+"f") % (round(f, i))

        self.gfx.applyPen(self.labelPen, Gfx.MASK_FONT)
        sx1 = self.tr.X(self.x1)-1;  sy1 = self.tr.Y(self.y1)-1
        sx2 = self.tr.X(self.x2)+1;  sy2 = self.tr.Y(self.y2)+1
        
        w, h = self.gfx.getTextSize(self.xaxis)
        x = sx1 + (sx2 - sx1 + 1)/2 - w/2
        y = sy1 - self.labelSize + h/4
        self.gfx.writeStr(x, y, self.xaxis)
        w, h = self.gfx.getTextSize("0")
        y = sy1 - h * 5/4;  lastX = -1000000
        for x in self._XaxisDivision():
            fstr = fmtNum(x, self.x2-self.x1)
            w,h = self.gfx.getTextSize(fstr)
            sx = self._scaleX(x) - w/2
            if sx+w > self.tr.sx2:  sx = self.tr.sx2 - w
            if sx > lastX + h/2:
                self.gfx.writeStr(sx, y, fstr)
                lastX = sx + w
        
        w, h = self.gfx.getTextSize(self.yaxis)
        x = sx1 - h*6/4
        if len(self.yaxis) >= 2:
            y = sy2 - (sy2 - sy1 + 1)/2 - w/2
            self.gfx.writeStr(x, y, self.yaxis, 90.0)
        else:
            y = sy2 - (sy2 - sy1 + 1)/2 - h/2
            self.gfx.writeStr(x-w, y, self.yaxis)
        w, h = self.gfx.getTextSize("0")
        x = sx1 - h/4;  lastY = -1000000
        for y in self._YaxisDivision():
            fstr = fmtNum(y, self.y2-self.y1)
            w,h = self.gfx.getTextSize(fstr)
            sy = self._scaleY(y) - w/2
            if sy+w > self.tr.sy2:  sy = self.tr.sy2 - w
            if sy > lastY + h/2:
                self.gfx.writeStr(x, sy, fstr, 90.0)
                lastY = sy + w
               
    def _shuffleDraw(self):
        """Draws the recorded data on the cartesian plane. The order in
        which the graphs are drawn is continuously changed, so that 
        overlapped graphs may still become visible. This results in
        Zebra speckled graphs for overlapping curves.
        """
        lengthDict = {}
        for name, l in self.values.items():
            lengthDict[name] = len(l)
        n = max(lengthDict.values()+[0])
        nameList = self.pens.keys()
        for name in nameList:
            if lengthDict[name] == 1:
                pen = self.pens[name]
                if isinstance(pen, DontDrawPen): continue                
                self.gfx.applyPen(pen, Gfx.MASK_LINE)
                x, y = self.values[name][0]
                if self._inside(x, y):
                    self.gfx.drawPoint(self._scaleX(x), self._scaleY(y))
        for i in range(1, n):
            for name in nameList:
                if lengthDict[name] > i:
                    pen = self.pens[name]
                    if isinstance(pen, DontDrawPen): continue
                    self.gfx.applyPen(pen, Gfx.MASK_LINE)
                    x1, y1 = self.values[name][i-1]
                    x2, y2 = self.values[name][i]
                    if self._inside(x1, y1) and self._inside(x2, y2):
                        self.gfx._drawLine(self._scaleX(x1),
                                           self._scaleY(y1),
                                           self._scaleX(x2),
                                           self._scaleY(y2))
            random.shuffle(nameList)
            
    def _evadeDraw(self):
        """Draws the recorded data onto the cartesian plane. If
        different graphs are overlapping they will be draw next to
        each other instead of on top of each other, so that overlapped
        graphs may still become visible. This may lead to somewhat
        inexact graphs as well as strange artifacts (zigzagged graphs) 
        in some cases.
        """
        pSet = set()
        names = self.pens.keys();  names.sort()
        for name in names:
            pen = self.pens[name]
            if isinstance(pen, DontDrawPen): continue            
            if pen.lineWidth == Gfx.THICK:  delta = 3
            elif pen.lineWidth == Gfx.MEDIUM: delta = 2
            else: delta = 1
            self.gfx.applyPen(pen, Gfx.MASK_LINE)
            poly = []
            for x,y in self.values[name]:
                if self._inside(x,y):
                    point = (self._scaleX(x), self._scaleY(y))
                    while point in pSet:
                        point = (point[0], point[1]+delta)
                    pSet.add(point)
                    poly.append(point)
                else:
                    self.gfx._drawPoly(poly)
                    poly = []
            self.gfx._drawPoly(poly)            
                
    def _drawData(self):
        """Draws the recorded data onto the cartesian plane.
        """
        if self.styleFlags & SHUFFLE_DRAW: self._shuffleDraw()
        elif self.styleFlags & EVADE_DRAW: self._evadeDraw()         
        else:            
            for name in self.penOrder:
                pen = self.pens[name]
                if isinstance(pen, DontDrawPen): continue
                self.gfx.applyPen(pen, Gfx.MASK_LINE)
                poly = []
                for x,y in self.values[name]:
                    if self._inside(x,y):
                        poly.append((self._scaleX(x), self._scaleY(y)))
                    else:
                        self.gfx._drawPoly(poly)
                        poly = []
                self.gfx._drawPoly(poly)

    def _drawTitle(self):
        """Writes the title of the graph.
        """
        sx1, sy1, sx2, sy2 = self.topFrame()
        self.gfx.applyPen(self.titlePen, Gfx.MASK_FONT)        
        w, h = self.gfx.getTextSize(self.titleStr)
        x = sx1 + (sx2-sx1+1-w) / 2;  y = sy1 + (sy2-sy1+1-h) / 2
        self.gfx.writeStr(x, y, self.titleStr)
        
    def _drawCaption(self):
        """Writes a description of all pens below the graph.
        """
        if self.pens == {}: return
        sx1, sy1, sx2, sy2 = self.bottomFrame()
        lines, columns = self._captionLCTuple
        w, h, th = self._captionESTuple
        y = sy2 - self.labelSize - th * MAGIC_CAPTIONSIZE_ADD / 2 + th/3
        dw = MAGIC_CAPTIONENTRY_EXTEND * th / MAGIC_CPATIONENTRY_DIV
        lw = MAGIC_CAPTIONENTRY_EXTEND * th - 2*dw
        penNames = self.pens.keys();  penNames.sort();  i = 0
        for name in penNames:
            if i == 0:
                #x = sx1+((sx2-sx1+1) - w * columns) / 2
                x = sx2 - w * columns
                y -= h;  i = columns                
            self.gfx.applyPen(self.pens[name], Gfx.MASK_LINE)
            self.gfx.drawLine(x+dw, y+th/2, x+lw, y+th/2)
            self.gfx.applyPen(self.captionPen, Gfx.MASK_FONT)
            self.gfx.writeStr(x+lw+2*dw, y, name)
            x += w;  i -= 1
            
    def _redrawFullGraph(self):
        self._clearFullGraph()
        self._drawGrid()
        self._drawLabels()
        self._drawData()     
            
    def _inside(self, x,y):
        """Returns True if point (x,y) is inside the graph."""
        return (x >= self.x1) and (x <= self.x2) and \
               (y >= self.y1) and (y <= self.y2)     
            
    def _adjustRangeToPoint(self, x, y):
        """Adjusts the graph range so that point x, y will fall inside
        the range.
        """
        x1, y1, x2, y2 = self.x1, self.y1, self.x2, self.y2
        if x < x1: x1 = x - abs(x2-x)*0.15
        elif x > x2: x2 = x + abs(x-x1)*0.15
        if y < y1: y1 = y - abs(y2-y)*0.15
        elif y > y2: y2 = y + abs(y-y1)*0.15
        self.adjustRange(x1, y1, x2, y2)        

    def _assertRangeParameters(self):
        assert self.x2 > self.x1, "x2 must be greater than x1!"
        assert self.y2 > self.y1, "y2 must be greater than y1!"
        assert not LOG_X & self.styleFlags or self.x1 >= 1, \
            "x1 must be greater or equal 1 when using a logarithmic scale!"
        assert not LOG_Y & self.styleFlags or self.y1 >= 1, \
            "y1 must be greater or equal 1 when using a logarithmic scale!"
            
    def adjustRange(self, x1, y1, x2, y2):
        """Adjusts the range of the coordinate plane."""
        self._assertRangeParameters()
        self.x1, self.x2 = x1, x2
        self.y1, self.y2 = y1, y2
        self._calcStretchFactors()
        HardFramedScreen.adjustRange(self, x1, y1, x2, y2)
        self._redrawFullGraph()

    def setStyle(self, styleFlags=None, axisPen=None, labelPen=None,
                 titlePen=None, captionPen=None, backgroundPen = None,
                 redraw = True):
        """Changes the style of the graph. A parameter value of None
        means that this parameter shall not be changed.
        """
        RD_TITLE, RD_LABELS, RD_CAPTION, RD_GRAPH = map(lambda i:2**i, range(4))
        RD_NONE = 0
        RD_ALL = RD_TITLE|RD_LABELS|RD_CAPTION|RD_GRAPH
        redrawFlags = RD_NONE
        updateGeometry = False
        oldStyleFlags = self.styleFlags
        
        if styleFlags != None:
            if (MASK_LAYOUT & styleFlags) != (MASK_LAYOUT & self.styleFlags):
                self._assertRangeParameters()
                updateGeometry = True
                redrawFlags |= RD_ALL
            elif (MASK_GRAPHSTYLE & styleFlags) != \
                 (MASK_GRAPHSTYLE & self.styleFlags):
                redrawFlags |= RD_GRAPH
            elif ((LOG_X|LOG_Y) & styleFlags) != \
                 ((LOG_X|LOG_Y) & self.styleFlags):
                redrawFlags |= RD_LABELS|RD_GRAPH
            self.styleFlags = styleFlags
        else: styleFlags = 0
            
        if axisPen != None:
            self.axisPen = axisPen
            redrawFlags |= RD_GRAPH 
        if labelPen != None:
            self.labelPen = labelPen
            redrawFlags |= RD_LABELS
        if titlePen != None:
            self.titlePen = titlePen
            redrawFlags |= RD_TITLE
        if backgroundPen != None:
            self.backgroundPen = backgroundPen
            redrawFlags |= RD_ALL
        if captionPen != None:
            if self.captionPen.fontSize != captionPen.fontSize:  
                redrawFlags |= RD_ALL
                updateGeometry = True
            else:  redrawFlags |= RD_CAPTION
            self.captionPen = captionPen
        
        if oldStyleFlags & AUTO_ADJUST and \
        not self.styleFlags & AUTO_ADJUST:
            x1, y1, x2, y2 = self.x1, self.y1, self.x2, self.y2
            for name in self.pens.keys():
                for x,y in self.values[name]:
                    if x < x1:  x1 = x
                    elif x > x2:  x2 = x
                    if y < y1:  y1 = y
                    elif y > y2:  y2 = y
            self.adjustRange(x1, y1, x2, y2) # implies redraw
            redrawFlags &= ~RD_GRAPH
        elif oldStyleFlags & KEEP_ASPECT and \
        not self.styleFlags & KEEP_ASPECT:
            redrawFlags |= RD_GRAPH        

        if updateGeometry: self._calcFrame()
        if redraw:
            if redrawFlags == RD_ALL:  self.redraw()
            else:
                if redrawFlags & RD_TITLE:
                    self._clearTitle()
                    self._drawTitle()
                if redrawFlags & RD_CAPTION:
                    self._clearCaption()
                    self._drawCaption()
                if (redrawFlags & RD_LABELS) and (redrawFlags & RD_GRAPH):
                    self._redrawFullGraph()
                else:
                    if redrawFlags & RD_LABELS:
                        self._clearLabels()
                        self._drawLabels()
                    elif redrawFlags & RD_GRAPH:
                        self._clearGraph()
                        self._drawGrid()
                        self._drawData()
                

    def setTitle(self, title):
        """Changes the title of the graph."""
        self.titleStr = title
        self._clearTitle()
        self._drawTitle()
            
    def setLabels(self, xaxis=None, yaxis=None):
        """Changes the labeling of the graph."""        
        if xaxis != None:  self.xaxis = xaxis
        if yaxis != None:  self.yaxis = yaxis         
        if self.styleFlags & LABELS:
            self._clearLabels()
            self._drawLabels()

    def resizedGfx(self):
        HardFramedScreen.resizedGfx(self)
        self._calcFrame()
        self.redraw()
        
    def changeGfx(self, gfx):
        self.dpi = gfx.getResolution()
        return HardFramedScreen.changeGfx(self, gfx)
                            
    def redrawGraph(self):
        """Redraws only the graph."""
        self._clearGraph()
        self._drawGrid()
        self._drawData()
        
    def redrawCaption(self):
        """Redraws the caption region."""
        if self.styleFlags & CAPTION:
            if self._calcFrame():  self._redrawFullGraph()
            self._clearCaption()
            self._drawCaption()

    def redraw(self):
        """Redraws everything: the graph as well as the title and 
        the caption."""
        self._clear(self.sx1, self.sy1, self.sx2, self.sy2)
        self._drawGrid()
        if self.styleFlags & LABELS:  self._drawLabels()
        self._drawData()
        if self.styleFlags & CAPTION:  self._drawCaption()
        if self.styleFlags & TITLE:  self._drawTitle()

    def reset(self, x1, y1, x2, y2):
        """Removes all pens and readjusts the range of the coordinate plane.
        """
        self.pens = {};  self.values = {}; self.penOrder = []
        self.adjustRange(x1, y1, x2, y2)                  

    def addPen(self, name, pen=AUTO_GENERATE_PEN, updateCaption=True):
        """Adds a new pen."""
        if isinstance(pen, AutoPen):
            pen = copy.deepcopy(pen)
            pen.color = Colors.colors[self.colorIndex]
            self.colorIndex += 1
            if self.colorIndex >= len(Colors.colors):
                self.colorIndex = 0
        self.penOrder.append(name)
        self.pens[name] = pen
        self.values[name] = []
        if updateCaption: self.redrawCaption()

    def exchangePen(self, name, pen, redraw = True):
        """Changes the color and attributes of a pen."""
        assert self.pens.has_key[name], "Cannot exchange pen '"+\
               name+"' because it did not exist."
        self.pens[name] = pen
        if redraw:
            self.redrawCaption()
            if self.values[name]:  self.redrawGraph()
        
    def removePen(self, name, redraw = True):
        """Removes a pen."""
        del self.pens[name]
        self.penOrder.remove(name)
        flag = self.values[name] != []
        del self.values[name]
        if flag and redraw:  self.redrawGraph()

    def addValue(self, name, x, y):
        """Adds another value to the value table of the pen named 'name'.
        """
        if not self._inside(x, y):
            if self.styleFlags & AUTO_ADJUST:
                self._adjustRangeToPoint(x, y)
            else: return        
        self.values[name].append((x,y))        
        vl = self.values[name]
        if not self._inside(x, y):
            if self.styleFlags & AUTO_ADJUST:
                self._adjustRangeToPoint(x, y)
            else: return
        pen = self.pens[name]
        if isinstance(pen, DontDrawPen): return
        self.gfx.applyPen(pen, Gfx.MASK_LINE)            
        if len(vl) > 1:
            x1, y1 = vl[-2]
            if not self._inside(x1, y1): return
            self.gfx._drawLine(self._scaleX(x1), self._scaleY(y1),
                               self._scaleX(x), self._scaleY(y))
        else:
            self.gfx.drawPoint(self._scaleX(x), self._scaleY(y))

    def peek(self, x, y):
        """screen coordinates -> coordinates on the graph."""
        return (self._invX(x), self._invY(y))

    def xaxisSteps(self, x1, x2):
        """-> List of virtual x-coordinates with one point for
        each screen pixel."""
        a = self._scaleX(x1);  b = self._scaleX(x2)
        return map(self._invX, range(a, b+2)) # it's b+2 not b+1,
                                              # range errors!
    def yaxisSteps(self, y1, y2):
        """-> List of virtual x-coordinates with one point for
        each screen pixel."""        
        a = self._scaleY(y1);  b = self._scaleY(y2)
        return map(self._invY, range(a, b+2))

## uncomment the following to break jython compatibility ;)
    
##    def xaxisIter(self, x1, x2):
##        """-> iterate over virtual x-coordinates with one point for
##        each screen pixel."""
##        a = self._scaleX(x1);  b = self._scaleX(x2)
##        for x in xrange(a, b+2): yield self._invX(x)
##
##    def yaxisIter(self, y1, y2):
##        """-> iterate over virtual x-coordinates with one point for
##        each screen pixel."""        
##        a = self._scaleY(y1);  b = self._scaleY(y2)
##        for y in xrange(a, b+2): yield self._invY(y)


## saving the graph (not yet tested)!

##    def reprGraph(self, withPens = False, lineFeeds = False):
##        """Returns a string representation of the graph, including
##        pen names, pens (optional) and value lists."""
##        if lineFeeds:
##            lf = "\n"; spc = " "
##        else:
##            lf  = ""; spc = ""
##        sl = ["[", lf]
##        for name in self.penOrder:
##            sl.extend(spc, "[", repr(name), ",", spc)
##            if withPens:
##                sl.extend(repr(self.pens[name]), ",", spc, lf)
##            sl.extend(spc, spc, repr(self.values[name]), lf, spc, "]", lf)
##        sl.extend("]", lf)
##        return "".join(sl)

##    def saveGraph(self, fName):
##        """Saves the vectors of the graph to a file named 'fName'.
##        Returns true, if successful."""
##        try:
##            f = file(fName, "w")
##        except IOError:
##            return False
##        try:
##            f.write(self.reprGraph())
##        except IOError:
##            ret = False
##        else:
##            ret = True
##        f.close()
##        return ret
        

########################################################################
#
#   class OptimizingFilter
#
########################################################################

OPT_DONT, OPT_X, OPT_Y = map(lambda i:2**i, range(3))

class OptimizingFilter(object):
    """Optimizes the the output on a graph on screen for speed  
    (at a possible cost of accuracy) by leaving out all those
    points that have the same screen X- (or Y-) coordinate as the the 
    last added point.
    
    The optimization is most usefull if the domain of the graph is
    much larger than the screen resolution. Since only one the first
    Y (resp. X) value is drawn for each X (resp Y) value the optimized
    graph might actually look different than the full graph, although
    this should not matter in most cases. Since points that are filtered
    out are simply dropped and thus do not occur in the value list of
    the graph object, it is not possible to regain accuracy by zooming
    or resizing the window. Instead it will be necessary to recalculate
    the graph. (This is the cost for the speed and memory benefits 
    gained by using the optimizing filter.)
 
    Attributes:
        graph   - Graph object: the graph that is used for drawing
        flags   - int (bitset): the flags that determine the behaviour
            of the optimizer: OPT_DONT turns of Optimization (this 
            allows switching between optimized and non optimized 
            output without putting another if clause into the drawing
            loop). OPT_X and OPT_Y determine whether the x or the y
            value is to be regared as the independend variable.
    """
    def __init__(self, graph, flags = OPT_X):
        assert bitsum((OPT_X|OPT_Y) & flags) != 1, \
            "Orientation not given or ambiguous !"
        self.graph = graph
        self.flags = flags
        self.graphChanged()
        
    def graphChanged(self):
        """Takes notice of a readjusted or resized graph.
        """
        if OPT_X & self.flags:
            self.steps = self.graph.xaxisSteps(self.graph.x1, 
                                               self.graph.x2)
        else:
            self.steps = self.graph.yaxisSteps(self.graph.y1, 
                                               self.graph.y2)
        self.index = {}

    def addValue(self, name, x, y):
        """Adds a point to the graph only if the screen X (resp. Y)
        coordinate differs from the last point.
        """
        if OPT_X & self.flags:  pos = x
        else:  pos = y
        if not (OPT_DONT & self.flags):
            try:
                if pos >= self.steps[self.index.setdefault(name, 0)]:
                    self.index[name] += 1
                    self.graph.addValue(name, x, y)
            except IndexError:
                pass # index errors mean that pos is out of range anyway
        else: self.graph.addValue(name, x, y)


########################################################################
#
#   Tests
#
########################################################################

if __name__ == "__main__":
    import systemTest
#    systemTest.Test_Graph()
    systemTest.Test_GraphLg()

       

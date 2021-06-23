# Simplex

"""Provides classes to draw different types of two dimensional simplex 
diagrams. A two dimensional simplex diagram is an equal sided triangle,
where each point inside the triangle represents a ratio of three 
variables. This could for example be the population ratio of three
species in biology.
"""

import math, random

import Graph, Gfx
from Compatibility import *


# population ratios should add up to 1.0. This following constant
# defines the maximum allowed error for this sum.

ERROR_TOLERANCE = 1.0 / 10000.0   
                                    
ERROR_CHECKING = False


########################################################################
#
#   class Plotter
#
########################################################################

SIMPLEX_H = math.sqrt(0.75)
MAGIC_TITLESIZE_FACTOR = 3


def drawArrow(gfx, x1, y1, x2, y2):
    if x1 == x2 and y1 == y2:
        gfx.drawPoint(x1, y1)
        #gfx.drawLine(x1-1, y1-1, x1+1, y1+1)
        #gfx.drawLine(x1-1, y1+1, x1+1, y1-1)
    else:    
        gfx.drawLine(x1, y1, x2, y2)
        dx = float(x2-x1);  dy = float(y2-y1)     
        l = math.sqrt(dx*dx + dy*dy)
        if l > 0:
            dx /= l;  dy /= l
            l /= 3.
            px = x2 - dx * l;  py = y2 - dy * l
            ax = int(px - dy * l + 0.5);  ay = int(py + dx * l + 0.5)
            bx = int(px + dy * l + 0.5);  by = int(py - dx * l + 0.5)
            gfx.drawLine(x2, y2, ax, ay)
            gfx.drawLine(x2, y2, bx, by)


class Plotter(Graph.HardFramedScreen):
    """Plotter for simple triangle diagrams.

    Triangle diagrams are commonly used in game theory to visualize
    the evolution of dynamical systems of three types of players. The
    edges of the triangle represent system states where the whole
    population consists only of players of one single type, whereas
    points in the interior of the triangle represent mixed populations
    according to the given player ratios.
    """
    def __init__(self, gfx, title="Simplex Diagram", 
                 p1="P1", p2="P2", p3="P3", styleFlags = 0,
                 titlePen = Gfx.BLACK_PEN, labelPen = Gfx.BLACK_PEN,
                 simplexPen=Gfx.BLACK_PEN, backgroundPen=Gfx.WHITE_PEN,
                 section=Graph.REGION_FULLSCREEN):
        top = self._calcTitleSize(gfx, title, titlePen)
        Graph.HardFramedScreen.__init__(self, gfx,  -0.1, -0.1, 
           1.1, SIMPLEX_H + 0.1, section, top, 0, 0, 0, keepAspect=True)
        self.title = title
        self.p1, self.p2, self.p3 = p1, p2, p3
        self.styleFlags = styleFlags
        self.titlePen = titlePen;  self.labelPen = labelPen
        self.simplexPen = simplexPen; self.backgroundPen = backgroundPen
        self.clear()
        
    def _calcTitleSize(self, gfx, title, titlePen):
        """Calculates the size of the title frame, depending on the
        selected font."""
        if title == "": return 0
        gfx.applyPen(titlePen, Gfx.MASK_FONT)
        th = gfx.getTextSize("0g")[1]
        return int(th * MAGIC_TITLESIZE_FACTOR + 0.5)        
   
    def _clearLabels(self):
        """Clears the labels."""
        x1, y1, x2, y2 = self.innerFrame()
        ya = self.tr.Y(0.0)-1;  yb = self.tr.Y(SIMPLEX_H)+1
        self.gfx.applyPen(self.backgroundPen, Gfx.MASK_FILL)
        self.gfx.fillRect(x1, y1, x2-x1+1, ya-y1+1)  
        self.gfx.fillRect(x1, yb, x2-x1+1, y2-yb+1)

    def _clearTitle(self):
        """Clears the title."""
        if self.title != "":
            self.gfx.applyPen(self.backgroundPen, Gfx.MASK_FILL)
            x1, y1, x2, y2 = self.topFrame()
            self.gfx.fillRect(x1, y1, x2-x1+1, y2-y1+1)
            
    def _clearSimplex(self):
        """Clears the simplex."""
        x1 = self.tr.X(0.0);  y1 = self.tr.Y(0.0)
        x2 = self.tr.X(1.0);  y2 = self.tr.Y(SIMPLEX_H)
        self.gfx.applyPen(self.backgroundPen, Gfx.MASK_FILL)
        self.gfx.fillRect(x1, y1, x2-x1+1, y2-y1+1)
        
    def _clear(self):
        """Clears everything (simplex, title and labels)."""
        self.gfx.applyPen(self.backgroundPen, Gfx.MASK_FILL)
        self.gfx.fillRect(self.sx1, self.sy1, 
                          self.sx2-self.sx1+1, self.sy2-self.sy1+1)        
        
    def _drawLabels(self):
        """Draws the labes at the three corners of the simplex."""
        self.gfx.applyPen(self.labelPen, Gfx.MASK_FONT)
        w,h = self.gfx.getTextSize(self.p1)
        x,y = self.tr.X(0.0)-w/2, self.tr.Y(0.0)-h*12/10
        self.gfx.writeStr(x, y, self.p1)
        w,h = self.gfx.getTextSize(self.p2)
        x,y = self.tr.X(1.0)-w/2, self.tr.Y(0.0)-h*12/10
        self.gfx.writeStr(x, y, self.p2)
        w,h = self.gfx.getTextSize(self.p3)
        x,y = self.tr.X(0.5)-w/2, self.tr.Y(SIMPLEX_H)+h/2
        self.gfx.writeStr(x, y, self.p3)
        
    def _drawTitle(self):
        """Draws the title."""
        if self.title != "":
            sx1, sy1, sx2, sy2 = self.topFrame()
            self.gfx.applyPen(self.titlePen, Gfx.MASK_FONT)        
            w, h = self.gfx.getTextSize(self.title)
            x = sx1 + (sx2-sx1+1-w) / 2;  y = sy1 + (sy2-sy1+1-h) / 2
            self.gfx.writeStr(x, y, self.title)
            
    def _drawEmptySimplex(self):
        """Draws the empty simplex."""
        self.gfx.applyPen(self.simplexPen, Gfx.MASK_LINE)
        self.gfx.drawPoly(self.tr.transform([
                                    self.transform((1.0, 0.0, 0.0)),
                                    self.transform((0.0, 1.0, 0.0)),
                                    self.transform((0.0, 0.0, 1.0)),
                                    self.transform((1.0, 0.0, 0.0))]))

    def clear(self):
        """Clears the whole canvas and redraws titel, labels and an
        empty simplex."""
        self._clear()
        self._drawLabels()
        self._drawTitle()
        self._drawEmptySimplex()   
        
    def clearSimplex(self):
        """Clears only the simplx diagram without affecting the
        title or the labels."""
        self._clearSimplex()
        self._drawEmptySimplex()
        
    def setStyle(self, styleFlags=None, titlePen=None, labelPen=None,
                 simplexPen=None, backgroundPen=None):
        """Sets the drawing style of the simplex diagram"""
        redraw = False
        if styleFlags != None and self.styleFlags != styleFlags:
            self.styleFlags = styleFlags
            redraw = True
        if labelPen != None:  self.labelPen = labelPen
        if simplexPen != None:  self.simplexPen = simplexPen
        if backgroundPen != None:  self.backgroundPen = backgroundPen
        if titlePen != None:  
            self.titlePen = titlePen
            top = self._calcTitleSize(self.gfx, self.title, titlePen)
            if top != self.top:
                self.adjustFrame(top, 0, 0, 0)
                redraw = True
        if redraw:  self.redraw()
        
    def setTitle(self, title):
        """Sets the player title"""
        self.title = title
        top = self._calcTitleSize(self.gfx, self.title, self.titlePen)
        if top != self.top:
            self.adjustFrame(top, 0, 0, 0)
            self.clear()
        else:  
            self._clearTitle()
            self._drawTitle()
        
    def setLabels(self, p1, p2, p3):
        """Sets the player names"""
        self.p1, self.p2, self.p3 = p1, p2, p3
        self._clearLabels();  self._drawLabels()
        
    def resizedGfx(self):
        """Takes notice of a resized graphics context.
        Note: The triangle diagram will be cleared after resizing!
        """
        Graph.HardFramedScreen.resizedGfx(self)
        self.clear()

    def redraw(self):
        """Redraws the (empty) diagram."""
        self.clear()
               
    def transform(self, pr):
        """Population Ratio (3-tuple) -> (x,y)"""
        return (pr[1]+pr[2]*0.5, SIMPLEX_H*pr[2])

    def inverse(self, xy):
        """Virtual Coordinates (x,y) -> Population ratio (3-tuple)"""
        p3 = xy[1] / SIMPLEX_H
        p2 = xy[0] - p3*0.5
        p1 = 1.0 - p2
        return (p1, p2, p3)

    def peek(self, x, y):
        """Screen coordinates -> Population ratio (3-tuple)
        In case (x,y) is not a point within the triangle diagram,
        the zero population (0.0, 0.0, 0.0) is being returned. 
        """
        vx, vy = self.tr.invX(x), self.tr.invY(y)
        pr = self.inverse((vx,vy))
        if abs(pr[0]+pr[1]+pr[2]-1.0) < ERROR_TOLERANCE and \
           pr[0] > 0.0 and pr[1] > 0.0 and pr[2] > 0.0:
            return pr
        else: return (0.0, 0.0, 0.0)        
        
    #
    #    following: the drawing operations
    #
        
    def applyPen(self, pen):
        """Sets the pen for the following drawing operations."""
        self.gfx.applyPen(pen, Gfx.MASK_LINE)
        
    def setColor(self, rgbTuple):
        """Sets the color fo the following drawing operations.
        A call to apply pen will override this setting."""
        self.gfx.setColor(rgbTuple)
                
    def plot(self, pr):
        """Draws a point at position pr (population ration as 3-tuple).
        """
        x, y = self.transform(pr)
        self.gfx.drawPoint(self.tr.X(x), self.tr.Y(y))     
        
    def line(self, pr1, pr2):
        """Draws a line from pr1 to pr2."""
        x1, y1 = self.transform(pr1)
        x2, y2 = self.transform(pr2)
        self.gfx.drawLine(self.tr.X(x1), self.tr.Y(y1),
                          self.tr.X(x2), self.tr.Y(y2))

    def turtleDraw(self, pr1, pr2, length, autoScale=True, arrow=True):
        """Draws a line from pr1 in the direction of pr2."""
        if autoScale:
           sf = math.sqrt((pr2[0]-pr1[0])**2 + (pr2[1]-pr1[1])**2 + \
                          (pr2[2]-pr1[2])**2)
           length = (length*sf*0.05)**0.45
        x1, y1 = self.transform(pr1)
        x2, y2 = self.transform(pr2)
        dx = x2-x1;  dy = y2-y1
        l = math.sqrt(dx*dx + dy*dy)
        if l > 0.000000000001: # l != 0, but with regard of precision errors
            x2 = x1+dx*length/l
            y2 = y1+dy*length/l
        else: x2, y2 = x1, y1
        if arrow:
            drawArrow(self.gfx, self.tr.X(x1), self.tr.Y(y1),
                      self.tr.X(x2), self.tr.Y(y2))
        else:
            self.gfx.drawLine(self.tr.X(x1), self.tr.Y(y1),
                              self.tr.X(x2), self.tr.Y(y2))

    def spot(self, pr, size):
        """Draws a spot (rectangle) of size 'size' around pr."""
        x, y = self.transform(pr)
        s = size*1.2    # since gfx-area ranges from -0.1 to 1.1
        x1 = x - s / 2.0;  y1 = y - (s*SIMPLEX_H)/2.0
        w1 = x + s/2.0;  w2 = x - s/2.0
        h1 = y + (s*SIMPLEX_H)/2.0;  h2 = y - (s*SIMPLEX_H)/2.0
        self.gfx.fillRect(self.tr.X(x1)+1, self.tr.Y(y1),
                          self.tr.X(w1) - self.tr.X(w2),
                          self.tr.Y(h1) - self.tr.Y(h2))



class PermutedPlotter(Plotter):
    """Plotter for simple triangle diagrams.

    In contrast to class Plotter, the class PermutedPlotter
    allows to permutate the edges of the diagram in an arbitrary way
    before plotting.
    """
    def __init__(self, gfx, title="Simplex Diagram", 
                 p1="P1", p2="P2", p3="P3", styleFlags = 0,
                 titlePen = Gfx.BLACK_PEN, labelPen = Gfx.BLACK_PEN,
                 simplexPen=Gfx.BLACK_PEN, backgroundPen=Gfx.WHITE_PEN,
                 section=Graph.REGION_FULLSCREEN, permutation=(0,1,2)):
        Plotter.__init__(self, gfx, title, p1, p2, p3, styleFlags,
                         titlePen, labelPen, simplexPen, backgrounPen,
                         section)
        self.pm = (0,1,2);  self.inv = (0,1,2)
        self.map = self.zero_permutation
        self.setPermutation(permutation)

    def setPermutation(self, permutation):
        """Use 'permutation' for the following drawing commands."""
        l = list(permutation).sort()
        if l != [0,1,2]:
            raise ValueError, "%s is not a valid permutation!" \
                              % str(permutation)
        self.pm = permutation
        for i in xrange(3):
            self.inv[self.pm[i]] = i
        if self.pm == (0,1,2):
            self.map = self.zero_permutation
        else:  self.map = self.permutate
    
    def permutate(self, pr):
        """-> permutation of point pr"""
        return (pr[self.pm[0]], pr[self.pm[1]], pr[self.pm[2]])

    def zero_permutation(self, pr):
        """-> pr"""
        return pr

    def transform(self, pr):
        return Plotter.transform(self, self.map(pr))

    def inverse(self, xy):
        pr = Plotter.inverse(self, xy)
        return (pr[self.inv[0]], pr[self.inv[1]], pr[self.inv[2]])           



########################################################################
#
#   misc. functions 
#
########################################################################


RASTER_PureStrategies = [(1.0,0.0,0.0),(0.0,1.0,0.0),(0.0,0.0,1.0)]
RASTER_StrategyPairs = [(0.5,0.5,0.0),(0.5,0.0,0.5),(0.0,0.5,0.5)]
RASTER_Center = [(1/3.0, 1/3.0, 1/3.0)]
RASTER_WeightedPairs = [(0.5*5/6, 0.5*5/6, 1.0/6),
                        (0.5*5/6, 1.0/6, 0.5*5/6),
                        (1.0/6, 0.5*5/6, 0.5*5/6)]
RASTER_1 = RASTER_PureStrategies + RASTER_StrategyPairs + \
           RASTER_Center + RASTER_WeightedPairs

def GenRaster(density):
    """density (= points in one row) -> point list."""
    assert density >= 2, "density is %i, but must be >= 2" % density
    pl = []
    for y in range(density):
        n = density-y
        p3 = float(y) / (density-1)
        f = 1.0 - p3
        for x in range(n):
            if n > 1:            
                p1 = float(x) / (n-1) * f
                p2 = float(n-1-x) / (n-1) * f
            else: p1 = 0.0; p2 = 0.0
            pl.append((p1, p2, p3))
    return pl


def RandomGrid(N):
    """Generate a random raster with N points."""
    pl = []
    while N > 0:
        a = random.random()
        b = 1.0 - random.random()
        if b < a: c = a;  a = b;  b = c
        pl.append((a, b-a, 1.0-b))
        N -= 1
    return pl


RASTER_DEFAULT = GenRaster(30)
RASTER_RANDOM = RandomGrid(500)

##~ 
##~ def DarkenColor(color, strength=0.1):
##~     """Darken Color: rgbTuple -> rgbTuple"""
##~     return tuple([x-x*strength for x in color])
##~ 
##~ def InvertedDarkenColor(color, strength=0.1):
##~     """Brighten Color: rgbTuple -> rgbTuple"""
##~     st = strength**0.2
##~     return tuple([x-x*(1.0-st) for x in color])
##~ 
##~ def KeepColor(color, strengh=0.0):
##~     """Retrun the same color: rgbTuple -> tgbTuple"""
##~     return color

def scaleColor(ca, cb, strength):
    "Interpolates between the colors ca and cb using atan(strength)"
    factor = math.atan(strength) / (math.pi/2)
    r = ca[0] + (cb[0]-ca[0]) * factor
    g = ca[1] + (cb[1]-ca[1]) * factor
    b = ca[2] + (cb[2]-ca[2]) * factor
    return (r,g,b)


########################################################################
#
#   class NullVisualizer
#
########################################################################

class NullVisualizer(object):
    """This is a dummy visualizer. It has a similar interface like
    the other visualizer classes, but it does not draw anything except
    the empty simplex.
    """
    def __init__(self, plotter, function=None, raster=None,
                 baseColor=None, endColor=None, colorFunc=None):
        self.plotter = plotter
    def setFunction(self, function):
        pass
    def setRaster(self, raster):
        pass
    def setDensity(self, density):
        pass
    def changeColors(self, baseColor=None, endColor=None,
                     colorFunc=None):
        pass
    def show(self):
        pass
    def resizedGfx(self):
        self.plotter.resizedGfx() 
    def redraw(self):
        self.plotter.clear()
    

########################################################################
#
#   class VectorField
#
########################################################################


class VectorField(NullVisualizer):
    """Draws a vectorfield based on an arbitrary set of sample points.   
    """

    def __init__(self, plotter, function, raster=RASTER_DEFAULT,
                 baseColor=(0.0, 0.0, 0.0), endColor=(1.0, 0.7, 0.3),
                 colorFunc=scaleColor, scaleArrows = False):
        """Init with a triangle plotter, a list of points each of which
        represents a certain population distribution among the three
        players and a population dynamical function.
        """
        self.plotter = plotter
        self.function = function
        self.points = raster
        self.arrowLen = self._arrowLength()
        self.transformed = [self.function(p) for p in self.points]
        self.color = baseColor
        self.colorB = endColor
        self.colorFunc = colorFunc
        self.scale = scaleArrows
        self.attributesChangedFlag = False

    def _arrowLength(self):
        """-> length of arrows, depending on the density of the raster."""
        return 1.0 / (2.0*(math.sqrt(len(self.points)+0.25)-0.5))

    def setFunction(self, function):
        """Changes the function to display."""
        self.function = function
        self.attributesChangedFlag = True

    def setRaster(self, raster):
        """Changes the sample points raster."""
        self.points = raster
        self.arrowLen = self._arrowLength()
        self.attributesChangedFlag = True

    def setDensity(self, density):
        """Sets the granularity of the diagram."""
        self.setRaster(GenRaster(density))
        self.attributesChangedFlag = True

    def changeColors(self, baseColor=(0.0, 0.0, 0.0),
                     endColor=(1.0, 0.7, 0.3), colorFunc=scaleColor):
        """Change the colors of the diagram."""
        self.color = baseColor
        self.colorB = endColor
        self.colorFunc = colorFunc
        self.attributesChangedFlag = True

    def _plot(self, pl):
        """Draw a list of points onto the simplex diagram."""
        self.plotter.setColor(self.color)
        for pr in pl:
            self.plotter.plot(pr)

    def show(self):
        """Draw VectorField."""
        def distance(a,b):
            """Difference between two population ratios"""
            return math.sqrt(((b[0]-a[0])**2 + (b[1]-a[1])**2 + \
                             (b[2]-a[2])**2) / 3.0)
        if self.attributesChangedFlag:
            self.plotter.clearSimplex()
            self.transformed = [self.function(p) for p in self.points]
            self.attributesChangedFlag = False
        for a,b in map(None, self.points, self.transformed):
            d = distance(a, b)
            c = self.colorFunc(self.color, self.colorB, d)
            self.plotter.setColor(c)
            self.plotter.turtleDraw(a, b, self.arrowLen, self.scale)

    def resizedGfx(self):
        """Takes notice of a resized graphics context and redraws the
        diagram."""
        self.plotter.resizedGfx()
        self.attributesChangedFlag = False
        self.show()        

    def redraw(self):
        """Redraws the diagram"""
        self.plotter.clear()
        self.attributesChangedFlag = False
        self.show()



########################################################################
#
#   class Trajectory
#
########################################################################


class TrajectoryDiagram(VectorField):
    """Draw the trajectories of an arbitrary set of starting points
    into a triangle diagram.   
    """
    def __init__(self, plotter, function, raster=RASTER_DEFAULT,
                 baseColor=(1.0, 0.6, 0.6), endColor=(0.0, 0.0, 0.0), 
                 colorFunc=scaleColor, redrawable=True):
        VectorField.__init__(self, plotter, function, raster, 
                             baseColor, endColor, colorFunc)
        self.shade = 0.0
        self.redrawable = redrawable
        self.originalRaster = self.points
        self.history = [self.points]
        self.MAGIC_SHOW = 8

    def setRedrawable(self, redrawable):
        """Turns the auto redraw property on or off."""
        self.redrawable = redrawable

    def setFunction(self, function):
        self.points = self.originalRaster
        self.history = [self.points]
        VectorField.setFunction(self, function)

    def setRaster(self, raster):
        self.points = raster
        self.originalRaster = self.points
        self.history = [self.points]
        self.attributesChangedFlag = True
    
    def _draw(self, pl, npl):
        """Connect old points to new (transformed) points."""
        c = self.colorFunc(self.color, self.colorB, self.shade)
        self.plotter.setColor(c)
        for i in range(len(pl)):
            self.plotter.line(pl[i], npl[i])
        self.shade += 0.15

    def step(self, n=1):
        """Calulate and draw the next n steps."""
        if self.attributesChangedFlag:
            self.attributesChangedFlag = False
            self.plotter.clearSimplex()
            self.shade = 0.0
        while n > 0:
            newPoints = [self.function(p) for p in self.points]
            self._draw(self.points, newPoints)
            self.points = newPoints
            if self.redrawable:  self.history.append(self.points)
            n -= 1

    def show(self):
        """Shows the trajectories."""
        self.shade = 0.0
        if len(self.history) > 1:
            self.plotter.clearSimplex()
            self.attributesChangedFlag = False
            for i in range(1, len(self.history)):
                self._draw(self.history[i-1], self.history[i])
        else:  self.step(self.MAGIC_SHOW)
            

########################################################################
#
#   class Patches
#
########################################################################


def VerifyPointList(pl, tolerance):
    """For every point check the condition abs((p1+p2+p3)-1)<=tolerance
    """
    for pr in pl:
        assert abs(pr[0]+pr[1]+pr[2]-1.0) <= tolerance, \
               "Point (%f, %f, %f) is not a valid " % pr + \
               "population ratio!" 


class PatchDiagram(object):
    """A kind of simplex diagram that allows for easy visualization
    of attraction areas and points of attraction."""

    def __init__(self, plotter, function, density = 51,
                 color1 = (1.0, 0.0, 0.0), color2 = (0.0, 1.0, 0.0),
                 color3 = (0.0, 0.0, 1.0), check = ERROR_CHECKING):
        """Init Diagram with a triangle plotter, the population
        dynamical function, the density (e.g. resolution) and the
        colors for every corner of the triangle.
        """
        self.plotter = plotter
        self.checkingFlag = check
        self.offsets = []
        self.colorTable = {}
        self.c1 = color1
        self.c2 = color2
        self.c3 = color3
        self.function = function
        self.density = 2
        self.MAGIC_SHOW = 30
        self.setDensity(density)

    def _assignColor(self, pr):
        """Return the color assoziated with the point pr."""
        r = self.c1[0]*pr[0] + self.c2[0]*pr[1] + self.c3[0]*pr[2]
        g = self.c1[1]*pr[0] + self.c2[1]*pr[1] + self.c3[1]*pr[2]
        b = self.c1[2]*pr[0] + self.c2[2]*pr[1] + self.c3[2]*pr[2]
        return (r, g, b)   

    def _genColorTable(self):
        colorTable = {}
        for p in self.points:
            colorTable[p] = self._assignColor(p)
        return colorTable

    def _checkColorTable(self):
        if self.colorTable == {}:
            self.colorTable = self._genColorTable()

    def setFunction(self, function):
        self.function = function
        self.colorTable = {}
            
    def setDensity(self, density):
        """Sets the granularity of the patches diagram."""
        assert density >= 2, "density is %i, but must be >= 2"%density
        self.density = density
        self.spotWidth = ((self.density+1)/float(self.density)) / \
                         float(self.density)
        self.spotWidth *= 1.05  # rounding error correction
        self.points = GenRaster(self.density)
        self.offsets = []               # create fast lookup table
        y = self.density; offset = 0
        while y > 0:
            self.offsets.append(offset)
            offset += y
            y -= 1        
        self.colorTable = {}

    def setEdgeColors(self, color1, color2, color3):
        """Sets the edge colors."""
        self.c1 = color1
        self.c2 = color2
        self.c3 = color3
        self.colorTable = {}

    def _draw(self):
        """Draws the Patches Diagram."""
        if self.colorTable != {}:  CT = self.colorTable
        else:
            CT = self._genColorTable()
            self.plotter.clear()
        for p in self.points:
            self.plotter.setColor(CT[p])
            self.plotter.spot(p, self.spotWidth)
            
    def _getNearest(self, pr):
        """Return the nearest point to p on the grid.
        """
        def dist(a, b):
            return (a[0]-b[0])**2+(a[1]-b[1])**2+(a[2]-b[2])**2

        if self.checkingFlag: VerifyPointList([pr], 0.01/self.density)
        ec = 0.1 / self.density
        y = int((self.density-1) * pr[2] + 0.5)
        if pr[2] < 1.0:
            x = int((self.density-y-1) * pr[0] / (1.0-pr[2]) + ec)
        else: x = 0
            
        try:
            p1 = self.points[self.offsets[y]+x]
            p2 = self.points[self.offsets[y]+x+1]
            p3 = self.points[self.offsets[y+1]+x]
        except IndexError:
            p2 = p1;  p3 = p1
            
        
        d1 = dist(pr, p1);  d2 = dist(pr, p2);  d3 = dist(pr, p3)
        if d1 <= d2 and d1 <= d3:  return p1
        elif d2 <= d3: return p2
        else: return p3

    def step(self, n=1):
        """Caluculate the next n steps and update diagram."""       
        self._checkColorTable()
        while n > 0:
            newCT = {}
            for p in self.points:
                q = self._getNearest(self.function(p))
                if self.checkingFlag:
                    VerifyPointList([q], ERROR_TOLERANCE)
                newCT[p] = self.colorTable[q]
            self.colorTable = newCT
            n -= 1
        self._draw()

    def show(self):
        """Show the patched diagram either in its current state or after
        10 steps."""             
        if self.colorTable != {}:  self._draw()
        else:  self.step(self.MAGIC_SHOW)

    def showFixedPoints(self, color):
        """Search for possible fixed points. Only useful after
        calling method 'step'.
        """
        self.plotter.setColor(color)
        for p in self.points:
            if self.colorTable[p] == self._assignColor(p):
                self.plotter.spot(p, self.spotWidth)

    def resizedGfx(self):
        self.plotter.resizedGfx()
        self._draw()    

    def redraw(self):
        self.plotter.clear()
        self._draw()


        
########################################################################
#
#   Diagram
#
########################################################################

VECTORS, SCALED_VECTORS, TRAJECTORIES, PATCHES, NULL = \
                                            map(lambda i:2**i, range(5))

class Diagram(Plotter):
    """Universal class for visualizing the population dynamics of
    a three-species population on a 2-dimensional simplex diagram.

    Attributes (read only):
        title, p1, p2, p2 - strings: Strings for the title and the
            three corners of the diagram.
        styleFlags - integer, interpreted as a bitfield of flags:
            The style or rather flavour of the simplex diagram.
            Presently four flavours are possible: VECTORS for drawing
            the diagram as a vector field with many little arrows;
            TRAJECTORIES for drawing pseudo trajectories; PATCHES
            for drawing a patched diagram, where each point in the
            diagram has a unique color in the beginning. From generation
            to generation, however, colors are adjusted such that
            every point ("patch") takes the color of the point it
            has moved to. This exposes areas of attraction in the
            diagram. NULL is a dummy that draws nothing!
        visualizer - class: the visualizing class: VectorField,
            Trajectory or Patches.
        function - f(p)->p', where p and p' are 3 tuples of floats
            that add up to 1.0: population dynamics function.
        raster - the point raster of the simplex diagram.
        density - list of 3-tuples of floats each of which adds up
            to 1.0: the density (of the point raster) or the simplex
            diagram.
        color1, color2, color3 - (r,g,b) tuples, where r,g and b are
            floats in range of [0.0, 1.0]: For patch diagrams these
            are the edge colors of the three edges of the diagram. For
            trajectory diagrams color1 is the starting color and color2
            is the color towards which later steps of the trajectory are
            shaded. For vector fields the range between color1 and
            color2 is used to indicate the strength of the vector field.
        colorFunc - f(ca, cb, strength) -> c, where ca and cb are colors
            and strength is a float from [0, infinity]: This function
            produces a color shade from 'ca', 'cb' and 'strength',
            usually somewhere on the line between 'ca' and 'cb'.
        titlePen, labelPen, simplexPen, backgroundPen - Gfx.Pen: Pens
            for the respective parts of the simplex diagram.
        section - 4-tuple of floats from then range [0.0, 1.0]: the
            part of the screen to be used for the diagram.
    """
    def __init__(self, gfx, function, title="Simplex Diagram",
                 p1="A", p2="B", p3="C", styleFlags = VECTORS,
                 raster = RASTER_DEFAULT, density = -1,
                 color1 = (0.,0.,1.), color2 = (0.,1.,0.),
                 color3 = (1.,0.,0.), colorFunc = scaleColor,
                 titlePen = Gfx.BLACK_PEN, labelPen = Gfx.BLACK_PEN,
                 simplexPen=Gfx.BLACK_PEN, backgroundPen=Gfx.WHITE_PEN,
                 section=Graph.REGION_FULLSCREEN):
        Plotter.__init__(self, gfx, title, p1, p2, p3, styleFlags,
                titlePen, labelPen, simplexPen, backgroundPen, section)
        self.function = function
        self.raster = raster
        self.density = density
        if self.density < 2:  self._adjustDensity()        
        else:  self.raster = GenRaster(self.density)
        self.color1, self.color2, self.color3 = color1, color2, color3
        self.colorFunc = colorFunc
        self._selectVisualizer()

    def _selectVisualizer(self):       
        if self.styleFlags & VECTORS or self.styleFlags & SCALED_VECTORS:
            scale = self.styleFlags & SCALED_VECTORS
            self.visualizer = VectorField(self, self.function,
                self.raster, self.color1, self.color2, self.colorFunc, scale)
        elif self.styleFlags & TRAJECTORIES:
            self.visualizer = TrajectoryDiagram(self, self.function,
                self.raster, self.color1, self.color2, self.colorFunc)
        elif self.styleFlags & PATCHES:
            self.visualizer = PatchDiagram(self, self.function,
                self.density, self.color1, self.color2, self.color3)
        elif self.styleFlags & NULL:
            self.visualizer = NullVisualizer(self)
        else:  assert 0, "No flavor specified for simplex diagram!"

    def _adjustDensity(self):
        """Sets the granularity of the patches diagram accroding to the
        size (i.e. granularity) of the raster."""
        l = len(self.raster)
        assert l >= 3, "raster contains %i sample points, "%l+\
                       "but at least 3 sample points are requires!"
        self.density = int(math.sqrt(2*l + 0.25) - 0.5)
        
    def setStyle(self, styleFlags=None, titlePen=None, labelPen=None,
                 simplexPen=None, backgroundPen=None):
        """Sets the drawing style of the simplex diagram."""
        if styleFlags != None and styleFlags != self.styleFlags:
            self.styleFlags = styleFlags
            self.clear()
            self._selectVisualizer()
        Plotter.setStyle(self, styleFlags, titlePen, labelPen,
                         simplexPen, backgroundPen)
        
    def setFunction(self, function):
        "Changes the population dynamical function."
        self.function = function
        self.visualizer.setFunction(function)
        
    def setRaster(self, raster):
        "Changes the raster of sample points (population distributions)."
        self.raster = raster
        self._adjustDensity()
        if not PATCHES & self.styleFlags:
            self.visualizer.setRaster(raster)
        else:  self.visualizer.setDensity(self.density)
        
    def setDensity(self, density):
        """Generates a raster of uniformly distributed sample points
        (population distributions) with the given density."""
        self.density = density
        self.raster = GenRaster(self.density)
        if PATCHES & self.styleFlags:
            self.visualizer.setDensity(self.density)
        else:  self.visualizer.setRaster(self.raster)
        
    def changeColors(self, color1 = (0.,1.,0.), color2 = (1.,0.,0.),
                     color3 = (0.,0.,1.), colorFunc=scaleColor):
        """Changes the colors of diagram, including a color modifying
        function. Note: The semantics of these paramters may differ
        depending on the visualizer."""
        self.color1, self.color2, self.color3 = color1, color2, color3
        self.colorFunc = colorFunc
        if PATCHES & self.styleFlags:
            self.visualizer.setEdgeColors(color1, color2, color3)
        else:
            self.visualizer.changeColors(color1, color2, colorFunc)

    def show(self, steps = -1):
        """Shows the diagram calculating 'steps' generations for
        dyniamic diagrams (trajectories or patches)."""
        if (VECTORS|SCALED_VECTORS|NULL) & self.styleFlags:
            self.visualizer.show()
        else:
            if steps == -1:  n = self.visualizer.MAGIC_SHOW
            else:  n = steps
            self.visualizer.step(n)

    def showFixedPoints(self, color):
        """Shows candidates for fixed points (only if style = PATCHES).
        """
        assert PATCHES & self.styleFlags, "Can only show potential"+\
            " fixed points when the simplex diagram style is PATCHES!"
        self.visualizer.showFixedPoints(color)
        
    def redraw(self):
        "Draws the diagram."
        Plotter.redraw(self)
        self.visualizer.show()
        
    def resizedGfx(self):
        """Takes notice of a resized graphics context and redraws the
        diagram."""
        Plotter.resizedGfx(self)
        self.visualizer.show()


########################################################################
#
#   Tests
#
########################################################################
  
if __name__ == "__main__":
    import systemTest
    systemTest.TestSimplexDiagram()
    
    

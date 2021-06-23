#!/usr/bin/python
# systemTest

"""Runs a system test for all modules of Plotter.

Tests Gfx, wxGfx, tkGfx, gtkGfx, Graph and TDiagram by displaying
graphical images with these modules. Due to the interactive
nature of display functions a unit test of these modules is not
really feasible.
"""

########################################################################
#
#  Test Suite
#
########################################################################

import random, math, copy
import Gfx, Graph, Simplex
from Compatibility import *


GR = None

def TestDriver(gfx):
    """Test Gfx.Interface. 'gfx' must be an object derived
    from a class that implements GfxDriver.GfxInterface."""

    w,h = gfx.getSize()
    if w < 400 or h < 300:
        raise "Graphics area too small: %d, %d !" % (w,h)

    gfx.clear()

    poly = [(10,20),(200, 10), (250, 100), (100, 180), (30, 40), (10,20)]
    gfx.setColor((0.7, 0.7, 0.5))  
     
    gfx.setFillPattern(Gfx.PATTERNED)
    gfx.fillPoly(poly)
    gfx.setColor((1.0, 0.3, 0.3))
    gfx.setLinePattern(Gfx.DASHED)
    gfx.setLineWidth(Gfx.THIN)
    gfx.drawPoly(poly)

    gfx.setLinePattern(Gfx.DOTTED)
    gfx.setLineWidth(Gfx.THIN)
    gfx.drawRect(200, 200, 100, 100)
    
    gfx.setLineWidth(Gfx.THICK)
    gfx.setLinePattern(Gfx.DASHED)
    gfx.drawRect(300, 300, 120, 120)
    gfx.setLineWidth(Gfx.THIN)
    
    gfx.setLinePattern(Gfx.CONTINUOUS)
    gfx.setLineWidth(Gfx.MEDIUM)
    gfx.setFillPattern(Gfx.SOLID)
    gfx.setColor((0.3, 0.3, 0.3))
    gfx.fillRect(100,150,200,100)
    gfx.setColor((0.8, 0.0, 0.0))
    gfx.drawRect(150,150,210,110)
    gfx.setColor((0.1, 1.0, 0.1))
    gfx.setFont(Gfx.SANS, Gfx.NORMAL, "")
    gfx.writeStr(160,160, "Grafik")
    gfx.setFont(Gfx.SERIF, Gfx.LARGE, "bi")
    gfx.setColor((0.1, 1.0, 0.5))
    gfx.writeStr(170, 180, "Test")

    gfx.setFont(Gfx.SANS, Gfx.NORMAL, "")
    gfx.writeStr(100, 200, "wxGraph")
    gfx.writeStr(0, 0, "0")
    gfx.writeStr(90, 190, "Rotated", 90.0)
    gfx.setColor((0.5, 0.5, 0.5))
    gfx.drawLine(10, 10, 200, 100)
    for x in range(0, 361, 15):
        gfx.writeStr(500, 300, "Rotate %i"%x, float(x))
    gfx.setColor(Gfx.BLACK)
    gfx.writeStr(500, 100, "Rotation", 0.0)
    gfx.setColor(Gfx.RED)
    gfx.writeStr(500, 100, "Rotation", 90.0)
    gfx.setColor(Gfx.GREEN)
    gfx.writeStr(500, 100, "Rotation", 45.0)

    gfx.setLineWidth(Gfx.THIN)
    gfx.setColor(Gfx.BLUE)
    gfx.drawRect(350, 50, 100, 50)
    gfx.setColor(Gfx.RED)
    gfx.fillRect(350, 50, 100, 50)
##    gfx.setColor(Gfx.GREEN)
##    gfx.drawRect(350, 50, 100, 50)

def Test():
    gfx = GR.Window()
    TestDriver(gfx)
    gfx.drawPoly([])
    gfx.drawPoly([(5,5)])
    gfx.fillPoly([])
    gfx.fillPoly([(2,2)])
    gfx.setColor((1.,0.,0.))
    gfx.setLineWidth(Gfx.THIN)
    gfx.drawRect(0,0,640,480)
    gfx.setColor((0.,0.,1.))
    gfx.drawLine(0,0,639,0)
    gfx.drawLine(0,479,639,479)
    gfx.setColor((0.,1.,0.))
    gfx.drawLine(0,0,0,479)
    gfx.drawLine(639,0,639,479)
    gfx.setColor((1.,0.,0.))
    gfx.drawPoint(320, 240)
    gfx.waitUntilClosed()    

def paintCallback(dc):
    gfx = Driver(dc)
    gfx.drawLine(-10, -10, 100, 100)

def wxGfx_TestPostscript():
    gfx = Window()
    gfx.DumpPostscript(gfx.win, "test.ps", paintCallback)
    gfx.waitUntilClosed()


def Test_wxGfx():
    global GR
    import wxGfx as GR
    Test()
    
def Test_tkGfx():
    global GR
    import tkGfx as GR
    Test()
    
def Test_gtkGfx():
    global GR
    import gtkGfx as GR
    Test()

def Test_awtGfx():
    global GR
    import awtGfx as GR
    Test()

def Test_nilDevice():
    gfx = Gfx.nilDriver(800, 600)
    TestDriver(gfx)

def Test_psGfx():
    import psGfx
    gfx = psGfx.Driver()
    TestDriver(gfx)
    gfx.save("Test_Postscript.eps")
    
    
##~ def TestCoordinateTransformer(gfx):
##~     """Test CoordinateTransformer by plotting a function."""
##~ 
##~     w,h = gfx.getSize()
##~     if w < 200 or h < 200:
##~         raise "Graphics area too small: %d, %d !" % (w,h)
##~ 
##~     gfx.clear((1.0, 1.0, 1.0))
##~     gfx.setLineThickness(gfx.MEDIUM)
##~     tr = CoordinateTransformer(0, 0, w-1, h-1, -0.5, -1.0, 2.0, 2.5)
##~ 
##~     gfx.setColor((0.0, 0.0, 0.0))
##~     gfx.drawLine(tr.X(-0.5), tr.Y(0.0), tr.X(2.0), tr.Y(0.0))   # x-axis
##~     gfx.drawLine(tr.X(0.0), tr.Y(-1.0), tr.X(0.0), tr.Y(2.5))   # y-axis
##~ 
##~     x = -0.5
##~     dx = 0.1
##~     table = []
##~     while x <= 2.0:
##~         y = x**3
##~         table.append((x, y))
##~         x += dx
##~ 
##~     gfx.setColor((1.0, 0.1, 0.1))
##~     gfx.drawPoly(tr.transform(table))
    
def frange(start, stop, step):
    """frange(start, stop, step) -> list of floats"""
    l = []
    if start <= stop and step > 0: 
        x = start
        while x <= stop:
            l.append(x)
            x += step
        return l
    elif start >= stop and step < 0:
        x = start
        while x >= stop:
            l.append(x)
            x += step
        return l
    elif start == stop and step == 0: return [start]
    else:
        raise ValueError,"conflicting values for start, stop and step:"\
              + " %f, %f, %f" % (start, stop, step)          
    
def Test_Graph():
    getGR()
    gfx = GR.Window()
    gr = Graph.Cartesian(gfx, -8.0, -8.0, 8.0, 8.0, 
                   axisPen = Gfx.Pen(color=(0.0, 0.0, 1.0), lineWidth=Gfx.MEDIUM),
                   labelPen = Gfx.Pen(color=(0.6, 0.1, 0.1)),
                   styleFlags=Graph.TITLE|Graph.CAPTION|Graph.LABELS| \
                            Graph.SHUFFLE_DRAW|Graph.FULL_GRID|Graph.AXISES|\
                            Graph.KEEP_ASPECT)
    gr.addPen("X**3", Gfx.RED_PEN)
    gr.addPen("X**2", Gfx.BLUE_PEN)
    gr.addPen("X", Gfx.YELLOW_PEN)
    gr.addPen("X**4", Gfx.TURKEY_PEN)
    # gr.addPen("Z012345678901234567890123456789", Gfx.GREEN_PEN)
    # for i in range(14):  gr.addPen(str(i), Gfx.BLACK_PEN)
    for x in frange(-8.0, 8.0, 0.02):
        gr.addValue("X**3", x, x**3)
        gr.addValue("X**2", x, x**2)
        gr.addValue("X", x, x)
        gr.addValue("X**4", x, x**4)
        # gr.addValue("Z012345678901234567890123456789", x, x*2)        
    gr.setTitle("f(x) = x*x*x")
    gr.setLabels("X-Achse", "Y-Achse")
    #gr.setTypeFlags(Graph.AUTO_ADJUST)
    #gr.redrawGraph()
    gfx.waitUntilClosed()


def Test_Graph2():
    getGR()
    gfx = GR.Window()
    gr = Graph.Cartesian(gfx, -8.0, -8.0, 8.0, 8.0, 
                   axisPen = Gfx.Pen(color=(0.0, 0.0, 1.0), lineWidth=Gfx.MEDIUM),
                   labelPen = Gfx.Pen(color=(0.6, 0.1, 0.1)),
                   styleFlags=Graph.TITLE|Graph.CAPTION|Graph.LABELS| \
                            Graph.SHUFFLE_DRAW|Graph.FULL_GRID|Graph.AXISES|\
                            Graph.KEEP_ASPECT)
    pen = copy.copy(Gfx.RED_PEN)
    pen.linePattern = Gfx.DASHED
    pen.lineWidth = Gfx.MEDIUM
    pen2 = copy.copy(Gfx.BLUE_PEN)
    pen2.linePattern = Gfx.DASHED
    pen2.lineWidth = Gfx.MEDIUM
    pen3 = copy.copy(Gfx.GREEN_PEN)
    pen3.linePattern = Gfx.DOTTED
    pen3.lineWidth = Gfx.MEDIUM
    gr.addPen("sin(x)", pen)
    gr.addPen("cos(x)", pen3)
    gr.addPen("line", pen2)
    for x in frange(-8.0, 8.0, 0.02):
        gr.addValue("sin(x)", x, math.sin(x))
        gr.addValue("cos(x)", x, math.cos(x))
    gr.addValue("line", -8,-8)
    gr.addValue("line", 8, 8)
    gr.setTitle("f(x) = x*x*x")
    gr.setLabels("X-Achse", "Y-Achse")
    gr.redraw()
    gfx.waitUntilClosed()        
    

def Test_GraphLg():
    getGR()
    gfx = GR.Window()
    gr = Graph.Cartesian(gfx, 1.0, -8.0, 1100.0, 8.0, 
                   axisPen = Gfx.Pen(color=(0.0, 0.0, 1.0), lineWidth=Gfx.MEDIUM),
                   labelPen = Gfx.Pen(color=(0.6, 0.1, 0.1)),
                   styleFlags=Graph.TITLE|Graph.CAPTION|Graph.LABELS| \
                            Graph.SHUFFLE_DRAW|Graph.FULL_GRID|Graph.AXISES| \
                            Graph.LOG_X)
    gr.addPen("sin(log(x))")
    gr.addPen("log(x)")
    points = gr.xaxisSteps(1.0, 1100.0)
#    print len(points), points[:10], points[-10:]
    for x in points:
        gr.addValue("sin(log(x))", x, math.sin(math.log(x)))
        gr.addValue("log(x)", x, math.log(x))
    gr.setTitle("log(x), sin(log(x)")
    gr.setLabels("X-Achse", "Y-Achse")
    # gr.setTypeFlags(Graph.AUTO_ADJUST)
    gr.redrawGraph()
    gfx.waitUntilClosed() 

    
########################################################################
#
#   Simplex Diagram Tests
#
########################################################################

def TestNearest():
    """Test method getNearest of class PatchedTriangle"""
    gfx = GR.Window()
    plotter = Simplex.Plotter(gfx)
    diagram = Simplex.Patches(plotter, lambda p: p)
    # Test 1
    for p in diagram.points:
        plotter.setColor((1.0, 0.0, 0.0))
        plotter.plot(p)
        q = diagram.getNearest(p)
        plotter.setColor((0.0, 1.0, 0.0))
        plotter.plot(q)
    gfx.waitUntilClosed()

    gfx = GR.Window()
    plotter = Simplex.Plotter(gfx)
    diagram = Simplex.Patches(plotter, lambda p: p)
    # Test 2
    diagram.plotter.clear()
    d = 500
    for y in range(d):
        w = d-y
        for x in range(w):
            p2 = y/float(d)
            p1 = (1.0-p2)*x/float(w)
            p0 = 1.0-p2-p1
            p = (p0, p1, p2)
            q = diagram.getNearest(p)
            c = diagram.colorTable[q]
            plotter.setColor(c)
            plotter.plot(p)
    plotter.setColor((0.0, 0.0, 0.0))
    for p in diagram.points:
        plotter.plot(p)
    gfx.waitUntilClosed()


DemandGame = { "11":1/3.0, "12":1/3.0, "13":1/3.0, 
               "21":2/3.0, "22":0.0,   "23":0.0,
               "31":1/2.0, "32":0.0,   "33":1/2.0 }


def PopulationDynamics(pr, pay, e=0.0, noise=0.0):
    """population ratio, payofftable, correlation, noise ->
    new population ratio.
    """
    n1, n2, n3 = pr[0], pr[1], pr[2]
    p1=pay["11"]*(n1+e*(n2+n3))+pay["12"]*(n2-e*n2)+pay["13"]*(n3-e*n3)
    p2=pay["22"]*(n2+e*(n1+n3))+pay["21"]*(n1-e*n1)+pay["23"]*(n3-e*n3)
    p3=pay["33"]*(n3+e*(n1+n2))+pay["31"]*(n1-e*n1)+pay["32"]*(n2-e*n2)
    P = p1+p3+p3/3.0
    if P > 0.0:  n1 *= p1/P;  n2 *= p2/P;  n3 *= p3/P
    N = n1+n2+n3
    if N == 0.0:  n1, n2, n3 = pr[0], pr[1], pr[2];  N = 1.0
    m = N*noise
    a = random.random();  b = 1.0-random.random()
    if b < a: c = a;  a = b;  b = c
    n1 = n1 - n1*noise + m*a
    n2 = n2 - n2*noise + m*(b-a)
    n3 = n3 - n3*noise + m*(1.0-b)
    return (n1/N, n2/N, n3/N)


def TestSimplexDiagram():
    getGR()
    gfx = GR.Window(title="Simplex Diagram Test")
    f = lambda p: PopulationDynamics(p,DemandGame, e=0.0, noise=0.0)
    diag = Simplex.Diagram(gfx, f)
    diag.show()
    diag.setStyle(styleFlags = Simplex.PATCHES)
    diag.show(5)
    diag.setStyle(styleFlags = Simplex.TRAJECTORIES)
    diag.changeColors((1.,1.,0.),(0.,0.,0.))
    diag.show()
    gfx.waitUntilClosed()
    
def TestTrajectoryDiagram():
    getGR()
    gfx = GR.Window(title="Demand Game - Trajectory Diagram")
    tp = Simplex.Plotter(gfx)
    diag = Simplex.TrajectoryDiagram(tp,lambda p:
                  PopulationDynamics(p,DemandGame, e=0.0, noise=0.0),
                    raster = Simplex.RASTER_RANDOM, redrawable=False)
##    for i in range(15):
##        diag.step(1)
##        gfx.win.Refresh()
##        gfx.win.Update()
    diag.step(10)
    #diag.redraw()
    gfx.waitUntilClosed()

def TestVectorField():
    getGR()
    gfx = GR.Window(title="Demand Game - Vector Field")
    tp = Simplex.Plotter(gfx)
    diag = Simplex.VectorField(tp,lambda p:
                  PopulationDynamics(p,DemandGame, e=0.0, noise=0.0),
                           raster = Simplex.RASTER_DEFAULT)
##    for i in range(15):
##        diag.step(1)
##        gfx.win.Refresh()
##        gfx.win.Update()
    diag.show()
    gfx.waitUntilClosed()

def TestPatchedTriangle():
    gfx = GR.Window(title="Demand Game - setup for the progrssive graph")
    tp = Simplex.Plotter(gfx)
    diag = Simplex.PatchDiagram(tp,lambda p:
                    PopulationDynamics(p,DemandGame,e=0.0,noise=0.0),
                           density=50)
    gfx.waitUntilClosed()
    
    gfx = GR.Window(title="Demand Game - progressive graph")
    tp = Simplex.Plotter(gfx)
    diag = Simplex.PatchDiagram(tp,lambda p:
                    PopulationDynamics(p,DemandGame,e=0.0,noise=0.0),
                           density=50)
    for i in range(25):
        diag.step(1)
        gfx.refresh()
    diag.showFixedPoints((1.0, 0.5, 0.0))
    gfx.waitUntilClosed()

def TestPatchDensity():
    for density in range(53, 75):
        gfx = GR.Window(title="Test Patch Density")
        tp = Simplex.Plotter(gfx)
        diag = Simplex.Patches(tp,lambda p:
                    PopulationDynamics(p,DemandGame,e=0.0,noise=0.0),
                    density)
        gfx.waitUntilClosed()    
        
def Test_Simplex():        
    getGR()
    TestTrajectoryDiagram()
    TestVectorField()
    #TestNearest()
    TestPatchedTriangle()
    #TestPatchDensity()        

def getGR():
    global GR
    if GR == None:
        try:
            import java, pawt
            import awtGfx as GR
        except:
            import wxGfx as GR
            #import gtkGfx as GR
            #import tkGfx as GR
            print GR.__name__
    
if __name__ == "__main__":
    getGR()
#    Test_gtkGfx()
#    Test_tkGfx()    
#    Test_wxGfx()
    Test_Graph2()
#    Test_Simplex()
#    Test_GraphLg()    

#! /usr/bin/python
# TestGfx.py - Test Module for Gfx.py


import random

import Gfx, wxGfx
from wxPython.wx import *


def rnd():
    return random.random()-0.5


class Landscape:
    def __init__(self):
        self.setup()

    def setup(self):
        self.iter = 1
        self.scale = 0.9
        self.amp = 1.0
        self.net = [[self.amp*rnd(), self.amp*rnd()], [self.amp*rnd()]]
        self.amp /= 2.0

        self.lastColor = (-1.0, -1.0, -1.0)
        

    def nextIteration(self):
        net = []
        for line in range(len(self.net)-1):
            net.extend([[],[]])
            for column in range(len(self.net[line])-1):
                net[-2].append(self.net[line][column])
                net[-2].append((self.net[line][column] +
                                self.net[line][column+1]) / 2.0 +
                               rnd() * self.amp)
                net[-1].append((self.net[line][column] +
                                self.net[line+1][column]) / 2.0 +
                               rnd() * self.amp)
                net[-1].append((self.net[line][column+1] +
                                self.net[line+1][column]) / 2.0 +
                               rnd() * self.amp)
            net[-2].append(self.net[line][-1])
        net.append(self.net[-1])
        self.amp /= 2.0
        self.net = net
        self.iter += 1


    def paintWireframe(self, gfx):
        """Redraw the current stage of the Landscape as wireframe.
        """

        def color(z1, z2):
            if z1 <= 0.0 and z2 <= 0.0:  return (0.0, 0.5, 1.0)
            elif z1 >= 0.4 and z2 >= 0.4:  return (0.6, 0.6, 0.6)
            else:  return (0.1, 1.0, 0.1)

        def drawLine(x1, y1, x2, y2, c):
            if self.lastColor != c:
                gfx.setColor(c)
                self.lastColor = c
            gfx.drawLine(int(x1), int(y1), int(x2), int(y2))
            

        w,h = gfx.getSize()
        dx = w/6.0;     dy = h/6.0        
        w *= 2.0/3.0;   h *= 1.0/2.0
        gfx.clear()

        delta = 1.0 / (len(self.net)-1)
        y = 0.0
        for line in range(len(self.net)-1):
            x = line * delta / 2.0
            for column in range(len(self.net[line])-1):
                z1 = self.net[line][column]
                z2 = self.net[line][column+1]
                z3 = self.net[line+1][column]
                if z1 < 0.0:  z1 = 0.0
                if z2 < 0.0:  z2 = 0.0
                if z3 < 0.0:  z3 = 0.0
                x1,y1 = x, y+z1*self.scale
                x2,y2 = x+delta, y+z2*self.scale
                x3,y3 = x+delta/2.0, y+delta+z3*self.scale
                c1 = color(z1, z2)
                c2 = color(z1, z3)
                c3 = color(z2, z3)
                drawLine(x1*w+dx,y1*h+dy, x2*w+dx,y2*h+dy, c1)
                drawLine(x1*w+dx,y1*h+dy, x3*w+dx,y3*h+dy, c2)
                drawLine(x2*w+dx,y2*h+dy, x3*w+dx,y3*h+dy, c3)
                x += delta
            y += delta


    def paintSolid(self, gfx):
        """Redraw the current landscape.
        """

        def color(edges, z1, z2, z3):
            # much too simple algorithm
            if z1 <= 0.0 and z2 <= 0.0 and z3 <= 0.0:  baseC = (0.0, 0.5, 1.0)
            elif z1 >= 0.4 and z2 >= 0.4 and z3 >= 0.4:  baseC = (0.6, 0.6, 0.6)
            else:  baseC = (0.1, 1.0, 0.1)
            dv = 1.0+10.0*max(abs(z1-z2), abs(z2-z3))
            return (baseC[0]/dv, baseC[1]/dv, baseC[2]/dv)

        w,h = gfx.getSize()
        dx = w/6.0;     dy = h/3.0        
        w *= 2.0/3.0;   h *= 1.0/2.0
        gfx.clear()

        delta = 1.0 / (len(self.net)-1)
        y = 0.0
        for line in range(len(self.net)-1):
            x = line * delta / 2.0
            for column in range(len(self.net[line])-1):
                z1 = self.net[line][column]
                z2 = self.net[line][column+1]
                z3 = self.net[line+1][column]
                if z1 < 0.0:  z1 = 0.0
                if z2 < 0.0:  z2 = 0.0
                if z3 < 0.0:  z3 = 0.0
                x1,y1 = x, y-z1*self.scale
                x2,y2 = x+delta, y-z2*self.scale
                x3,y3 = x+delta/2.0, y+delta-z3*self.scale
                edges = [(x1*w+dx, y1*h+dy), (x2*w+dx, y2*h+dy),
                         (x3*w+dx, y3*h+dy)]
                gfx.setFillColor(color(edges, z1, z2, z3))                
                gfx.fillPoly(edges)
                try:
                    z4 = self.net[line+1][column+1]
                    if z4 < 0.0:  z4 = 0
                    x4, y4 = x+delta*3.0/2.0, y+delta-z4*self.scale
                    edges[0] = (x4*w+dx, y4*h+dy)
                    gfx.setFillColor(color(edges, z4, z2, z3))
                    gfx.fillPoly(edges)
                except IndexError: pass
                x += delta
            y += delta        
    


class TestApp(wxApp):
    def __init__(self):
        wxApp.__init__(self, 0)
        self.iter = 0

    def OnInit(self):
        self.landscape = Landscape()
        self.win = wxFrame(None, -1, "Test - GfxDriver")
        self.sizer = wxBoxSizer(wxVERTICAL)
        self.paintArea = wxWindow(self.win, -1, size=(640, 400))
        self.paintArea.SetSizeHints(100, 100, 1024, 768)
        self.sizer.Add(self.paintArea, 1, wxEXPAND)
        self.button = wxButton(self.win, 100, "Next Step",
                               size=wxSize(100, 30))
        self.sizer.Add(self.button, 0, wxALIGN_CENTER_HORIZONTAL)
        self.win.SetSizer(self.sizer)
        self.sizer.SetSizeHints(self.win)

        self.refresh = True
        EVT_BUTTON(self.button, -1, self.OnButton)
        EVT_PAINT(self.paintArea, self.OnPaint)
        EVT_IDLE(self.win, self.OnIdle)

        self.win.SetSize(wxSize(640, 400))
        self.win.Show(1)
        self.SetTopWindow(self.win)
        self.gfx = wxGfx.Driver(None)
        return 1

    def OnButton(self, event):
        self.iter += 1
        if self.iter > 6:
            self.landscape.setup()
            self.iter = 0
        else:
            self.landscape.nextIteration()
        self.refresh = True

    def OnIdle(self, event):
        if self.refresh:
            self.DC = wxClientDC(self.paintArea)
            self.DC.BeginDrawing()
            self.gfx.changeDC(self.DC)
            self.landscape.paintWireframe(self.gfx)
            # self.landscape.paintSolid(self.gfx)
            self.gfx.changeDC(None)
            self.DC.EndDrawing()
            self.refresh = False

    def OnPaint(self, event):
        self.refresh = True
        event.Skip()

    def run(self):
        self.win.Refresh()
        self.MainLoop()


if __name__ == "__main__":
    app = TestApp()
    app.run()

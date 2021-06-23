#!/usr/bin/python

# wx.Gfx -    Implementation of the Gfx.Driver Interface in a 
#   wx.Windows enviroment

"""Implementes Gfx.Driver using wx.Windows. 

Addionally contains a simple postscript plotting module
based on the wx.Printout class. (Currently this works only under Linux)
"""

import math
import wx
import Gfx


driverName = "wxGfx"

assert wx.VERSION[0] > 2 or (wx.VERSION[0]==2 and wx.VERSION[1]>=4), \
       "wxGfx.py requires wxPython Version 2.4 or higher!"

if wx.VERSION[0] == 2 and wx.VERSION[1] >= 6: _canRotateText = True
elif wx.Platform != "__WXGTK__": _canRotateText = True
else: _canRotateText = False

########################################################################
#
#   Compatibility with wxPython 2.5.1, which was not backward
#   compatible!
#
########################################################################

if wx.VERSION[0] == 2 and wx.VERSION[1] == 5 and wx.VERSION[2] <= 1:
    class DCCompatibilityWrapper(object):
        def __init__(self, dc):
            self.dc = dc
        def Clear(self):
            self.dc.Clear()
        def DrawLines(self, points):
            self.dc.DrawLines(points)
        def DrawPolygon(self, points):
            self.dc.DrawPolygon(points)
        def SetAxisOrientation(self, x, y):
            self.dc.SetAxisOrientation(x, y)
        def SetBackground(self, color):
            self.dc.SetBackground(color)
        def SetPen(self, pen):
            self.dc.SetPen(pen)
        def SetBrush(self, brush):
            self.dc.SetBrush(brush)
        def SetFont(self, font):
            self.dc.SetFont(font)
        def SetTextForeground(self, color):
            self.dc.SetTextForeground(color)
        def SetTextBackground(self, color):
            self.dc.SetTextBackground(color)
        def GetSizeTuple(self):
            return self.dc.GetSizeTuple()
        def Blit(self, dstX, dstY, w, h, srcDC, srcX, srcY):
            self.dc.BlitXY(dstX, dstY, w, h, srcDC, srcX, srcY)
        def DrawPoint(self, x, y):
            self.dc.DrawPointXY(x, y)
        def DrawLine(self, x1, y1, x2, y2):
            self.dc.DrawLineXY(x1, y1, x2, y2)
        def DrawText(self, str, x, y):
            self.dc.DrawTextXY(str, x, y)
        def DrawRotatedText(self, str, x, y, angle):
            self.dc.DrawRotatedTextXY(str, x, y, angle)
    def UnwrapDC(dc):
        return dc.dc
else:
    def DCCompatibilityWrapper(dc):
        return dc
    def UnwrapDC(dc):
        return dc
 

########################################################################
#
#   class Driver
#
########################################################################

class Driver(Gfx.Driver):
    """A graphics driver for  wx.Windows.
    For an explanation of the inherited methods see GfxInterface.py.
    """

    def __init__(self, dc):
        """Initialize canvas on the device context dc."""
        Gfx.Driver.__init__(self)
        self.font = wx.Font(12, wx.MODERN, wx.NORMAL, wx.NORMAL,
                           encoding=wx.FONTENCODING_ISO8859_1)
        self.pen = wx.Pen(wx.Colour(0, 0, 0), 1, wx.SOLID)
        self.pen.SetCap(wx.CAP_ROUND)
        self.brush = wx.Brush(wx.Colour(0, 0, 0), wx.SOLID)
        self.dc = None
        self.color = (0.0, 0.0, 0.0)        
        self.changeDC(dc)
        if dc:
            self.reset()
            if not isinstance(dc, wx.PostScriptDC): self.clear()

    def changeDC(self, dc):
        """Use a new dc for the following drawing commands."""
        oldDC = self.getDC()
        self.dc = DCCompatibilityWrapper(dc)
        if dc:
            self.resizedGfx()
            dc.SetAxisOrientation(True, False)
            dc.SetBackground(wx.Brush(wx.Colour(255, 255, 255)))
            dc.SetPen(self.pen)
            dc.SetBrush(self.brush)
            dc.SetFont(self.font)            
            dc.SetTextForeground(wx.Colour(int(round(self.color[0]*255)),
                                          int(round(self.color[1]*255)),
                                         int(round(self.color[2]*255))))
        return oldDC
                     
    def getDC(self):
        """-> wx.DC of this graphics drivers object"""
        return UnwrapDC(self.dc)

    def resizedGfx(self):
        """Take notice if the underlying device has been resized."""
##        if isinstance(self.dc, wx.PostScriptDC):
##            self.dpi = self.dc.GetResolution()
##            self.w = self.dpi*6
##            self.h = self.dpi*6
##        else:
        try:
            self.w, self.h = self.dc.GetSizeTuple()
        except wx.PyAssertionError:
            self.w, self.h = 100, 100
        self.dpi = 100

    def getSize(self):       
        return self.w, self.h

    def getResolution(self):
        return self.dpi
        
    def setColor(self, rgbTuple):     
        self.color = rgbTuple
        wxCol = wx.Colour(int(round(rgbTuple[0]*255)),
                          int(round(rgbTuple[1]*255)),
                          int(round(rgbTuple[2]*255)))
        self.pen.SetColour(wxCol)
        self.brush.SetColour(wxCol)
        self.dc.SetTextForeground(wxCol)
        self.dc.SetPen(self.pen)
        self.dc.SetBrush(self.brush)
     

    def setLineWidth(self, width):
        self.lineWidth = width
        if width == Gfx.THIN: tn = 1
        elif width == Gfx.MEDIUM: tn = 2
        elif width == Gfx.THICK: tn = 3
        else: raise ValueError, \
                    "'thickness' must be 'thin', 'medium' or thick' !"
        self.pen.SetWidth(tn)
        self.dc.SetPen(self.pen)

    def setLinePattern(self, pattern):
        self.linePattern = pattern
        if pattern == Gfx.CONTINUOUS: lp = wx.SOLID
        elif pattern == Gfx.DASHED: lp = wx.SHORT_DASH
        elif pattern == Gfx.DOTTED: lp = wx.DOT
        else: raise ValueError, \
                    "'pattern' must be 'continuous','dashed' " + \
                    "or 'dotted'"
        self.pen.SetStyle(lp)
        self.dc.SetPen(self.pen)

    def setFillPattern(self, pattern):
        self.fillPattern = pattern
        if pattern == Gfx.SOLID: fp = wx.SOLID
        elif pattern == Gfx.PATTERN_A: fp = wx.BDIAGONAL_HATCH
        elif pattern == Gfx.PATTERN_B: fp = wx.FDIAGONAL_HATCH
        elif pattern == Gfx.PATTERN_C: fp = wx.CROSSDIAG_HATCH
        else: raise ValueError, \
                    "'pattern' must be 'solid' or 'patternA', " + \
                    "'patternB', 'patternC' !"
        self.brush.SetStyle(fp)
        self.dc.SetBrush(self.brush)

    def setFont(self, ftype, size, weight):
        self.fontType = ftype
        self.fontSize = size
        self.fontWeight = weight
        if ftype == Gfx.SANS: ff = wx.SWISS
        elif ftype == Gfx.SERIF: ff = wx.ROMAN
        elif ftype == Gfx.FIXED: ff = wx.MODERN
        else: raise ValueError, \
                    "'type' must be 'sans', 'serif' or 'fixed' !"
        if size == Gfx.SMALL: fs = 8
        elif size == Gfx.NORMAL: fs = 12
        elif size == Gfx.LARGE: fs = 16
        else: raise ValueError, \
                    "'size' must be 'small', 'normal' or 'large' !"
        fst = wx.NORMAL
        fw = wx.NORMAL
        if "i" in weight: fst = wx.ITALIC
        elif "b" in weight: fw = wx.BOLD
        self.font = wx.Font(fs, ff, fst, fw,
                           encoding=wx.FONTENCODING_ISO8859_1)
        self.dc.SetFont(self.font)


    def getTextSize(self, text):
        try:
            return self.dc.GetTextExtent(text)
        except AttributeError:
            if self.fontSize == Gfx.SMALL: fs = 8
            elif self.fontSize == Gfx.NORMAL: fs = 12
            elif self.fontSize == Gfx.LARGE: fs = 16
            return (len(text) * fs * 2/3, fs)   # very inexact


    def clear(self, rgbTuple=(1.0, 1.0, 1.0)):
        if isinstance(self.dc, wx.PostScriptDC):
            oldcolor = self.color
            oldFillPattern = self.fillPattern
            self.setColor(rgbTuple)
            self.setFillPattern(Gfx.SOLID)
            self.fillRect(0, 0, self.w, self.h)
            self.setColor(oldColor)
            self.setFillPattern(oldFillPattern)
        else:
            self.dc.SetBackground(wx.Brush(wx.Colour(
                                          int(round(rgbTuple[0]*255)),
                                          int(round(rgbTuple[1]*255)),
                                          int(round(rgbTuple[2]*255)))))
            self.dc.Clear()


    def drawPoint(self, x, y):
        if self.lineWidth == Gfx.THIN:
            self.dc.DrawPoint(x, self.h-y-1)
        else:
            self.dc.DrawLine(x, self.h-y-1, x, self.h-y-1)

    def drawLine(self, x1, y1, x2, y2):
        self.dc.DrawLine(x1, self.h-y1-1, x2, self.h-y2-1)

    def drawPoly(self, array):
        if array:
            points = [wx.Point(p[0],self.h-p[1]-1) for p in array]
            self.dc.DrawLines(points)

# somehow the following does not draw filled rectangles!?
##    def fillRect(self, x, y, w, h):
##        self.dc.SetPen(wx.TRANSPARENT_PEN)
##        self.dc.DrawRectangle(x, y, w, h)
##        self.dc.SetPen(self.pen)

    def fillRect(self, x, y, w, h):
        self.fillPoly([(x,y-1), (x+w,y-1), (x+w,y+h-1), (x, y+h-1)])
        # x+w,y+h are used instead of x+w-1, y+h-1, because
        # otherwise the rectangle misses one line / column!?

    def fillPoly(self, array):
        if array:
            self.dc.SetPen(wx.TRANSPARENT_PEN)
            points = [wx.Point(p[0],self.h-p[1]-1) for p in array]
            self.dc.DrawPolygon(points)
            self.dc.SetPen(self.pen)


    def writeStr(self, x, y, str, rotationAngle=0.0):
        w, h = self.getTextSize(str)
        if rotationAngle == 0.0:
            self.dc.DrawText(str, x, self.h-y-h)
        else:
            a = rotationAngle / 180.0 * math.pi
            da = math.atan2(h,0)-a
            dw = int(h*math.cos(da)+0.5)
            dh = int(h*math.sin(da)+0.5)-h
            if _canRotateText:
                # Unfortunately, DrawRotatedText does not work 
                # under some configurations!
                self.dc.DrawRotatedText(str, x-dw, self.h-y-h-dh,rotationAngle)
                return
            _buffer = wx.EmptyBitmap(w, h)
            dc = DCCompatibilityWrapper(wx.BufferedDC(None, _buffer))
            dc.SetBackground(wx.BLACK_BRUSH)
            dc.Clear()
            dc.SetFont(self.font)
            dc.SetTextForeground((255,255,255))
            dc.SetTextBackground((0, 0, 0))
            dc.DrawText(str, 0, 0)
            if _buffer.__dict__.has_key("ConvertToImage"):
                image = _buffer.ConvertToImage()
            else:
                image = wx.ImageFromBitmap(_buffer)
            data = image.GetData()
            for dy in range(h):
                for dx in range(w):
                    if ord(data[(dy*w + dx)*3]) > 128:
                        r = math.sqrt(dx**2+dy**2)
                        da = math.atan2(dy,dx) - a
                        xx = int(r * math.cos(da)+0.5)
                        yy = int(r * math.sin(da)+0.5)
                        self.dc.DrawPoint(x+xx-dw, self.h-y-h+yy-dh)


########################################################################
#
#   class Window
#
########################################################################


class Window(Driver, Gfx.Window):
    
    def __init__(self, size=(640, 480), title="wx.Graph", app=None):
        if app != None:
            self.app = app
        else:
            self.app = wx.PySimpleApp()
            
        self.win = wx.Frame(None, -1, title, style=
                            wx.DEFAULT_FRAME_STYLE)
        self.win.SetSize(size)
        self.win.Show(1)
        #self.app.SetTopWindow(self.win)
        #self.win.Refresh()
        
        size = self.win.GetClientSize()        
        self.buffer = wx.EmptyBitmap(size.width, size.height)
        dc = wx.BufferedDC(None, self.buffer)
        self.app.SetTopWindow(self.win)
        wx.EVT_PAINT(self.win, self._OnPaint)
        Driver.__init__(self, dc)

    def _OnPaint(self, event):
        dc = DCCompatibilityWrapper(wx.PaintDC(self.win))
        dc.Blit(0, 0, self.w, self.h, self.getDC(), 0, 0)

    def refresh(self):
        self.win.Refresh()
        self.win.Update()

    def quit(self):
        self.win.Close()
        self.win.Destroy()
        
    def waitUntilClosed(self):
        self.app.MainLoop()



class PostscriptPrintout(wx.Printout):
    """DEPRECATED!"""
    def __init__(self, printData, callBack):
        """Initialize class with a filename and a callback function that
        takes the printer DC as argument. The callback functions task is
        to draw the page content onto the given DC.
        """
        wx.Printout.__init__(self)
        self.callBack = callBack
        self.printData = printData

    def HasPage(self, page):
        return (page <= 1)

    def GetPageInfo(self):
        return (1,1,1,1)

    def OnPrintPage(self, page):
        dc = self.GetDC()
        #dc = wx.PostScriptDC(self.printData)
        #dc.StartDoc("Postscript")
        self.callBack(dc)
        #dc.EndDoc()
        return True


def DumpPostscript(frame, fileName, callBack, orientation = "Portrait"):
        """WARNING: DumpPostscript is deprecated! Use module psGfx instead!
        
        Dump data to a postscript file. 'frame' is wx.Frame (needed for
        wx.Printer), 'fileName' ist the name for the postscript file and
        'callBack' is the function used for setting up the page.
        'callBack' takes a PostScriptDC as argument. 'orientation' sets
        the page orientation of the output, it can take either the values
        wx.PORTRAIT or wx.LANDSCAPE or the string values 'Portrait' or
        'Landscape'.
        """
        print "wxGfx.DumpPostscript is deprecated, use module psGfx instead!" 
        assert callBack != None, "No page setup function specified!"
        if type(orientation) == type(""):
            if orientation.lower() == "portrait":
                orientation = wx.PORTRAIT
            elif orientation.lower() == "landscape":
                orientation = wx.LANDSCAPE
            else:
                raise AssertionError, "Unknown orientation: %s"%orientation
        pd = wx.PrintData()
        pd.SetPrintMode(wx.PRINT_MODE_STREAM)
        pd.SetFilename(fileName)
        pd.SetOrientation(orientation)
        pdd = wx.PrintDialogData()
        pdd.SetPrintData(pd)
        pdd.EnablePrintToFile(True)
        pdd.SetPrintToFile(True)       
        printer = wx.Printer(pdd)
        printout = PostscriptPrintout(pd, callBack)        
        printer.Print(frame, printout, False)
        printout.Destroy()


##def DumpPostscript(frame, fileName, callBack, orientation = "Portrait"):
##        """Dump data to a postscript file. 'frame' is wx.Frame (needed for
##        wx.Printer), 'fileName' ist the name for the postscript file and
##        'callBack' is the function used for setting up the page.
##        'callBack' takes a PostScriptDC as argument. 'orientation' sets
##        the page orientation of the output, it can take either the values
##        wx.PORTRAIT or wx.LANDSCAPE or the string values 'Portrait' or
##        'Landscape'.
##        """
##        assert callBack != None, "No page setup function specified!"
##        if type(orientation) == type(""):
##            if orientation.lower() == "portrait":
##                orientation = wx.PORTRAIT
##            elif orientation.lower() == "landscape":
##                orientation = wx.LANDSCAPE
##            else:
##                raise AssertionError, "Unknown orientation: %s"%orientation
##        pd = wx.PrintData()
##        pd.SetPrintMode(wx.PRINT_MODE_STREAM)
##        pd.SetFilename(fileName)
##        pd.SetOrientation(orientation)
##        dc = wx.PostScriptDC(pd)
##        outputStream = wx.FileOutputStream(fileName)
##        assert outputStream.Ok(), "Could not get an output stream!"
##        nd = pd.GetNativeData()
##        nd.SetOutputStream(outputStream)
##        dc.StartDoc(fileName)
##        dc.StartPage()
##        callBack(dc)
##        dc.EndPage()
##        dc.EndDoc()
        
########################################################################
#
#   Test
#
########################################################################
        
if __name__ == "__main__":
    import systemTest
    systemTest.Test_wxGfx()

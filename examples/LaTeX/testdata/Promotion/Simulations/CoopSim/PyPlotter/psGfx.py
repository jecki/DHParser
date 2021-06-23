# psGfx - Implementation of Gfx.Driver that writes postscript files.

"""Implements Gfx.Driver for Postscript"""

import Gfx
from Compatibility import *

driverName = "psGfx"


########################################################################
#
#   constants
#
########################################################################

DPI = 72
RES_X,RES_Y = 842, 595

REENCODE = """
/reencodeISO {
dup dup findfont dup length dict begin
{ 1 index /FID ne { def }{ pop pop } ifelse } forall
/Encoding ISOLatin1Encoding def
currentdict end definefont
} def
/ISOLatin1Encoding [
/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
/space/exclam/quotedbl/numbersign/dollar/percent/ampersand/quoteright
/parenleft/parenright/asterisk/plus/comma/minus/period/slash
/zero/one/two/three/four/five/six/seven/eight/nine/colon/semicolon
/less/equal/greater/question/at/A/B/C/D/E/F/G/H/I/J/K/L/M/N
/O/P/Q/R/S/T/U/V/W/X/Y/Z/bracketleft/backslash/bracketright
/asciicircum/underscore/quoteleft/a/b/c/d/e/f/g/h/i/j/k/l/m
/n/o/p/q/r/s/t/u/v/w/x/y/z/braceleft/bar/braceright/asciitilde
/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef/.notdef
/.notdef/dotlessi/grave/acute/circumflex/tilde/macron/breve
/dotaccent/dieresis/.notdef/ring/cedilla/.notdef/hungarumlaut
/ogonek/caron/space/exclamdown/cent/sterling/currency/yen/brokenbar
/section/dieresis/copyright/ordfeminine/guillemotleft/logicalnot
/hyphen/registered/macron/degree/plusminus/twosuperior/threesuperior
/acute/mu/paragraph/periodcentered/cedilla/onesuperior/ordmasculine
/guillemotright/onequarter/onehalf/threequarters/questiondown
/Agrave/Aacute/Acircumflex/Atilde/Adieresis/Aring/AE/Ccedilla
/Egrave/Eacute/Ecircumflex/Edieresis/Igrave/Iacute/Icircumflex
/Idieresis/Eth/Ntilde/Ograve/Oacute/Ocircumflex/Otilde/Odieresis
/multiply/Oslash/Ugrave/Uacute/Ucircumflex/Udieresis/Yacute
/Thorn/germandbls/agrave/aacute/acircumflex/atilde/adieresis
/aring/ae/ccedilla/egrave/eacute/ecircumflex/edieresis/igrave
/iacute/icircumflex/idieresis/eth/ntilde/ograve/oacute/ocircumflex
/otilde/odieresis/divide/oslash/ugrave/uacute/ucircumflex/udieresis
/yacute/thorn/ydieresis
] def
"""

PS_DOCSTART = """%%!PS-Adobe-3.0 EPSF-3.0
%%%%BoundingBox: 0 0 %d %d
%%%%Creator: PyPlotter.psGfx graphics driver
%%%%LanguageLevel: 2
%%%%EndComments
%%%%BeginProlog
%s
%%%%EndProlog

""" % (RES_X, RES_Y, REENCODE)

PS_DOCEND = """%%EOF
"""

PS_PAGESTART = """%%Page: 1 1
"""

PS_PAGEEND = """
"""


########################################################################
#
#   class Driver
#
########################################################################

class Driver(Gfx.Driver):
    """A postscript graphics driver      
    """

    def __init__(self):
        Gfx.Driver.__init__(self)
        self.ps = []
        self.clear()      

    def getPostscript(self):
        """Returns the postscript commands as one long string!"""
        return "".join(self.ps+[PS_PAGEEND,PS_DOCEND])

    def save(self, fName):
        """Saves the contents as a file."""
        f = file(fName, "w")
        f.write(self.getPostscript())
        f.close()
    
    def reset(self):
        self.setColor((0.0, 0.0, 0.0))
        self.setLineWidth(THIN)
        self.setLinePattern(CONTINUOUS)
        self.setFillPattern(SOLID)
        self.setFont(SANS, NORMAL, PLAIN)

    def getSize(self):
        return (RES_X,RES_Y)

    def getResolution(self):
        return DPI
    
        
    def setColor(self, rgbTuple):
        self.color = rgbTuple
        self.ps.append("%f %f %f setrgbcolor\n"%rgbTuple)

    def setLineWidth(self, width):
        self.lineWidth = width
        if width == Gfx.THIN: tn = 1.0
        elif width == Gfx.MEDIUM: tn = 2.0
        elif width == Gfx.THICK: tn = 3.0
        else: raise ValueError, \
                    "'thickness' must be 'thin', 'medium' or thick' !"
        self.ps.append("%f setlinewidth\n"%tn)
        
    def setLinePattern(self, pattern):
        self.linePattern = pattern
        if pattern == Gfx.CONTINUOUS: lp = "[] 0"
        elif pattern == Gfx.DASHED: lp = "[4 4] 2"
        elif pattern == Gfx.DOTTED: lp = "[2 5] 0"
        else: raise ValueError, \
                    "'pattern' must be 'continuous','dashed' " + \
                    "or 'dotted'"
        self.ps.append("%s setdash\n"%lp)

    def setFillPattern(self, pattern):
        self.fillPattern = pattern
        # so what?

    def setFont(self, ftype, size, weight):
        self.fontType = ftype
        self.fontSize = size
        self.fontWeight = weight
        verrorStr = "'weight' must be '','b','i' or 'bi'!"
        if ftype == Gfx.FIXED:
            if weight == Gfx.BOLDITALIC: name = "/Courier-BoldOblique"
            elif weight == Gfx.ITALIC: name = "/Courier-Oblique"
            elif weight == Gfx.BOLD: name = "/Courier-Bold"
            elif weight == Gfx.PLAIN: name = "/Courier"
            else: raise ValueError, verrorStr
        elif ftype == Gfx.SERIF:
            if weight == Gfx.BOLDITALIC: name = "/Times-BoldItalic"
            elif weight == Gfx.ITALIC: name = "/Times-Italic"
            elif weight == Gfx.BOLD: name = "/Times-Bold"
            elif weight == Gfx.PLAIN: name = "/Times-Roman"
            else: raise ValueError, verrorStr            
        elif ftype == Gfx.SANS:
            if weight == Gfx.BOLDITALIC: name = "/Helvetica-BoldOblique"
            elif weight == Gfx.ITALIC: name = "/Helvetica-Oblique"
            elif weight == Gfx.BOLD: name = "/Helvetica-Bold"
            elif weight == Gfx.PLAIN: name = "/Helvetica"
            else: raise ValueError, verrorStr            
        else: raise ValueError, \
                    "'type' must be 'sans', 'serif' or 'fixed' !"
        self.ps.append(name + " reencodeISO def\n")
        self.ps.append(name + " findfont\n")
        if size == Gfx.SMALL: fs = 8.0
        elif size == Gfx.NORMAL: fs = 12.0
        elif size == Gfx.LARGE: fs = 16.0
        else: raise ValueError, \
                    "'size' must be 'small', 'normal' or 'large' !"
        self.ps.append("%f scalefont setfont\n"%fs)         
        
    def getTextSize(self, text):
        if self.fontSize == Gfx.SMALL: fs, w = 8, 4
        elif self.fontSize == Gfx.NORMAL: fs, w = 12, 3
        elif self.fontSize == Gfx.LARGE: fs, w = 16, 3
        return (len(text) * fs * w/7, fs)   # very inexact!        
    
       
    def clear(self, rgbTuple = (1.0, 1.0, 1.0)):
        self.ps = [PS_DOCSTART, PS_PAGESTART]
        if rgbTuple != (1.0, 1.0, 1.0):
            w,h = self.getSize()
            saveColor, savePattern = self.color, self.fillPattern
            self.setFillPattern(Gfx.SOLID)
            self.setColor(rgbTuple)
            self.fillRect(0,0,w-1, h-1)
            self.color, self.fillPattern = saveColor, savePattern
        self.setColor(self.color)
        self.setLineWidth(self.lineWidth)
        self.setLinePattern(self.linePattern)
        self.setFillPattern(self.fillPattern)
        self.setFont(self.fontType, self.fontSize, self.fontWeight)   

    def drawPoint(self, x, y):
        self.ps.append("newpath\n%d %d moveto\n%d %d lineto\nstroke\n" % \
                       (x,y,x+1,y))
    
    def drawLine(self, x1, y1, x2, y2):
        self.ps.append("newpath\n%d %d moveto\n%d %d lineto\nstroke\n" % \
                       (x1,y1,x2,y2))
        
    def drawPoly(self, array):
        if len(array) == 0: return
        x,y = array[0]
        self.ps.append("newpath\n%d %d moveto\n" % (x,y))
        for x,y in array: self.ps.append("%d %d lineto\n"%(x,y))
        self.ps.append("stroke\n")

    def fillPoly(self, array):
        self.drawPoly(array)
        self.ps[-1] ="fill\n"

    def writeStr(self, x, y, text, rotationAngle=0.0):
        self.ps.append("%d %d moveto\n"%(x,y))
        if rotationAngle != 0.0:
            self.ps.append("%f rotate\n" % rotationAngle)
        t = ["("]
        for ch in text:
            if ch == ")" or ch == "(" or ch == "\\": t.append("\\"+ch)
            elif ord(ch) >= 128: t.append("\\%o"%ord(ch))
            else: t.append(ch)
        t.append(") show\n")
        self.ps.append("".join(t))
        if rotationAngle != 0.0:
            self.ps.append("%f rotate\n" % (-rotationAngle))


        
if __name__ == "__main__":
    import systemTest
    systemTest.Test_psGfx()        

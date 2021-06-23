#!/usr/bin/python

"""
CoopSim 0.9.9 beta 2 - The Evolution of Cooperation

A computer simulation of the reiterated 2 person prisoners dilemma.
(Based on Robert Axelrod's book: "The Evolution of Cooperation")

(c) GNU Public License

Author: Eckhart Arnold
e-mail: eckhart_arnold@hotmail.com


with contributions from:
    Alex Mainzer
    Bjoern van den Bruck
    Christian Erlen
    Stefan Pennartz
    Sven Sommer
    Paul Boehm
"""

import inspect, copy, re, sets, os, sys, math
from bz2 import BZ2File as ZIPFile
import cPickle as pickle
import wx
assert wx.VERSION[0] >= 2, "Need a wxWidgets version of 2.4 or newer. "+\
                           "Yours is %s !"%str(wx.VERSION)
if wx.VERSION[0] == 2 and wx.VERSION[1] <= 6: 
    from wxPython.lib.dialogs import wxMultipleChoiceDialog, wxScrolledMessageDialog
    from wxPython.lib.layoutf import Layoutf
    from wxPython.html import wxHtmlWindow, wxHW_SCROLLBAR_AUTO
else:
    from wx.lib.dialogs import MultipleChoiceDialog as wxMultipleChoiceDialog
    from wx.lib.dialogs import ScrolledMessageDialog as wxScrolledMessageDialog
    from wx.lib.layoutf import Layoutf    
    from wx.html import HtmlWindow as wxHtmlWindow
    from wx.html import HW_SCROLLBAR_AUTO as wxHW_SCROLLBAR_AUTO

from PyPlotter import Gfx, wxGfx, psGfx, Colors, Graph, Simplex
from PopulationDynamics import Dynamics
from PopulationDynamics.Compatibility import *
import Simulation, Strategies, PolymorphicStrategies, Logging, icons


# psyco support to speed up the program
# (delete or comment out the following lines,
#  if it takes too much memory!)
try:
    import psyco
    # psyco.log()
    psyco.profile()
    psyco.cannotcompile(re.compile)
    psyco.cannotcompile(re.sub)
    print "Using psyco JIT to speed up program..."
except ImportError:
    pass


###############################################################################
#
# Customization Flags
#
# usually these should not be changed here, edit module Customized.py instead!
#
###############################################################################

DISABLE_USER_STRATEGIES = False   
SIMPLEX_FLAVOR = Simplex.VECTORS # Simplex.TRAJECTORIES
SIMPLEX_DO_NOTHING, SIMPLEX_REDRAW, SIMPLEX_RESIZE = 0, 1, 3

SAVE_IMAGE_WIDTH, SAVE_IMAGE_HEIGHT = 1280, 960
HTML_IMAGE_WIDTH, HTML_IMAGE_HEIGHT = 640, 400  
AUTO_IMAGE_WIDTH, AUTO_IMAGE_HEIGHT = -1, -1

try:
    import Customized
    CUSTOMIZED_COOPSIM = True
    cmFlags = set(dir(Customized))
    if "DISABLE_USER_STRATEGIES" in cmFlags:
        DISABLE_USER_STRATEGIES = Customized.DISABLE_USER_STRATEIGES
    if "SIMPLEX_FLAVOR" in cmFlags: SIMPLEX_FLAVOR = Customized.SIMPLEX_FLAVOR
    cmFlags = None
except ImportError:
    CUSTOMIZED_COOPSIM = False

if not DISABLE_USER_STRATEGIES:
    sys.path.append(os.path.expanduser("~"))

###############################################################################
    

GPLMissingMessage = """
This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public
License as published by the Free Software Foundation; either
version 2 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
General Public License for more details.

For some unknown reason the file "LICENSE.GPL" seems to be missing 
in the distribution directory of this program. You can still get 
the full text of the GPL License under 

  http://www.gnu.org/copyleft/gpl.html 
  
or write to 

  Free Software Foundation, Inc.
  59 Temple Place - Suite 330
  Boston, MA 02111-1307 USA
"""


EmptyUserStrategiesPy = """
## Here you can define your own user strategies as well as custom
## simulation setups. All user Strategies must be derived from
## the class Strategies.Strategy and implement the firstMove as
## well as the nextMove methods. Remember that in order to use a user
## defined strategy class, it must be instantiated. See the example
## below.

## Modules Simulation and Strategies must be imported here in order to
## define user strategies and/or custom simulation setups.

from Simulation import *
from Strategies import *
from PyPlotter import Simplex


## Here is an example for a user strategy.
## Don't forget to instantiate any user defined classes !!!

# class LesserTFT(Strategy):
#     "Retailiate only when not having retailiated in the last round already."
#     def firstMove(self):
#         return 1  # start friendly
#     def nextMove(self, myMoves, opMoves):
#         if opMoves[-1] == 0 and myMoves[-1] != 0:
#             return 0  # retailiate
#         else: 
#             return 1  # cooperate
# lesser_tft = LesserTFT()



## If your strategy uses random numbers, be shure to set the member
## variable 'randomizing' to true to indicate the use of random
## numbers, so that several samples of each match against this
## strategy are taken. The constructor of your class strategy class
## that uses random numbers could look like this:
##
## class RandomizingStrategy(Strategy):
##     def __init__(self):
##         Strategy.__init__(self) # call the constructor of the parent class
##         self.randomizing = True # indicate use of random numbers
##
##     ...
##



## To define a custom setup, you have will have to instantiate the SimSetup
## class and possibly also the Degenerator class (if you want to artificially 
## induce an evolutionary drift for example). The constructor of the SimSetup
## class takes the following keyword parameters:
##
##    name         = string: name of the model
##    strategyList = list of Strategy objects: the list of the strategies
##    population   = tuple: population share for each strategy
##    correlation  = float [0.0-1.0]: correlation factor
##    gameNoise    = float [0.0-1.0]: in game noise
##    noise        = float [0.0-1.0]: evolutionary background noise
##    iterations   = int:  number of iterations for one match
##    samples      = int:  number of sample matches to take (only useful for 
##                   randomizing strategies)
##    payoff       = tuple of floats:  payoff tuple (T, R, P, S)
##    demes        = tuple of ints: (number of demes, min. size, max. size,
##                                   reshaping interval)
##    mutators     = list of Motator objects: description of possible
##                   mutation (or rather degeneration) of strategies during  
##                   the course of the evolutionary development.
##
## The class Mutator is instantiated with the following parameters:
##
##    original    = int: the ordinal number of the strategy that is going
##                    to mutate
##    mutated     = int: the ordinal number of the startegy that 'original' is
##                    going to mutate into 
##    rate        = float [0.0 - 1.0]: mutation rate
##
## Here is an example simulation setup using mutators:

# custom_setup = SimSetup(name         = "Grim => Dove, Tester", 
#                         strategyList = [Grim(), Dove(), Tester()], 
#                         population   = (0.8, 0.01, 0.19), 
#                         mutators     = [Mutator(0, 1, 0.01)])



## Two state automata are automata that have at most two states. There
## are exactly 26 two state automata. To include the two state automata
## into the set of strategies that can be selected in the simulation
## setup dialog, uncomment the following line.

# twostateautomata = genAllAutomata()


## To change the flavor of the simplex diagram uncomment one(!) of the
## following lines

# SIMPLEX_FLAVOR = Simplex.NULL           # Turn off simplex drawing!
# SIMPLEX_FLAVOR = Simplex.TRAJECTORIES   # WARNING: this is slow!
# SIMPLEX_FLAVOR = Simplex.SCALED_VECTORS # arrows scaled by field strength
# SIMPLEX_FLAVOR = Simplex.VECTORS        # standard simplex

"""


def ClearUserStrategies():
    f = file(os.path.expanduser("~")+"/UserStrategies.py", "w")
    f.write(EmptyUserStrategiesPy)
    f.close()

if not DISABLE_USER_STRATEGIES:
    ClearUserStrategies()
    import UserStrategies

def ScanModule(module):
    return [module+"."+token for token in dir(eval(module))]

dirStrategies = ScanModule("Strategies")
dirStrategies.extend(ScanModule("PolymorphicStrategies"))
dirUserStrategies = [] # ScanModule("UserStrategies")]
if CUSTOMIZED_COOPSIM:
    dirUserStrategies.extend(["Customized."+token \
                              for token in dir(Customized)])

def gatherStrategies():
    strategyList = []
    classes = sets.Set([Strategies.Strategy])
    
    def checkIn(obj):
        if isinstance(obj, Strategies.Strategy) and \
           not obj in strategyList:
            strategyList.append(obj)
            classes.add(obj.__class__)    
    
    for objName in dirStrategies + dirUserStrategies:
        obj = eval(objName)
        if isinstance(obj, list):
            for item in obj: checkIn(item)
        else: checkIn(obj)
##~     for objName in dirStrategies + dirUserStrategies:
##~         obj = eval(objName)        
##~         if inspect.isclass(obj) and \
##~            issubclass(obj, Strategies.Strategy) and \
##~            not obj in classes:
##~             objInstance = eval(objName+"()")
##~             strategyList.append(objInstance)
    if CUSTOMIZED_COOPSIM and Customized.__dict__.has_key("filterStrategies"):
        return Customized.filterStrategies(strategyList)
    else:  return strategyList
                 
exampleModel = Simulation.SimSetup("Simple Example", [Strategies.TitForTat(),
                                                      Strategies.Grim(),
                                                      Strategies.Random()])
exampleModel._userDefined = False

def gatherModels():
    modelDict = {}
    for objName in dirUserStrategies: # + globals().keys()  
        obj = eval(objName)
        if isinstance(obj, Simulation.SimSetup):
            modelDict[obj.name] = obj
        elif isinstance(obj, list):
            for item in obj:
                if isinstance(item, Simulation.SimSetup):
                    modelDict[item.name] = item
    if CUSTOMIZED_COOPSIM and Customized.__dict__.has_key("filterModels"):
        return Customized.filterModels(modelDict)
    else: return modelDict


def pickSimplexRaster():
    if SIMPLEX_FLAVOR == Simplex.TRAJECTORIES: return Simplex.RASTER_RANDOM
    else: return Simplex.RASTER_DEFAULT

###############################################################################
#
# Setup Dialog
#
###############################################################################

def checkPayoff(T, R, P, S):
    """-> True, if  T > R > P > S  and  2R > T+S"""
    return T > R and R > P and P > S and 2*R > T+S


class FSpinCtrl(object):
    """A spin ctrl for floating point values. (Objects of this class are not
    widgets themselves (FSpinCtrl is not derived from wxControl),
    but rather collections of a TextCtrl and SpinButton widget).
    """
    def __init__(self, parent, labelStr, start, stop, divisor, fval, validf):
        self.start, self.stop = start, stop
        self.divisor, self.fval = divisor, fval
        self.validator = validf
        self.digits = int(math.log10(self.divisor+0.5))+1
        self.fmStr = "%."+str(self.digits)+"f"
        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.label = wx.StaticText(parent, -1, labelStr)
        self.sizer.Add(self.label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        self.text = wx.TextCtrl(parent, -1, self.fstr(), (30, 50), (40, -1))
        self.sizer.Add(self.text)
        self.spin = wx.SpinButton(parent, -1, (30, 50), (15, -1), 
                                  style = wx.SP_VERTICAL)
        self.spin.SetRange(start, stop)
        self.spin.SetValue(int(self.fval * self.divisor))
        self.sizer.Add(self.spin)
        wx.EVT_SPIN(self.spin, -1, self.OnSpin)
        wx.EVT_KILL_FOCUS(self.text, self.OnText)
        
    def fstr(self):
        return self.fmStr%self.fval

    def _checkIn(self, f):
        oldf = self.fval
        val = f * self.divisor
        if val < self.start:  self.fval = self.start / float(self.divisor)
        elif val > self.stop: self.fval = self.stop / float(self.divisor)
        else: self.fval = f
        return oldf != self.fval

    def OnText(self, event):
        try:
            f = float(self.text.GetValue())
            f2 = round(f*self.divisor)/self.divisor
            if self._checkIn(f2):
                self.spin.SetValue(int(self.fval * self.divisor))
        except ValueError:
            self.text.SetValue(self.fstr())
        else:
            if f != self.fval:
                self.text.SetValue(self.fstr())
        self.validator()

    def OnSpin(self, event):
        val = self.spin.GetValue()
        self.fval = float(val) / float(self.divisor)
        self.text.SetValue(self.fstr())
        self.validator()

    def GetValue(self):
        return self.fval

    def SetValue(self, f):
        if self._checkIn(f):
            self.spin.SetValue(int(self.fval * self.divisor))
            self.text.SetValue(self.fstr())

    def SetToolTipString(self, tps):
        self.spin.SetToolTipString(tps)
        self.text.SetToolTipString(tps)

        

class SetupDialog(wx.Dialog):
    def __init__(self, parent, setupTemplate, setupName = ""):
        wx.Dialog.__init__(self, parent, -1, "Simulation Setup")       
        self.setup = copy.copy(setupTemplate)
        if setupName: self.setup.name = setupName
        zombie = Simulation.SimSetup("Zombie")
        self.setup._userDefined = False
        self.setup.indexDict = zombie.indexDict
        self.setup.cachedPM = zombie.cachedPM
        self.setup.cachedLog = zombie.cachedLog
        if self.setup.iterations != zombie.iterations:
            self.setup.name += " iterations=%i! "%self.setup.iterations
        #if self.setup.payoff != zombie.payoff:
        #    self.setup.name += " non standard payoff! "
        self.setup.mutators = zombie.mutators
        self.setup.demes = zombie.demes
        self.lastValidPayoff = self.setup.payoff
        self.ok = False
        self.strategyDict = {}
        for s in gatherStrategies():
            self.strategyDict[str(s)] = s
        self.selectedList = [str(s) for s in self.setup.strategyList]
        self.selectedList.sort()
        self.availableList = [s for s in self.strategyDict.keys() \
                                if not s in self.selectedList]
        self.availableList.sort()

        sizer = wx.BoxSizer(wx.VERTICAL)

        box = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self, -1, "Model Name")
        box.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)        
        self.name = wx.TextCtrl(self, -1, self.setup.name, size=(200,-1))
        box.Add(self.name, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        sizer.Add(box, 0, wx.ALIGN_CENTRE|wx.ALL, 5)        

        line = wx.StaticLine(self, -1, size=(20,-1), style=wx.LI_HORIZONTAL)
        sizer.Add(line, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.RIGHT|wx.TOP, 5)

        box = wx.BoxSizer(wx.HORIZONTAL)

        vbox = wx.BoxSizer(wx.VERTICAL)
        label = wx.StaticText(self, -1, "Available Strategies:")
        vbox.Add(label, 0, wx.ALIGN_LEFT|wx.ALL, 5)
        self.pool = wx.ListBox(self, -1, (5, 5), (200, 220),
                              self.availableList, wx.LB_EXTENDED)
        wx.EVT_LEFT_UP(self.pool, self.OnPoolLB)                              
        wx.EVT_LISTBOX_DCLICK(self.pool, -1, self.OnPoolLB_DCLICK)
        vbox.Add(self.pool, 0, wx.ALIGN_CENTRE|wx.ALL, 5)        
        box.Add(vbox, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
        self.poolSel = set()

        vbox = wx.BoxSizer(wx.VERTICAL)
        self.pickBtn = wx.Button(self, -1, " >> ")
        wx.EVT_BUTTON(self.pickBtn, -1, self.OnPick)        
        vbox.Add(self.pickBtn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        self.unpickBtn = wx.Button(self, -1, " << ")
        wx.EVT_BUTTON(self.unpickBtn, -1, self.OnUnpick)        
        vbox.Add(self.unpickBtn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        box.Add(vbox, 0, wx.ALIGN_CENTER_VERTICAL, 5)

        vbox = wx.BoxSizer(wx.VERTICAL)
        label = wx.StaticText(self, -1, "Selected Strategies:")
        vbox.Add(label, 0, wx.ALIGN_LEFT|wx.ALL, 5)
        self.selected = wx.ListBox(self, -1, (5, 5), (200, 220),
                                   self.selectedList, wx.LB_EXTENDED)
        wx.EVT_LEFT_UP(self.selected, self.OnSelectedLB)
        wx.EVT_LISTBOX_DCLICK(self.selected, -1, self.OnSelectedLB_DCLICK)
        vbox.Add(self.selected, 0, wx.ALIGN_CENTRE|wx.ALL, 5)        
        box.Add(vbox, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
        self.selSel = set()
        
        sizer.Add(box, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        label = wx.StaticText(self, -1, "Description:")
        sizer.Add(label, 0, wx.ALIGN_LEFT, 5)
        self.description = wx.TextCtrl(self, -1, "",
                                       size = (-1, 80),
                                       style = wx.TE_MULTILINE|wx.TE_READONLY)
        yellow = wx.Colour(255,255,192);  black = wx.Colour(0,0,0)
        self.description.SetDefaultStyle(wx.TextAttr(black,yellow))
        self.description.SetStyle(0, 0, wx.TextAttr(black,yellow))
        self.description.SetBackgroundColour(yellow)
        self.describe = ""
        sizer.Add(self.description, 0, wx.ALIGN_LEFT|wx.EXPAND, 5)
        
        box = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self, -1, "Payoff ")
        box.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        T, R, P, S = self.setup.payoff
        self.Tctrl = FSpinCtrl(self, "T:", 0, 200, 20, T, self.validate)
        self.Tctrl.SetToolTipString("T (temptation) is the payoff a\n"+\
                                    "player receives for defecting\n"+\
                                    "when the other player cooperates")
        box.Add(self.Tctrl.sizer, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        self.Rctrl = FSpinCtrl(self, "R:", 0, 200, 20, R, self.validate)
        self.Rctrl.SetToolTipString("R (reward) is the payoff a\n"+\
                                    "player receives for cooperating\n"+\
                                    "when the other player cooperates")
        box.Add(self.Rctrl.sizer, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        self.Pctrl = FSpinCtrl(self, "P:", 0, 200, 20, P, self.validate)
        self.Pctrl.SetToolTipString("P (punishment) is the payoff a\n"+\
                                    "player receives for defecting\n"+\
                                    "when the other player defects")        
        box.Add(self.Pctrl.sizer, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        self.Sctrl = FSpinCtrl(self, "S:", 0, 200, 20, S, self.validate)
        self.Sctrl.SetToolTipString("S (sucker's payoff) is the payoff a\n"+\
                                    "player receives for cooperating\n"+\
                                    "when the other player defects")
        box.Add(self.Sctrl.sizer, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        # self.wbm = wx.Bitmap(sys.path[0]+"/icons/warn.png",wx.BITMAP_TYPE_PNG)
        # self.empty = wx.Bitmap(sys.path[0]+"/icons/empty.png",
        #                        wx.BITMAP_TYPE_PNG)
        self.wbm = wx.BitmapFromXPMData(icons.Dict["warn"])
        self.empty = wx.BitmapFromXPMData(icons.Dict["empty"])
        self.warning = wx.BitmapButton(self, -1, self.empty,
                                       style = wx.NO_BORDER)
        self.warntps = "The payoff parameters T,R,P,S \n"+\
                       "must fulfill the two conditions:\n"+\
                       "T > R > P > S  and  T+S < 2R\n"+\
                       "Please adjust the parameters accordingly!"
        wx.EVT_BUTTON(self.warning, -1, self.OnWarning)
        box.Add(self.warning, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        self.resetBtn = wx.Button(self, -1, "< Reset")
        self.resetBtn.SetToolTipString("Reset the payoff parameters\n"+\
                                       "to the original values.")
        wx.EVT_BUTTON(self.resetBtn, -1, self.OnReset)
        box.Add(self.resetBtn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)        
        sizer.Add(box, 0, wx.ALIGN_CENTRE|wx.ALL, 5)        

        box = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self, -1, "Correlation (%)")
        box.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        c = int(self.setup.correlation*100)
        self.correlation = wx.SpinCtrl(self, -1, str(c), (30, 50), (50, -1))
        self.correlation.SetRange(0, 100)
        self.correlation.SetToolTipString("The higher the correlation, "+\
                  "the more likely it is for a player\n"+\
                  "to meet players with the same strategy.\n"+\
                  "0 %: random matching (only population shares matter)\n"+\
                  "100 %: players exclusively meet with players "+\
                  "of the same type")
        box.Add(self.correlation, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        label = wx.StaticText(self, -1, " Game Noise (%)")
        box.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        gn = int(self.setup.gameNoise*100)
        self.gameNoise = wx.SpinCtrl(self, -1, str(gn), (30, 50), (50, -1))
        self.gameNoise.SetRange(0, 100)
        self.gameNoise.SetToolTipString("Chance by which the intended "+\
                                        "move of a player\nis switched "+\
                                        "into its opposite.\n"+\
                                        "0 % = no mistakes\n"+\
                                        "100 % = all moves switched.")
        box.Add(self.gameNoise, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        
        label = wx.StaticText(self, -1, " Background Noise (%)")
        box.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        n = int(self.setup.noise*100)
        self.noise = wx.SpinCtrl(self, -1, str(n), (30, 50), (50, -1))
        self.noise.SetRange(0,100)
        self.noise.SetToolTipString("Amount of random disturbance in the "+\
                                    "evolutionary process.\n"+\
                                    "0 % = no disturbances.\n"+\
                                    "100 % = fitness reduced randomly down "+\
                                    "to almost zero")
        box.Add(self.noise, 0, wx.ALIGN_CENTRE|wx.ALL, 5)        
        sizer.Add(box, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        
        line = wx.StaticLine(self, -1, size=(20,-1), style=wx.LI_HORIZONTAL)
        sizer.Add(line, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.RIGHT|wx.TOP, 5)

        box = wx.BoxSizer(wx.HORIZONTAL)
        btn = wx.Button(self, wx.ID_OK, " OK ")
        btn.SetDefault()
        btn.SetHelpText("The OK button completes the dialog")
        box.Add(btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        btn = wx.Button(self, wx.ID_CANCEL, " Cancel ")
        btn.SetHelpText("The Cancel button cnacels the dialog.")
        box.Add(btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        sizer.Add(box, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        self.SetSizer(sizer)
        self.SetAutoLayout(True)
        sizer.Fit(self)
        self.CenterOnParent(wx.BOTH)         

    def SetPayoff(self, payoff):
        self.Tctrl.SetValue(payoff[0])
        self.Rctrl.SetValue(payoff[1])
        self.Pctrl.SetValue(payoff[2])
        self.Sctrl.SetValue(payoff[3])

    def OnReset(self, event):
        self.SetPayoff(self.setup.payoff)
        self.validate()

    def readPayoff(self):
        T = self.Tctrl.GetValue()
        R = self.Rctrl.GetValue()
        P = self.Pctrl.GetValue()
        S = self.Sctrl.GetValue()
        return (T,R,P,S)

    def validate(self):
        payoff = self.readPayoff()
        if not checkPayoff(*payoff):
            if self.warning.GetBitmapLabel() != self.wbm:
                self.warning.SetBitmapLabel(self.wbm)                
                self.warning.SetToolTipString(self.warntps)
        else:
            self.lastValidPayoff = payoff
            if self.warning.GetBitmapLabel() == self.wbm:
                self.warning.SetBitmapLabel(self.empty)
                self.warning.SetToolTipString("")

    def OnWarning(self, event):
        self.SetPayoff(self.lastValidPayoff)
        self.validate()
            

    def OnPick(self, event):
        sel = self.pool.GetSelections()
        for s in sel:  self.selectedList.append(self.availableList[s])
        self.availableList = list(sets.Set(self.availableList) - \
                                  sets.Set(self.selectedList))
        self.availableList.sort()
        self.selectedList.sort()
        self.pool.Set(self.availableList)
        self.selected.Set(self.selectedList)

    def OnUnpick(self, event):
        sel = self.selected.GetSelections()
        for s in sel:  self.availableList.append(self.selectedList[s])
        self.selectedList = list(sets.Set(self.selectedList) - \
                                 sets.Set(self.availableList))
        self.availableList.sort()
        self.selectedList.sort()
        self.pool.Set(self.availableList)
        self.selected.Set(self.selectedList)

    def ShowDescription(self, strategyName):
        self.description.Clear()
        self.description.AppendText(strategyName+" ---\n")
        docString = self.strategyDict[strategyName].__doc__
        if not docString:  docString = " "
        lines = docString.splitlines()
        strippedLines = [l.lstrip() for l in lines]
        docText = "\n".join(strippedLines)
        self.description.AppendText(docText)
        self.description.SetInsertionPoint(0)        

    def OnPoolLB(self, event):
        sel = set(self.pool.GetSelections())
        delta = self.poolSel ^ sel
        if len(delta) >= 1:  n = tuple(delta)[0]
        else:  n = -1
        if n >= 0 and n < len(self.availableList):
            self.ShowDescription(self.availableList[n])
        self.poolSel = sel
        event.Skip()

    def OnPoolLB_DCLICK(self, event):
        self.OnPick(event)

    def OnSelectedLB(self, event):
        sel = set(self.selected.GetSelections())
        delta = self.selSel ^ sel
        if len(delta) >= 1:  n = tuple(delta)[0]
        else:  n = -1
        if n >= 0 and n < len(self.selectedList):        
            self.ShowDescription(self.selectedList[n])
        self.selSel = sel
        event.Skip()

    def OnSelectedLB_DCLICK(self, event):
        self.OnUnpick(event)

    def ShowModal(self, *_args, **_kwargs):
        while True:
            ret = wx.Dialog.ShowModal(self, *_args, **_kwargs)
            self.ok = (ret == wx.ID_OK)
            if self.ok:
                T,R,P,S = self.readPayoff()
                if not checkPayoff(T,R,P,S):
                    dialog = wx.MessageDialog(self,
                        "Sorry, but the payoff parameters\n"+\
                        "T, R, P, S = %.2f, %.2f, %.2f, %.2f\n"%(T,R,P,S)+\
                        "violate one or both of the conditions:\n"+\
                        "        1. T > R > P > S\n"+\
                        "        2.   T+S < 2R\n\n"+\
                        "Press 'OK' to quit dialog and reset\n"+\
                        "the payoff parameters to:\n"+\
                        "T, R, P, S = %.2f, %.2f, %.2f, %.2f\n"%\
                        self.setup.payoff,     
                        "Alert", wx.OK|wx.CANCEL|wx.ICON_ERROR)
                    query = dialog.ShowModal()
                    dialog.Destroy()
                    if query != wx.ID_OK: continue
                else:  self.setup.payoff = (T, R, P, S)
                self.setup.name = self.name.GetValue()
                self.setup.gameNoise = self.gameNoise.GetValue()/100.0
                self.setup.noise = self.noise.GetValue()/100.0
                self.setup.correlation = self.correlation.GetValue()/100.0
                if self.selectedList == []:
                    dialog = wx.MessageDialog(self,
                        "Sorry, but you must select\n"+\
                        "at least one strategy!\n\n"+\
                        "Press 'OK' to quit dialog and reset\n"+\
                        "the strategy list.", "Alert",
                        wx.OK|wx.CANCEL|wx.ICON_ERROR)
                    query = dialog.ShowModal()
                    dialog.Destroy()
                    if query != wx.ID_OK: continue
                else: self.setup.strategyList = [self.strategyDict[s] \
                                                 for s in self.selectedList]
                self.setup.population = Dynamics.UniformDistribution(\
                                        len(self.setup.strategyList))
            break
        return ret

    def GetValue(self):
        assert self.ok, "Can't read value of canceld 'Edit Sim' dialog!"
        return self.setup
                                       

###############################################################################
#
# HTML Help Dialog
#
###############################################################################                                       
                                       
class HTMLHelpDialog(wx.Dialog):
    def __init__(self, parent, fileName, 
                 pos = wx.DefaultPosition, size = (720,560), 
                 style = wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER):
        wx.Dialog.__init__(self, parent, -1, "CoopSim Help", pos, size)
        x, y = pos
        if x == -1 and y == -1:
            self.CenterOnParent(wx.BOTH)
        text = wxHtmlWindow(self, -1, wx.DefaultPosition,
                            wx.DefaultSize, name="CoopSim Help")
        text.LoadPage(fileName)
        ok = wx.Button(self, wx.ID_OK, "OK")
        text.SetConstraints(Layoutf('t=t5#1;b=t5#2;l=l5#1;r=r5#1', (self,ok)))
        ok.SetConstraints(Layoutf('b=b5#1;x%w50#1;w!80;h!25', (self,)))
        self.SetAutoLayout(1)
        self.Layout()


###############################################################################
#
# SimWindow
#
###############################################################################

class SimWindow(wx.Frame, Logging.LogNotificationInterface):
    def __init__(self):
        fileMenu = [    
            ("&Reset ...", self.OnNew,
             "Start a whole new set of simulations.", ""),
            None,
            ("&Open ...", self.OnOpen,
             "Open a saved set of simulation setups.", "open"),
            ("&Save", self.OnSave,
             "Save the current set of simulation setups.", "save"),
            ("Save &As ...", self.OnSaveAs,
             "Save the current set of simulation setups.", "saveAs"),
            None,
            ("E&xit", self.OnExit, "Exit the program.", "")
        ]
        editMenu = [
            ("&Copy Page", self.OnCopy, "Copy the content of the currently "+\
             "shown notebook page (graph, log or diagram, "+\
             "program code) to Clipboard.", "copy"),
            ("Save &Page As ...", self.OnSavePage,
             "Save the content of the currently shown page to a file.",
             "savePage")
        ]
        simMenu = [
            ("&New Simulation ...", self.OnNewSim, "Setup a new simulation.", 
             "new"),
            ("&Edit Simulation ...", self.OnEditSim,
             "Edit the setup of the current simulation.", "edit"),
            ("&Continue Simulation", self.OnContinueSim,
             "Continue the simulation for as many more generations as "+\
             "already been calculated.", "continue"),
            None
        ]
        helpMenu = [
            ("&Help ...", self.OnHelp, "Show program documentation", "help"),
            ("&License ...", self.OnLicense, "Show license information", ""),
            None,
            ("&About ...", self.OnAbout, "Show copyright info", "")
        ]
        menuList = [
            ("&File", fileMenu),
            ("&Edit", editMenu),
            ("Si&mulation", simMenu),
            ("&Help", helpMenu)
        ]
        self.PAGE_TNMT = "Tournament"        
        self.PAGE_ECO = "Ecological Simulation"
        self.PAGE_SIMPLEX = "Simplex Diagram"
        self.PAGE_USER = "User Defined Strategies"
        self.nbHelpTexts = { self.PAGE_TNMT : "Full log file of the tournament.",
                             self.PAGE_ECO :
                             "Graph of the population dynamical simulation "+\
                             "with a given (usually equally distributed) "+\
                             "starting population.",
                             self.PAGE_SIMPLEX :
                             "Simplex Diagram showing the populational "+\
                             "dynamics of the system of three strategies "+\
                             "for different starting populations.",
                             self.PAGE_USER :
                             "Here you can enter your own strategies.""" }

        self.models = gatherModels()
        self.models["Simple Example"] = exampleModel
        self.simMenuIDs = {}
        
        self.simSetup = self.models["Simple Example"]
        self.hasUnsaved = False
        self.fileName = ""
        
        self.progressDialog = None       
        
        wx.Frame.__init__(self, id=wx.NewId(), name='', parent=None,
                size=wx.Size(760, 560), style=wx.DEFAULT_FRAME_STYLE,
                title="CoopSim: A Computer Simulation of the Evolution of Cooperation")

        self.busyCursor = False
        self.statusBar = wx.StatusBar(self, -1)
        self.statusBar.SetFieldsCount(2)
        self.statusBar.SetStatusText("", 0)
        self.statusBar.SetStatusText("Ready.", 1)
        self.SetStatusBar(self.statusBar)
        self.statusBar.SetStatusWidths([-1,140])

        self.toolBar = wx.ToolBar(self, -1, wx.DefaultPosition, wx.DefaultSize,
                                  wx.TB_HORIZONTAL|wx.TB_FLAT)
        self.toolBar.SetToolBitmapSize(wx.Size(20, 20))
        self.menuBar = wx.MenuBar()
        for menuName, menuDesc in menuList:
            menu = wx.Menu()
            if menuName == "Si&mulation":  self.simMenu = menu
            for entry in menuDesc:
                if entry:
                    name, event, helpText, icon = entry
                    mid = wx.NewId()
                    item = wx.MenuItem(menu, mid, name, helpText, 0)
                    menu.AppendItem(item)
                    wx.EVT_MENU(self, mid, event)
                    if icon:
                        toolTipStr = filter(lambda ch: ch != "&", name)
                        #bitmap = wx.Bitmap(sys.path[0]+"/icons/"+icon+".png", 
                        #                   wx.BITMAP_TYPE_PNG)
                        bitmap = wx.BitmapFromXPMData(icons.Dict[icon])
                        self.toolBar.AddTool(mid, bitmap,
                                             shortHelpString = toolTipStr,
                                             longHelpString = helpText)
                else:  menu.AppendSeparator()
            if menuName != "&Help":  self.toolBar.AddSeparator()
            self.menuBar.Append(menu, menuName)
        self.SetMenuBar(self.menuBar)
        self.redoModelsMenu()        
        self.toolBar.Realize()
        self.SetToolBar(self.toolBar)

        self.noteBook = wx.Notebook(self, wx.NewId(), style=wx.NB_TOP)
        self.lastPage = self.PAGE_TNMT
        self.currentPage = self.PAGE_TNMT
        
        self.logPanel = wx.Panel(self.noteBook, -1)
        self.noteBook.AddPage(self.logPanel, self.PAGE_TNMT)
        self.logBook = wxHtmlWindow(self.logPanel, -1,
                                    style=wxHW_SCROLLBAR_AUTO)
        sizer = wx.BoxSizer()
        sizer.Add(self.logBook, 1, wx.EXPAND)
        self.logPanel.SetSizer(sizer)
        self.log = Logging.HTMLLog()
    
        self.graphPanel = wx.Panel(self.noteBook, -1)
        self.noteBook.AddPage(self.graphPanel, self.PAGE_ECO)
        self.graphBitmap = wx.EmptyBitmap(800, 600)
        self.graphDC = wx.BufferedDC(None, self.graphBitmap)
        self.graphDriver = wxGfx.Driver(self.graphDC)
        self.graph = Graph.Cartesian(self.graphDriver,
            0, 0.0, 50, 1.0,
            "Population dynamical simulation of the reiterated "+\
            "Prisoners Dilemma", "Generations", "Population")
        wx.EVT_PAINT(self.graphPanel, self.OnGraphPaint)        

        self.simplexPanel = wx.Panel(self.noteBook, -1)
        self.noteBook.AddPage(self.simplexPanel, self.PAGE_SIMPLEX)
        self.simplexBitmap = wx.EmptyBitmap(800, 600)
        self.simplexDC = wx.BufferedDC(None, self.simplexBitmap)
        self.simplexDriver = wxGfx.Driver(self.simplexDC)
        self.simplex = Simplex.Diagram(self.simplexDriver, lambda p:p,
            "Simplex diagram of the population dynamics of the "+\
            "reiterated Prisoners Dilemma",
            "Strategy 1", "Strategy 2", "Strategy 3",
             styleFlags = SIMPLEX_FLAVOR, raster=pickSimplexRaster())
        self.simplexPending = SIMPLEX_REDRAW
        wx.EVT_PAINT(self.simplexPanel, self.OnSimplexPaint)

        self.progPanel = wx.Panel(self.noteBook, -1)
        if not DISABLE_USER_STRATEGIES:
            self.noteBook.AddPage(self.progPanel, self.PAGE_USER)
        ffont = wx.Font(12, wx.MODERN, wx.NORMAL, wx.NORMAL)
        tAttr = wx.TextAttr(wx.Colour(0,0,0))
        tAttr.SetFont(ffont)
        self.progEditor = wx.TextCtrl(self.progPanel, -1,
            style=wx.TE_MULTILINE|wx.TE_DONTWRAP|wx.TE_RICH)
        self.progEditor.SetDefaultStyle(tAttr)
        self.progEditor.AppendText(EmptyUserStrategiesPy)
        self.progEditor.SetInsertionPoint(0)
        sizer = wx.BoxSizer()
        sizer.Add(self.progEditor, 1, wx.EXPAND)
        self.progPanel.SetSizer(sizer)
        
        wx.EVT_NOTEBOOK_PAGE_CHANGED(self.noteBook, -1, self.OnNotebook)        

        # self.resizeFlag = False
        self.selectNB = -1
        wx.EVT_SIZE(self, self.OnSize)
        # Due to a bug (?) of the Linux/Gtk version of wxWidgets 2.4.2
        # the use of a timer is necessary for redraw after resize !
        timerId = wx.NewId()
        self.redrawTimer = wx.Timer(self, timerId)
        wx.EVT_TIMER(self, timerId, self.OnTimer)
        self.initFlag = True
        wx.EVT_IDLE(self, self.OnIdle)
        wx.EVT_CLOSE(self, self.OnExit)
        
        self.simulation = Simulation.Simulation(self.graph, self.simplex,
                                                self.log, self)
        self.clearUnsavedFlag()

    def checkUnsaved(self):
        return self.hasUnsaved or self.progEditor.IsModified()
    
    def clearUnsavedFlag(self):
        self.hasUnsaved = False
        self.progEditor.DiscardEdits()
        
    def progressIndicator(self, f, title = "Please wait...", 
                          message = "Determining payoff table..."):
        if self.progressDialog == None:
            if f < 0.999:
                self.progressDialog = wx.ProgressDialog(title, message,
                                                        1000, self, 0)
        elif f >= 0.999:
            self.progressDialog.Destroy()
            self.progressDialog = None
        else:
            self.progressDialog.Update(int(f*1000))

    def redoModelsMenu(self):
        itemList = self.simMenu.GetMenuItems()
        for item in itemList[4:]:  self.simMenu.Remove(item.GetId())
        modelNames = self.models.keys()
        modelNames.sort()
        self.simMenuIds = {}
        for name in modelNames:
            mid = wx.NewId()
            self.simMenuIds[mid] = name
            item = wx.MenuItem(self.simMenu, mid, name, "", wx.ITEM_CHECK)            
            self.simMenu.AppendItem(item)
            if name == self.simSetup.name:  item.Check(True)
            wx.EVT_MENU(self, mid, self.OnPickModel)
        self.simMenu.AppendSeparator()
        mid = wx.NewId()
        item = wx.MenuItem(self.simMenu, mid, "&Remove Models ...",
                 "Remove one or more of the simulation models from list.", 0)
        self.simMenu.AppendItem(item)
        wx.EVT_MENU(self, mid, self.OnRemoveModels)
    
    def updateLog(self, logStr):
        self.logBook.SetPage(re.sub("<img.*?>","",logStr))

    def appendLog(self, logStr):
        self.logBook.AppendToPage(re.sub("<img.*?>","",logStr))
        
    def logToStart(self):
        self.logBook.Scroll(0, 0)
        
    def statusBarHint(self, hint):
        self.statusBar.SetStatusText(hint, 1)
        if hint == "Ready.":
            if self.busyCursor:
                wx.EndBusyCursor()
                self.busyCursor = False
        elif not self.busyCursor:
            wx.BeginBusyCursor()
            self.busyCursor = True
        self.statusBar.Refresh()
        self.statusBar.Update()

    def elimStaleModels(self):
        strategyDict = {}
        for s in gatherStrategies():  strategyDict[str(s)] = s    
        remKeys = []
        for key, model in self.models.items():
            try:
                sl = [strategyDict[str(s)] for s in model.strategyList]
            except KeyError:
                remKeys.append(key)
            else:
                model.strategyList = sl
        for key in remKeys:  del self.models[key]
        if remKeys != []:
            dialog = wx.MessageDialog(self,
                "The following models have been eliminated from\n"\
                "the models list, because they refer to strategies\n"\
                "that are not any more existant:\n"+"\n".join(remKeys),
                "Alert", wx.OK|wx.ICON_INFORMATION)
            dialog.ShowModal()
            dialog.Destroy()
        self.redoModelsMenu()   
        
    def interpretCustomCode(self):
        global dirUserStrategies, UserStrategies, SIMPLEX_FLAVOR
        self.statusBarHint("Evaluating...")
        error_flag = False; updateSimplexFlag = False; returnValue = True
        code = self.progEditor.GetValue()
        try:
            f = file(os.path.expanduser("~")+"/UserStrategies.py", "w")
            f.write(code)
            f.close()
            if "UserStrategies" in sys.modules.keys():
                del sys.modules["UserStrategies"]
            import UserStrategies
            # reload(UserStrategies) did not work, why?
        except IOError,(errno, strerr):
            dialog = wx.MessageDialog(self, "IOError(%s): %s while processing "\
                                      "custom code"%(errno,strerr),
                                      "Error", wx.OK|wx.ICON_ERROR)
            dialog.ShowModal()
            dialog.Destroy()
            returnValue = False
        except SyntaxError:
            ei = sys.exc_info()
            error_flag = True
            error_string = str(ei[0])+": "+str(ei[1])
            error_lineno = ei[1].lineno
            lines = code.splitlines()
            if error_lineno <= len(lines) and error_lineno > 0:
                error_line = lines[error_lineno-1]
        except:
            ei = sys.exc_info()
            error_flag = True
            error_string = str(ei[0])+": "+str(ei[1])
            error_lineno = 0
            error_line = "?"
            
        if error_flag:
            if sys.modules.has_key("UserStrategies"):
                del sys.modules["UserStrategies"]
            dirUserStrategies = []
            dialog = wx.MessageDialog(self,
                error_string+"\n"+\
                "Line "+str(error_lineno)+": "+error_line[:60]+"\n"+\
                "Would you like to change to the program editor?",
                "Error in user program", wx.YES_NO|wx.CANCEL|wx.ICON_ERROR)
            res = dialog.ShowModal()
            dialog.Destroy()
            if res == wx.ID_YES:
                self.selectNB = 3
                returnValue = False
            else:  returnValue = True
        else:
            dirUserStrategies = ["UserStrategies."+token \
                                 for token in dir(UserStrategies)]
            if CUSTOMIZED_COOPSIM:
                dirUserStrategies.extend(["Customized."+token \
                                          for token in dir(Customized)])
            try:
                if SIMPLEX_FLAVOR != UserStrategies.SIMPLEX_FLAVOR:
                    SIMPLEX_FLAVOR = UserStrategies.SIMPLEX_FLAVOR
                    self.simplex.setStyle(SIMPLEX_FLAVOR)
                    self.simplex.setRaster(pickSimplexRaster())
                    updateSimplexFlag = True
            except AttributeError: pass 

        self.models.update(gatherModels())
        self.elimStaleModels()          
        if not self.simSetup.name in self.models.keys():  
            self.simSetup = exampleModel
            self.simulation.newSetup(self.simSetup, self.progressIndicator)
            self.continueSim()   
        elif self.simSetup != self.models[self.simSetup.name]:
            self.simSetup = self.models[self.simSetup.name]
            self.simulation.newSetup(self.simSetup, self.progressIndicator)
            self.continueSim()
        else:
            self.simSetup = self.models[self.simSetup.name]
            if updateSimplexFlag:
                self.simplexPending |= SIMPLEX_REDRAW
                self.updateSimplex()
        self.statusBarHint("Ready.")            
        return returnValue

    def saveState(self, fileName):
        try:
            self.progressIndicator(0.0, message="Saving simulation state...")
            f = ZIPFile(fileName, "w")
            pickle.dump(self.progEditor.GetValue(), f)
            self.progressIndicator(0.2)
            pickle.dump(self.models, f)
            self.progressIndicator(0.8)
            pickle.dump(self.simSetup, f)
            f.close()
            self.clearUnsavedFlag()
            self.progressIndicator(1.0)
        except IOError,(errno, strerr):
            dialog = wx.MessageDialog(self, "IOError(%s): %s"%(errno,strerr),
                                      "Error", wx.OK|wx.ICON_ERROR)
            dialog.ShowModal()
            dialog.Destroy()

    def loadState(self, fileName):
        try:
            if fileName.endswith(".txt") or fileName.endswith(".py"):
                self.progressIndicator(0.0, message="Loading custom code...")
                f = file(fileName, "r")
                customCode = f.read()
                self.progEditor.Clear()
                self.progEditor.AppendText(customCode)
                f.close()
                self.interpretCustomCode()
            else:
                self.progressIndicator(0.0,
                                       message="Loading simulation state...")
                f = ZIPFile(fileName, "r")
                customCode = pickle.load(f)
                self.progEditor.Clear()
                self.progEditor.AppendText(customCode)
                self.progressIndicator(0.2)
                self.models = pickle.load(f)
                self.progressIndicator(0.8)
                self.simSetup = pickle.load(f)
                f.close()            
                self.interpretCustomCode()
                self.simulation.newSetup(self.simSetup, self.progressIndicator)
                self.clearUnsavedFlag()
                # self.continueSim()  
            self.progressIndicator(1.0)
        except IOError,(errno, strerr):
            dialog = wx.MessageDialog(self, "IOError(%s): %s"%(errno,strerr),
                                      "Error", wx.OK|wx.ICON_ERROR)
            dialog.ShowModal()
            dialog.Destroy()
        except EOFError:
            dialog = wx.MessageDialog(self, "Unexpected end of file!",
                                      "Error", wx.OK|wx.ICON_ERROR)
            dialog.ShowModal()
            dialog.Destroy()        

    def updateGraph(self, destDC = None):
        if self.currentPage == self.PAGE_ECO:
            if not destDC: destDC = wx.ClientDC(self.graphPanel)
            w,h = self.graphDC.GetSizeTuple()
            destDC.Blit(0, 0, w, h, self.graphDC, 0, 0) 
        
    def updateSimplex(self, destDC = None):
        if self.currentPage == self.PAGE_SIMPLEX:
            if not destDC: destDC = wx.ClientDC(self.simplexPanel)
            if self.simplexPending == SIMPLEX_REDRAW:
                self.statusBarHint("Running...")                
                self.simplex.redraw()
            elif self.simplexPending == SIMPLEX_RESIZE:
                self.statusBarHint("Running...")                
                self.simplex.resizedGfx()
            self.statusBarHint("Ready.")
            self.simplexPending = SIMPLEX_DO_NOTHING
            w,h = self.simplexDC.GetSizeTuple()
            destDC.Blit(0, 0, w, h, self.simplexDC, 0, 0)
       
    def OnTimer(self, event):
        oldGS = self.graphDC.GetSize()
        oldSS = self.simplexDC.GetSize()
        GS = self.graphPanel.GetClientSizeTuple()
        SS = self.simplexPanel.GetClientSizeTuple()
        if GS == oldGS and SS == oldSS:  self.redrawTimer.Stop()
        else:
            if GS != oldGS:
                w,h = GS
                self.graphBitmap = wx.EmptyBitmap(w, h)
                self.graphDC = wx.BufferedDC(None, self.graphBitmap)
                self.graphDriver.changeDC(self.graphDC)
                self.graph.resizedGfx()
                self.updateGraph()                
            if SS != oldSS:
                w,h = SS
                self.simplexBitmap = wx.EmptyBitmap(w, h)
                self.simplexDC = wx.BufferedDC(None, self.simplexBitmap)
                self.simplexDriver.changeDC(self.simplexDC)            
                self.simplexPending = SIMPLEX_RESIZE
                self.updateSimplex()
            
    def OnIdle(self, event):
        if self.initFlag:
            # wxGtk Bug (?) workaround; otherwise the graphic panels
            # are not visible in the beginning
            self.noteBook.SetSelection(1)
            self.noteBook.SetSelection(2)
            self.SetSize(wx.Size(800,600))
            self.noteBook.SetSelection(0)
            self.initFlag = False
            return               
        if self.selectNB >= 0:
            self.noteBook.SetSelection(self.selectNB)
            self.selectNB = -1        

    def OnSimplexPaint(self, event):
        self.updateSimplex(wx.PaintDC(event.GetEventObject()))
        event.Skip()

    def OnGraphPaint(self, event):
        self.updateGraph(wx.PaintDC(event.GetEventObject()))
        event.Skip()        

    def OnSize(self, event):
        self.redrawTimer.Start(100, wx.TIMER_CONTINUOUS)
        event.Skip()

    def OnNotebook(self, event):
        nb = event.GetSelection()
        if nb >= 0:
            pstr = self.noteBook.GetPageText(nb)
            self.lastPage = self.currentPage
            self.currentPage = pstr
            self.statusBar.SetStatusText(self.nbHelpTexts[pstr])
        event.Skip()
        if self.lastPage == self.PAGE_USER and \
           self.currentPage != self.PAGE_USER:
            self.interpretCustomCode()

    def OnNew(self, event):
        if self.checkUnsaved():
            dialog = wx.MessageDialog(self, 
                                      "Do you really want to start a new\n"+\
                                      "simulation series? All changes will\n"+\
                                      "be lost!", "Warning", 
                                      wx.YES_NO|wx.CANCEL|wx.ICON_QUESTION)
            result = dialog.ShowModal()
            dialog.Destroy()
            if result != wx.ID_YES:  return
        self.updateLog("")
        self.progEditor.Clear()
        self.progEditor.AppendText(EmptyUserStrategiesPy)
        self.progEditor.SetInsertionPoint(0)
        self.models = gatherModels()
        self.models["Simple Example"] = exampleModel
        self.simSetup = self.models["Simple Example"]
        self.simulation.newSetup(self.simSetup, self.progressIndicator)
        self.redoModelsMenu()
        self.clearUnsavedFlag()
        self.updateGraph()

    def OnOpen(self, event):
        if self.checkUnsaved():
            dialog = wx.MessageDialog(self, 
                                      "Do you really want to open an existing\n"\
                                      "simulation series? All changes will\n"\
                                      "be lost!", "Warning", 
                                      wx.YES_NO|wx.CANCEL|wx.ICON_QUESTION)
            result = dialog.ShowModal()
            dialog.Destroy()
            if result != wx.ID_YES:  return
        dialog = wx.FileDialog(self, "Open Simulation", os.getcwd(), "",
                               "CoopSim Files (*.sim)|*.sim|" +\
                               "Python Code (*.py)|*.py|All Files (*)|*",
                               wx.OPEN|wx.CHANGE_DIR)
        if dialog.ShowModal() == wx.ID_OK:
            self.fileName = dialog.GetFilename()
            self.loadState(self.fileName)
        dialog.Destroy()
            
    def OnSave(self, event):
        if self.fileName == "":  self.OnSaveAs(event)
        else:  self.saveState(self.fileName)

    def saveAsDialog(self, title, fileExt):
        wildcard = reduce(lambda a,b: a+"|"+b+"|*"+b, fileExt, "")[1:]
        dialog = wx.FileDialog(self, title, os.getcwd(), self.simSetup.fname(),
                               wildcard, wx.SAVE|wx.CHANGE_DIR)
        if dialog.ShowModal() == wx.ID_OK:
            fileName = dialog.GetFilename()
            dialog.Destroy()
            base, ext = os.path.splitext(fileName)
            fileName = base + fileExt[dialog.GetFilterIndex()]
            try:
                f = file(fileName, "r")
                f.close()
                dialog = wx.MessageDialog(self, 
                   "File '%s' already exists! Do you really want to\n"\
                   "overwrite file '%s' ?" % (fileName, fileName),
                   "Warning", wx.YES_NO|wx.CANCEL|wx.ICON_QUESTION)
                result = dialog.ShowModal()
                dialog.Destroy()
                if result == wx.ID_YES:  return fileName
            except IOError:
                return fileName
        else:
            dialog.Destroy()
            return ""

    def OnSaveAs(self, event):
        fName = self.saveAsDialog("Save Simulation", [".sim"])
        if fName != "":
            self.fileName = fName
            self.saveState(fName)

    def OnExit(self, event):
        if self.checkUnsaved():
            dialog = wx.MessageDialog(self, 
                "The program contains unsaved data!\n"\
                "Do you really want to quit ?",
                "Really Quit", wx.YES_NO|wx.CANCEL|wx.ICON_QUESTION)
            result = dialog.ShowModal()
            dialog.Destroy()
            if result != wx.ID_YES: return        
        self.noteBook.SetSelection(0)
        wx.EVT_CLOSE(self, None)
        self.Close(True)
        

    def redrawInBuffer(self, w = SAVE_IMAGE_WIDTH, h = SAVE_IMAGE_HEIGHT):
        if w == AUTO_IMAGE_WIDTH or h == AUTO_IMAGE_HEIGHT:
            if self.currentPage == self.PAGE_ECO:
                w, h = self.graphDriver.getSize()
            else: w, h = self.simplexDriver.getSize()
        buf = wx.EmptyBitmap(w, h)
        gd = wxGfx.Driver(wx.BufferedDC(None, buf))
        if self.currentPage == self.PAGE_ECO:
            self.graph.changeGfx(gd)
        elif self.currentPage == self.PAGE_SIMPLEX:
            self.simplex.changeGfx(gd)
        return buf

    def redrawAsPostscript(self, postscriptGd):
        if self.currentPage == self.PAGE_ECO:
            self.graph.changeGfx(postscriptGd)
        elif self.currentPage == self.PAGE_SIMPLEX:
            self.simplex.changeGfx(postscriptGd)

    def restoreGfx(self):
        if self.currentPage == self.PAGE_ECO:
            self.graph.changeGfx(self.graphDriver)
        elif self.currentPage == self.PAGE_SIMPLEX:
            self.simplex.changeGfx(self.simplexDriver)

    def dumpHTMLImages(self, w = SAVE_IMAGE_WIDTH, h = SAVE_IMAGE_HEIGHT):
        try:
            os.mkdir(self.simulation.imgdirName)
        except OSError, errobj: # catch dir exists error
            if errobj.errno != 17:  raise OSError, errobj
        N = float(len(self.simulation.rangeStack)+1); count = 1
        msg = "Writing images for HTML page..."
        self.progressIndicator(0.0, message = msg)
        buf = wx.EmptyBitmap(w, h)
        buf2 = wx.EmptyBitmap(HTML_IMAGE_WIDTH, HTML_IMAGE_HEIGHT)
        gd = wxGfx.Driver(wx.BufferedDC(None, buf))
        gd2 = wxGfx.Driver(wx.BufferedDC(None, buf2))
        if len(self.simSetup.strategyList) == 3:
            self.simplex.changeGfx(gd)
            image = wx.ImageFromBitmap(buf)
            path = self.simulation.imgdirName+"/"+self.simulation.simplexName
            image.SaveFile(path+".png", wx.BITMAP_TYPE_PNG)
            image.Destroy()
            self.progressIndicator(0.5/N, message = msg)         
            self.simplex.changeGfx(gd2)
            image = wx.ImageFromBitmap(buf2)
            image.SaveFile(path+"_web.png", wx.BITMAP_TYPE_PNG)
            image.Destroy()
            self.simplex.changeGfx(self.simplexDriver)
        self.progressIndicator(1.0/N, message = msg)        
        for imgName, x1, y1, x2, y2 in self.simulation.rangeStack:
            self.graph.adjustRange(x1, y1, x2, y2)
            self.graph.changeGfx(gd)            
            image = wx.ImageFromBitmap(buf)
            path = self.simulation.imgdirName + "/" + imgName
            image.SaveFile(path+".png", wx.BITMAP_TYPE_PNG)
            image.Destroy()
            self.progressIndicator((count+0.5)/N, message = msg)
            self.graph.changeGfx(gd2)
            image = wx.ImageFromBitmap(buf2)
            image.SaveFile(path+"_web.png", wx.BITMAP_TYPE_PNG)
            image.Destroy()
            count += 1; self.progressIndicator(count/N, message = msg)
        self.graph.changeGfx(self.graphDriver)
        self.progressIndicator(1.0, message = msg)
        
    def toClipboard(self, data):
        if wx.TheClipboard.Open():
            wx.TheClipboard.AddData(data)
            wx.TheClipboard.Flush()
            wx.TheClipboard.Close()
        else:
            dialog = wx.MessageDialog(self,
                "Sorry, couldn't copy data! Clipboard not available.",
                "Error", wx.OK|wx.ICON_ERROR)
            dialog.ShowModal()
            dialog.Destroy()

    def OnCopy(self, event):
        if self.currentPage == self.PAGE_ECO or \
           self.currentPage == self.PAGE_SIMPLEX:
            data = wx.BitmapDataObject(self.redrawInBuffer())
            self.toClipboard(data)
            self.restoreGfx()
        elif self.currentPage == self.PAGE_TNMT:
##            data = wx.TextDataObject(self.logBook.GetValue())
            data = wx.TextDataObject(self.log.getASCIIPage())
            self.toClipboard(data)
        elif self.currentPage == self.PAGE_USER:
            data = wx.TextDataObject(self.progEditor.GetValue())
            self.toClipboard(data)

    def OnSavePage(self, event):
        if self.currentPage == self.PAGE_ECO or \
           self.currentPage == self.PAGE_SIMPLEX:
            fName = self.saveAsDialog('Save "'+self.currentPage+\
                                  '" as ...', [".png",".jpg", ".eps"])
            if fName != "":
                if fName[-4:] == ".eps":
                    try:
                        psgd = psGfx.Driver()
                        self.redrawAsPostscript(psgd)                       
                        psgd.save(fName)
                    except IOError,(errno, strerr):
                        dialog = wx.MessageDialog(self, "IOError(%s): %s" % \
                                                  (errno,strerr), "Error",
                                                  wx.OK|wx.ICON_ERROR)
                        dialog.ShowModal()
                        dialog.Destroy()
                    self.restoreGfx()                         
                else:
                    image = wx.ImageFromBitmap(self.redrawInBuffer())
                    if fName[-4:] == ".jpg": ftype = wx.BITMAP_TYPE_JPEG
                    else: ftype = wx.BITMAP_TYPE_PNG
                    image.SaveFile(fName, ftype)
                    self.restoreGfx()
                    image.Destroy()
        else:
            if self.currentPage == self.PAGE_TNMT:
                fName = self.saveAsDialog('Save "'+self.currentPage+\
                                          '" as ...', [".html", ".txt"])
##                text = self.logBook.GetValue()
                if fName[-5:] == ".html":
                    text = self.log.getHTMLPage()
                    self.dumpHTMLImages()
                else: text = self.log.getASCIIPage()                
            elif self.currentPage == self.PAGE_USER:
                text = self.progEditor.GetValue()
                fName = self.saveAsDialog('Save "'+self.currentPage+\
                                          '" as ...', [".py"])                
            else:  return
            if fName != "":
                try:
                    f = file(fName, "w")
                    f.write(text)
                    f.close()
                except IOError,(errno, strerr):
                    dialog = wx.MessageDialog(self,
                        "IOError(%s): %s" % (errno,strerr),
                        "Error", wx.OK|wx.ICON_ERROR)
                    dialog.ShowModal()
                    dialog.Destroy()

    def continueSim(self):
        self.statusBarHint("Running...")
        self.simulation.continueSim(refreshCallback = self.updateGraph,
                                    withSimplex = False)
        self.statusBarHint("Ready.")
        if self.simulation.updateSimplexFlag:
            self.simplexPending |= SIMPLEX_REDRAW
        self.updateGraph(); self.updateSimplex()        

    def OnNewSim(self, event):
        def fixNewName():
            name = self.simSetup.name.rstrip()
            l = name.split(" ")
            if l[-1].isdigit():
                i = int(l[-1]); name = " ".join(l[:-1])
            else: i = 2
            base_name = name
            while self.models.has_key(name):  
                name = base_name+" "+str(i); i += 1
            return name
        if self.currentPage == self.PAGE_USER:
            if not self.interpretCustomCode(): return
        if self.simSetup._userDefined:
            dialog = wx.MessageDialog(self, 
                        "You are going to create a new simulation\n"+\
                        "setup based on a user defined setup. The \n"+\
                        "attributes: mutators, demes and population,\n"+\
                        "can not be edited in the setup dialog\n"+\
                        "setup dialog. These attributes will therefore\n"+\
                        "be reseted to their default values! Only the\n"+\
                        "attributes payoff and iterations will be kept.",
                        "Alert", 
                        wx.OK|wx.ICON_WARNING)
            dialog.ShowModal()
            dialog.Destroy()
        dialog = SetupDialog(self, self.simSetup, fixNewName())
        result = dialog.ShowModal()
        dialog.Destroy()
        if result == wx.ID_OK:
            self.simSetup = dialog.GetValue()
            self.simSetup.name = fixNewName()
            self.models[self.simSetup.name] = self.simSetup
            self.redoModelsMenu()
            self.statusBarHint("Running...")
            # print self.simSetup._payoffArray
            self.simulation.newSetup(self.simSetup, self.progressIndicator)
            self.statusBarHint("Ready.")            
            self.continueSim()
            self.hasUnsaved = True

    def OnEditSim(self, event):
        if self.currentPage == self.PAGE_USER:
            if not self.interpretCustomCode(): return
        if self.simSetup._userDefined:
            dialog = wx.MessageDialog(self, 
                        "Simulation setup: '%s' is a\n" % \
                        self.simSetup.name + \
                        "user defined simulation setup! User defined\n"+\
                        "setups can not be edited with the setup dialog!\n"+\
                        "To create a new simulation setup based on the\n"+\
                        "current user setup, select 'New Simulation' in\n"+\
                        "the 'Simulation' menu.",
                        "Alert", 
                        wx.OK|wx.ICON_ERROR)
            dialog.ShowModal()
            dialog.Destroy()
            return        
        name = self.simSetup.name
        dialog = SetupDialog(self, self.simSetup, self.simSetup.name)
        result = dialog.ShowModal()
        dialog.Destroy()
        if result == wx.ID_OK:
            self.simSetup = dialog.GetValue()
            if self.models.has_key(name):  del self.models[name]
            self.models[self.simSetup.name] = self.simSetup
            self.redoModelsMenu()
            self.statusBarHint("Running...")            
            self.simulation.newSetup(self.simSetup, self.progressIndicator)
            self.statusBarHint("Ready.")            
            self.continueSim()
            self.hasUnsaved = True

    def OnContinueSim(self, event):
        if not self.simulation.setup:
            self.statusBarHint("Running...")
            self.simulation.newSetup(self.simSetup, self.progressIndicator)
            self.statusBarHint("Ready.")
        self.continueSim()

    def OnPickModel(self, event):    
        mid = event.GetId()
        for item  in self.simMenu.GetMenuItems():
            if item.IsCheckable() and item.IsChecked(): item.Check(False)
        self.simMenu.Check(mid, True)
        self.simSetup = self.models[self.simMenuIds[mid]]
        self.statusBarHint("Running...")        
        self.simulation.newSetup(self.simSetup, self.progressIndicator)
        self.statusBarHint("Ready.")        
        self.continueSim()

    def OnRemoveModels(self, event):
        lst = self.models.keys()
        if self.simSetup.name in lst: lst.remove(self.simSetup.name)
        lst.sort()
        dialog = wxMultipleChoiceDialog(self, "Select models to remove:",
                                        "Remove Models",lst)
        if dialog.ShowModal() == wx.ID_OK:
            lst = dialog.GetValueString()
            for modelName in lst:  del self.models[modelName]
            self.redoModelsMenu()
        dialog.Destroy()

    def OnHelp(self, event):
        pathes = [sys.path[0]+"/docs/CoopSim_Doc/index.html",
                  str(os.environ.get("_MEIPASS2"))+"/index.html"]
        for p in pathes:
            if os.path.exists(p):
                path = p
                break
        else: path = ""        
        dialog = HTMLHelpDialog(self, path)
        dialog.ShowModal()
        dialog.Destroy()
        
    def OnAbout(self, event):
        dialog = wxScrolledMessageDialog(self, __doc__, "About")
        dialog.ShowModal()
        dialog.Destroy()
       
    def OnLicense(self, event):
        pathes = [sys.path[0]+"/LICENSE.GPL",
                  sys.path[0]+"/license.gpl",
                  sys.path[0]+"/License.gpl",
                  str(os.environ.get("_MEIPASS2"))+"/LICENSE.GPL",
                  str(os.environ.get("_MEIPASS2"))+"/license.gpl",
                  str(os.environ.get("_MEIPASS2"))+"/License.gpl"]
        for p in pathes:
            if os.path.exists(p):
                path = p
                break
        else: path = ""
        try:
            f = file(path, "r")
            GPL = f.read()
            f.close()
        except IOError,(errno, strerr):
            dialog = wx.MessageDialog(self, "IOError(%s): %s"%(errno,strerr),
                                      "Error", wx.OK|wx.ICON_ERROR)
            dialog.ShowModal()
            dialog.Destroy()
            GPL = GPLMissingMessage
        dialog = wxScrolledMessageDialog(self, GPL, "License Information")
        dialog.ShowModal()
        dialog.Destroy()

    def SafeYield(self):
        wx.SafeYield(self, True)



class SimulationApp(wx.App):
    def OnInit(self):
        wx.InitAllImageHandlers()
        self.main = SimWindow()
        self.main.Show()
        self.SetTopWindow(self.main)
        return True


def main():
    application = SimulationApp(0)
    if CUSTOMIZED_COOPSIM and Customized.__dict__.has_key("main"):
        Customized.main(application.main)
    application.MainLoop()
    try:
        os.remove(os.path.expanduser("~/")+"UserStrategies.py")
        os.remove(os.path.expanduser("~/")+"UserStrategies.pyc")
    except OSError:
        pass # do not fail, if files did not exist

if __name__ == '__main__':
    main()
    

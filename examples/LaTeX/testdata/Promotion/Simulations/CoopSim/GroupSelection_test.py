#!/usr/bin/python
"""Test for module group selection.
"""

import gtk
from gtk import gdk
from PyPlotter import gtkGfx, gtkSupport, psGfx

import GroupSelection
from GroupSelection import *


########################################################################
#
# Strategy sets
#
########################################################################

strategy_mix = (Tester(), TitForTat(), Pavlov(), Grim(), Random(),
               Hawk(), Tranquillizer(), Dove(), Joss())
automata = tuple(genAllAutomata())
TFTs = tuple(genParameterizedTFTs(0.0, 1.0, 0.2, 0.0, 1.0, 0.2))
dove_hawk = (Dove(), Hawk())


########################################################################
#
# Simulation class
#
########################################################################


class GroupSimulation(object):
    def __init__(self, strategies, N, minSize, maxSize, reshapeInterval=10):
        self.reshapeInterval = reshapeInterval
        self.strategies = strategies
        self.N = N;  self.minSize = minSize;  self.maxSize = maxSize
        superdeme = PDDeme(self.strategies).spawn(N, minSize, maxSize)
        superdeme.name = "Aggregation"        
        # groupdeme = PDDeme(self.strategies).spawn(N, minSize, maxSize)
        groupdeme = copy.deepcopy(superdeme)
        groupdeme.name = "Group Selection"
        
        self.worlds = [None]*3;  self.views = [None]*4
        self.worlds[1] = superdeme
        self.worlds[0] = self.worlds[1].aggregate()
        self.worlds[0].name = "No Demes"
        self.worlds[2] = groupdeme
        
        self.views[0] = DemeView(self.worlds[0], Gfx.nilDriver(),
                                 "No Demes")
        self.views[1] = DemeView(self.worlds[1], Gfx.nilDriver(),
                                 "Simple Aggregation", weighted = False)
        self.views[2] = DemeView(self.worlds[1], Gfx.nilDriver(),
                                 "Weighted Aggregation", weighted = True)
        self.views[3] = DemeView(self.worlds[2], Gfx.nilDriver(),
                                 "Group Selection", weighted = True)
        self.win = gtkSupport.NotebookWindow([v.title for v in self.views],
                                             (800,600),
                                             "Cooperation & Group Selection")
        for v in self.views: self.win.addRedrawHook(v.title, v.redraw)
        for cv in self.win.pages.values():
            cv.canvas.connect("button-press-event", self.onMouseButton)
            cv.canvas.set_events(gdk.EXPOSURE_MASK|gdk.BUTTON_PRESS_MASK)        
        self.win.show()

    def evolution(self, generations=100):
        for i in xrange(generations):
            if i > 0 and i % self.reshapeInterval == 0:
                self.worlds[2].reshape(self.N, self.minSize, self.maxSize)
            for k in xrange(len(self.worlds)): self.worlds[k].replicate()
            for k in xrange(len(self.views)):  self.views[k].update()
            
    def onMouseButton(self, widget, event):
        if event.button == 2 or event.button == 3:
            dialog = gtk.FileChooserDialog(action = gtk.FILE_CHOOSER_ACTION_SAVE,
                                           buttons = ("Save", gtk.RESPONSE_OK,
                                                      "Cancel", gtk.RESPONSE_CANCEL))
            fltr = gtk.FileFilter()
            fltr.add_pattern("*.eps")
            fltr.set_name("EPS-Grafik")
            dialog.add_filter(fltr)
            if dialog.run() == gtk.RESPONSE_OK:
                fname = dialog.get_filename()
                if not fname.endswith(".eps"):  fname += ".eps"
                label = self.win.get_currentPage()
                for view in self.views:
                    if view.title == label: break
                else: raise AssertionError, "No page with label %s"%label
                ps = psGfx.Driver()
                view.redraw(ps)
                ps.save(fname)
            dialog.hide()
            dialog.destroy()            
##            dialog = gtk.FileChooserDialog(action = gtk.FILE_CHOOSER_ACTION_SAVE,
##                                           buttons = ("Save", gtk.RESPONSE_OK,
##                                                      "Cancel", gtk.RESPONSE_CANCEL))
##            fltr = gtk.FileFilter()
##            fltr.add_pattern("*.png")
##            fltr.set_name("PNG-Grafik")
##            dialog.add_filter(fltr)
##            if dialog.run() == gtk.RESPONSE_OK:
##                fname = dialog.get_filename()
##                if not fname.endswith(".png"):  fname += ".png"
##                self.win.savePage(name = fname)
##            dialog.hide()
##            dialog.destroy()
            
        

########################################################################
#
# Test
#
########################################################################

def printRankings(sim):
    for rank, name, share in sim.worlds[0].aggregate().ranking():
        print "%2i. %s %1.5f"%(rank, name.ljust(40), share)
    print "\n"+"-"*40+"\n"
    for rank, name, share in sim.worlds[1].aggregate(False).ranking():
        print "%2i. %s %1.5f"%(rank, name.ljust(40), share)
    print "\n"+"-"*40+"\n"
    for rank, name, share in sim.worlds[1].aggregate(True).ranking():
        print "%2i. %s %1.5f"%(rank, name.ljust(40), share)
    print "\n"+"-"*40+"\n"
    for rank, name, share in sim.worlds[2].aggregate(True).ranking():
        print "%2i. %s %1.5f"%(rank, name.ljust(40), share)           

def Test1():
    sim = GroupSimulation(automata, 100, 3, 7)
    sim.evolution()
    printRankings(sim)
    sim.win.waitUntilClosed()

def Test2():
    sim = GroupSimulation(dove_hawk, 25, 1, 2)
    sim.evolution()
    sim.win.waitUntilClosed()

def Test3():
    sim = GroupSimulation(dove_hawk, 25, 2, 2)
    sim.evolution(200)
    sim.win.waitUntilClosed()

def Test4():
    sim = GroupSimulation(strategy_mix, 100, 3,7)
    sim.evolution()
    printRankings(sim)
    sim.win.waitUntilClosed()

def Test5():
    sim = GroupSimulation(TFTs, 100, 3, 7)
    sim.evolution()
    printRankings(sim)
    sim.win.waitUntilClosed()

def Test6():
    sim = GroupSimulation((Tester(), Dove()), 25, 2, 2)
    sim.evolution()
    sim.win.waitUntilClosed()


def Test7():
    GroupSelection.PD_PAYOFF = array([[[1.0, 1.0], [5.9, 0.0]],\
                                      [[0.0, 5.9], [3.0, 3.0]]])
    sim = GroupSimulation((SignallingCheater(), Dove(), Grim(), TitForTat()), 10, 1, 3)
    sim.evolution(300)
    sim.win.waitUntilClosed()

def Test8():
    GroupSelection.PD_PAYOFF = array([[[1.0, 1.0], [5.9, 0.0]],\
                                      [[0.0, 5.9], [3.0, 3.0]]])
    sim = GroupSimulation((SignallingCheater(), Dove(), Grim(), TitForTat()), 10, 2, 3)
    sim.evolution(300)
    sim.win.waitUntilClosed()


if __name__ == "__main__":
#    Test1()
#    Test2()
    Test3()
#    Test4()
#    Test5()
#    Test6()
    Test7()
#    Test8()



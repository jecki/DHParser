# simulation setup and simulation objects

from __future__ import generators # retain python 2.2 compatibility
from decimal import *
import copy, re
from PyPlotter import Gfx, Colors
from PopulationDynamics import Dynamics
import PrisonersDilemma as PD
from PopulationDynamics.Compatibility import *
from Logging import H1,H2,H3, H1X,H2X,H3X, LogNotificationInterface, HTMLLog


NUM_GENERATIONS = 50 # number of generations to start with in the
                     # population dynamical simulation
NUM_SAMPLES = PD.NUM_SAMPLES # Samples to take of a match if randomizing
                             # strategies or in game noise is involved
NO_GRAPH_OPTIMIZATION = False # graph drawing will be slowed down but
                              # accuracy is increased to printing and saving 


###############################################################################
#
# classes for the description of simulation setups
#
###############################################################################


class Mutator(object):
    """Describes the mutation of a strategy in the simulation.
    
    original    = int: the ordinal number of the strategy that is going
                    to mutate
    mutated = int: the ordinal number of the startegy that 'original' is
                    going to mutate into 
    rate        = float [0.0 - 1.0]: mutation rate
    """
    def __eq__(self, other):
        if not isinstance(other, Mutator):  return False
        if self.original != other.original:  return False
        if self.mutated != other.mutated:  return False
        if self.rate != other.rate:  return False
        return True
        
    def __ne__(self, other):
        return not self.__eq__(other)
        
    def __init__(self, original, mutated, rate=0.01):
        self.original = original
        self.mutated = mutated
        self.rate = rate



class SimSetup(object):
    """Contains all data defining a simulation.
    
    name         = string: name of the model
    strategyList = list of Strategy objects: the list of the strategies
    population   = tuple: population share for each strategy
    correlation  = float [0.0-1.0]: correlation factor
    gameNoise    = float [0.0-1.0]: in game noise
    noise        = float [0.0-1.0]: evolutionary background noise
    iterations   = int:  number of iterations for one match
    samples      = int:  number of sample matches to take (only useful for 
                   randomizing strategies)
    payoff       = tuple of floats:  payoff tuple (T, R, P, S)
    mutators     = list of Mutator objects: description of possible
                    mutation of strategies during the course of the
                    evolutionary development.
    cachedPM     = cached payoff matrix
    cachedLog    = cached tournament log object
    """
    def __eq__(self, other):
        if not isinstance(other, SimSetup):  return False
        # names make no difference! if self.name != other.name:  return False
        if len(self.strategyList) != len(other.strategyList): 
            return False
        for i in xrange(len(self.strategyList)):
            if self.strategyList[i] != other.strategyList[i]:  return False
        if self.population != other.population:  return False
        if self.correlation != other.correlation:  return False
        if self.gameNoise != other.gameNoise:  return False
        if self.noise != other.noise:  return False
        if self.iterations != other.iterations:  return False
        if self.samples != other.samples: return False
        if self.payoff != other.payoff:  return False
        if len(self.mutators) != len(other.mutators):
            return False
        for i in xrange(len(self.mutators)):
            if self.mutators[i] != other.mutators[i]:  return False
        return True

    def __ne__(self, other):
        return not self.__eq__(other)

##    def __setattr__(self, name, value):
##        object.__setattr__(self, name, value)
##        if name == "population":
##            assert len(value) == len(self.strategyList),
##                   "population vector does not match length of strategy list!"
##        elif name == "strategyList":
##            if len(value) != len(self.population):
##                obejct.__setattr__(self, "population",
##                                   Dynamics.UniformDistribution(len(value)))
        
    def __init__(self, name, strategyList = [], population = None,
              correlation = 0.0, gameNoise = 0.0, noise = 0.0,
              iterations = 200, samples = NUM_SAMPLES, payoff = (5.,3.,1.,0.),
              mutators = [], PM = None, log = None):
        self.name = name
        self.strategyList = strategyList
        if population == None:
            self.population = Dynamics.UniformDistribution(len(self.strategyList))
        else: self.population = population
        self.correlation = correlation
        self.gameNoise = gameNoise
        self.noise = noise
        self.iterations = iterations
        self.samples = samples
        self.payoff = payoff
        self.mutators = mutators
        self.cachedPM = PM
        self.cachedLog = log
        self._userDefined = True # SimApp marks its own setups as False

    def fname(self):
        """Returns the name of the setup as a proper file name."""
        return self.name.replace("*","x").replace("?","x").replace("/","x")\
               .replace("\\","x").replace(" ","_")

    def htmlRepresentation(self):
        """Returns extensive information about this setup in HTML format."""
        def rr(s):
            "replace trailing zeros with blanks"
            l = len(s);  s2 = s.rstrip("0")
            return (s2 + "&nbsp;"*(l - len(s2)))
        html = ["<p>" + H2 + '<a name="setup"></a>Simulation setup of ' + \
                self.name + H2X + "<br />\n\n"]
##        t = "<b>Strategies:</b> "
##        for s in self.strategyList:
##            t += str(s)
##            if len(t) >= 70:
##                t += "<br />\n";  html.append(t);  t = ""
##            else:  t += ", "
##        if t != "": html.append(t[:-2]+"<br />\n")
        html.append("<b>Strategies:</b> ")
        snames = [str(s) for s in self.strategyList]
        html.append(", ".join(snames))
        html.append("<br /><br />\n\n<tt>")
        p0 = self.population[0]; scale = 1.0/(1000*len(self.population))
        for p in self.population:
            if abs(p - p0) > scale:
                pop = [rr("%1.5f"%s) for s in self.population]
                lines = [", ".join(pop[i:i+5]) for i in xrange(0,len(pop),5)]
                html.append("<b>population shares:</b><br />\n")
                html.append("<br />\n".join(lines))
                html.append("<br /><br />\n\n")     
                break
        else:
            html.append("uniform population distribution<br /><br />\n\n")
        if self.mutators != []:
            html.append("<b>mutations:</b><br />\n")
            for d in self.mutators:
                s1 = str(self.strategyList[d.original])
                s2 = str(self.strategyList[d.mutated])
                s1 += "&nbsp;" * max(20-len(s1), 1)
                s2 += "&nbsp;" * max(20-len(s2), 1)
                html.append(s1 + "=>&nbsp;" + s2 + "&nbsp;" + \
                            ("%1.5f" % d.rate).rstrip("0") + "<br />\n")
            html.append("<br />\n")
        if self.correlation != 0.0:
            html.append("correlation:"+"&nbsp;"*8+"%f<br />\n"%self.correlation)
        if self.gameNoise != 0.0:
            html.append("game Noise:"+"&nbsp;"*9+"%f<br />\n"%self.gameNoise)
        if self.noise != 0.0:
            html.append("evolutionary Noise:&nbsp;%f<br />\n"%self.noise)
        html.append("payoff parameters:&nbsp;&nbsp;" + \
                    str(self.payoff) + "<br />\n")
        html.append("iterations:"+"&nbsp;"*9+"%i<br />\n"%self.iterations)
        if self.gameNoise > 0.0 or \
           reduce(lambda a,b: a or b.randomizing, self.strategyList, True):
            html.append("match samples:"+"&nbsp;"*6+"%i<br />\n"%self.samples)
        html.append("</tt></p>\n")
        return "".join(html)

###############################################################################
#
# Simulation class
#
###############################################################################

# generator functions to optimize graph drawing

class xaxisIter(object):
    """-> iterate over virtual x-coordinates with one point for
    each screen pixel.
    """
    def __init__(self, graph, x1, x2):
        self.graph = graph
        a = self.graph._scaleX(x1);  b = self.graph._scaleX(x2)
        self.rngIter = xrange(a, b+2).__iter__()
        self.pos = self.graph._invX(self.rngIter.next())

    def check(self, x):
        if x >= self.pos:
            try:
                self.pos = self.graph._invX(self.rngIter.next())
            except StopIteration:
                pass # actually this should never happen, catching it anyway! 
            return True
        else: return NO_GRAPH_OPTIMIZATION


def mutation(population, degenList):
    """Apply mutation to a population"""
    p = list(population)
    for d in degenList:
        x = population[d.original] * d.rate
        p[d.original] -= x
        p[d.mutated] += x
    return tuple(p)


NORMAL_CAPTION_PEN = Gfx.BLACK_PEN
SMALL_CAPTION_PEN = Gfx.Pen(color = Gfx.BLACK, fsize = Gfx.SMALL)

class Simulation(object):
    """The simulation class is responsible for running a simulation
    and produing an output of the results in graphical form as well
    as as html log.

    Attributes:
        graph       : A Graph.Cartesian object for the graphical representation
                      of the population dynamics
        simlpex     : A Simplex.Diagram object for producing a simplex
                      diagram of the population dynamics (only if exactly
                      three strategies are present in the simulation!)
        notifier    : A Logging.LogNotificationInterface for communicating
                      the progress of the simulation to the GUI
        log         : A Logging.HTMLLog for logging the simulation results
        setup       : A copy (!) of the simulation setup. (The progress of
                      the population dynamical simulation is written into
                      the 'population' field of this copy)
        payoffMatrix: The payoff matrix of the tournament part of the
                      simulation
        dynamicsFunction: The dynamics function for the population dynamical
                      development
        rangeStack  : Sequence of the respective range parameters of the
                      simulation graph (x1,y1,x2,y2), one for each call
                      of the method 'continueSim'
        imgDirName  : Name of the directory to write the images of the html
                      log to (only if the log is actually saved to disk!)
        simplexName : file name of the simplex graph, if the html log is saved
        firstGeneration: the first generation to start the next population
                      dynamical cycle with (when calling continueSim)
        lastGeneration: the last generation of the next cycle
    """
    
    def __init__(self, graph, simplex, log, notifier):
        self.graph = graph
        self.simplex = simplex
        self.notifier = notifier
        self.log = log
        self.setup = None
        self.payoffMatrix = None
        self.dynamicsFunction = None
        self.rangeStack = []
        self.imgdirName = ""
        self.simplexName = ""
        self.firstGeneration = 1
        self.lastGeneration = NUM_GENERATIONS
        self._dontLogTwiceFlag = False

    def _prepareEvLog(self):
        if not self._alreadyLogged:
            self._alreadyLogged = True
            self.imgdirName = self.setup.fname() + "_images"
            self.log.appendAt("toc",
                '<a href="#evranking">4. Evolutionary Simulation</a><br />\n')
            self.log.append(H2 + \
                '<a name="evranking"></a>Evolutionary Simulation:' + \
                H2X + "<br />\n\n")
            if len(self.setup.strategyList) == 3:
                self.simplexName = self.setup.fname() + "_simplex"
                path = self.imgdirName + "/" + self.simplexName
                self.log.append('<div align="center">' + \
                                '<a href="'+path+'.png">' + \
                                '<img src="'+path+'_web.png" alt="Image: '+\
                                self.simplexName + '.png not found!" />' + \
                                '</a></div><br /><br />\n')
            self.log.entryPoint("evranking")
            

    def newSetup(self, setup, progressCallback = lambda f:1):
        self._alreadyLogged = False
        self.setup = copy.copy(setup)
        for s in self.setup.strategyList:  s.register(self.setup)          
        self.firstGeneration = 1;
        self.lastGeneration = NUM_GENERATIONS
        if self.setup.cachedPM == None:
            self.log.clear()
            self.log.pageTitle(self.setup.name)
            self.log.append(H1+'<a name="top"></a>CoopSim - Simulation: '+\
                            self.setup.name + H1X + "\n\n")
            self.log.append(H2+'<a name="toc"></a>Table of Contents'+ \
                            H2X + "\n\n<p>")
            self.log.append('<a href="#setup">0. Simulation Setup</a><br />\n')
            self.log.entryPoint("toc")
            self.log.append("</p><br />\n")            
            self.log.append(setup.htmlRepresentation())
            self.log.append('<div align="right"><a href="#top">[top]' + \
                            '</a></div><br />\n')            
            p = self.setup.payoff
            a = array([[[p[2],p[2]],[p[0],p[3]]],[[p[3],p[0]],[p[1],p[1]]]])
            self.payoffMatrix = PD.GenPayoffMatrix(self.setup.strategyList,
                                a, self.setup.iterations, self.setup.samples, 
                                self.setup.gameNoise,self.log,progressCallback)
            setup.cachedPM = self.payoffMatrix
            self.setup.cachedPM = setup.cachedPM
            setup.cachedLog = self.log.backup()
            self.setup.cachedLog = setup.cachedLog
        else:
            self.payoffMatrix = self.setup.cachedPM
            self.log.replay(self.setup.cachedLog)
        self.notifier.updateLog(self.log.getHTMLPage())

        ## want decimals ?
        setcontext(Context(prec=500))
        for x in xrange(len(self.setup.population)):
            for y in xrange(len(self.setup.population)):
                self.payoffMatrix[x, y] = Decimal(repr(self.payoffMatrix[x,y]))
        self.setup.correlation = Decimal(repr(self.setup.correlation))
        self.setup.noise = Decimal(repr(self.setup.noise))
        p = [Decimal(repr(x)) for x in self.setup.population]
        self.setup.population = tuple(p)
        ## end decimals
        
        df = Dynamics.GenDynamicsFunction(self.payoffMatrix,
                                          self.setup.correlation,
                                          self.setup.noise, 2)
        if self.setup.mutators == []:
            self.dynamicsFunction = df
        else:
            self.dynamicsFunction = lambda p: mutation(df(p), \
                                                  self.setup.mutators)

        ysize = 1.0 / max(1.0, len(self.setup.strategyList)-1)
        self.graph.reset(0, 0.0, self.lastGeneration, ysize)
        self.rangeStack = []
        i = 0
        for s in self.setup.strategyList:
            if Colors.colors[i] == (1.0, 1.0, 0.0):  i += 1
            self.graph.addPen(str(s), Gfx.Pen(Colors.colors[i], Gfx.MEDIUM),
                              False)
            i += 1
            if i > len(Colors.colors):  i = 0
        self.graph.setTitle('Population dynamics of "'+self.setup.name+'"')
        if len(self.setup.strategyList) > 10:
            self.graph.setStyle(captionPen = SMALL_CAPTION_PEN, redraw = False)
        else:
            self.graph.setStyle(captionPen = NORMAL_CAPTION_PEN, redraw = False)
        self.graph.redrawCaption()
        
        if len(self.setup.strategyList) == 3:
            self.simplex.setFunction(self.dynamicsFunction)            
            self.simplex.setTitle('Simplex diagram of "'+self.setup.name+'"')
            self.simplex.setLabels(str(self.setup.strategyList[0]),
                                   str(self.setup.strategyList[1]),
                                   str(self.setup.strategyList[2]))
        else:
            self.simplex.setFunction(lambda p:p)            
            if len(self.setup.strategyList) > 3:
                self.simplex.setTitle("Too many strategies for " + \
                                      "a simplex diagram!")
            else:
                self.simplex.setTitle("Too few strategies for "\
                                      "a simplex diagram!")
            self.simplex.setLabels("","","")
        self._prepareEvLog()


    def continueSim(self, record = None):
        if self.setup == None:  return
        self.notifier.statusBarHint("Running...")
        if self.firstGeneration > 1:
            self.graph.adjustRange(0, 0.0, self.lastGeneration, self.graph.y2)
        else:
            k = 0
            for s in self.setup.strategyList:
                self.graph.addValue(str(s), 0, float(self.setup.population[k]))
                k += 1
            #self.simplex.show()
        p = self.setup.population
        pixelSteps = xaxisIter(self.graph, self.firstGeneration,
                               self.lastGeneration)
        for i in xrange(self.firstGeneration, self.lastGeneration+1):
            p = self.dynamicsFunction(p)
            if pixelSteps.check(i):
                k = 0
                for s in self.setup.strategyList:
                    self.graph.addValue(str(s), i, float(p[k]))
                    k += 1
            if record != None: record.append(p)
        self.setup.population = p
        
        self._prepareEvLog()
        anchor = "generation%i" % self.lastGeneration
        linkstr = '&nbsp;&nbsp;&nbsp;&nbsp;<a href="#'+anchor+'">'+ \
                  'Ranking after %i generations</a>' % \
                  self.lastGeneration + "<br />\n"
        self.log.appendAt("toc", linkstr)
        self.log.appendAt("evranking", re.sub("&nbsp;","",linkstr))
        self.log.append("\n"+H3+'<a name="'+anchor+'"></a>' +\
                        "Ranking after %i generations:" % \
                        self.lastGeneration + H3X + "<br />\n\n<p><pre>")
        ranking = zip(self.setup.population,
            #Dynamics._QuickFitness2(self.setup.population, self.payoffMatrix),
            [str(s) for s in self.setup.strategyList])
        ranking.sort();  ranking.reverse()
        k = 1
        for r, name in ranking:
            s = "%3i." % k + name + " "*max(40-len(name),1) + \
                "%1.4f  " % r + "\n"
            self.log.append(s)
            k += 1
        self.log.append("</pre><br />\n")
        imgName = self.setup.fname() + "_gn%i" % self.lastGeneration
        path = self.imgdirName + "/" + imgName
        self.log.append('<div align="center">'+\
                        '<a href="' + path + '.png">' + \
                        '<img src="'+path+'_web.png"'+'" alt="Image: ' + \
                        imgName + '.png not found!" /></a></div><br />\n')
        self.log.append("</p>\n")
        self.log.append('<div align="right"><a href="#top">[top]' + \
                        '</a></div><br />\n')
        self.rangeStack.append((imgName, self.graph.x1, self.graph.y1,
                                self.graph.x2, min(self.graph.y2, 1.0)))        
        self.notifier.updateLog(self.log.getHTMLPage())
        if self.firstGeneration <= 1:  self.notifier.logToStart()
        self.firstGeneration = self.lastGeneration + 1
        self.lastGeneration = self.lastGeneration * 2
        self.notifier.statusBarHint("Ready.")


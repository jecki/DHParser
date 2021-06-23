# simulation setup and simulation objects
# WORST SPAGETTI CODE EVER!

from __future__ import generators # retain python 2.2 compatibility
import copy, re
from PyPlotter import Gfx, Colors
from PopulationDynamics import Dynamics
import PrisonersDilemma as PD
from Strategies import *
from PolymorphicStrategies import *
import GroupSelection as GS
from PopulationDynamics.Compatibility import *
from Logging import H1,H2,H3, H1X,H2X,H3X, LogNotificationInterface, HTMLLog


NUM_GENERATIONS = 50 # number of generations to start with in the
                     # population dynamical simulation
NUM_SAMPLES = PD.NUM_SAMPLES # Samples to take of a match if randomizing
                             # strategies or in game noise is involved
NO_GRAPH_OPTIMIZATION = False # graph drawing will be slowed down but
                              # accuracy is increased (for printing and saving) 


###############################################################################
#
# Deme class for group selection that takes into account all parameters
# from the simulation setup.
#
###############################################################################

class RichPDDeme(GS.PDDeme):
    """A Deme where the species represent stategies in the reiterated
    two person prisoner's dilemma. Other than GS.PDDeme, RichPDDeme
    takes all simulation parameters into account.

    Attributes:
        mutators:   customized list of mutators for this deme
        setup:      the parameters of the simulation
        fF   :      fitness function
    """    
    def __init__(self, setup, name="", species_override = None,
                 distribution_or = None):
        if species_override == None: species_override = setup.strategyList
        if distribution_or == None: distribution_or = setup.population
        # assert GS.check_instances(species_override, Strategy),\
        #        "All species must be prisoner's dilemma strategies!"

        self.mutators = []
        for m in setup.mutators:
            if m.rate > 0.0:
                mt = m.transform(setup.strategyList, species_override)
                if mt.mutated == len(species_override):
                    species_override = species_override + \
                                       [setup.strategyList[m.mutated]]
                    distribution_or = array(list(distribution_or) + [0.0])
                self.mutators.append(mt)
        
        GS.PDDeme.__init__(self, species_override, distribution_or, name)
        self.setup = setup 
        # self.payoff = None
        if self.setup.correlation:
            self.fF = lambda d,p: Dynamics.Fitness2(d,p,self.setup.correlation)
        else:  self.fF = Dynamics.QuickFitness2

    def new(self, species, distribution = None, name=""):
        return self.__class__(self.setup, name, species, distribution)

    def container(self, demes, distribution, name=""):
        return RichSuperDeme(self.setup, name, demes, distribution)

    def merged(self, *others):
        """Retruns a copy of the deme that is merged with a sequence of
        other demes. The species and distribution arrays of the new
        deme have the same order as setup.strategyList!"""
        species_dict = {};  share_dict = {}
        for deme in (self,)+others:
            for i in xrange(len(deme.species)):
                species = deme.species[i]
                name = str(species)
                if species_dict.has_key(name):
                    share_dict[name] += deme.distribution[i]
                else:
                    species_dict[name] = species
                    share_dict[name] = deme.distribution[i]
        species = [s for s in self.setup.strategyList \
                   if species_dict.has_key(s.name)] # keep species order!
        dist = array([share_dict[s.name] for s in species])
        return self.new(species, dist)

    def _fitness(self):
        if self.polymorphic:
            self.payoff = self.setup.genReducedPayoffMatrix(self.species)
        elif self.payoff == None:
            self.payoff = self.setup.derivePayoffMatrix(self.species)
        return self.fF(self.distribution, self.payoff)
    
    def replicate(self):
        if self.setup.noise:
            p = Dynamics.Replicator(self.distribution, self.fitness(),
                                    self.setup.noise)
        else:
            p = Dynamics.QuickReplicator(self.distribution, self.fitness())
        if self.mutators: p = mutation(asarray(p), self.mutators)
        self.distribution = asarray(p)
        self.evolution()

    def evolution(self):
        """Lets the polymorphic strategies evolve, in case there are any."""
        for s in self.species:
            if isinstance(s, PolymorphicStrategy):
                s.evolve(self)


class RichSuperDeme(GS.SuperDeme):
    """A super deme that takes into account all simulation parameters,
    like evolutionary noise etc.

    Attributes:
        setup:      the simulation parameters
        rF:         replicator function
    """  
    def __init__(self, setup, name="", species_override = None,
                 distribution_or = None):
        if species_override == None: species_override = setup.strategyList
        if distribution_or == None: distribution_or = setup.population
        GS.SuperDeme.__init__(self, species_override, distribution_or, name)        
        self.setup = setup
        if self.setup.noise:
            self.rF = lambda d,f: Dynamics.Replicator(d, f, self.setup.noise)
        else:  self.rF = Dynamics.QuickReplicator

    def new(self, species, distribution = None, name=""):
        return self.__class__(self.setup, name, species, distribution)

    def container(self, demes, distribution, name=""):
        return self.__class__(self.setup, name, demes, distribution)

    def replicate(self):
        #for d in self.species:
        #    if isinstance(d, GS.Deme):  d.replicate()
        for d in self.species: d.replicate # species should be demes anyway!
        self.distribution = self.rF(self.distribution, self.fitness())


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
        
    def __init__(self, original, mutated, rate=0.01):
        self.original = original
        self.mutated = mutated
        self.rate = rate

    def transform(self, src, dst):
        """Returns a new mutator, adjusted for strategy set 'dst', assumed
        that self is adjusted for strategy set 'src'.

        Usually this entails only adjustments of the indices m.original
        and m.mutated to the new list. Special cases occur, when the
        strategies indexed by either m.original or m.mutated are not included
        in dst. If m.mutated is not in dst, then mutated is set to
        len(dst). If m.original is not in dst, then rate is set to 0.0.
        """
        original, mutated, rate = self.original, self.mutated, self.rate
        d = {}
        for i in xrange(len(dst)):  d[dst[i].name] = i
        original_name = src[self.original].name
        mutated_name = src[self.mutated].name
        if d.has_key(original_name):  original = d[original_name]
        else: rate = 0.0
        if d.has_key(mutated_name):  mutated = d[mutated_name]
        else: mutated = len(dst)
        return Mutator(original, mutated, rate)

def mutation(population, mutatorList):
    """Apply mutation to a population"""
    p = population.copy()
    for m in mutatorList:
        x = population[m.original] * m.rate
        p[m.original] -= x
        p[m.mutated] += x
    return p


class DemeDescriptor(object):
    """Describes the deme structure of the simulation.

    num     = number of demes
    minSize,
    maxSize = minimum and maximum size of the demes
    interval = how many generations it takes, until demes are reshaped
    """
    def __eq__(self, other):
        if not isinstance(other, DemeDescriptor): return False    
        if self.num != other.num or self.minSize != other.minSize or \
           self.maxSize != other.maxSize or self.interval != other.inverval:
            return False
        return True

    def __init__(self, num, minSize, maxSize, reshapeInterval):
        self.num = num
        self.minSize = minSize
        self.maxSize = maxSize
        self.interval = reshapeInterval

    def verify(self, popsize):
        """-> sufficient demes for population size."""
        return self.minSize * self.num >= popsize

    def asTuple(self):
        """-> (num, minSize, maxSize, interval)."""
        return (self.num, self.minSize, self.maxSize, self.interval)
        

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
    demes        = DemeDescriptor: defines the deme structure of the
                    population, or 'None' if there are no demes    
    mutators     = list of Mutator objects: description of possible
                    mutation of strategies during the course of the
                    evolutionary development.
    indexDict    = dictionary of strategy indices indexed by strategy names
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
        if tuple(self.population) != tuple(other.population):  return False
        if self.correlation != other.correlation:  return False
        if self.gameNoise != other.gameNoise:  return False
        if self.noise != other.noise:  return False
        if self.iterations != other.iterations:  return False
        if self.samples != other.samples: return False
        if self.payoff != other.payoff:  return False
        if len(self.mutators) != len(other.mutators):
            return False
        if self.demes != other.demes: return False        
        for i in xrange(len(self.mutators)):
            if self.mutators[i] != other.mutators[i]:  return False
        return True


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
              demes = None, mutators = [], PM = None, log = None):
        self.name = name
        self.strategyList = strategyList
        if population == None:
            self.population = Dynamics.UniformDistribution(len(self.strategyList))
        else: self.population = array(population)
        self.correlation = correlation
        self.gameNoise = gameNoise
        self.noise = noise
        self.iterations = iterations
        self.samples = samples
        self.__payoff = payoff; p = payoff
        self._payoffArray = array([[[p[2],p[2]],[p[0],p[3]]],
                                   [[p[3],p[0]],[p[1],p[1]]]])
        self.mutators = mutators
        if demes:
            if not isinstance(demes, DemeDescriptor): # assume demes is a 4-tuple
                demes = DemeDescriptor(*demes)
            assert demes.verify(len(strategyList)), \
                          "Not enough demes or demes too small for population!"
        self.demes = demes
        self.indexDict = None
        self.cachedPM = PM
        self.cachedLog = log
        self._userDefined = True # SimApp marks its own setups as False

    def getPayoff(self):
        return self.__payoff
    def setPayoff(self, p):
        self.__payoff = p
        self._payoffArray = array([[[p[2],p[2]],[p[0],p[3]]],
                                   [[p[3],p[0]],[p[1],p[1]]]])
    payoff = property(getPayoff, setPayoff)

    def fname(self):
        """Returns the name of the setup as a proper file name."""
        return self.name.replace("*","x").replace("?","x").replace("/","x")\
               .replace("\\","x").replace(" ","_")

    def getPayoffMatrix(self, log = None, progressCallback = lambda f:1):
        """Returns the payoff matrix for the setup."""
        if self.cachedPM == None:
            self.cachedPM = PD.GenPayoffMatrix(self.strategyList,
              self._payoffArray, self.iterations, self.samples, self.gameNoise,
              log, progressCallback)
        return self.cachedPM

    def genReducedPayoffMatrix(self, strategies):
        """Returns a payoff matrix for the subset 'strategies' of the
        strategyList only. The payoff matrix is always freshly generated."""        
        return PD.GenPayoffMatrix(strategies, self._payoffArray,
                                  self.iterations, self.samples,
                                  self.gameNoise)
            
    def derivePayoffMatrix(self, strategies):
        """Returns a payoff matrix for the subset 'strategies' of the
        strategyList only."""
        if self.indexDict == None:
            self.indexDict = {}
            for i in xrange(len(self.strategyList)):
                self.indexDict[self.strategyList[i].name] = i        
        m = self.getPayoffMatrix()
        l = len(strategies)
        dm = zeros((l,l),"d")
        for i in xrange(l):
            r = self.indexDict[strategies[i].name]
            for k in xrange(l):
                c = self.indexDict[strategies[k].name]
                dm[i,k] = m[r,c]
        return dm

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
            html.append("uniform population distribution<br />\n")
        if self.demes != None:
            html.append("%i demes with sizes varying from %i to %i.<br />\n" % \
                (self.demes.num, self.demes.minSize, self.demes.maxSize))
            if self.demes.interval == 1:
                html.append("Population is reshaped every generation<br /><br />\n\n")
            else:
                html.append("Population is reshaped every %i generations<br /><br />\n\n" % \
                            self.demes.interval)
        else: html.append("<br />\n")
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
        html.append("payoff parameters:&nbsp;T,R,P,S = "+\
                    "%.2f, %.2f, %.2f, %.2f"%self.payoff + "<br />\n")
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
        setup       : A copy (!) of the simulation setup.
        masterDeme  : The "root" of the population structure. If the population
                      is not divided into different demes, then 'masterDeme'
                      contains only one subdeme with the whole population
        simplexMD   : Master Deme for the simplex representation
        payoffMatrix: The payoff matrix of the tournament part of the
                      simulation
        rangeStack  : Sequence of the respective range parameters of the
                      simulation graph (x1,y1,x2,y2), one for each call
                      of the method 'continueSim'
        imgDirName  : Name of the directory to write the images of the html
                      log to (only if the log is actually saved to disk!)
        simplexName : file name of the simplex graph, if the html log is saved
        firstGeneration: the first generation to start the next population
                      dynamical cycle with (when calling continueSim)
        lastGeneration: the last generation of the next cycle

        numStgies   : number of Strategies
        bestStgies  : 3-tuple: the numbers of the three strategies with the
                      greatest population share.
        updateSimplexFlag: simplex data has changes and simplex needs to be
                      updated.
    """
    
    def __init__(self, graph, simplex, log, notifier):
        self.graph = graph
        self.simplex = simplex
        self.notifier = notifier
        self.log = log
        self.setup = None
        self.masterDeme = None
        self.simplexMD = None
        self.payoffMatrix = None
        self.rangeStack = []
        self.imgdirName = ""
        self.simplexName = ""
        self.firstGeneration = 1
        self.lastGeneration = NUM_GENERATIONS
        self.numStgies = 0
        self.bestStgies = (0,0,0)
        self.updateSimplexFlag = False
        self._dontLogTwiceFlag = False

    def _prepareEvLog(self):
        if not self._alreadyLogged:
            self._alreadyLogged = True
            self.imgdirName = self.setup.fname() + "_images"
            if PD.MATCH_LOG_OUTSOURCED: nr = "3"
            else: nr = "4"
            self.log.appendAt("toc", '<a href="#evranking">' + nr + \
                              '. Evolutionary Simulation</a><br />\n')
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

    def createMasterDeme(self, population_override = None):
        if population_override == None:
            population_override = self.setup.population
        if self.setup.demes:
            md = RichPDDeme(self.setup, distribution_or=population_override).\
                 spawn(self.setup.demes.num, self.setup.demes.minSize,
                       self.setup.demes.maxSize)
            md.counter = self.setup.demes.interval
        else:
            md = RichPDDeme(self.setup, distribution_or=population_override)
            md.counter = -1
        return md

    def dynamics(self, masterDeme):
        if masterDeme.counter == 0:
            masterDeme.reshape(self.setup.demes.num,
                               self.setup.demes.minSize,
                               self.setup.demes.maxSize)
            masterDeme.counter = self.setup.demes.interval
        masterDeme.replicate()
        masterDeme.counter -= 1
##        s=self.masterDeme.aggregate().species
##        assert s == self.setup.strategyList, "order of species changed!"
        return masterDeme.aggregate().distribution        

    def simplexDynamics(self, population):
        if self.simplexMD == None or \
           isinstance(self.simplexMD, GS.SuperDeme) or \
           any(self.simplexMD.distribution != population):
            self.simplexMD = self.createMasterDeme(population)
        return self.dynamics(self.simplexMD)

    def extendedDynamics(self, population):
        realP = [0.0] * self.numStgies
        realP[self.bestStgies[0]] = population[0]
        realP[self.bestStgies[1]] = population[1]
        realP[self.bestStgies[2]] = population[2]
        realP = self.simplexDynamics(tuple(realP))
        return (realP[self.bestStgies[0]],
                realP[self.bestStgies[1]],
                realP[self.bestStgies[2]])

    def _bestT(self):
        """-> (n,m) best and second best strategy in the tournament."""
        M = self.payoffMatrix
        l = [(sum(M[i]),i) for i in xrange(self.numStgies)]
        l.sort(reverse=True)
        return (l[0][1], l[1][1], l[2][1])

    def _bestP(self):
        """-> (n,m) best and second best strategy populationwise."""
        l = [(self.setup.population[i], i) for i in xrange(self.numStgies)]
        l.sort(reverse=True)
        return (l[0][1], l[1][1], l[2][1])
    
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
            self.log.entryPoint("title")
            self.log.append(H2+'<a name="toc"></a>Table of Contents'+ \
                            H2X + "\n\n<p>")
            self.log.append('<a href="#setup">0. Simulation Setup</a><br />\n')
            self.log.entryPoint("toc")
            self.log.append("</p><br />\n")            
            self.log.append(setup.htmlRepresentation())
            self.log.append('<div align="right"><a href="#top">[top]' + \
                            '</a></div><br />\n')            
            self.payoffMatrix = setup.getPayoffMatrix(self.log,
                                                      progressCallback)
            setup.cachedPM = self.payoffMatrix
            self.setup.cachedPM = setup.cachedPM
            setup.cachedLog = self.log.backup()
            self.setup.cachedLog = setup.cachedLog
        else:
            self.payoffMatrix = self.setup.cachedPM
            self.log.replay(self.setup.cachedLog)
        self.notifier.updateLog(self.log.getHTMLPage())
        self.masterDeme = None;  self.simplexMD = None
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

        self.numStgies = len(self.setup.strategyList)
        self.simplex.setTitle('Simplex diagram of "'+self.setup.name+'"')
        if self.numStgies == 3:
            self.simplex.setFunction(self.simplexDynamics)
            self.simplex.setLabels(str(self.setup.strategyList[0]),
                                   str(self.setup.strategyList[1]),
                                   str(self.setup.strategyList[2]))
        elif self.numStgies > 3:
            #self.simplex.setTitle("Too many strategies for " + \
            #                      "a simplex diagram!")
            self.bestStgies = self._bestT()
            self.simplex.setFunction(self.extendedDynamics)
            sl = self.setup.strategyList
            self.simplex.setLabels(str(sl[self.bestStgies[0]]),
                                   str(sl[self.bestStgies[1]]),
                                   str(sl[self.bestStgies[2]]))
        else:
            self.simplex.setFunction(lambda p:p)                 
            self.simplex.setTitle("Too few strategies for "\
                                  "a simplex diagram!")
            self.simplex.setLabels("","","")
        self._prepareEvLog()


    def continueSim(self, record = None, refreshCallback = lambda :1,
                    withSimplex = True):
        if self.setup == None:  return
        self.notifier.statusBarHint("Running...")
        self.updateSimplexFlag = False
        if self.firstGeneration > 1:
            self.graph.adjustRange(0, 0.0, self.lastGeneration, self.graph.y2)
            if self.numStgies > 3:
                oldBest = set(self.bestStgies)
                self.bestStgies = self._bestP()
                if oldBest != set(self.bestStgies):
                    self.simplex.setFunction(self.extendedDynamics)                
                    sl = self.setup.strategyList
                    self.simplex.setLabels(str(sl[self.bestStgies[0]]),
                                           str(sl[self.bestStgies[1]]),
                                           str(sl[self.bestStgies[2]]))
                    if withSimplex: self.simplex.show()
                    else: self.updateSimplexFlag = True
        else:
            k = 0
            for s in self.setup.strategyList:
                self.graph.addValue(str(s), 0, self.setup.population[k])
                k += 1
            if withSimplex: self.simplex.show()
            else: self. updateSimplexFlag = True
            self.masterDeme = self.createMasterDeme()
        pixelSteps = xaxisIter(self.graph, self.firstGeneration,
                               self.lastGeneration)
        refreshTicker = (self.lastGeneration + 1 - self.firstGeneration) / 10
        for i in xrange(self.firstGeneration, self.lastGeneration+1):
            p = self.dynamics(self.masterDeme)
            if pixelSteps.check(i):
                k = 0
                for s in self.setup.strategyList:
                    self.graph.addValue(str(s), i, p[k])
                    k += 1
            if i % refreshTicker == 0: refreshCallback()
            # if i % 120 == 0: self.notifier.SafeYield()
            if record: record.append(p)
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
            Dynamics.QuickFitness2(self.setup.population, self.payoffMatrix),
            [str(s) for s in self.setup.strategyList])
        ranking.sort();  ranking.reverse()
        k = 1
        for r, f, name in ranking:
            s = "%3i." % k + name + " "*max(40-len(name),1) + \
                "%1.4f  "%r + "(%1.4f)"%f + "\n" # repr(r) + "\n"
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


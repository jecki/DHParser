#!/usr/bin/python
# groupselection.py

import random, copy
from PyPlotter import Graph, Gfx
import PrisonersDilemma as PD
from Strategies import *
from PolymorphicStrategies import *
from PopulationDynamics.Dynamics import *
from PopulationDynamics.Compatibility import *

PD_PAYOFF = array([[[1.0, 1.0], [3.5, 0.0]],\
                   [[0.0, 3.5], [3.0, 3.0]]])

########################################################################
#
# Deme classes
#
########################################################################

deme_code = 0
def GenericIdentifier():
    global deme_code
    deme_code += 1
    return "Deme"+hex(deme_code)


class Deme(object):
    """Represents a deme, i.e. a (sub-)population that is defined
    by the species in the deme as well as their distribution.
    Deme populations are not usually normalized. They need to be
    normalized explicitly by call to the 'normalize' method.
    (A species can be any object that can be identified by str(species).
    Species are always identified by str(species) and never by references,
    i.e. two different objects returning the same name for str(obj) are
    considered one and the same species. When merging (see method merged) one
    of these objects may be dropped arbitrarily. Or to put it another way:
    If the species change their characteristics, i.e. if they evolve, they
    should change their names two. For genetic species the genome should
    therefore always be encoded in the name of the species.)

    Attributes (read only!):
        name            - name of the deme
        species         - list of species
        distribution    - distribution of the strategies
        fitnessCache    - cache for the fitness values
    """  
    def __str__(self):
        return self.name

    def __setattr__(self, name, value):
        """If the distribution value change the fitnessChache is cleared."""
        if name == "distribution":
            object.__setattr__(self, "fitnessCache", None)
        object.__setattr__(self, name, value)
   
    def __init__(self, species, distribution = None, name=""):
        """Initializes the Deme with the list of species, the distribution
        vector and a name (if desired). The list of species is always
        deep-copied into the meme to allow for independet evolution of the
        species. However, species with the same name in different demes may
        be merged back, when demes are merged.
        """
        assert len(species) > 0, "Too few species (%i)!"%len(species)
        assert distribution == None or len(species) == len(distribution), \
               "Species list and distribution array are of unequal size!"
        self.fitnessCache = None     
        if distribution != None: self.__distribution = asarray(distribution)
        else: self.__distribution = UniformDistribution(len(species))
        if name: self.name = name
        else: self.name = GenericIdentifier()
        self.species = copy.deepcopy(species)

    def getDistribution(self):
        return self.__distribution
    def setDistribution(self, d):
        self.__distribution = d
        self.fitnessCache = None
    distribution = property(getDistribution, setDistribution)

    def new(self, species, distribution = None, name=""):
        """Create a deme object of the same type."""
        return self.__class__(species, distribution, name)

    def container(self, demes, distribution, name=""):
        """Create a super deme that is a suitable container for
        demes of the type of this deme."""
        return SuperDeme(demes, distribution, name)

    def merged(self, *others):
        """Returns a copy of the deme that is merged with a sequence of
        other demes. The order of species in the merged deme is arbitrary!"""
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
        species = species_dict.values()
        dist = array([share_dict[s.name] for s in species])
        return self.new(species, dist)

    def __add__(self, other):
        """Returns a copy of the deme that is merged with another"""
        return self.merged(other)

    def __mul__(self, faktor):
        """Returns a deme where all population shares are multiplied
        with 'faktor'"""
        ndist = self.distribution * faktor
        return self.new(self.species, ndist)
        
    def normalized(self):
        """Returns a normalized (population shares add up to 1.0)
        copy of the deme."""
        return self.new(self.species, norm(self.distribution))

    def normalize(self):
        """Normalizes the population share in place."""
        self.distribution = norm(self.distribution)

    def _fitness(self):
        """Determines the fitness values for the species of the
        deme."""
        raise NotImplementedError

    def fitness(self):
        """Returns the fitnesses of the species (as Numeric.array)."""
        if self.fitnessCache == None: self.fitnessCache = self._fitness()
        return self.fitnessCache

    def replicate(self):
        """Updates the distribution to the next generation."""
        self.distribution = norm(self.distribution * self.fitness())

    def aggregate(self, weighted = True):
        """Returns a new deme where all species of all subdemes are
        recursively aggregated. If 'weighted' is false the
        distribution (relative size) of the demes will not be taken
        into account. If there are no subdemes, 'self' is returned.
        Warning: If a new deme is created, the order of the species 
        in this new deme arbitrary!"""
        return self

    def spawn(self, N, minSize, maxSize):
        """Returns a super deme of N demes with sizes varying between
        'minSize' and 'maxSize' and populations randomly picked from
        this deme."""
        pool = self.distribution #.copy() # don't need a copy!
        sizes = [random.randint(minSize, maxSize) for i in xrange(N)]
        assert sum(sizes) >= len(pool), "Too few or too small demes to spawn!"
        rng = range(len(pool))
        sg = [[] for i in rng];  l = 0
        for count in xrange(N):
            s = sizes[count]
            if l < len(pool):
                g = range(l, min(l+s, len(pool)))
                g.extend(random.sample(rng, max(0,l+s-len(pool))))
                l += s
            else:  g = random.sample(rng, s)
            for st in g:  sg[st].append(count)
        species = [[] for i in xrange(N)]
        distribution = [[] for i in xrange(N)]
        for i in xrange(len(sg)):
            chunks = list(RandomDistribution(len(sg[i])) * pool[i])
            for g in sg[i]:
                species[g].append(self.species[i])
                distribution[g].append(chunks.pop())
        demes = []
        for i in xrange(N): demes.append(self.new(species[i], distribution[i]))
        #assert almostEqual(sum([sum(d.distribution) for d in demes]), 1.0), \
        #    "self test failed %f"%sum([sum(d.distribution) for d in demes])
        distribution = norm(array([sum(d.distribution) for d in demes]))
        for d in demes: d.normalize()
        return self.container(demes, distribution)

    def ranking(self):
        """-> list of (rank, species name, population share) tuples."""
        l = zip(self.distribution,[str(s) for s in self.species])
        l.sort(); l.reverse()
        ranking = [(r+1, l[r][1], l[r][0]) for r in xrange(len(l))]
        return ranking


class SuperDeme(Deme):
    """A Deme that contains other demes as species.

    In order to determine the fitness of the (Sub-)Demes the 
    simplemost model of a group selection process is implemented:
    The fitness of the (Sub-)Demes is the dot product of the vector of
    the fitness values of the species with the vector of population
    shares. As this is not generally true, but depends on the concrete
    group selection mechanism to be modelled, method '_fitness' should
    usually be overloaded with a method implementing the right fitness
    algorithm.
    """
    def _fitness(self):
        return array([matrixmultiply(d.fitness(), d.distribution) \
                      for d in self.species])
    
    def replicate(self):
        for d in self.species:
            if isinstance(d, Deme):  d.replicate()
        Deme.replicate(self)

    def aggregate(self, weighted = True):
        l = []
        for i in xrange(len(self.species)):
            d = self.species[i]
            if isinstance(d, SuperDeme): d = d.aggregate(weighted)
            if weighted:
                l.append(d * self.distribution[i])
            else:
                l.append(d)
        d = l[0].merged(*l[1:])
        d.normalize()
        return d

    def reshaped(self, N=-1, minSize=-1, maxSize=-1):
        """Returns a superdeme with the same population but a
        reshaped deme structure."""
        pool = self.aggregate(weighted = True);  n = len(pool.species)
        if N <= 0: N = len(self.species)
        if minSize <= 0: minSize = max(1, N/7)
        if maxSize <= 0: maxSize = min(l, max(2, N/4)) 
        superdeme = pool.spawn(N, minSize, maxSize)
        return superdeme

    def reshape(self, N=-1, minSize=-1, maxSize=-1):
        """Reshape the deme structure of this deme."""
        sd = self.reshaped(N, minSize, maxSize)
        self.species = sd.species
        self.distribution = sd.distribution        


########################################################################
#
# class PDDeme, PDSuperDeme
#
########################################################################


def check_instances(lst, cls):
    """-> True if all objects in the list are instances of class 'cls'.
    """
    for obj in lst:
        if not isinstance(obj, cls):  return False
    return True


class PDDeme(Deme):
    """A Deme where the species represent strategies in the reiterated
    two person prisoner's dilemma.

    Attributes:
        payoff      - the payoff matrix of the deme (due to lazy
                      creation payoff is 'None' until _fitness is
                      called for the first time.
                    
        polymorphic - A boolean that indicates whether the deme
                     contains any strategies that may change from
                     generation to generation, e.g. evolutionary
                     strategies. If this is true than the payoff
                     matrix will be recalculated between before
                     every new generation.
    """   
    def __init__(self, strategies, distribution=None, name=""):
        assert check_instances(strategies, Strategy),\
               "All species must be prisoner's dilemma strategies!"        
        Deme.__init__(self, strategies, distribution, name)
        self.polymorphic = False
        for s in strategies:
            if isinstance(s, PolymorphicStrategy):
                self.polymorphic = True
                break
        self.payoff = None

    def _fitness(self):
        if self.polymorphic or self.payoff == None:
            self.payoff = PD.GenPayoffMatrix(self.species, payoffs=PD_PAYOFF)
        return matrixmultiply(self.payoff, self.distribution)


########################################################################
#
# class DemeView
#
########################################################################

class DemeView(object):
    """A viewer for demes.

    Attributes:
        generation  - integer: the number of generation. It will be
                      increased automatically with every call to
                      the update method
        deme        - the deme that in monitored by this viewer
        graph       - the graph that visualizes the evolution of the
                      deme
        title       - title of the graph
        weighted    - boolean: if the deme is a super deme then
                      species aggregation is weighted by the deme size
    """
    def __init__(self, deme, gfxDriver, title = "", weighted = True):
        self.generation = 0
        self.deme = deme
        self.weighted = weighted
        if title: self.title = title
        else: self.title = str(deme)
        self.graph = Graph.Cartesian(gfxDriver, 0, 0.0, 100,
                                     1.1/len(deme.species),
                                     title, "Generations",
                                     "Population")
        agg = deme.aggregate(False)
        for s in agg.species:
            self.graph.addPen(str(s), updateCaption=False)
        self.graph.redrawCaption()
        self.update()

    def update(self):
        """Updates the deme view."""
        agg = self.deme.aggregate(self.weighted)
        for i in xrange(len(agg.species)):
            name = str(agg.species[i])
            value = agg.distribution[i]
            self.graph.addValue(name, self.generation, value)
        self.generation += 1

    def redraw(self, driver):
        """Redraws the graph."""
        if self.graph.gfx != driver:
            self.graph.changeGfx(driver)
        self.graph.resizedGfx()



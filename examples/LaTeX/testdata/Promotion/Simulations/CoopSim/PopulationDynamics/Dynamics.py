"""Basic functions for replicator dynamics

When using this module from an application typically only the the Function
GetReplicator' will be needed to generate a suitable replicator dynamics
function.
"""

import random, warnings
from Compatibility import *

#-------------------------------------------------------------------------------
#
# Some miscellanous classes, functions etc.
#
#-------------------------------------------------------------------------------

def GenTuples(dimension, count):
    """Generates an iterator of number tuples
    Each number is counted from 0 to count-1 from right to left. Example:
    For dimension=2, count=3 the generated iterator yields (0,0), (0,1),
    (0,2), (1,0), (1,1), (1,2), (2,0), (2,1), (2,2)

    dimension - positive integer, Dimension of the generated tuples
    count - positive integer, Range of each digit of the generated tuples
    return value - iterator of tuples
    """
    if dimension == 1:
        for i in range(count): yield (i,)
    elif dimension > 1:
        for i in range(count):
            for k in GenTuples(dimension-1, count):
                yield (i,)+k
    else:  raise ValueError, "tuple dimension "+dimention+" is not allowed!"


# if compatibility with python 2.1 or jython is needed, comment out the
# the generator above and uncomment the class below

##class GenTuples(object):
##    """Iterator of number tuples
##
##    Each number is counted from 0 to count-1 from right to left. Example:
##    For dimension=2, count=3 the generated iterator yields (0,0), (0,1),
##    (0,2), (1,0), (1,1), (1,2), (2,0), (2,1), (2,2)
##    """
##    def __init__(self, dimension, count):
##        """Constructs the GenTuples iterator object.
##
##        dimension - positive integer, Dimension of the generated tuples
##        count - positive integer, Range of each digit of the generated tuples
##        """
##        self.dimension = dimension
##        self.count = count
##        self.stop = count**dimension
##    
##    def __getitem__(self, i):
##        """Returns the i-th tuple in line."""
##        if i >= self.stop:  raise IndexError
##        l = []
##        for x in xrange(self.dimension):
##            n = i % self.count
##            l.insert(0, n)
##            i /= self.count
##        return tuple(l)

#-------------------------------------------------------------------------------
#
# Function for generating (population) distributions
#
#-------------------------------------------------------------------------------

#
# In the following a distribution is always a list of floating point numbers
# between 0.0 and 1.0 that add up to 1.0. (It partitions the interval [0.0, 1.0]
# into a number of partitions of possibly different size.)

def RandomDistribution(n):
    """Creates a random distribution

    n - positive integer: Number of elements of in the distribution
    
    return value - list of floats: Distribution,
        with 0.0 <= t[i] <= 0 and sum(t) == 1.0
    """
    assert n >= 0, "The number of elements in a distribution "\
                   "must at least be 0, not %i !" % n
    if n == 0: return ()
    r = [abs(float(i % 2) - random.random()) for i in range(n-1)]
    r.sort()
    r.extend([1.0,0.0]) 
    return array([r[i]-r[i-1] for i in range(n)])

#    p = [random.random() for x in xrange(n)]
#    S = sum(p)
#    p = map(lambda x: x/S, p)
#    return array(p)


def UniformDistribution(n, noise=0.0):
    """Creates an a uniform distribution
    
    n - positive integer: Number of elements
    noise - float: Noise level (0.0 <= noise <= 1.0)
    return value - tuple of floats: Distribution,
        with 0.0 <= t[i] <=  1.0 and sum(t) == 1.0
    """
    assert n >= 0, "The number of elements in a distribution "\
                   "must at least be 0, not %i !" % n
    if n == 0: return ()
    if noise < 0.0 or noise > 1.0:
        raise ValueError, "noise = %f, must be 0.0 <= noise <= 1.0" % noise
    r = 1.0/n;  rn = r*(1.0-noise)
    p = [random.uniform(rn, r) for i in xrange(n)]
    N = sum(p)
    for i in xrange(n):  p[i] /= N

##    Alternative noise model
##
##    p = [1.0/n for i in range(n)] 
##    if noise > 0.0 and noise <= 1.0:
##        r = RandomPopulation(n)
##        for i in range(n):  p[i] = p[i]*(1.0-noise) + r[i]*noise
##    elif noise != 0.0:  raise ValueError, "0.0 <= noise <= 1.0, not %f" % noise

    return array(p)


def RandomSelect(distribution):
    """Randomly selects an item from a distribution
    The size of the species determines the probability with which it will be
    selected.

    population - tuple of floats: Distribution
    
    return value - integer: index of the selected element (or partition resp.)
    """
    def rselect(slices, r, a, b):
        if b-a <= 1 : return a
        m = (a+b)/2
        if r >= slices[m]:  return rselect(slices, r, m, b)
        else: return rselect(slices, r, a, m)

    if len(distribution) == 0:
        raise ValueError, "Cannot select an element from an empty distribution"
    slices = [0.0]
    for p in distribution:  slices.append(p+slices[-1])
    return rselect(slices, random.random(), 0, len(slices))
 

def norm(distribution):
    """Normalize array 'distribution', so that its entries
    add up to 1.0."""
    S = sum(distribution)
    if  S <= 0.0:
        # raise ValueError, "Cannot normalize empty distribution!"
        return distribution # do nothing
    return distribution / S


def RandomSample(distribution, n):
    """Randomly selects n items from a distribution without replacement."""
    # assert n <= len(distribution), "Cannot select %i individuals from a population of less than %i individuals"%(n,n)
    if n > len(distribution): n = len(distribution)
    dist = distribution.copy()
    sample = []
    for i in xrange(n):
        try: dist = norm(dist)
        except ValueError: break        
        item = RandomSelect(dist)
        sample.append(item)
        dist[item] = 0.0
    return array(sample)


#-------------------------------------------------------------------------------
#
#   Functions to determine the fitness of a population based on
#   2 or more person games between the individuals.
#
#-------------------------------------------------------------------------------

def _Fitness2(population, payoff, e):
    """Determines the relative fitness of species based on a two player game."""
    n = population
    L = len(n)
    Sn = sum(n) # should always be 1, shouldn't it? Then why not optimize???
    p = []    
    for i in xrange(L):
        s = 0.0
        for k in xrange(L):
            if i == k:
                s += payoff[i,k]*(n[i]+e*(Sn-n[i]))
            else: 
                s += payoff[i,k]*(n[k]-e*n[k])
        p.append(s)
    return p

def _numeric_Fitness2(population, payoff, e):
    """Determines the relative fitness of species based on a two player game."""
    n = asarray(population)
    L = len(n)
    Sn = sum(n)
    pay = payoff.copy()
    d = diagonal(payoff)
    # putmask(pay, identity(L), 0.0)
    for i in xrange(L): pay[i,i] = 0.0
    p = dot(pay,(n - e*n)) + d * (n + e*(Sn-n))
    return p

if HAS_NUMERIC:  Fitness2 = _numeric_Fitness2
else: Fitness2 = _Fitness2
        

def _SampledFitness2(population, payoff, e, samples):
    """Determine the relative fitness of the species based on a two player game
    taking into accound a correlation of e and using a representative selection 
    of sample matches instead of taking into account every possible combination.
    """
    n = population
    L = len(n)
#    if isinstance(samples, float):
#        samples = int(samples*L*L+0.5)
    Sn = sum(n)
    p = []
    for i in xrange(L):
        m = []
        for k in xrange(L):
            if i == k:  m.append(n[i]+e*(Sn-n[i]))
            else: m.append(n[k]-e*n[k])
        s = 0.0
        for k in xrange(samples):
            s += payoff[i, RandomSelect(m)]
        p.append(s/samples)
    return p    

SampledFitness2 = _SampledFitness2


def _QuickFitness2(population, payoff):
    """Determines the relative fitness of the species based on a two player game
    A faster replacement for 'Fitness2' if correlation e = 0.0.
    """
    n = population
    L = len(n)
    p = []
    for i in xrange(L):
        s = 0.0
        for k in xrange(L):
            s += payoff[i,k]*n[k]
        p.append(s)
    return p

def _numeric_QuickFitness2(population, payoff):
    """Determines the relative fitness of the species based on a two player game
    A faster replacement for 'Fitness2' if correlation e = 0.0.
    """
    return matrixmultiply(payoff, asarray(population))

if HAS_NUMERIC: QuickFitness2 = _numeric_QuickFitness2
else: QuickFitness2 = _QuickFitness2
    


def _SampledQuickFitness2(population, payoff, samples):
    """Determine the relative fitness of the species based on a two player game
    assuming that correlation is 0 and using a representative selection of
    sample matches instead of taking into account every possible combination.
    """
    n = population
    L = len(n)
    p = []
    for i in xrange(L):
        s = 0.0
        for k in xrange(samples):
            s += payoff[i, RandomSelect(n)]
        p.append(s/samples)
    return p

SampledQuickFitness2 = _SampledQuickFitness2

    
def _QuickFitness(population, payoff, N):
    """Determines the relative fitness of the species based on a N-player game 
    Correlation factor e is assumed to be 0.0.
    """
    n = population
    L = len(n)
    p = []
    for i in xrange(L):
        s = 0.0
        for k in GenTuples(N-1, L):
            s += payoff[(i,)+k] * reduce(lambda x,y:x*y, map(lambda x:n[x],k))
        p.append(s)
    return p

QuickFitness = _QuickFitness


def _SampledQuickFitness(population, payoff, N, samples):
    """Determine the relative fitness of the species based on an N-player game
    assuming that correlation is 0 and using a representative selection of
    sample matches instead of taking into account every possible combination.
    """
    n = population
    L = len(n)
    p = []
    for i in xrange(L):
        s = 0.0
        for k in xrange(samples):
            t = tuple([i]+[RandomSelect(n) for v in xrange(N-1)])
            s += payoff[t]
        p.append(s/samples)
    return p

SampledQuickFitness = _SampledQuickFitness


def _Fitness(population, payoff, e, N):
    """Determines the relative fitness of species based on an N-player game"""
    n = population
    L = len(n)
    p = []
    I = set(range(L))
    for i in xrange(L):
        s = 0.0
        for k in GenTuples(N-1, L):
            K = set(k)
            Sn = sum(map(lambda y:n[y],filter(lambda x: x != i, I-K)))
            d = {}
            for r in K:
                if r == i:  d[r] = n[r] + e*Sn
                else:       d[r] = n[r] - e*n[r]            
            s += payoff[(i,)+k] * reduce(lambda x,y:x*y, map(lambda x:d[x],k))
        p.append(s)
    return p

Fitness = _Fitness


def _SampledFitness(population, payoff, e, N, samples):
    """Determines the relative fitness of the species based on an N-player game
    taking into accound a correlation of e and using a representative selection 
    of sample matches instead of taking into account every possible combination.
    """
    n = population
    L = len(n)
    Sn = sum(n)    
    p = []
    for i in xrange(L):
        s = 0.0
        m = []
        for k in xrange(L):
            if i == k:  m.append(n[i]+e*(Sn-n[i]))
            else: m.append(n[k]-e*n[k])        
        for k in xrange(samples):
            t = tuple([i]+[RandomSelect(m) for v in xrange(N-1)])
            s += payoff[t]
        p.append(s/samples)
    return p    

SampledFitness = _SampledFitness


def _FunctionSelector(population, N, samples, stdFunction, sampleFunction,
                      baseParams):
    """Fitness function that determines on the fly whether to use
    a sampling algorithm or not.
    """
    L = len(population)
    combinations = L**N
    if samples < 1.0:  samples = int(combinations*samples+0.5)
    if samples == 0: samples = 1
    if samples < combinations:
        return sampleFunction(population, *(baseParams + (samples,)))
    else: return stdFunction(population, * baseParams)
    

class GenFitnessFunction(object):
    def __init__(self, payoff, e=0.0, N=2, samples=1.0):
        """Generate a fitness function for the given parameters.

            A fitness function if a function that takes a population ratio as
            argument and returns the fitnesses of the species of the population.

        payoff - payoff[a,b,c,...] should yield the payoff of player a when
            playing with players a,b,c,... .

        e - correlation factor, float (range: 0.0 to 1.0): The higher the
            correlation factor the more likely it is that individuals interact
            with individuals of the same species instead of a different species.
            e = 0.0 means random interaction. e = 1.0 means interaction is fully
            confined to the same species.

        N - integer: Number of players in one game, N >= 1

        samples - integer or float: number (or percentage) of samples to be taken.
            If samples = 1.0 or if the number of possible combinations is smaller
            than samples no sampling algorithm will be used.

        return value - function (population) -> fitness: Function that
            computes the fitnesses of the species of the population.

            population - tuple of floats: Population ratio. Each number in the
                tuple represents the share the respective species has from the
                whole population.

            fitness (return value) - list of positive floats: List of the relative
                fitnesses of each species.
        """
        self.payoff, self.e, self.N, self.samples = payoff, e, N, samples

        if isinstance(e, 0.0.__class__) and (e < 0.0 or e > 1.0):
            raise ValueError, "e = %f violates 0.0 <= e <= 1.0"%e
        if samples <= 0: raise ValueError, "samples %f <= 0 !"%samples

        if N == 1:
            if isinstance(e, 0.0.__class__) and (e != 0.0):
                warnings.warn("Correlation e != %f is meaningless if N == 1"%e,
                              UserWarning)
            self.stdFunction = lambda p: array([payoff[i,] for i in range(len(p))])
            self.params = tuple()
        elif N == 2:
            if e == 0.0:
                self.stdFunction = QuickFitness2
                self.params = (payoff,)
                self.sampleFunction = SampledQuickFitness2
            else:
                self.stdFunction = Fitness2
                self.params = (payoff, e)
                self.sampleFunction = SampledFitness2
        elif N > 2:
            if e == 0.0:
                self.stdFunction = QuickFitness
                self.params = (payoff, N)
                self.sampleFunction = SampledQuickFitness
            else:
                self.stdFunction = _Fitness
                self.params = (payoff, e, N)
                self.sampleFunction = SampledFitness
        else: raise ValueError, "N must be >= 1, not %i !" % N
        if samples != 1.0 and N > 1:
            self.function = _FunctionSelector
            self.baseParams = self.params
            self.params = (self.N, self.samples, self.stdFunction,
                           self.sampleFunction, self.baseParams)
        else:
            self.function = self.stdFunction
        
    def __call__(self, population):
        return self.function(population, *self.params)

        
#-------------------------------------------------------------------------------
#
#   replicator dynamical functions
#
#-------------------------------------------------------------------------------

def _Replicator(population, fitness, noise):
    """Determines the population distribution of the next generation."""
    n = list(population)
    L = len(population)
    f = fitness
    
    for i in xrange(L):  n[i] *= f[i]- random.uniform(0,f[i]*noise)
    N = sum(n)
    if N == 0.0: # <- this should never be true, except for precision errors!
        n = list(population)
        for i in xrange(L):  n[i] *= 1.0 - random.uniform(0, noise)
        N = sum(n)
        if N == 0.0: return population
    for i in xrange(L): n[i] /= N

##    Alternative noise model:
##
##    for i in xrange(L): n[i] *= f[i]
##    N = sum(n) 
##    if N == 0.0:  n = list(population);  N = 1.0
##    m = N*noise
##    r = [abs(float(i % 2) - random.random()) for i in range(L-1)]
##    r.sort()
##    r.extend([1.0,0.0])
##    for i in xrange(L): n[i] = (n[i] - n[i]*noise + m*(r[i]-r[i-1])) / N
        
    return tuple(n)


def _numeric_Replicator(population, fitness, noise):
    """Replacement for function _Replicator that makes use of numerical
    python (module Numeric or (even better) numarray required!)
    """
    n = asarray(population)
    L = len(population)
    f = fitness
    n = n * (f - f * uniform(0, noise, (L,)))
    N = sum(n)
    if N == 0.0: # actually, this should never happen!
        return _numeric_QuickReplicator(population, fitness)
    return n / N

if HAS_NUMERIC: Replicator = _numeric_Replicator
else: Replicator = _Replicator


def _QuickReplicator(population, fitness):
    """Determines the distribution of species in the next generation
    A faster replacement for Replicator if noise = 0.0. 
    """  
    n = list(population)
    L = len(population)
    f = fitness
    for i in xrange(L): n[i] *= f[i]
    N = sum(n)
    if N == 0.0: return population
    for i in xrange(L): n[i] /= N
    return tuple(n)

def _numeric_QuickReplicator(population, fitness):
    """Replacement for _QuickReplicator that makes use of numerical python"""
    p = population * fitness
    N = sum(p)
    if N == 0.0: return population
    else: return p/N

if HAS_NUMERIC: QuickReplicator = _numeric_QuickReplicator
else: QuickReplicator = _QuickReplicator 


class GenDynamicsFunction(object):
    def __init__(self, payoff, e=0.0, noise=0.0, N=2, samples=1.0):
        """Generate a replicator dynamics function

        A replicator dynamics function determines the composition of the
        population of the next generation from the composition of the population
        of the previous generation.

        payoff - two dimensional array of floats: payoff[a,b] should yield the 
            payoff of player a when playing against player b.

        e - correlation factor, float (range: 0.0 to 1.0): The higher the
            correlation factor the more likely it is that individuals interact
            with individuals of the same species instead of a different species.
            e = 0.0 means random interaction. e = 1.0 means interaction is fully
            confined to the same species.

        noise - float: randomness of the redistribution between species. A noise
            level of 0.0 means that redistribution is solely based on fittnes. A
            noise level of 1.0 means that it is totally random.  

        N - integer (N >= 1): Number of players in one game, e.g. number of
            individuals that interact at once.

        samples - integer or float: number (or percentage) of samples to be taken.
            If samples = 1.0 or if the number of possible combinations is smaller
            than samples no sampling algorithm will be used.        

        return value - function (population) -> population: A replicator function
            that takes a population distribution as argument and computes the
            population distribution of the next generation.

            population - tuple of floats: Population ratio. Each number in the
                tuple represents the share the respective species has from the
                whole population.
            return value - the same.
    """
        if isinstance(noise, 0.0.__class__) and (noise < 0.0 or noise > 1.0):
            raise ValueError,"noise = %f violates 0.0 <= noise <= 1.0"%noise
        self.fitness = GenFitnessFunction(payoff, e, N, samples)
        if noise == 0.0:
            self.function = QuickReplicator
            self.params = tuple()
        else:
            self.noise = noise
            self.function = Replicator
            self.params = (self.noise, )
            
    def __call__(self, population):
        return self.function(population, self.fitness(population),
                             *self.params)



########################################################################
#
#   Tests
#
########################################################################


if __name__ == "__main__":
    import systemTest
    systemTest.DynamicsTest()
    


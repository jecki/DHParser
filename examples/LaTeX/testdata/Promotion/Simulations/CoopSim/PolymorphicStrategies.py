"""Polymorphic strategies are strategies that may change between the
generational cycles of the population dynamical process.

One type of polymorphic strategies are meta strategies that imitate one of the
ordinary strategies and that can change the strategy they imitate
between the generational cycles of the population dynamical simulation.

The most common meta strategy would be 'copy the best', i.e.
a polymorphic strategy that imitates an arbitrary ordinary strategy
in the first generation and always imitates the strategy with the greatest
evolutionary success in following generations.

Another type of polymorphic strategies could be evolutionary strategies that
are base on genetic algorithms.
"""


import random, copy
from Strategies import *


###############################################################################
#
# Base class for polymorphic strategies
#
###############################################################################

class PolymorphicStrategy(Strategy):
    """Abstract base class for all polymorphic strategies.
    """ 
    def evolve(self, deme):
        """Adjusts the polymorphic strategy."""
        raise NotImplementedError



###############################################################################
#
# Base class for meta strategies
#
###############################################################################

class MetaStrategy(PolymorphicStrategy):
    """Abstract base class for all meta strategies.

    Attributes:
        snatched  - the ordinary strategy that is imitated by the
                    polymorphic strategy.
    """
    def __init__(self):
        PolymorphicStrategy.__init__(self)
        self.snatched = None
        self.snatch(TitForTat())

    def _pick(self, strategies, performances):
        """Snatches the strategy with the best performance.
        If there are several equally good strategies, then if the
        "snatched" strategy is among them it is picked. Otherwise a
        strategy is picked randomly from the best strategies.
        """
        ranking = [(strategies[i], performances[i]) \
                   for i in xrange(len(strategies)) \
                   if not isinstance(strategies[i], PolymorphicStrategy)]
        ranking.sort(key = lambda x: -x[1])
        bestP = ranking[0][1]
        snatchedName = str(self.snatched)
        i = 0
        while i < len(ranking) and ranking[i][1] == bestP:
            if str(ranking[i][0]) == snatchedName: return
            i += 1
        selected = random.choice(ranking[:i+1])[0]
        print str(self)+": "+str(self.snatched)+" -> "+str(selected)        
        self.snatch(selected)

    def register(self, simSetup):
        self.snatched.register(simSetup)

    def firstMove(self):
        return self.snatched.firstMove()

    def nextMove(self, myMoves, opMoves):
        return self.snatched.nextMove(myMoves, opMoves)

    def evolve(self, deme):
        raise NotImplementedError
    
    def snatch(self, stgy):
        """Imitate the strategy 'stgy' in the following generations."""
        assert not isinstance(stgy, PolymorphicStrategy), \
            "Polymorphic strategies cannot be imitated themselves."      
        self.snatched = copy.copy(stgy)
        self.randomizing = stgy.randomizing


################################################################################
#
# Copy the Best, Copy the Majority
#
################################################################################

class CopyTheBest(MetaStrategy):
    """A meta strategy that copies the best ordinary strategy, i.e.
    the ordinary strategy which has the highest fitness.
    """
    def evolve(self, deme):
        self._pick(deme.species, deme.fitness())


class CopyTheMajority(MetaStrategy):
    """A meta strategy that copies the ordinary strategy with the highest
    population share.
    """
    def evolve(self, deme):
        self._pick(deme.species, deme.distribution)


_copythebest = CopyTheBest()
_copythemajority = CopyTheMajority()

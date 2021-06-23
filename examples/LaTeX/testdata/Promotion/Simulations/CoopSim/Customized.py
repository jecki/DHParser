"""Module "Customized.py" may contain user extensions to CoopSim.
Use with care!!!"""

## Just like on the "User Defined Strategies" page of the CoopSim application
## window, you can define your own user strategies as well as custom
## simulation setups in this module. The advantage of using module customized
## the "User Defined Strategies" page is that you can use your own python
## editor. Also, it is possible to take full control of the whole
## application via the function Customized.main (see below) that is called
## immediatly after initializing the CoopSim main application window.

## All user Strategies in this module must be derived from
## the class Strategies.Strategy and implement the firstMove as
## well as the nextMove methods. Remember that in order to use a user
## defined strategy class, it must be instantiated. See the example
## below.

## Modules Simulation and Strategies must be imported here in order to
## define user strategies and/or custom simulation setups.

from Simulation import *
from Strategies import *


### The following flags from CoopSim can be overridden here:
##
##DISABLE_USER_STRATEGIES = False   
##SIMPLEX_FLAVOR = Simplex.VECTORS # Simplex.TRAJECTORIES


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

def main(simwindow):
    """Customized.main will be calld right after initializing the
    CoopSim main application window. (Use with care!!!)"""
    pass

def filterStrategies(sl):
    """Filters the set of available strategies."""
    return sl

def filterModels(md):
    """Filters the set of available modles."""
    return md

##def filterStrategies(sl):
##    """Only two state automata strategies."""
##    # example: only two state automata and user defined strategies!
##    fl = [s for s in sl if sl.__class__.__module__ == "UserStratgies" \
##          and not sl.__class__ == TwoStateAutomaton]
##    fl.extend(genAllAutomata())
##    return fl
##
##def filterModels(md):
##    """Only one model with all two state automata."""
##    for k in md:
##        if md[k].__class__.__module__ != "UserStrategies": del md[k]
##    am = SimSetup("All Automata", genAllAutomata())
##    am._userDefined = False
##    md[am.name] = am
##    return md


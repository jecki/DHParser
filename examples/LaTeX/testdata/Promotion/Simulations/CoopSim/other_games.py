
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

twostateautomata = genAllAutomata()

CHICKEN = (5., 4., 0., 2.)
chicken_game = SimSetup(name         = "Chicken Game",
                        strategyList = twostateautomata,
                        payoff       = CHICKEN)

STAG_HUNT = (3., 5., 1., 0.)
stag_hunt_game = SimSetup(name         = "Stag Hunt",
                          strategyList = twostateautomata,
                          payoff       = STAG_HUNT) 


## To change the flavor of the simplex diagram uncomment one(!) of the
## following lines

# SIMPLEX_FLAVOR = Simplex.NULL           # Turn off simplex drawing!
# SIMPLEX_FLAVOR = Simplex.TRAJECTORIES   # WARNING: this is slow!
# SIMPLEX_FLAVOR = Simplex.SCALED_VECTORS # arrows scaled by field strength
# SIMPLEX_FLAVOR = Simplex.VECTORS        # standard simplex


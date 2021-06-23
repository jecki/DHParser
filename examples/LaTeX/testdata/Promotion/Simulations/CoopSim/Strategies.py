"""Implements Strategies for the 2-player prisoner's dilemma as
finite automata."""

import random
# makes sure that there is set support for Python versions < 2.3
from PyPlotter.Compatibility import *  


###############################################################################
#
# Some convenient helper functions
#
###############################################################################

def invertMove(move):
    """--> inverted move. (0 becomes1 and 1 becomes 0)"""
    if move == 0:  return 1
    else:  return 0

def frequency(myMoves, opMoves, myType, opType):
    """--> frequency of the oponent playing myType (either 0 or 1) if
    I played opType (either 0 or 1) the round before."""
    #startRound = opMoves.index(0)
    #i = len(myMoves)-1 - startRound
    i = len(myMoves)-1
    N = 0;  M = 0
    while i > 0:
        if myMoves[-(i+1)] == myType:
            N += 1
            if opMoves[-i] == opType:
                M += 1
        i -= 1
    if N == 0:  return 1.0  # rather arbitrary choice !!!
    else:  return float(M) / float(N)

def PCC(myMoves, opMoves):
    """--> frequency of the oponent cooperating if I cooperated
    the round before."""
    return frequency(myMoves, opMoves, 1, 1)

def PCD(myMoves, opMoves):
    """--> frequency of the oponent cooperating if I did not
    cooperate the round before."""
    return frequency(myMoves, opMoves, 0, 1)

def PDC(myMoves, opMoves):
    """--> frequency of the oponent defecting if I cooperated
    the round before."""
    return frequency(myMoves, opMoves, 1, 0)



###############################################################################
#
# Base class for all strategies in the reiterated 2-person prisoner's dilemma
#
###############################################################################

class Strategy(object):
    """Abstract base class for all Strategies.

    Public attributes:
        simSetup    - Reference to the simulation setup
        randomizing - Flag that indicates whether this strategy makes use
                      of random numbers.
    """
    def __str__(self):
        return self.name

    def __repr__(self):
        return self.__class__.__name__+"()"

    def __eq__(self, other):
        if isinstance(other, Strategy):  return self.name == other.name
        else:  return False
        
    def __ne__(self, other):
        return not self.__eq__(other)
        
    def __init__(self):
        """Initialize Strategy. The name is set to the class name"""
        self.name = self.__class__.__name__
        self.simSetup = None
        self.randomizing = False
        
    def register(self, simSetup):
        """Gives the strategy access to the simulation parameters.
        This is needed for certain cheating strategies like
        end game cheaters, but should normally not be used!"""
        self.simSetup = simSetup

    def firstMove(self):
        """Determines whether the first move is cooperative (1) or not (0)

        return value  - integer, 0 or 1, where 0 means do not cooperate and
            1 means cooperate.
        """
        raise NotImplementedError

    def nextMove(self, myMoves, opMoves):
        """Determines whether the next move is cooperative (1) or not (0)

        myMoves - list of integers (0 or 1): all preceeding moves of this
            player
        opMoves - list of integers (0 or 1): preceeding moves of opponent

        return value  - integer, 0 or 1, where 0 means 'do not cooperate' and
            1 means 'cooperate'.
        """
        raise NotImplementedError


###############################################################################
#
# diverse strategies for the 2 person reiterated PD
#
###############################################################################
    
class Dove(Strategy):
    """Always cooperates no matter what the other player does."""
    def firstMove(self):
        return 1
    def nextMove(self, myMoves, opMoves):
        return 1

class Hawk(Strategy):
    """Never cooperate no matter what the other player does."""
    def firstMove(self):
        return 0
    def nextMove(self, myMoves, opMoves):
        return 0

class TitForTat(Strategy):
    """Plays 'tit for tat': Starts friendly and defects if the other
    player did so in the last round."""
    def firstMove(self):
        return 1
    def nextMove(self, myMoves, opMoves):
        return opMoves[-1]

class TatForTit(TitForTat):
    """Plays 'tat for tit'. Punishes defections like TFT, but also
    starts with a defection."""
    def firstMove(self):
        return 0

class TitForTwoTats(Strategy):
    """Punishes defections only every second time. Starts friendly."""
    def firstMove(self):
        self.defectionCounter = 0
        return 1
    def nextMove(self, myMoves, opMoves):
        if opMoves[-1] == 0:  self.defectionCounter += 1
        if self.defectionCounter >= 2:
            self.defectionCounter = 0
            return 0
        else:  return 1

class TwoTitsForTat(Strategy):
    """Punishes every defection with two defections. Starts friendly."""
    def firstMove(self):
        self.punishCounter = 0
        return 1
    def nextMove(self, myMoves, opMoves):
        if self.punishCounter >= 1:
            self.punishCounter -= 1
            return 0
        elif opMoves[-1] == 0:
            self.punishCounter = 1
            return 0
        else:  return 1

class Grim(Strategy):
    """Cooperates until the first defection of the opponent, then 
    nevers cooperates any more.
    """
    def firstMove(self):
        self.punish = False
        return 1
    def nextMove(self, myMoves, opMoves):
        if self.punish:  return 0
        elif opMoves[-1] == 1:  return 1
        else:  
            self.punish = True
            return 0

class Pavlov(Strategy):
    """Plays 'win stay, loose shift'. Starts with a defection."""
    def firstMove(self):
        self.condition = 0
        return self.condition
    def nextMove(self, myMoves, opMoves):
        if opMoves[-1] == 0:
            self.condition = invertMove(self.condition)
        return self.condition

class Random(Strategy):
    """Plays random moves."""
    def __init__(self):
        Strategy.__init__(self)
        self.randomizing = True
    def firstMove(self):
        return random.randint(0,1)
    def nextMove(self, myMoves, opMoves):
        return random.randint(0,1)
    
class FixedPattern(Strategy):
    """Plays a given pattern all the time."""
    def __repr__(self):
        return self.__class__.__name__+"("+repr(self.path)+")"
    def __init__(self, path=(1,0,0,1)):
        Strategy.__init__(self)
        self.path = path
        for i in self.path: self.name += str(i)
    def firstMove(self):
        self.pos = 0
        return self.path[self.pos]
    def nextMove(self, myMoves, opMoves):
        self.pos = (self.pos+1) % len(self.path)
        return self.path[self.pos]

class SignalingCheater(Strategy):
    """Plays a fixed pattern as a signal first. If the signal
    is finished and the opponent has played the same signal,
    Signaling cheater cooperates for the rest of the game.
    Otherwise it defects for the rest of the game."""
    def __repr__(self):
        return self.__class__.__name__+"("+repr(self.signal)+")"
    def __init__(self, signal=(0,1,1)):
        Strategy.__init__(self)
        self.signal = signal
        for i in self.signal: self.name += str(i)
    def firstMove(self):
        self.pos = 0
        return self.signal[self.pos]
    def nextMove(self, myMoves, opMoves):
        self.pos += 1
        if self.pos < len(self.signal):
            return self.signal[self.pos]
        else:
            if tuple(opMoves[:len(self.signal)]) == self.signal:
                return 1
            else: return 0

class Tester(Strategy):
    """Plays defective in the first two rounds. If the opponent
    does not react (by defecting), Tester plays defective in every
    second round. Otherwise it plays 'Tit for Tat' after two rounds
    of unconditioned cooperation (to console the opponent).
    """
    def firstMove(self):
        self.state = "Test"
        return 0
    def nextMove(self, myMoves, opMoves):
        if self.state == "Test":
            self.state = "Evaluate"
            return 0
        elif self.state == "Evaluate":
            if opMoves[-1] == 0:  
                self.state = "Consolation"
                return 1
            else:
                self.state = "Dove"
                return 0
        elif self.state == "Consolation":
            self.state = "TitForTat"
            return 1
        elif self.state == "Dove":
            self.state = "Hawk"
            return 1
        elif self.state == "Hawk":
            self.state = "Dove"
            return 0
        elif self.state == "TitForTat":
            return opMoves[-1]
        else:  
            raise AssertionError, \
                  "Tester: state %s is not a valid state!"%self.state

class GenerousTFT(Strategy):
    """Plays 'tit for tat', but tries to break up series of continued mutual
    defection or alternating defection and cooperation by an (otherwise)
    unmotivated cooperation offer."""
    def firstMove(self):
        return 1
    def nextMove(self, myMoves, opMoves):
        if len(myMoves) >= 5 and \
           (myMoves[-5:] == [0,0,0,0,0] or myMoves[-5:] == [1,0,1,0,1]):
            return 1
        else: return opMoves[-1]

class Joss(Strategy):
    """Plays 'tit for tat', but defects unmotivated with a random
    probability of 10 per cent."""
    def __init__(self):
        Strategy.__init__(self)
        self.randomizing = True
    def firstMove(self):
        return 1
    def nextMove(self, myMoves, opMoves):
        if opMoves[-1] == 0:  return 0
        else:
            if random.random() < 0.1:  return 0
            else:  return 1

class Downing(Strategy):
    """Tries to estimate the probability of beeing punished. Cooperates if this
    probability is greater than a certain value (0.9 by default), otherwise
    tries to deceive.
    """
    def __repr__(self):
        return self.__class__.__name__+"("+repr(self.threshold)+")"    
    def __init__(self, threshold = 0.9):
        Strategy.__init__(self)
        self.threshold = threshold
        self.name += " %1.2f"%self.threshold
    def firstMove(self):
        return 1
    def nextMove(self, myMoves, opMoves):
        if len(myMoves) < 3: return 1
        elif len(myMoves) < 6:  return 0
        elif len(myMoves) == 6:  return 1
        else:
            i = min(len(myMoves)-1, 20)
            playedD = 0;  punished = 0
            while i > 0:
                if myMoves[-(i+1)] == 0:
                    playedD += 1
                    if opMoves[-i] == 0:
                        punished += 1
                i -= 1
            if playedD == 0:
                return opMoves[-1]
            else:
                punishFreq = float(punished) / float(playedD)
                if punishFreq > self.threshold:
                    return 1
                else:  return 0
                
class Tranquilizer(Strategy):
    """Plays 'tit for two tats', but with an continuously increasing
    number of unmotivated random defections."""
    def __init__(self):
        Strategy.__init__(self)
        self.randomizing = True
    def firstMove(self):
        self.evilFactor = 0.0
        return 1
    def nextMove(self, myMoves, opMoves):
        if self.evilFactor < 0.5:  self.evilFactor += 0.01
        if opMoves[-2:] == [0,0]:
            return 0
        else:
            if random.random() < self.evilFactor: return 0
            else:  return 1

class ParameterizedTFT(Strategy):
    """Plays 'Tit for Tat' with a certain amount of random errors that
    is defined by the evil rate (probability of defecting instead of
    cooperating) and good rate (probability of cooperating instead of
    defecting).
    """
    def __repr__(self):
        return self.__class__.__name__ + "(" + repr(self.goodrate) + \
               ", " + repr(self.evilrate) + ")"    
    def __init__(self, goodrate=0.2, evilrate=0.05):
        assert goodrate >= 0.0 and goodrate <= 1.0, "goodrate must be >= 0 and <= 1!"
        assert evilrate >= 0.0 and evilrate <= 1.0, "evilrate must be >= 0 and <= 1!"
        Strategy.__init__(self)
        self.randomizing = True
        self.goodrate = goodrate
        self.evilrate = evilrate
        self.name = "P_TFT %1.2f %1.2f" % (self.goodrate,self.evilrate)
        if self.goodrate == 1.0 and self.evilrate == 0.0:
            self.name += " (Dove)"
        elif self.evilrate == 1.0 and self.goodrate == 0.0:
            self.name += " (Hawk)"
        elif self.goodrate == 0.0 and self.evilrate == 0.0:
            self.name += " (TitForTat)"
        elif self.goodrate == 0.5 and self.evilrate == 0.5:
            self.name += " (Random)"
        elif self.goodrate == 1.0 and self.evilrate == 1.0:
            self.name += " (Inverted)"
    def firstMove(self):
        if random.random() < self.evilrate:  return 0
        else:  return 1
    def nextMove(self, myMoves, opMoves):
        if opMoves[-1] == 0:
            if random.random() < self.goodrate:  return 1
            else:  return 0
        else:
            if random.random() < self.evilrate:  return 0
            else:  return 1          

            
class EndGameCheater(TitForTat):
    """Plays 'tit for tat', but cheats in the 
    last n rounds. (n = 1 per default)."""
    def __repr__(self):
        return self.__class__.__name__+"("+repr(self.n)+")"    
    def __init__(self, n=1):
        TitForTat.__init__(self)
        self.n = n
        self.name += "%3i"%n
    def firstMove(self):
        if self.simSetup.iterations - self.n <= 0:
            return 0
        else:  return 1
    def nextMove(self, myMoves, opMoves):
        if len(myMoves) >= self.simSetup.iterations - self.n:
            return 0
        else:
            return TitForTat.nextMove(self, myMoves, opMoves)


###############################################################################
#
# Two State Automata
#
###############################################################################


class TwoStateAutomaton(Strategy):
    """Plays one of 26 two state automata strategies. The
    strategy of the automata will be determined by a
    five character string that is passed to the constructor.
    Each character can be either 'D' (Dove) or 'H' (Hawk).

    The characters read as follows:
        first  character:    starting state
        2nd and 3rd:         when in state 'D': set state
                             to 2nd char if oponent played
                             'D' or to 3rd char if oponent
                             played 'H'

        4th and 5th:         when in state 'H': see above...

    Example:
        'DDHDH' - Tit for Tat
        'DDHHH' - Grim
    """
    def __repr__(self):
        return self.__class__.__name__+"("+repr(self.programString)+")"
    def __init__(self, programString="DDHDH"):
        Strategy.__init__(self)
        self.name = "AM: " + programString

        dic = { 'D':1, 'H':0 }
        self.initialState = dic[programString[0]]
        self.state = self.initialState
        self.progString = programString
        self.prog = [ [dic[programString[4]], dic[programString[3]]], \
                      [dic[programString[2]], dic[programString[1]]] ]

        # give some of the automata a more understandable name

        if   programString == "DDHHH":  self.name += " (GRIM)"
        elif programString == "DDHDH":  self.name += " (TIT FOR TAT)"
        elif programString == "DDHHD":  self.name += " (TWEEDLEDUM)"
        elif programString == "DDHDD":  self.name += " (TWEEDLEDEE)"
        elif programString == "HDDHD":  self.name += " (TWEETYPIE)"
        elif programString == "HDHDH":  self.name += " (TAT FOR TIT)"
        elif programString == "HDHHD":  self.name += " (PAVLOV)"
        elif programString == "HDHDD":  self.name += " (SIMPLETON)"
        elif programString == "HHDHD":  self.name += " (INVERTED)"
        elif programString[0:3] == "DDD": self.name += " (DOVE)"
        elif programString[0] == "H" and programString[3:5] == "HH":
            self.name += " (HAWK)"
    def firstMove(self):
        self.state = self.initialState
        return self.state
    def nextMove(self, myMoves, opMoves):
        self.state = self.prog[self.state][opMoves[-1]]
        return self.state


###############################################################################
#
# class Programmed
#
###############################################################################

##~ class Programmed(Strategy):
##~     def __init__(self, program="1", expected="1", punishCycles=10000):
##~         Strategy.__init__(self)
##~         if program == "1111" and expected == "1110":
##~             self.name = "Humpty " + str(punishCycles)
##~         elif program == "1110" and expected == "1111":
##~             self.name = "Dumpty " + str(punishCycles)
##~         else:
##~             self.name = "Prog %s,%s,%i"%(program,expected,punishCycles)
##~         assert len(program) == len(expected), \
##~             "Program %s and %s do not have the same length!" \
##~             % (program, expected)
##~         self.program = program
##~         self.length = len(program)
##~         self.expected = expected[-1] + expected[:-1]     
##~         self.punishCycles = -1
##~     def firstMove(self):
##~         self.pointer = 1
##~         self.punish = 0
##~         return int(self.program[0])
##~     def nextMove(self, myMoves, opMoves):
##~         if self.punish > 0:
##~             self.punish -= 1
##~             self.pointer = (self.pointer + 1) % self.length            
##~             return 0
##~         elif self.punish == 0:
##~             self.punish -= 1
##~             move = int(self.program[self.pointer])
##~             self.pointer = (self.pointer + 1) % self.length
##~             return move            
##~         else:
##~             if opMoves[-1] != int(self.expected[self.pointer]):
##~                 self.punish = self.punishCycles - 1
##~                 self.pointer = (self.pointer + 1) % self.length                
##~                 return 0
##~             else:
##~                 move = int(self.program[self.pointer])
##~                 self.pointer = (self.pointer + 1) % self.length
##~                 return move

                
###############################################################################
#
# More Strategies
#
###############################################################################

class MrX(Strategy):
    """submitted by: Bjoern van den Bruck
    Step 1: Start defecting until opponent defects for the first time.
    Step 2: Cooperate 5 times
    Step 3: Analyse opponent behaviour during the last four rounds:
            0 or 1 defections: go back to step 1
            2 defections:      play random 
            3,4 defections:    play tit for tat
    """
    def __init__(self):
        Strategy.__init__(self)
        self.randomizing = True
    def firstMove(self):
        self.state = "Step 1"
        self.counter = 0
        return 0
    def nextMove(self, myMoves, opMoves):
        while True:
            if self.state == "Step 1":
                if opMoves[-1] == 1:  return 0
                else:
                    self.state = "Step 2"
                    self.counter = 5
                    return 1
            elif self.state == "Step 2":
                self.counter -= 1
                if self.counter <= 1:  self.state = "Step 3"
                return 1
            elif self.state == "Step 3":
                defections = 3 - sum(opMoves[-3:])
                if defections <= 1: self.state = "Step 1"
                elif defections == 2: self.state = "Random"
                else:  self.state = "TFT"
            elif self.state == "Random":
                return random.randint(0,1)            
            else:
                return opMoves[-1]

class Stefan_Pennartz(Strategy):
    """submitted by: Stefan Pennartz
    
    Start cooperating. Analyse all previous opponent moves. If the 
    cooperation ratio is greater than 50% play TFT, otherwise don't
    cooperate. 
    """
    def firstMove(self):
        return 1
    def nextMove(self, myMoves, opMoves):
        coopRatio = sum(opMoves)/float(len(opMoves))
        if coopRatio > 0.5: return opMoves[-1]
        else:  return 0

class FriendlyHuman(Strategy):
    """submitted by: Alex Mainzer
    Table based stratgy. (No description yet!)
    """
    def firstMove(self):
        self.coopList = [1, 11, 21, 31, 3, 2, 13, 23, 22, 33, 5, 4, 15, 25, 7, 6, 17, 27, 26, 37] 
        self.allList = [1, 0, 11, 10, 21, 20, 31, 30, 3, 2, 13, 12, 23, 22, 33, 32, 5, 4, 15, 14, 25, 24, 35, 34, 7, 6, 17, 16, 27, 26, 37, 36]
        self.winsCounter = 1
        self.lostsCounter = 1
        self.deflectsCounter = 0
        self.graciousLimit = 15
        self.madeOffer = 0
        return 1
    
    def nextMove(self, myMoves, opMoves):
        if opMoves[-1] == 1 and myMoves[-1] == 0: self.lostsCounter += 1    # zaehler fuer verlorenen zuege
        if opMoves[-1] == 0 and myMoves[-1] == 1: self.winsCounter += 1     # zaehler fuer gewonnene zuege
        if opMoves[-1] == 0:
            self.deflectsCounter += 1       # zaehler fuer aufeinanderfolgende deflections
        else:
            self.deflectsCounter = 0

        # zaehler, um festzustellen op eine cooperation angeboten wurde
        self.madeOffer += 1
        if self.madeOffer == 3:
            self.madeOffer = 0

        # TitForTat fuer die ersten beide zuege spielen
        if len(myMoves) <= 2:
            if opMoves[-1] == 0:
                return 0
            else:
                return 1
        else:
            # falls eine neue zugkombination auftritt, diesen aus der liste entfernen
            self.toVal = (myMoves[-1]+myMoves[-2]*2)*10+opMoves[-1]+opMoves[-2]*2+opMoves[-3]*4
            for x in self.allList[:]:
                if x == self.toVal: self.allList.remove(x)  
            # willkuer spricht fuer random, und wird ausgebeutet
            if len(self.allList) < 5:          
                return 0
            # versuche lange reihen von deflections zu unterbrechen
            elif self.deflectsCounter > 4 and len(myMoves) > self.graciousLimit:
                self.madeOffer = 1
                self.graciousLimit *= 5     # zeitspanne bis zur naechsten deflection exp vergroessern
                return 1
            # wenn die bilanz der letzen 5 zuege negativ wird, keine cooperation mehr 
            elif self.madeOffer == 0 and len(myMoves) > 5 and opMoves[-1]+opMoves[-2]+opMoves[-3]+opMoves[-4]+opMoves[-5] < 3:
                return 0
            # wenn die bilanz auf lange sicht negativ wird, keine cooperation mehr
            elif len(myMoves) > 9 and self.winsCounter/self.lostsCounter < .90:
                return 0
            # ansonsten spiele den regulaeren zug
            else:
                self.returnValue = 0
                for x in self.coopList[:]:
                    if x == self.toVal: self.returnValue = 1
                return self.returnValue


class LessGrim(Strategy):
    """submitted by: Sven Sommer
    1. Sei freundlich (Fang immer mit "K" an)
    2. Provoziere nicht (Defektiere nie als erster)
    3. Sei beleidigt (Defektiert der Gegner, defektiere in den folgenden Zuegen)
    4. Akzeptiere grosszuegige Angebote (Kooperiert der Gegner nach Defektion
       mind. zwei Mal hintereinander, kooperiere ebenfalls zwei Mal)
    5. Sei konsequent (Tu in der Regel das, was du in der letzten Runde getan hast)    
    """
    def firstMove(self):
        return 1
    def nextMove(self, myMoves, opMoves):
        if len(myMoves) <= 3:  return opMoves[-1]
        elif opMoves[-2:] == [1,1]:  return 1
        elif opMoves[-3:-1] == [1,1] and myMoves[-2] == 0:  return 1
        elif myMoves[-1] == 0:  return 0
        elif opMoves[-1] == 0:  return 0
        else:  return 1


def genericDowning(round, myMoves, opMoves, startRound=0, friendly=False):
    if friendly:
        if round - startRound <= 3:  return 1
        if round - startRound <= 6:  return 0
        if round - startRound == 7:  return 1
    else:
        if round - startRound <= 3:  return 0
        if round - startRound <= 7:  return 1
    pcc = PCC(myMoves, opMoves)
    pcd = PCD(myMoves, opMoves)
    pdc = PDC(myMoves, opMoves)
    if pdc > 0.5:  return 0
    if pcd >= pcc:  return 0
    return 1

class GenericDowning(Strategy):
    """submitted by Sven Sommer"""
    def __repr__(self):
        return self.__class__.__name__+"("+repr(self.friendly)+")"    
    def __init__(self, friendly = True):
        Strategy.__init__(self)
        self.friendly = friendly
        if friendly: self.name += " (friendly)"
    def firstMove(self):
        return 1
    def nextMove(self, myMoves, opMoves):
        return genericDowning(len(myMoves), myMoves, opMoves, 0, self.friendly)


class Smart(Strategy):
    """submitted by: Sven Sommer
    1. Sei freundlich (Fang immer mit "K" an)
    2. Provoziere nicht (Defektier nie als erster)
    3. Kenne deinen Feind (Defektiert der Gegner, teste ihn)
        3a. Defektiere dreimal
        3b. Kooperiere viermal
    4. Pass dich an (ab der Runde, in der der Gegner zum erstem Mal
       defektiert hat)
        4a. Berechne die Wahrscheinlichkeit, dass der Gegner kooperiert,
            wenn ich kooperier: P(k|k)
        4b. Berechne die Wahrscheinlichkeit, dass der Gegner kooperiert,
            wenn ich defektier: P(k|d)
        4c. Berechne die Wahrscheinlichkeit, dass der Gegner defektiert,
            wenn ich kooperier: P(d|k)
    5. Lass dich nicht ausbeuten (Defektier, wenn P(d|k) > 0.5)
    6. Beute zu gutmuetige Strategien aus (Defektier, wenn P(k|d)>=P(k|k))
    7. Kooperier ansonsten    
    """
    def firstMove(self):
        self.firstDefection = -1
        return 1
    def nextMove(self, myMoves, opMoves):
        if self.firstDefection < 0:
            if opMoves[-1] == 0:
                self.firstDefection = len(myMoves)-1
                return 0
            else:  return 1
        else:  return genericDowning(len(myMoves), myMoves, opMoves,
                               self.firstDefection, friendly = False)

        
class Absurdistan1(Strategy):
    """submitted by: Christian Erlen
    1. Spiele TitForTat, bis der Gegner zweimal in Folge defektiert.
    2. Bestrafe den Gegner durch zwei Defektionen
    3. Spiele TitForTat, bis der Gegner erneut zweimal in Folge defektiert.
    4. Analyse Phase 1 und Phase 2 im Hinblick auf die relative Haeufigkeit
        von Kooperation
        a) Zunehmende Unfreundlichkeit (Phase 1 enthielt mehr Kooperation
           als Phase 2) -> Defektiere solange, bis der Gegner ein
           Friedensangebot macht (zwei Kooperationen in Folge). Beginne dann
           wieder mit Phase 1
        b) Zunehmende Freundlichkeit (Phase 1 enthielt gleichviel oder
           weniger Kooperation als Phase 2): Spiele Phase 1 (nach Bestrafung)
    """
    def firstMove(self):
        self.state = "Phase 1"
        self.resetCounters()
        return 1
    def resetCounters(self):
        self.s1n = 0;  self.s1c = 0
        self.s2n = 0;  self.s2c = 0
    def nextMove(self, myMoves, opMoves):
        if self.state == "Phase 1":
            self.s1n += 1;  self.s1c += opMoves[-1]
            if self.s1n >= 2 and opMoves[-2:] == [0,0]:
                self.state = "Phase 2"
                return 0 # erste Bestrafungsdefektion
            return opMoves[-1]
        elif self.state == "Phase 2":
            self.state = "Phase 3"
            return 0 # zweite Bestrafungsdefektion
        elif self.state == "Phase 3":
            self.s2n += 1;  self.s2c += opMoves[-1]
            if self.s2n >= 2 and opMoves[-2:] == [0,0]:
                self.state = "Phase 4"
                return 0
            return opMoves[-1]
        elif self.state == "Phase 4":
            rc1 = self.s1c / float(self.s1n)
            rc2 = self.s2c / float(self.s2n)
            self.resetCounters()
            if rc1 > rc2:
                self.state = "Phase 5"
                return 0
            else:
                self.state = "Phase 1"
                return 0
        elif self.state == "Phase 5":
            if opMoves[-2:] == [1, 1]:
                self.state = "Phase 1"
                return 1
            else:  return 0
        else:  raise AssertionError, \
                     "Absurdistan1: self.state = %s not valid"%self.state


class Stabilize(Strategy):
    """submitted by: Paul Boehm
        1. Start out with Tit-for-Tat for 4 Moves
        2. Remember Patterns of length 4.
        3. Defect if more than 20 different patterns are counted
           and the peer is deemed mentally unstable.
    """
    def firstMove(self):
        self.patterns = set()
        return 1
    def nextMove(self, myMoves, opMoves):
        # Start out with Tit-for-Tat for 4 Moves
        if len(opMoves) < 4:
            return opMoves[-1]

        # After that start counting patterns
        pattern = (myMoves[-1], myMoves[-2], myMoves[-3], myMoves[-4],
                   opMoves[-1], opMoves[-2], opMoves[-3], opMoves[-4])
        self.patterns.add(pattern)

        # And defect when the peer seems mentally unstable.
        if len(self.patterns) > 20:
            return 0

        # Otherwise continue with Tit-for-a-Tat
        return opMoves[-1]


class ThreeTimesOut(Strategy):
    """submitted by Philip Seehausen"""
    def firstMove(self):
        self.block = False
        return 1
    def nextMove(self, myMoves, opMoves):
        if self.block: return 0
        if len(myMoves) <= 2:  return 1
        if opMoves[:3] == [0,0,0]:
            self.block = True
            return 0
        else: return 1

class PIN(Strategy):
    """submitted by Philip Seehausen"""
    def firstMove(self):
        self.block = False
        return 0
    def nextMove(self, myMoves, opMoves):
        if self.block:
            if opMoves[-3:] == [1, 1, 1]:
                self.block = False
                return 1
            else: return 0
        else:
            if len(opMoves) >= 3 and opMoves[-3:] == [0, 0, 0]:
                self.block = True
                return 0
            return opMoves[-1]

class AcquaintanceAndTrust(Strategy):
    """submitted by Philip Seehausen"""
    def firstMove(self):
        self.distrust = 0
        return 1
    def nextMove(self, myMoves, opMoves):
        if opMoves[-1] == 0:  self.distrust += 1
        if self.distrust > 0:
            if opMoves[-self.distrust:] == [1] * self.distrust:
                self.distrust = 0
                return 1
            else:
                return 0
        else: return 1
            

###############################################################################
#
# Instantiate Strategies
#
# (if a Strategy class is not instantiated it will not be visible
#  in the game setup dialog. However, it can still be instantiated
#  via the "User Defined Strategies" tab...)
#
###############################################################################

_a = AcquaintanceAndTrust()
_b = PIN()
_c = ThreeTimesOut()

_dove = Dove()
_hawk = Hawk()
_titfortat = TitForTat()
_tatfortit = TatForTit()
_titfortwotats = TitForTwoTats()
_twotitsfortat = TwoTitsForTat()
_grim = Grim()
_pavlov = Pavlov()
_random = Random()
_fixedPattern1001 = FixedPattern((1,1,0,1))
_signalingCheater = SignalingCheater()
_tester = Tester()
_generoustft = GenerousTFT()
_joss = Joss()
_downing = Downing(0.9)
_tranquilizer = Tranquilizer()
## _parameterizedTFT = ParameterizedTFT()

_mrx = MrX()
_stefan_pennartz = Stefan_Pennartz()
_friendlyhuman = FriendlyHuman()
_lessgrim = LessGrim()
_genericDowning = GenericDowning()
_smart = Smart()
_absurdistan = Absurdistan1()
_stabilize = Stabilize()

# The end game cheaters are not regular strategies, because
# they make use of the normally unknown information, when
# the series of iterated PD-games ends. They are included
# only for the the purpose of demonstrating the end game
# effect. In the evolutionary simulation the end game
# effect is very weak, that is: it takes million or billions
# of generations until the system converges to the "Allways
# Defect"-equilibirum!

## _endgamecheater1 = EndGameCheater(1)
## _endgamecheater2 = EndGameCheater(2)
## _endgamecheater3 = EndGameCheater(3)

# to create an arbitrary number of end game cheaters
# edit and uncomment the following line or add a 
# similar line to the "User Defined Strategies" page

## endgamecheaters = [EndGameCheater(i) for i in xrange(1, 200)]

# To avoid confusing the user with too man awkward strategies
# the two state automate are not enabled when the application
# starts. They can be enabled later on by adding a call to
# the following function and saving the return value in a list
# on the "User Defined Strategies" page.

def genAllAutomata():
    """Return a list of all possible two state automata.
    These include the two possible one state automata DOVE and HAWK."""
    l = []
    for i in range(32):
        prog = ""
        for k in range(5):
            if i & (1 << k):  prog += "D"
            else:             prog += "H"

        if (prog[0:3] == "DDD" and prog[3:5] != "DD") or \
           (prog[0] == "H" and prog[3:5] == "HH" and prog[1:3] != "HH"):
            # do not create any doublettes
            continue
        else:
            l.append(TwoStateAutomaton(prog))
    return l

# uncomment or add the following line to the
# "User Defined Strategies" page to enable
# the two state automo

# twostateautomata = genAllAutomata()

# generator functions for parameterized TFTs

def genParameterizedTFTs(grFrom, grTo, grStep,
                         erFrom, erTo, erStep):
    """Generate a list of parameterized TitFotTat strategies.
    The gr* and er* parameters define the range for the
    good- and evilrates (see class ParameterizedTFT for an exmplanation).
    """
    l = []
    goodrate = grFrom
    while goodrate <= grTo:
        evilrate = erFrom
        while evilrate <= erTo:
            l.append(ParameterizedTFT(goodrate, evilrate))
            evilrate += erStep
        goodrate += grStep
    return l

## manyTFTs = genParameterizedTFTs(0.0, 1.0, 0.25, 0.0, 1.0, 0.25)

def genEndGameCheaters(r1, r2):
    """Generate all EndGameCheaters that start cheating from round r1 to r2,
    counted from the last round."""
    return [EndGameCheater(r) for r in xrange(r1, r2+1)]
    
    

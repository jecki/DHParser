"""Functions for the repeated 2 or N-Person symmetric prisoners dilemma."""

import copy, random, math, re
from PopulationDynamics.Compatibility import *
from PolymorphicStrategies import *
from Logging import H1, H2, H3, H1X, H2X, H3X, HTMLLog

   
MATCH_LOG_LEN = 100
NUM_SAMPLES = 10 # Number of matches for calculating the average score
                # in case randomizing strategies or game noise is used
PD_2P_PAYOFF = array([[[1, 1], [5, 0]],\
                      [[0, 5], [3, 3]]])
##PD_2P_PAYOFF = array([[[1.0, 1.0], [3.5, 0.0]],\
##                      [[0.0, 3.5], [3.0, 3.0]]])
MATCH_LOG_OUTSOURCED = False
MATCH_LOG_DIRECTORY = "Matchlogs"
USE_CACHE = True # Cache matches for reuse
if not USE_CACHE:
    MATCH_LOG_OUTSOURCED = False


def vsstr(playerA, playerB):
    return re.sub(" |:|-|,|<|>", "_", str(playerA) + "_vs_" + str(playerB))

###############################################################################
#
# Match Cache
#
###############################################################################

class MatchesCache(object):
    def __init__(self):
        self.cache = {}
        self.pending = None
    def __len__(self):
        return len(self.cache)
    def __genkey(self, pl):
        # return "".join([str(p) for p in pl])
        if isinstance(pl[0], MetaStrategy):  s0 = str(pl[0].snatched)
        else:  s0 = str(pl[0])
        if isinstance(pl[1], MetaStrategy):  s1 = str(pl[1].snatched)
        else:  s1 = str(pl[1])
        return (s0,s1,tuple(ravel(pl[2])),pl[3],pl[4],pl[5])
    def check(self, *parameters):
        if not USE_CACHE: return False
        key = self.__genkey(parameters)
        if self.cache.has_key(key):
            self.pending = self.cache[key]
            return True
        else:  return False
    def fetch(self):
        return self.pending
    def store(self, result, *parameters):
        if not USE_CACHE: return
        if isinstance(parameters[0], PolymorphicStrategy): return
        if isinstance(parameters[1], PolymorphicStrategy): return
        key = self.__genkey(parameters)
        self.cache[key] = tuple(result)
        
cache = MatchesCache()
outsourced_match_logs = MatchesCache()
outsourced_last_name = ""

def outsourced_pages():
    """->(matchlog, filename) for each cached match log."""
    assert MATCH_LOG_OUTSOURCED, "Outsourced match log has been turned off."
    for key, value in outsourced_match_logs.cache.iteritems(): yield value
    
    
###############################################################################
#
# The reiterated 2 players prisoners dilemma
#
###############################################################################

def noiseFilter(move, noise):
    """Turns 'move' into its opposite with the probability noise."""
    if random.random() < noise:
        if move == 1:  return 0
        else:  return 1
    else:  return move

def printLog(start, stop, movesA, movesB):
    s = ""; l = ["<pre>"]
    for i in xrange(start, stop):
        s += str(movesA[i]) + " " + str(movesB[i]) 
        if (i+1) % 10 == 0:
            l.append(s+"\n")
            s = ""
        else: s += " "*3
    if s != "": l.append("\n")
    l.append(s+"</pre>")
    return l    
    
def ReiteratedPD(playerA, playerB, payoffs, iterations, 
                 samples = NUM_SAMPLES, noise = 0.0, log=None):
    """Plays a repeated 2 person PD with the given strategies,
    payoff matrix and number of iterations.

    playerA, playerB - Strategy objects. Strategies of player A and B
        respectively
    payoffs - numeric array (or wrapped array). Payoff matrix of the
        PD-Game.
    iterations - integer or float. Number of rounds to play (if integer) or
        termination probability for each round (if float)
    noise - float [0.0 - 1.0]: probability of disturbances. Disturbances a
        simulated by turning the intended move of a player into its opposite.
    samples - number of sample matches (only useful for randomizing strategies)
    log (optional) - list. A list to which the log of the match is
        appended.

    return value - tuple of floats. The average payoff of for each strategy
    """
    global outsourced_last_name
    if type(iterations) == type(0.):
        if iterations <= 0.0 or iterations >= 1.0:
            raise ValueError, "%f violates 0.0 < iterations < 1.0 !"%iterations
        iterations = int(math.log(0.5, iterations)+0.5)
    elif iterations <= 0:  raise ValueError, "%i iterations <= 0 !"%iterations

    if not (playerA.randomizing or playerB.randomizing or noise != 0.0):
        samples = 1

    if cache.check(playerA, playerB, payoffs, iterations, samples, noise):
        result, movesA, movesB = cache.fetch()        
    else:
        result = [0, 0]
        for x in xrange(samples):
            A = noiseFilter(playerA.firstMove(), noise)
            B = noiseFilter(playerB.firstMove(), noise)
            movesA = [A]
            movesB = [B]
            result[0] += payoffs[A,B,0]
            result[1] += payoffs[A,B,1]
        
            for r in xrange(iterations-1):
                A = noiseFilter(playerA.nextMove(movesA, movesB), noise)
                B = noiseFilter(playerB.nextMove(movesB, movesA), noise)
                movesA.append(A)
                movesB.append(B)
                result[0] += payoffs[A,B,0]
                result[1] += payoffs[A,B,1]
        result[0] /= float(samples*iterations)
        result[1] /= float(samples*iterations)
        cache.store((tuple(result), tuple(movesA), tuple(movesB)),
                    playerA, playerB, payoffs, iterations, samples, noise)
        
    if log != None:
        if MATCH_LOG_OUTSOURCED and outsourced_match_logs.check(playerA,
           playerB, payoffs, iterations, samples, noise):
            l, outsourced_last_name = outsourced_match_logs.fetch()
            for item in l:  log.append(item)
        else:    
            nameA = str(playerA);  nameB = str(playerB)
            pointsA = "%1.3f"%result[0];  pointsB = "%1.3f"%result[1]
            s = nameA + " : " + nameB + \
                " "*max(3,(40-len(nameA)-len(nameB))) + \
                pointsA + " : " + pointsB
            log.append('<p><pre><a name="' + vsstr(playerA, playerB) + \
                       '"></a>'+ s + "</pre>\n")

            if MATCH_LOG_OUTSOURCED or MATCH_LOG_LEN >= iterations:
                log.extend(printLog(0, iterations, movesA, movesB))
            else:
                log.extend(printLog(0, MATCH_LOG_LEN/2, movesA, movesB))
                log.append("...\n")
                log.extend(printLog(iterations-MATCH_LOG_LEN/2, iterations, 
                                    movesA, movesB))
            log.append("</p><br />\n\n")

            if MATCH_LOG_OUTSOURCED:
                outsourced_last_name = MATCH_LOG_DIRECTORY + "/" + \
                    ("%5i"%len(outsourced_match_logs)).replace(" ","0") +\
                       vsstr(playerA, playerB) + ".html"
                outsourced_match_logs.store((log, outsourced_last_name),
                                            playerA, playerB, payoffs,
                                            iterations, samples, noise)
    return result


###############################################################################
#
#  A Tournament of strategies in the reiterated 2 players PD
#
###############################################################################

def GenPayoffMatrix(strategies, payoffs = PD_2P_PAYOFF, iterations = 200, 
                    samples = NUM_SAMPLES, noise = 0.0, log = None,
                    progressCallback = lambda f:1):
    """Generates a payoff matrix for all possible pairings of the
    given strategies.

    stragies - list of strategies
    payoffs  - payoff matrix for the 2 person prisoners dilemma
    iterations - float or int: number of iterations in the reiterated PD
    samples - int: number of samples (only useful for randomizing strategies)
    noise - float [0.0-1.0]: in game noise
    log - HTMLLog: simulation results are appended here.
    progressCallback - callback function with a single argument
        f - float[0.0-1.0] to indicate the progress in generating the payoff
        matrix.
    """
    strategies_copy = copy.deepcopy(strategies)
    M = [];  myLog = [];  resultLog = []; summaryLog = [];
    for i in xrange(len(strategies)):  M.append([0.]*len(strategies))
    l, c = 0,0;  lines = len(strategies);  full = float(lines * (lines + 1) / 2)
    for s in strategies:
        for t in strategies_copy[l:]:
            if log != None: matchLog = []
            else: matchLog = None
            a,b = ReiteratedPD(s, t, payoffs, iterations, samples, 
                               noise, matchLog)
            if l == c:
                M[l][c] = (a+b)/2.0
            else:
                M[l][c] = a;  M[c][l] = b
            if log != None:
                if MATCH_LOG_OUTSOURCED:
                    resultLog.append('<a href="'+outsourced_last_name + \
                                     '" target="_blank">' + \
                                     re.sub("<.*?>|\n","", matchLog[0]) + \
                                     "</a>\n")
                else:
                    resultLog.append('<a href="#'+vsstr(s,t)+'">' + \
                                     re.sub("<.*?>|\n","", matchLog[0]) + \
                                     "</a>\n")
                    myLog.extend(matchLog)
                    myLog.append('<div align="right"><a href="#top">[top]'+\
                                 '</a></div><br />\n')
            c += 1                
            progressCallback((l * lines - l*(l+1)/2 + c) / full)
        l += 1;  c = l

    if log != None:
        t = "";  l = 0;  points = []
        for s in strategies:
            total = sum(M[l])/float(len(strategies));  k = 0
            while k < len(points) and points[k] > total:  k += 1
            points.insert(k, total)
            summaryLog.insert(k, str(s)+":&nbsp;" + \
                              "&nbsp;"*max(1, 30 - len(str(s))) + \
                              "%1.4f"%total + "<br />\n")
            l += 1
        log.appendAt("toc",
                     '<a href="#ranking">1. Tournament Ranking</a><br />\n')
        log.appendAt("toc",
                     '<a href="#results">2. Match Results</a><br />\n')
        if not MATCH_LOG_OUTSOURCED:
            log.appendAt("toc",
                     '<a href="#logs">3. Detailed Match Logs</a><br />\n')
        log.append(H2+'<a name="ranking"></a>Tournament Ranking:'+H2X+ \
                   "<br />\n\n<p><tt>")
        log.extend(summaryLog)
        log.append("</tt></p>")
        log.append('<div align="right"><a href="#top">[top]</a></div>' + \
                   '<br /><br />\n\n')
        log.append(H2+'<a name="results"></a>Match Results:'+H2X+\
                   "<br />\n\n<p><pre>")
        log.extend(resultLog)
        log.append("</pre></p>\n")        
        log.append('<div align="right"><a href="#top">[top]</a></div>' + \
                   '<br /><br />\n\n')
        if not MATCH_LOG_OUTSOURCED:
            log.append(H2+'<a name="logs"></a>Detailed Match Logs:'+H2X+\
                   "<br />\n\n")
            log.extend(myLog)
        
    return array(M)


###############################################################################
#
# Tests
#
###############################################################################

##if __name__ == "__main__":
##    import systemTest
##    systemTest.PDTest()

"""
SocialChoiceDemoSim_run.py - A small simulation for demonstrating that
'critcal cases' appear only relatively rare when mapping individual
preferences unto collective preferences.

This is the front end for the simulation that conducts the simulations and
prints or plots the simulation results.
"""

from math import sqrt

try:
    import psyco
    psyco.full()
    print("psyco JIT speedup enabled")
except ImportError:
    pass

from matplotlib import pylab

from SocialChoiceDemoSim_main import *


def bestInCycle(utilities, cycles):
    """Returns True, if the element with the highest utility
    is caught in a cycle."""
    if len(cycles) == 0: return False
    mx = max(utilities)
    bestList = [i for i, u in enumerate(utilities) if u == mx]
    for best in bestList:
        for cyc in cycles:
            if best in cyc: 
                return True
    return False            

    
def simEffectAlternatives(plot, individuals, alternatives, 
                          cultureRatio = 0.0, repetitions = 100):
    labels = []
    for ind in individuals:
        cyclesDict = {}.fromkeys(alternatives, 0)
        for i in range(repetitions):
            for alt in alternatives:
                profile = genPartialCultureProfile(ind, alt, cultureRatio)
                utility, cyc = condorcet(profile)
                if len(cyc) > 0: cyclesDict[alt] += 1
    
        cycles = [cyclesDict[alt] / float(repetitions) for alt in alternatives]
        labels.append(str(ind)+" individuals")
        plot.plot(alternatives, cycles, label = labels[-1])
    
    plot.set_xlabel("number of alternatives")
    plot.set_ylabel("ratio of cyclic preferences")
    if cultureRatio == 0.0:
        plot.set_title("impartial culture")
    else:
        plot.set_title("partial culture r = %1.2f"%cultureRatio)  
    plot.legend(labels)


def simEffectIndividuals(plot, individuals, alternatives, 
                         cultureRatio = 0.0, repetitions = 100):
    labels = []
    for alt in alternatives:
        cyclesDict = {}.fromkeys(individuals, 0)        
        for i in range(repetitions):
            for ind in individuals:
                profile = genPartialCultureProfile(ind, alt, cultureRatio)
                utility, cyc = condorcet(profile)
                if len(cyc) > 0: cyclesDict[ind] += 1
    
        cycles = [cyclesDict[ind] / float(repetitions) for ind in individuals]    
        labels.append(str(alt)+" alternatives")
        plot.plot(individuals, cycles, label = labels[-1])
        
    plot.set_xlabel("number of individuals")
    plot.set_ylabel("ratio of cyclic preferences")
    if cultureRatio == 0.0:
        plot.set_title("impartial culture")
    else:
        plot.set_title("partial culture r = %1.2f"%cultureRatio)        
    plot.legend(labels)
     

def simSeriesAlternatives():
    figure = pylab.figure(figsize=(16.0, 9.0))
    
    individuals = [3, 10, 100, 1000]
    alternatives = range(3,10) + range (10,27,3)
        
    plot = figure.add_subplot(211)
    simEffectAlternatives(plot, individuals, alternatives, cultureRatio = 0.0, repetitions = 1000)
    
    plot = figure.add_subplot(212)
    simEffectAlternatives(plot, individuals, alternatives, cultureRatio = 0.1, repetitions = 1000)    
    
    figure.savefig("alternatives.eps", dpi=300)   

    
def simSeriesIndividuals():
    figure = pylab.figure(figsize=(16.0, 9.0))
    
    individuals = [3,4,5]+range(10,101,5)+range(125,1001,25)
    alternatives = [3,5,9]
        
    plot = figure.add_subplot(211)
    simEffectIndividuals(plot, individuals, alternatives, cultureRatio = 0.0, repetitions = 1000)
    
    plot = figure.add_subplot(212)
    simEffectIndividuals(plot, individuals, alternatives, cultureRatio = 0.1, repetitions = 1000)    
    
    figure.savefig("individuals.eps", dpi=300)        


if __name__ == "__main__":
#    simSeriesIndividuals()
    simSeriesAlternatives()
    pylab.show()


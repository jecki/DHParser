#!/usr/bin/python
# Example6.py - Schuessler's simulation


"""
Example6.py - A simulation of the reiterated PD with exit option.

Usually one would assume that cooperation in the reiterated PD
will break down if the player's are given a costless exit option
so that players can "hit and run". Rudolf Schuessler (reference
see below) has shown that this is not necessarily so.

The simulation (a simplyfied form of Schuessler's simulation) uses
two strategies: CONCO which cooperates as long as the partner does,
but makes use of it's exit option imediately when the partner does
not reciprocate cooperation. ALL_D defects in the first round and
then uses it's exit option. Partners are drawn from a strategy pool
that consists of the player's that have dismissed (or were dismissed
by) their parnter after the last round. 

(For a discussion of the reiterated PD with exit option seee:
Rudolf Schuessler: Kooperation unter Egoisten: Vier Dilemmata,
R. Oldenbourg, Muenchen 1997, S.61ff.)
"""

try:
    from PyPlotter import awtGfx as GfxDriver
except ImportError:
    from PyPlotter import wxGfx as GfxDriver

from PyPlotter import Graph, Gfx
import Dynamics
from Compatibility import array


# Definition of the Game

T, R, P, S = 6,4,2,1  # payoff parameter for the Prisoner's Dilemma

forced_exit = 0.05   # Chance that cooperation is terminated by external factors
initial_distribution = array([0.5, 0.5])
rounds = 200
generations = 50


def OneGeneration(distribution, rounds):
    """Calculate one generation of the reiterated PD-simulation
    with exit option. 'distribution' is a 2-tuple that contains
    the population shares of CONO and ALL_D player's. 'rounds'
    is the number of rounds that are played until the strategy
    distribution is updated through replicator dynamics. The
    return value is a 2-tuple of the average score for each
    strategy.
    """
    account = array([0.0, 0.0])
    cc = distribution[0]**2 / 2
    dd = distribution[1]**2 / 2
    cd = distribution[0] * distribution[1]
    
    for i in xrange(rounds):       
        account[0] += (2*cc*R + cd*S) / distribution[0]
        account[1] += (2*dd*P + cd*T) / distribution[1]

        poolC = cc * forced_exit * 2 + cd
        poolD = dd * 2 + cd
        pool = poolC + poolD
       
        cc += poolC**2 / (2 * pool) - cc*forced_exit
        dd = poolD**2 / (2 * pool)
        cd = poolC * poolD / pool
        
    account[0] /= rounds
    account[1] /= rounds
    return account


def Schuessler():
    """A simulation of the repeated PD with exit option.
    """

    # Open a window for graphics output.
    
    gfx = GfxDriver.Window(title = "Repeated PD with exit option")

    # Generate a dynamics function from the payoff table.
    # dynFunc = Dynamics.GenDynamicsFunction(payoff_table, e=0.0,noise=0.0)

    # Set the graph for plotting the plotting dynamics.

    graph = Graph.Cartesian(gfx, 0., 0., float(generations), 1.,
        "Repeated Prisoner's Dilemma with exit option",
        "generations", "population share")
    graph.addPen("CONCO", Gfx.Pen(color = Gfx.GREEN, lineWidth = Gfx.MEDIUM))
    graph.addPen("ALL_D", Gfx.Pen(color = Gfx.RED, lineWidth = Gfx.MEDIUM))

    # Calculate the population dynamics and plot the graph.

    population = initial_distribution
    graph.addValue("CONCO", 0, population[0])
    graph.addValue("ALL_D", 0, population[1])
    for g in range(1, generations+1):
        population = Dynamics.QuickReplicator(population, OneGeneration(population, rounds))
        graph.addValue("CONCO", g, population[0])
        graph.addValue("ALL_D", g, population[1])         
        if g % (generations/10) == 0:  gfx.refresh()

    # Wait until the user closes the window.

    gfx.waitUntilClosed()
    

if __name__ == "__main__":
    print __doc__
    Schuessler()


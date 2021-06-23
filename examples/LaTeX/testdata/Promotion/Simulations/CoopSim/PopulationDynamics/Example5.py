#!/usr/bin/python 
# Example5.py - currency game

"""
Example5.py - A simulation of the 'currency game'

The currency game simulates the establishment of a certain metal
(gold or silver) as standard currency. In a given population of
players, every player uses either gold or silver as currency.
Every round, each player considers changeing to an other currency:

Usually (that is with a probability of 1-epsilon) a player choses
the currency that is being used by the majority of players. On
rare occasions (that is with a probability of epsilon) a player
choses the currency at random.

It is to be expected that the system quickly assumes a state where
either almost only gold or almost only silver will be used. Due to
the random factor, the equilibria may be swapped over time. In the
long run both equilibria will be sustained over roughly equally long
periods. (This, however, can be changed by adjusting the factor
'gamma' which expresses a universally hold preference of the one
metal over the other.)

(Description of the 'currency game' following: Peyton Young:
Individual Strategy and Social Choice, Princeton and Oxford,
Princeton University Press, 1996, p.11-16.)
"""

import random

try:
    from PyPlotter import awtGfx as GfxDriver
except ImportError:
    from PyPlotter import wxGfx as GfxDriver

from PyPlotter import Graph, Gfx
import Dynamics
from Compatibility import array


## Definition of the currency game 

def CurrencyGame(distribution, epsilon=0.5, gamma=0.5):
    """Determines the number of players that will use gold or
    silver as currency in the next round."""

    N = distribution["gold"] + distribution["silver"]
    i = random.randint(1, N)
    if i <= distribution["gold"]:
        s = "gold"
        distribution["gold"] -= 1
    else:
        s = "silver"
        distribution["silver"] -= 1

    p = distribution["gold"] / float(N)
    x = random.random()
    if x >= epsilon:
        if p > gamma: distribution["gold"] += 1
        elif p < gamma: distribution["silver"] += 1
        else: distribution[s] += 1
    else:
        if random.random() >= 0.5: distribution["gold"] += 1
        else: distribution["silver"] += 1
            
    return distribution


def RunCurrencyGame():
    """A simulation of the 'currency game'."""

    # Open a window for graphics output.
    
    gfx = GfxDriver.Window(title = "Sender - Receiver Game")

    # Set the graph for plotting the plotting dynamics.

    graph = Graph.Cartesian(gfx, 0., 0., 500., 10.,
        "Currency Game", "rounds", "gold currency")
    graph.addPen("gold currency", Gfx.RED_PEN)

    distribution = {"gold": 5, "silver": 5}
    graph.addValue("gold currency", 0, distribution["gold"])

    # Play the currency game for 2500 rounds and plot the results.
    
    for g in range(1, 2501):
        distribution = CurrencyGame(distribution)
        graph.addValue("gold currency", g, distribution["gold"])
        if g % 100 == 0: gfx.refresh()

    ## Wait until the user closes the window.

    gfx.waitUntilClosed()

    

if __name__ == "__main__":
    print __doc__
    RunCurrencyGame()
    

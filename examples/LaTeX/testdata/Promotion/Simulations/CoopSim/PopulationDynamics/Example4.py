#!/usr/bin/python
# Example4.py - Sender - Receiver Game (full simulation)


"""
Example4.py - A population dynamical simulation of the
'sender - receiver game' with 16 strategies.

The 'sender-receiver game' is about signal transmission between
two players. Depending on a binary state variable taking the value
T1 or T2 the sender either transmitts signal M1 or signal M2.
It depends on the type of the sender which of these signal signifies
which internal state of the sender. The receiver does react on the
signal with either action A1 or action A2. If the action taken was
in accordance with the internal state of the sender, both players
get a reward, otherwise they do not.

For the sake of simplicity it is assumed that every player takes the
role of the sender for half of the time.

This simulation starts with randomly distributed population of the
16 possible player strategies. This population dynamics is calculated
for 50 generations and plotted into a common cartesian cordinate
system. After 50 generations one of the two stable equilibriums
("I1" or "I2") should have crystalized out.

(Description of the 'sender-receiver game' following: Brian Skyrms:
Evolution of the Social Contract, Cambridge University Press, 1996,
p.80-94.)
"""

try:
    from PyPlotter import awtGfx as GfxDriver
except ImportError:
    from PyPlotter import wxGfx as GfxDriver

from PyPlotter import Graph
import Dynamics
from Compatibility import array


# Definition of the sender receiver game:

PlayerTypes = {"I1":  "0101", "I2":  "1010", "I3":  "0110", "I4":  "1001",
               "I5":  "0100", "I6":  "1000", "I7":  "0111", "I8":  "1011",
               "I9":  "0001", "I10": "0010", "I11": "0000", "I12": "0011",
               "I13": "1101", "I14": "1110", "I15": "1100", "I16": "1111"}
PlayerNames = PlayerTypes.keys()


def Payoff(player1, player2):
    """Determins the payoffs depending on the player types.
    """
    s1 = [int(c) for c in PlayerTypes[player1][0:2]]
    r1 = [int(c) for c in PlayerTypes[player1][2:4]]
    s2 = [int(c) for c in PlayerTypes[player2][0:2]]
    r2 = [int(c) for c in PlayerTypes[player2][2:4]]
    payment = 0.0
    if r2[s1[0]] == 0: payment += 0.25
    if r2[s1[1]] == 1: payment += 0.25
    if r1[s2[0]] == 0: payment += 0.25
    if r1[s2[1]] == 1: payment += 0.25
    return payment


def GenPayoffTable(playerList):
    """Generates the payoff table for the players in 'playerList'.
    """
    table = []
    for player1 in playerList:
        line = []
        for player2 in playerList:
            line.append(Payoff(player1, player2))
        table.append(line)
    return table

payoff_table = array(GenPayoffTable(PlayerNames))


def SignalingGame():
    """Eine populationsdynamische Simulation des 'demand game'.
    """

    # Open a window for graphics output.
    
    gfx = GfxDriver.Window(title = "Sender - Receiver Game")

    # Generate a dynamics function from the payoff table.

    dynFunc = Dynamics.GenDynamicsFunction(payoff_table, e=0.0,noise=0.0)

    # Set the graph for plotting the plotting dynamics.

    graph = Graph.Cartesian(gfx, 0., 0., 10., 1.,
        "Sender - Receiver Game", "generations", "population share")
    for name in PlayerNames:  graph.addPen(name)

    # Calculate the population dynamics and plot the graph.

    population = Dynamics.RandomDistribution(len(PlayerNames))
    for g in range(51):
        for i in range(len(PlayerNames)):
            graph.addValue(PlayerNames[i], g, population[i])
        population = dynFunc(population)      
        if g % 10 == 0:  gfx.refresh()

    # Wait until the user closes the window.

    gfx.waitUntilClosed()
    

if __name__ == "__main__":
    print __doc__
    SignalingGame()
    

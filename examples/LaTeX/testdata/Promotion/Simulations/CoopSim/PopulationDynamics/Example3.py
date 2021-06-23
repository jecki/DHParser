#!/usr/bin/python
# Example3.py: Sender - Receiver Game (simplex diagram)


"""
Example3.py - An example for population dynamics in the
'sender-receiver game' 

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

From the 16 (named "I1" to "I16") possible player strategies, the
strategies I1, I3, and I4 are selected for visualizing the
population dynamics of populations with different shares of these
three players as a vector field in a simplex diagram.

The strategies I1, I2 and I3 play according to the following rules:

I1: Send signal M1, when in state T1 and M2 when in state T2.
    Perform action A1, when receiving signal M1 and A2 when receiving M2.

I3: Send signal M1, when in state T1 and M2 when in state T2.
    Perform action A2, when receiving signal M1 and A1 on signal M2.

I4: Send signal M2, when in state T1 and M1 when in state T2.
    Do A1, on receiving signal M1 and A2 on M2.

(Description of the 'sender-receiver game' following Brian Skyrms:
 Evolution of the Social Contract, Cambridge University Press,
 1996, p.80-94.)
"""

try:
    from PyPlotter import awtGfx as GfxDriver
except ImportError:
    from PyPlotter import wxGfx as GfxDriver

from PyPlotter import Simplex
import Dynamics
from Compatibility import array


# definition of the sender receiver game:

PlayerTypes = {"I1":  "0101", "I2":  "1010", "I3":  "0110", "I4":  "1001",
               "I5":  "0100", "I6":  "1000", "I7":  "0111", "I8":  "1011",
               "I9":  "0001", "I10": "0010", "I11": "0000", "I12": "0011",
               "I13": "1101", "I14": "1110", "I15": "1100", "I16": "1111"}
    

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

payoff_table = array(GenPayoffTable(["I3","I4","I1"]))


def SignalingGame():
    """A simulation of the 'sender - receiver game'.
    """
    
    # Open a window for graphics output.
    
    gfx = GfxDriver.Window(title = "Sender - Receiver Game")

    # Generate a dynamics function from the payoff table.

    dynFunc = Dynamics.GenDynamicsFunction(payoff_table, e=0.0,noise=0.0)

    # Set up a simplex diagram for showing the dynamics as a
    # vector field.
    
    diagram = Simplex.Diagram(gfx, dynFunc, "Sender - Receiver Game",
                              "I3", "I4", "I1",
                              styleFlags = Simplex.VECTORS,
                              raster = Simplex.GenRaster(25))

    # Show the vector field.

    diagram.show()

    # Wait until the user closes the window.

    gfx.waitUntilClosed()

    

if __name__ == "__main__":
    print __doc__
    SignalingGame()
    

#!/usr/bin/python
# Example2.py: Demand Game (patches diagram)

"""
Example1.py - An example for the population dynamical simulation of
the 'demand game' with three strategies.

The demand game is a game where a given amount of money is being
divided between two players accordings to the following rules

1. Each player may freely demand a certain share of the money. No
player knows, how much the other player demands.

2. If the sum of the demanded shares is smaller than the whole amount
of money, each player gets exactly the share that he has demanded.

3. But if the sum of the demanded shares exceeds the whole amount
then no player gets anything.

The following three player strategies are used:

Strategy 1:  Demand 1/3 of the whole amount of money
Strategy 2:  Demand 1/2 of the whole amount of money
Strategy 3:  Demand 2/3 of the whole amount of money

(See also: Brian Skyrms: Evolution of the Social Contract,
Cambridge University Press, 1996, p.11-21.)

In this example the population dynamics of the three player population
playing the demand game will be shown as coloured patches in a
simplex diagram. Each patch represents a certain disribution of the
population among the three player strategies. From generation to
generation the colour of the patches is updated so that each patch
takes the color of the patch that the population as drifted to. After
a while all areas of attraction should have the colour of their
respective attraction point.
"""

try:
    from PyPlotter import awtGfx as GfxDriver
except ImportError:
    from PyPlotter import wxGfx as GfxDriver
    
from PyPlotter import Simplex
import Dynamics
from Compatibility import array


payoff_table = array([[1./3, 1./3, 1./3],
                      [2./3,   0.,   0.],
                      [1./2,   0., 1./2]])

def DemandGame():
    """A population dynamical simulation of the demand game,
    demonstrating the use of simplex diagrams.
    """
    
    # Open a window for graphics output.
    
    gfx = GfxDriver.Window(title="Demand Game")   
    
    # Generate the appropriate dynamical function from the payoff table.
    
    dynamicsFunction = Dynamics.GenDynamicsFunction(payoff_table, e=0.0)

    # Set up a simplex diagram of patches with a density of 51.
    
    diagram = Simplex.Diagram(gfx, dynamicsFunction, "Demand Game",
                              "Demand 1/3", "Demand 2/3", "Demand 1/2",
                              styleFlags = Simplex.PATCHES, density = 51)

    # Calculate 20 generations and show the updated colours of the
    # patches after each generation.

    diagram.show(0)
    gfx.refresh()
    for i in range(20):
        diagram.show(1)
        gfx.refresh()

    # Finally, make the candidates for fixed points visible.

    diagram.showFixedPoints((1.0, 0.5, 0.0))
    gfx.refresh()

    # Wait until the application window is closed by the user.

    gfx.waitUntilClosed()
    

if __name__ == "__main__":
    print __doc__
    DemandGame()
    

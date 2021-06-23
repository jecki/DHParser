#!/usr/bin/python
# Example1.py: Demand Game (trajectory diagram)

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

In this example the population dynamics of a three player population
playing the demand game will be shown as trajectories in a simplex
diagram. The three player strategies are the following:

Strategy 1:  Demand 1/3 of the whole amount of money
Strategy 2:  Demand 1/2 of the whole amount of money
Strategy 3:  Demand 2/3 of the whole amount of money

(See also: Brian Skyrms: Evolution of the Social Contract,
Cambridge University Press, 1996, p.11-21.)
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
    
    #  Generate the appropriate dynamical function from the payoff table.
    
    dynamicsFunction = Dynamics.GenDynamicsFunction(payoff_table, e=0.0)

    # Set up a simplex diagram of pseudo trajectories with
    # 350 randomly distributed sample points.
    
    diagram = Simplex.Diagram(gfx, dynamicsFunction, "Demand Game",
                              "Demand 1/3", "Demand 2/3", "Demand 1/2",
                              styleFlags = Simplex.TRAJECTORIES,
                              raster = Simplex.RandomGrid(350))

    # Calculate and show the trajectories originating from these
    # staring points for a length of 8 generations.

    diagram.show(8)

    # Wait until the application window is closed by the user.

    gfx.waitUntilClosed()
    

if __name__ == "__main__":
    print __doc__
    DemandGame()
    

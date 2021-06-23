#!/usr/bin/python
# Example2.py: Simplex diagram of the demand game

"""
Example2.py - Demonstration of a simplex diagram. The example 
is a simulation of the 'demand game' with three strategies.

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

import random
import Simplex, Compatibility
GfxDriver = Compatibility.GetDriver()
print "Using Driver: ",GfxDriver.driverName


DemandGame = { "11":1/3.0, "12":1/3.0, "13":1/3.0, 
               "21":2/3.0, "22":0.0,   "23":0.0,
               "31":1/2.0, "32":0.0,   "33":1/2.0 }

def PopulationDynamics(pr, pay, e=0.0, noise=0.0):
    """population ratio, payofftable, correlation, noise ->
    new population ratio.
    """
    n1, n2, n3 = pr[0], pr[1], pr[2]
    p1=pay["11"]*(n1+e*(n2+n3))+pay["12"]*(n2-e*n2)+pay["13"]*(n3-e*n3)
    p2=pay["22"]*(n2+e*(n1+n3))+pay["21"]*(n1-e*n1)+pay["23"]*(n3-e*n3)
    p3=pay["33"]*(n3+e*(n1+n2))+pay["31"]*(n1-e*n1)+pay["32"]*(n2-e*n2)
    P = p1+p3+p3/3.0
    if P > 0.0:  n1 *= p1/P;  n2 *= p2/P;  n3 *= p3/P
    N = n1+n2+n3
    if N == 0.0:  n1, n2, n3 = pr[0], pr[1], pr[2];  N = 1.0
    m = N*noise
    a = random.random();  b = 1.0-random.random()
    if b < a: c = a;  a = b;  b = c
    n1 = n1 - n1*noise + m*a
    n2 = n2 - n2*noise + m*(b-a)
    n3 = n3 - n3*noise + m*(1.0-b)
    return (n1/N, n2/N, n3/N)

    
def RunDemandGame():
    """A population dynamical simulation of the demand game,
    demonstrating the use of simplex diagrams.
    """
    
    # Open a window for graphics output.
    
    gfx = GfxDriver.Window(title="Demand Game")   
    
    #  Define the dynamics function.
    
    dynamicsFunction = lambda p: PopulationDynamics(p,DemandGame, 
                                                    e=0.0,noise=0.0)

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
    RunDemandGame()
    

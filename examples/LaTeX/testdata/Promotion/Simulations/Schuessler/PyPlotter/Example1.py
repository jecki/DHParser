#!/usr/bin/python
# Example1.py: demonstration of the Graph.Cartesian class

"""
Example1.py - This is a simple example of the use of the 
Graph.Cartesian class to plot a graph on a cartesian
coordinate plain. 
"""

import math
import Graph, Gfx, Compatibility
GfxDriver = Compatibility.GetDriver()
print "Using Driver: ",GfxDriver.driverName
   
def GraphDemo():
    """Demonstrates the use of class Graph.Cartesian by plotting the
    function f(x) = sin(x).
    """
    
    # Open a window for graphics output.
    
    gfx = GfxDriver.Window(title="Function Plotter")   
    
    #  Set up the the graph, use a logarithmic scale
    
    gr = Graph.Cartesian(gfx, -math.pi*2, -1.1, math.pi*2, 1.1,
        "Demonstration of the PyPlotter.Graph.Cartesian class","X","Y")
    
    # plot the graph, calculating the function for each x value that corresponds to
    # a screen pixel
    
    gr.addPen("sin(x)", Gfx.RED_PEN)
    for x in gr.xaxisSteps(-math.pi*2, math.pi*2):
        gr.addValue("sin(x)", x, math.sin(x))
    
    # Wait until the application window is closed by the user.

    gfx.waitUntilClosed()
    

if __name__ == "__main__":
    print __doc__
    GraphDemo()
    

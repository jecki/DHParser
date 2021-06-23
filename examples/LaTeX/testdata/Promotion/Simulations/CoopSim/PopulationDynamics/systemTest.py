"""System Tests for the Evolution module.
"""


def DynamicsTest():
    try:
        from Plot import awtGfx as GR
    except:
        from Plot import wxGfx as GR
    from Plot import Simplex
    import Dynamics
    import ArrayWrapper
        
    DemandGame = ArrayWrapper.array([[1/3., 1/3., 1/3.], 
                                     [2/3., 0., 0.],
                                     [1/2., 0., 1/2.]])
   
    gfx = GR.Window()
    tp = Simplex.Plotter(gfx, "Demand 1/3", "Demand 2/3", "Demand 1/2")
    diag = Simplex.Trajectory(tp,
               Dynamics.GenDynamicsFunction(DemandGame, e=0.06, noise=0.1),
               raster = Simplex.GenRaster(25))
    diag.step(8)
    gfx.waitUntilClosed()


if __name__ == "__main__":
    DynamicsTest()

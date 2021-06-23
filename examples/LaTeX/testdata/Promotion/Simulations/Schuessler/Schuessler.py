"""Functions for the reiterated Prisoner's Dilemma with exit option.

For a discussion of the reiterated PD with exit option seee:
Rudolf Schuessler: Kooperation unter Egoisten: Vier Dilemmata,
R. Oldenbourg, Muenchen 1997, S.61ff. The concepts and strategies
in this modules are based on Schuessler's book."""

from PyPlotter import Graph, Gfx
from PyPlotter.Compatibility import *
GfxDriver = GetDriver()

# Definition of the Game

T, R, P, S = 6,4,2,1  # payoff parameters for the Prisoner's Dilemma

forced_exit = 0.05   # Chance that cooperation is terminated 
                     # by external factors
initial_distribution = (0.5, 0.5)
rounds = 200
generations = 50


def OneGeneration(distribution, rounds):
    """Calculate one generation of the reiterated PD-simulation
    with exit option. 'distribution' is a 2-tuple that contains
    the population shares of CONCO and ALL_D player's. 'rounds'
    is the number of rounds that are played until the strategy
    distribution is updated through replicator dynamics. The
    return value is a 2-tuple of the average score for each
    strategy.
    """
    account = [0.0, 0.0]
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
    return tuple(account)


def PopulationDynamics(population, fitness):
    """Determines the distribution of species in the next generation."""  
    n = list(population)
    L = len(population)
    f = fitness(population)
    for i in xrange(L): n[i] *= f[i]
    N = sum(n)
    if N == 0.0: return population
    for i in xrange(L): n[i] /= N
    return tuple(n)


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
    fitness = lambda p: OneGeneration(p, rounds)
    for g in range(1, generations+1):
        population = PopulationDynamics(population, fitness)
        graph.addValue("CONCO", g, population[0])
        graph.addValue("ALL_D", g, population[1])         
        if g % (generations/10) == 0:  gfx.refresh()

    # To save the graphics in eps uncomment the following line
    # graph.dumpPostscript("schuessler1.eps")

    # Wait until the user closes the window.

    gfx.waitUntilClosed()
    

if __name__ == "__main__":
    print __doc__
    Schuessler()


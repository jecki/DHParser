#!/usr/bin/python

"""Unit test for the Dynamics module."""

import unittest, copy, random
import Dynamics, ArrayWrapper
from Compatibility import *



class AutoTestCase(unittest.TestCase):
    def runTest(self):
        d = dir(self)
        for name in d:
            if name[:4] == "test": exec "self."+name+"()"


def AlmostEqual(a,b, allowedError = 0.0001):
    """Check whether a and b are equal up to an error."""
    if isinstance(a, float) or isinstance(a, int):
        return abs(a-b) <= max(abs(a), abs(b))*allowedError
    else:
        for x,y in map(None, a,b):
            if abs(x-y) > max(abs(x), abs(y))*allowedError: return False
        return True

def CorelatedGame(*args):
    """The more arguments are equal to the first argument,
    the higher the return value."""
    incr = 1.0/len(args)
    r = 0.0
    x = args[0]
    for y in args:
        if y == x:  r += incr
    return r

def GenRandomGame(dim, n, a=0.0, b=1.0):
    if dim < 1: raise ValueError, "dim must be >= 1"
    if dim > n: raise ValueError, "dim must be <= n"
    if dim == 1:
        return [random.uniform(a,b) for x in xrange(n)]
    else:
        return [GenRandomGame(dim-1, n, a, b) for x in xrange(n)]
        

class SelfTest(AutoTestCase):
    def testSelfAlmostEqual(self):
        """AlmostEqual should fail only for larger differences"""
        self.failUnless(AlmostEqual(1.0, 1.0))
        self.failIf(AlmostEqual(0.0001, 0.0002, 0.1))
        self.failUnless(AlmostEqual(1000001, 1000000, 0.01))
        self.failUnless(AlmostEqual((1.0, 0.0), (1.0, 0.0)))
        self.failIf(AlmostEqual((1.0, 1.0, 1.0), (1.0, 1.0, 0.0)))

    def testCorelatedGame(self):
        a = CorelatedGame(0,1,2)
        b = CorelatedGame(0,0,1)
        c = CorelatedGame(1,1,1)
        for x in range(5):
            for y in range(5):
                for z in range(5):
                    r = CorelatedGame(x, y, z)
                    if x == y and x == z: 
                        self.failUnless(r > a and r > b)
                    elif x == y or x == z:
                        self.failUnless(r > a and r < c)
                    else:
                        self.failUnless(r < b and r < c)
                        
    def testGenRandomGame(self):
        M = GenRandomGame(4, 5, 1.0, 2.0)
        for i in range(5**4):
            a = i / 5**3
            b = i % 5**3 / 5**2
            c = i % 5**2 / 5
            d = i % 5
            x = M[a][b][c][d]
            self.failIf(x < 1.0 or x > 2.0)


class TestHelperFunctions(AutoTestCase):   
    def testGenTuples(self):
        """GenTuples should generate increasing number tuples"""
        k = 0
        for i in Dynamics.GenTuples(3, 10):
            n = i[0]*100 + i[1]*10 + i[2]
            self.failUnlessEqual(n, k)
            k += 1
                         
    def testRandomDistributionLength(self):
        """RandomDistribution should return a population of the correct length"""
        # self.failUnlessRaises(ValueError, Dynamics.RandomDistribution(0))        
        p = Dynamics.RandomDistribution(10)
        self.failIf(len(p) != 10)
                         
    def testRandomDistribution(self):
        """RandomDistribution should always return a tuple that adds up to 1.0"""
        p = Dynamics.RandomDistribution(10)
        self.failUnless(AlmostEqual(sum(p), 1.0))
        
    def testUniformDistribution(self):
        """UniformDistribution should always return a tuple that adds up to 1.0"""
        p = Dynamics.UniformDistribution(10)
        self.failUnless(AlmostEqual(p, [1.0/10 for i in range(10)]))
        self.failUnless(AlmostEqual(sum(p), 1.0))
        noise = 0.1
        while noise <= 1.0:
            p = Dynamics.UniformDistribution(10)
            self.failUnless(AlmostEqual(sum(p), 1.0))
            noise += 0.1

    def testUniformDistributionNoise(self):
        """Noise should make a difference in UniformDistribution"""
        p = Dynamics.UniformDistribution(100)
        r = Dynamics.UniformDistribution(100, 0.1)
        self.failIf(AlmostEqual(p, r))
        self.failUnless(AlmostEqual(p, r, 0.101), "To much noise")

    def testRandomSelect(self):
        """Check RandomSelect function"""
        p = [0.0, 0.4, 0.0, 0.0, 0.6, 0.0, 0.0]
        for i in range(100):
            n = Dynamics.RandomSelect(p)
            self.failUnless(n == 1 or n == 4)
        p = Dynamics.RandomDistribution(37)
        for i in range(500):
            n = Dynamics.RandomSelect(p)
            self.failUnless(n >= 0 and n <= 36)
        p = Dynamics.RandomDistribution(68)
        for i in range(500):
            n = Dynamics.RandomSelect(p)
            self.failUnless(n >= 0 and n <= 67)
               
       
class TestFitness(AutoTestCase):    
    def setUp(self):
        self.DemandGame = array([[1.0/3, 1.0/3, 1.0/3],
                                 [2.0/3, 0.0,   0.0],
                                 [1.0/2, 0.0,   1.0/2]])
        self.pop1 = (1/3.0, 1/3.0, 1/3.0)

    def testTrivialCase(self):
        """GenFitness should yield a valid function even if N is only 1"""
        payoff = array([1.0, 2.0, 3.0])
        f = Dynamics.GenFitnessFunction(payoff, N=1)
        p = Dynamics.UniformDistribution(3, 0.8)
        r = f(p)
        for i in range(len(r)):
            self.failUnless(r[i] == payoff[i])
    
    def testQuickFitness2FairGame(self):
        """QuickFitness2 should yield equal fitnesses in a totally fair game"""
        G = ArrayWrapper.array(lambda a,b: 0.3)
        for i in range(20):
            p = Dynamics.RandomDistribution(5)
            f = Dynamics._QuickFitness2(p, G)
            for k in range(1,5):
                self.failIf(f[k] != f[0])       
        
    def testQuickFitness2DemandGame(self):
        """Test QuickFitness with the 'demand game'"""
        fitness = Dynamics._QuickFitness2(self.pop1, self.DemandGame)
        self.failUnless(fitness[2] > fitness[1] and fitness[2] >= fitness[0])       

    def testFitness2ZeroCorrelation(self):
        """Fitness2 should return the same results QuickFitness2 if e=0.0."""
        for i in range(20):
            G = array(GenRandomGame(2, 8))
            for k in range(5):
                p = Dynamics.RandomDistribution(8)
                compare = Dynamics._QuickFitness2(p, G)
                fitness = Dynamics._Fitness2(p, G, 0.0)
                self.failUnless(AlmostEqual(fitness, compare))
                
    def testFitness2Correlation(self):
        """Correlation should make a difference"""
        G = ArrayWrapper.array(CorelatedGame)
        for k in range(20):
            p = Dynamics.RandomDistribution(8)
            compare = Dynamics._QuickFitness2(p, G)
            fitness = Dynamics._Fitness2(p, G, 0.2)
            self.failIf(AlmostEqual(fitness, compare))
        
    
    def testQuickFitness2Players(self):
        """QuickFitness should not make a difference to QF2 in the 2 player case
        """
        for i in range(20):
            G = array(GenRandomGame(2, 8))
            for k in range(5):
                p = Dynamics.RandomDistribution(8)
                compare = Dynamics._QuickFitness2(p, G)
                fitness = Dynamics._QuickFitness(p, G, 2)
                self.failUnless(AlmostEqual(fitness, compare))        

    def testNumericQuickFitness2Players(self):
        """QuickFitness2 and numeric_QuickFitness2 should yield the same result
        """
        for i in range(20):
            G = array(GenRandomGame(2, 8))
            for k in range(5):
                p = Dynamics.RandomDistribution(8)
                compare = Dynamics._QuickFitness2(p, G)
                fitness = Dynamics._numeric_QuickFitness2(p, G)
                self.failUnless(AlmostEqual(fitness, compare)) 
    
    def testQuickFitnessFairGame(self):
        """Fitness should return equal fitnesses a 'totally fair' game"""
        G = ArrayWrapper.array(lambda a,b,c,d: 5.0)
        for i in range(10):
            r = Dynamics.RandomDistribution(7)
            f = Dynamics._QuickFitness(r, G, 4)
            for k in range(1,7):
                self.failIf(f[k] != f[0]) 
            
    def testFitness2Players(self):
        """Fitness should be the same as Fitness2 in the 2 player case"""
        for i in range(20):
            G = array(GenRandomGame(2, 8))
            for k in range(5):
                p = Dynamics.RandomDistribution(8)
                compare = Dynamics._Fitness2(p, G, 0.2)
                fitness = Dynamics._Fitness(p, G, 0.2, 2)
                self.failUnless(AlmostEqual(fitness, compare))    

    def testNumericFitness2Players(self):
        """Fitness2 and numeric_Fitness2 should yield the same values"""
        for i in range(20):
            G = array(GenRandomGame(2, 8))
            for k in range(5):
                p = Dynamics.RandomDistribution(8)
                compare = Dynamics._Fitness2(p, G, 0.2)
                fitness = Dynamics._numeric_Fitness2(p, G, 0.2)
                self.failUnless(AlmostEqual(fitness, compare))
                
    def testFitnessCorrelation(self):
        """Correlation should make a difference"""
        G = ArrayWrapper.array(CorelatedGame)
        for k in range(20):
            p = Dynamics.RandomDistribution(8)
            compare = Dynamics._QuickFitness(p, G, 3)
            fitness = Dynamics._Fitness(p, G, 0.2, 3)
            self.failIf(AlmostEqual(fitness, compare))                       
    
    def testFitnessZeroCorrelation(self):
        """Fitness should return the same results as QuickFitness if e=0.0."""
        for i in range(5):
            G = array(GenRandomGame(4, 7))
            for k in range(5):
                p = Dynamics.RandomDistribution(7)
                compare = Dynamics._QuickFitness(p, G, 4)
                fitness = Dynamics._Fitness(p, G, 0.0, 4)
                self.failUnless(AlmostEqual(fitness, compare))
    

class TestSamplingAlgorithm(AutoTestCase):
    def testSampledQuickFitness2(self):
        """SampledQuickFitness2 should yield similar results as QuickFitness2"""
        for i in range(5):
            G = array(GenRandomGame(2, 8))
            p = Dynamics.RandomDistribution(8)
            fitness = Dynamics._QuickFitness2(p, G)
            failures = 0
            for k in range(5):
                sampled = Dynamics._SampledQuickFitness2(p, G, 1000)
                if not AlmostEqual(fitness, sampled, 0.1): failures += 1
                self.failIf(failures > 1)
    
    def testSampledFitness2(self):
        """SampledFitness2 should yield roughly the same results as Fitness2"""
        for i in range(5):
            G = array(GenRandomGame(2, 8))
            p = Dynamics.RandomDistribution(8)
            fitness = Dynamics._Fitness2(p, G, 0.2)
            failures = 0
            for k in range(5):
                sampled = Dynamics._SampledFitness2(p, G, 0.2, 1000)
                if not AlmostEqual(fitness, sampled, 0.1): failures += 1
                self.failIf(failures > 1)

    def testSampledQuickFitness(self):
        """SampledQuickFitness should yield similar results as QuickFitness"""
        for i in range(5):
            G = array(GenRandomGame(4, 7))
            p = Dynamics.RandomDistribution(7)
            fitness = Dynamics._QuickFitness(p, G, 4)
            failures = 0
            for k in range(5):
                sampled = Dynamics._SampledQuickFitness(p, G, 4, 5000)
                if not AlmostEqual(fitness, sampled, 0.1): failures += 1
                self.failIf(failures > 1)

    def testSampledFitness(self):
        """SampledFitness should yield roughly the same results as Fitness"""
        for i in range(5):
            G = array(GenRandomGame(3, 8))
            p = Dynamics.RandomDistribution(8)
            fitness = Dynamics._Fitness(p, G, 0.2, 3)
            failures = 0
            for k in range(5):
                sampled = Dynamics._SampledFitness(p, G, 0.2, 3, 5000)
                if not AlmostEqual(fitness, sampled, 0.15): failures += 1
                self.failIf(failures > 1)


class TestReplicator(AutoTestCase):
    def testQuickReplicator1(self):
        """Results of QuickReplicator should be sound"""
        for i in xrange(50):
            p = Dynamics.RandomDistribution(50)
            f = array([random.random() for k in xrange(50)])
            r = Dynamics._QuickReplicator(p, f)
            for x in r:
                self.failIf(x < 0.0 or x > 1.0)
            self.failUnless(AlmostEqual(sum(r), 1.0))
        
    def testQuickReplicator2(self):
        """Population should not change when fitnesses are equal"""
        f = [1.0]*10
        for i in xrange(50):
            p = Dynamics.RandomDistribution(10)        
            r = Dynamics._QuickReplicator(p, f)
            self.failIf(not AlmostEqual(p, r))

    def testQuickReplicator3(self):
        """Different fitness values ought to have an impact"""
        p = Dynamics.UniformDistribution(10)
        f = array([1.0, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1])
        for i in xrange(5):
            r = Dynamics._QuickReplicator(p, f)
            for k in range(len(r)-1):
                self.failIf(r[k+1]>=r[k])
            p = r

    def testQuickReplicator4(self):
        """Extinct species should stay extinct."""
        for i in xrange(50):
            f = array([random.uniform(0.5, 1.5) for k in xrange(10)])
            x = random.randint(1, 9)
            p = Dynamics.UniformDistribution(x, 0.5)
            p = concatenate((p, array([0.0] * (10-x))))
            idx = [l for l in range(10) if p[l] == 0.0]
            r = Dynamics._QuickReplicator(p, f)
            for l in idx:
                self.failIf(r[l] != 0.0)

    def testReplicator1(self):
        """Results of Replicator should be sound"""
        for i in xrange(50):
            p = Dynamics.RandomDistribution(50)
            f = array([random.random() for k in xrange(50)])
            r = Dynamics._Replicator(p, f, random.random())
            for x in r:
                self.failIf(x < 0.0 or x > 1.0)
            self.failUnless(AlmostEqual(sum(r), 1.0))

    def testReplicator2(self):
        """Replicator should yield the same results as QR if noise = 0.0"""
        for i in xrange(50):
            p = Dynamics.RandomDistribution(20)
            f = array([random.random() for k in xrange(20)])
            r = Dynamics._QuickReplicator(p, f)
            r2 = Dynamics._Replicator(p, f, 0.0)
            self.failUnless(AlmostEqual(r, r2))

    def testReplicator3(self):
        """Noise should matter"""
        for i in xrange(50):
            p = Dynamics.RandomDistribution(100)
            f = array([random.random() for k in xrange(100)])
            r = Dynamics._QuickReplicator(p, f)
            r2 = Dynamics._Replicator(p, f, 0.5)
            self.failIf(AlmostEqual(r, r2))            

    def testReplicator4(self):
        """Little noise should only matter a little"""
        for i in xrange(50):
            p = Dynamics.RandomDistribution(100)
            f = array([random.random() for k in xrange(100)])
            r = Dynamics._QuickReplicator(p, f)
            r2 = Dynamics._Replicator(p, f, 0.01)
            self.failUnless(AlmostEqual(r, r2, 0.0101))

    def testNumericReplicator0(self):
        """Numeric QuickReplicator should yield the same result as QuickReplicator"""
        for i in xrange(50):
            p = Dynamics.RandomDistribution(20)
            f = array([random.random() for k in xrange(20)])
            r = Dynamics._numeric_QuickReplicator(p, f)
            r2 = Dynamics._numeric_QuickReplicator(p, f)
            self.failUnless(AlmostEqual(r, r2))

    def testNumericReplicator1(self):
        """Results of Replicator should be sound"""
        for i in xrange(50):
            p = Dynamics.RandomDistribution(50)
            f = array([random.random() for k in xrange(50)])
            r = Dynamics._numeric_Replicator(p, f, random.random())
            for x in r:
                self.failIf(x < 0.0 or x > 1.0)
            self.failUnless(AlmostEqual(sum(r), 1.0))

    def testNumericReplicator2(self):
        """Replicator should yield the same results as QR if noise = 0.0"""
        for i in xrange(50):
            p = Dynamics.RandomDistribution(20)
            f = array([random.random() for k in xrange(20)])
            r = Dynamics._numeric_QuickReplicator(p, f)
            r2 = Dynamics._numeric_Replicator(p, f, 0.0)
            self.failUnless(AlmostEqual(r, r2))

    def testNumericReplicator3(self):
        """Noise should matter"""
        for i in xrange(50):
            p = Dynamics.RandomDistribution(100)
            f = array([random.random() for k in xrange(100)])
            r = Dynamics._numeric_QuickReplicator(p, f)
            r2 = Dynamics._numeric_Replicator(p, f, 0.5)
            self.failIf(AlmostEqual(r, r2))            

    def testNumericReplicator4(self):
        """Little noise should only matter a little"""
        for i in xrange(50):
            p = Dynamics.RandomDistribution(100)
            f = array([random.random() for k in xrange(100)])
            r = Dynamics._numeric_QuickReplicator(p, f)
            r2 = Dynamics._numeric_Replicator(p, f, 0.01)
            self.failUnless(AlmostEqual(r, r2, 0.0101))
    
    
class TestGeneratorFunctions(AutoTestCase):
    def testGenFitnessFunction(self):
        """GenFitnessFunction should always return a valid fitness function"""
        g1 = array(GenRandomGame(2, 7))
        g2 = array(GenRandomGame(3, 7))
        f1 = Dynamics.GenFitnessFunction(g1, e=0.0, N=2)
        f2 = Dynamics.GenFitnessFunction(g1, e=0.2, N=2)
        f3 = Dynamics.GenFitnessFunction(g2, e=0.0, N=3)
        f4 = Dynamics.GenFitnessFunction(g2, e=0.2, N=3)
        f5 = Dynamics.GenFitnessFunction(g1, e=0.0, N=2, samples=0.3)
        f6 = Dynamics.GenFitnessFunction(g1, e=0.2, N=2, samples=5)
        f7 = Dynamics.GenFitnessFunction(g2, e=0.0, N=3, samples=10000)
        f8 = Dynamics.GenFitnessFunction(g2, e=0.4, N=3, samples=0.7)
        p = Dynamics.RandomDistribution(7)
        f1(p); f2(p); f3(p); f4(p); f5(p); f6(p); f7(p); f8(p)
        
    def testGenDynamicsFunction(self):
        """GenDynamicsFunction should always return a valid function"""
        g1 = array(GenRandomGame(2, 7))
        g2 = array(GenRandomGame(3, 7))
        d1 = Dynamics.GenDynamicsFunction(g1, e=0.0, noise=0.0, N=2)
        d2 = Dynamics.GenDynamicsFunction(g1, e=0.1, noise=0.0, N=2)        
        d3 = Dynamics.GenDynamicsFunction(g1, e=0.0, noise=0.1, N=2)        
        d4 = Dynamics.GenDynamicsFunction(g1, e=0.1, noise=0.1, N=2)
        d5 = Dynamics.GenDynamicsFunction(g2, e=0.0, noise=0.0, N=3)
        d6 = Dynamics.GenDynamicsFunction(g2, e=0.1, noise=0.0, N=3)        
        d7 = Dynamics.GenDynamicsFunction(g2, e=0.0, noise=0.1, N=3)        
        d8 = Dynamics.GenDynamicsFunction(g2, e=0.1, noise=0.1, N=3)        
        p = Dynamics.RandomDistribution(7)
        d1(p); d2(p); d3(p); d4(p); d5(p); d6(p); d7(p); d8(p)

def suite():
    return unittest.TestSuite((SelfTest(),
                               TestHelperFunctions(),
                               TestFitness(),
                               # TestSamplingAlgorithm(),
                               TestReplicator(),
                               TestGeneratorFunctions(),))
    
    
if __name__ == "__main__":
    myTestSuite = suite()
    testRunner = unittest.TextTestRunner(verbosity=2)
    testRunner.run(myTestSuite)
    

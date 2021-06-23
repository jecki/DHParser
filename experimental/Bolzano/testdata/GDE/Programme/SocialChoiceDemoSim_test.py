"""
SocialChoiceDemoSim_main.py - A small simulation for demonstrating that
'critcal cases' appear only relatively rare when mapping individual
preferences unto collective preferences.

This is the testing module of the simulation which contains unit test for 
the functions in the main module.
"""

from SocialChoiceDemoSim_main import *

DEBUG = False

failed = 0
passed = 0

class Fail(Exception):
    pass

def check(condition = False):
    global failed
    if not condition:
        print("FAILED!")
        failed += 1
        raise Fail

def succeed():
    global passed
    print("passed!")
    passed += 1

def run_tests(*tests):
    for test in tests:
        try:
            print("testing function "+test.__name__+"()...  "),
            test()
            succeed()
        except Fail:
            if DEBUG: raise Fail
    print("\n==> Tests passed: %i    Tests failed: %i"%(passed, failed))
    


def test_genRandomProfile():
    profile = genRandomProfile(50, 12)
    check(len(profile) == 50)
    for prefs in profile: 
        check(len(prefs) == 12)
        for alt in prefs: check(alt >= 0 and alt < 12)
        check(len(set(prefs)) == 12) # check for doublets
    
    
def test_genPartialCultureProfile():
    profile = genPartialCultureProfile(50, 22, 0.1)
    count = {}
    for p in profile:
        if p in count: 
            count[p] += 1
        else: 
            count[p] = 1
    check(max(count.values()) >= 5)
    profile = genPartialCultureProfile(30, 17, 1.0)
    for p in profile:
        check(p == profile[0])
    
    
def test_addedAlternatives():
    profile = genRandomProfile(25, 17)
    extProfile = addedAlternatives(profile, 3)
    for prefs in extProfile: 
        check(len(prefs) == 20)
        for alt in prefs: check(alt >= 0 and alt < 20)
        check(len(set(prefs)) == 20) # check for doublets
    check(reducedProfile(profile, set(range(17))) == profile)


def test_reducedProfile():
    profile = [(0,1,2,3),(2,0,3,1),(3,2,1,0)]
    check(reducedProfile(profile, set([1,3])) == [(1,3),(3,1),(3,1)])    


def test_rank():
    profile = [(0,1,2,3),(2,0,3,1),(3,2,1,0)]
    check(rank(profile) == [(0,1,2,3),(1,3,0,2),(3,2,1,0)])
    
    
def test_match():
    profile = [(0,2,1), (2,1,0)]
    ranking = rank(profile)
    check(match(0,1,ranking) == "~")
    check(match(0,2,ranking) == "~")
    check(match(1,2,ranking) == "<")
    check(match(2,1,ranking) == ">")
    

def test_collapseCycle():
    utility = [0.5, 0.7, 0.8, 0.8, 0.3, 0.3, 0.3]
    cycle = collapseCycle(5,1, utility, {0.0:-1, 0.5:0, 0.7:1, 1.0:-1})
    check(cycle == set([0,1,5]))
    check(utility == [0.5, 0.5, 0.8, 0.8, 0.3, 0.5, 0.3])
#    utility = [0.2, 0.5, 0.4, 0.3, 0.6, 0.8, 0.7, 0.9, 0.5, 0.6]
#    check(collapseCycle(6,2,utility) == set([1,2,4,6]))
#    check(utility == [0.2, 0.4, 0.4, 0.3, 0.4, 0.8, 0.4, 0.9, 0.5, 0.6])
#    check(collapseCycle(3,0,utility) == set([0,3]))
#    check(utility == [0.2, 0.4, 0.4, 0.2, 0.4, 0.8, 0.4, 0.9, 0.5, 0.6])
#    check(collapseCycle(9,7, utility) == set([5,7,9]))
#    check(utility == [0.2, 0.4, 0.4, 0.2, 0.4, 0.9, 0.4, 0.9, 0.5, 0.9])
#    check(collapseCycle(9,3, utility) == set([0,1,2,3,4,5,6,7,8,9]))
#    check(utility == [0.2]*10)
    
    
def test_addCycle():
    cycles = [set([0,1,4]), set([2,5,7,3])]
    addCycle(set([11,13,15]), cycles)
    check(cycles == [set([0,1,4]), set([2,5,7,3]), set([11,13,15])])
    addCycle(set([0,1,4,17]), cycles)
    check(cycles == [set([0,1,4,17]), set([2,5,7,3]), set([11,13,15])])
    
    
def test_condorcet():
    unanimityProfile = [(2,1,3,0,4),(2,1,3,0,4),(2,1,3,0,4)]    
    cyclicProfile = [(0,1,2),(1,2,0),(2,0,1)]
    
    utility, cycles = condorcet(unanimityProfile)
    check(cycles == [])
    check(simpleRanking(utility) == [2,1,3,0,4])

    for i in range(20):
        extendedProfile = addedAlternatives(unanimityProfile, 5)
        extendedUtility, extendedCycles = condorcet(extendedProfile)
        if extendedCycles == []:
            check(simpleRanking(utility) == 
                  simpleRanking(extendedUtility[:len(unanimityProfile[0])]))
    
    utility, cycles = condorcet(cyclicProfile)
    check(cycles == [set([0,1,2])])
    check(fullRanking(utility) == [set([0,1,2])])
    
    for i in range(20):
        extendedProfile = addedAlternatives(cyclicProfile, 5)
        extendedUtility, extendedCycles = condorcet(extendedProfile)
        if extendedCycles == []:   
            check(fullRanking(utility) == 
                  fullRanking(extendedUtility[:len(cyclicProfile[0])]))
    
    profile = [(3,2,1,0),(3,2,1,0),(3,2,1,0),(3,2,0,1),(3,0,2,1)]    
    utility, cycles = condorcet(profile)
    check(simpleRanking(utility) == [3,2,1,0])
    

def test_simpleRanking():
    utility = [0.2, 0.4, 0.5, 0.3, 0.7, 0.6, 0.1]
    check(simpleRanking(utility) == [4,5,2,1,3,0,6])
    

def test_fullRanking():
    utility = [0.2, 0.4, 0.5, 0.3, 0.7, 0.6, 0.1]
    check(fullRanking(utility) == [set([4]), set([5]), set([2]), set([1]),
                                   set([3]), set([0]), set([6])])
    utility = [0.2, 0.4, 0.3, 0.4, 0.5, 0.5, 0.1]
    check(fullRanking(utility) == [set([4,5]), set([1,3]), set([2]), 
                                   set([0]), set([6])])
    
def test_representation():
    fullRanking = [set([4,5,7,8]), set([1,10,6]), set([2,3,9]), set([0])]    
    cycles = [set([4,5,8]), set([2,3,9])]  
    check(representation(fullRanking, cycles) == 
          "e = f = i ~ h > b ~ g ~ k > c = d = j > a")
    check(representation(fullRanking, []) == 
          "e ~ f ~ h ~ i > b ~ g ~ k > c ~ d ~ j > a")
    

if __name__ == "__main__":
    run_tests(test_genRandomProfile, test_genPartialCultureProfile,
              test_reducedProfile, test_addedAlternatives,
              test_rank, test_match, test_collapseCycle, 
              test_addCycle, test_condorcet, 
              test_simpleRanking, test_fullRanking, test_representation)
    
    
"""
SocialChoiceDemoSim_main.py - A small simulation for demonstrating that
'critcal cases' appear only relatively rare when mapping individual
preferences unto collective preferences.

This is core module of the simulation which defines the condorcet method
and other things for simulating social welfare functions.
"""


import random

def genRandomProfile(individuals, alternatives):
    """Generates a random ("impartial-culture") preference profile 
    for a certain number of individuals and alternatives.
    """
    assert individuals <= 1000
    assert alternatives <= 26
    
    altList = [k for k in range(alternatives)]
    profile = []
    for i in range(individuals):
        random.shuffle(altList)
        profile.append(tuple(altList))
    return profile


def genPartialCultureProfile(individuals, alternatives, unanimityRatio):
    """Generates a "partial-culture" preference profile, i.e. a certain
    fraction of individuals shares the same preferences, while the
    preferences of the other individuals are distributed randomly.
    """
    assert individuals <= 1000
    assert alternatives <= 26
    assert unanimityRatio <= 1.0   
    
    homogenous = int(individuals * unanimityRatio + 0.5)
    homogenousPart = genRandomProfile(1, alternatives) * homogenous
    heterogenousPart = genRandomProfile(individuals - homogenous, alternatives)
    return heterogenousPart + homogenousPart
     

def addedAlternatives(profile, alternatives):
    """Returns a profile with randomly added further alternatives.
    """
    assert len(profile) > 0
    altList = range(len(profile[0]), len(profile[0])+alternatives)
    newProfile = []
    for prefs in profile:
        newPrefs = list(prefs)
        for alt in altList:
            newPrefs.insert(random.randint(0,len(newPrefs)), alt)
        newProfile.append(tuple(newPrefs))
    return newProfile


def reducedProfile(profile, altSet):
    """Returns a reduced profile that contains only certain alternatives.
    """
    return [tuple([p for p in prefs if p in altSet]) for prefs in profile]


def rank(profile):
    """Returns a profile of ranks of alternatives"""
    rankProfile = []
    for preferences in profile:
        ranking = list(range(len(preferences)))
        for k, alternative in enumerate(preferences):
            ranking[alternative] = k
        rankProfile.append(tuple(ranking))
    return rankProfile


def match(alt_1, alt_2, rankProfile):
    """Returns the preference relation (>, < or ~) between alt_1 and alt_2."""
    vote_1, vote_2 = 0, 0
    for ranking in rankProfile:
        if ranking[alt_1] < ranking[alt_2]:  # the lower the rank the better!
            vote_1 += 1
        else:
            vote_2 += 1
    if vote_1 > vote_2:
        return ">"
    elif vote_1 < vote_2:
        return "<"
    else:
        return "~" 
        

def collapseCycle(b, a, utility, firstAssigned):
    """Breaks a cycle between 'a' and 'b' by setting all utilities between
    the utility of 'a' and 'b' to the utility of the first element within
    the cycle."""
    assert b > a
    
    u1 = utility[a]
    u2 = utility[b]
    border = utility[b]
    if u1 > u2:
        u1,u2 = u2,u1
    
    if utility[b] in firstAssigned and firstAssigned[utility[b]] <= a:
        inCycle = lambda i : utility[i] >= u1 and utility[i] <= u2
    else:
        inCycle = lambda i : utility[i] >= u1 and utility[i] <= u2 \
                                              and utility[i] != border
    for u in utility:
        if u >= u1 and u <= u2:
            break
        
    cycle = set([a, b])
    utility[a] = u
    utility[b] = u
    for i in range(len(utility)):
        if inCycle(i):
            utility[i] = u
            cycle.add(i)
    return cycle


def addCycle(cycle, listOfCycles):
    """Adds a cycle to a list of cycles. If the cycle is a superset of an
    already existing cycle, it will replace the existing cycle."""
    for n, cyc in enumerate(listOfCycles):
        if len(cycle.intersection(cyc)) != 0:
            listOfCycles[n] = cycle.union(cyc)
            break
    else:
        listOfCycles.append(cycle)
        

def condorcet(profile):
    """Aggregates individual preferences according to the Condorect-method, 
    i.e. pairwise comparison of all alternatives. Returns a list of 
    (ordinal) utilities and a list of cycles.
    
    WARNING: The algorithm for cycle detection may not be completely accurate.
    Need a proof here. However, any inaccuracies, if they exist at all, only 
    concern cases in which there is more than one cycle.
    """
    alternatives = len(profile[0])
    rankProfile = rank(profile)
    collectiveRanking = []
    
    # 1. equal utility for all alternatives
    utility = [0.5 for k in range(alternatives)]
    firstAssigned = {0.0: -1,  
                     0.5:  0,  
                     1.0: -1}
    cycles = []
    
    for k in range(alternatives):
        utilityRange = firstAssigned.keys()
        utilityRange.sort()
        r = utilityRange.index(utility[k])
        worse = (utilityRange[r-1] + utilityRange[r]) / 2.0
        better = (utilityRange[r+1] + utilityRange[r]) / 2.0
        
        isPivot = firstAssigned.setdefault(utility[k], k) == k
                
        for l in range(k+1, alternatives):
            relation = match(l, k, rankProfile)
            
            if relation == '>':
                if utility[l] < utility[k] or \
                        (utility[l] == utility[k] and not isPivot):
                    addCycle(collapseCycle(l, k, utility, firstAssigned), 
                             cycles)
                elif utility[l] == utility[k]:
                    utility[l] = better
                    firstAssigned.setdefault(utility[l], l)
                    
            elif relation == '<':
                if utility[l] > utility[k] or \
                        (utility[l] == utility[k] and not isPivot):                  
                    addCycle(collapseCycle(l, k, utility, firstAssigned), 
                             cycles)
                elif utility[l] == utility[k]:
                    utility[l] = worse
                    firstAssigned.setdefault(utility[l], l)
                                                               
            else:
                if utility[l] != utility[k]:
                    addCycle(collapseCycle(l, k, utility, firstAssigned), 
                             cycles)
                    
    return (utility, cycles)
        

def simpleRanking(utility):
    """Returns the list of alternatives ordered by their utility."""
    pairs = [(utility[k], k) for k in range(len(utility))]
    pairs.sort()
    pairs.reverse()
    return [p[1] for p in pairs]


def fullRanking(utility):
    """Returns a list of sets of indifferent alternatives representing
    the 'utility'-list."""
    indifferenceClasses = {}
    for k,u in enumerate(utility):
        indifferenceClasses.setdefault(u, set([])).add(k)
    keys = list(indifferenceClasses.keys())
    keys.sort()
    keys.reverse()
    return [indifferenceClasses[k] for k in keys]

    
def representation(fullRanking, cycles):
    """Returns a string representation of 'fullRanking' taking into account
    possible 'cycles'. Example: "a > b = d = e > c ~ f". Here, the sign '=' 
    means that the alternatives are indifferent, because they were caught in 
    a cycle.
    """
    rep = []
    
    def addToRep(rep, altSet, sign, connection = '>'):
        lst = list(altSet)
        lst.sort()
        for alt in lst:
            rep.append(chr(alt+ord('a')))
            rep.append(sign)
        rep[-1] = connection
        
    for indifferenceClass in fullRanking:
        for cyc in cycles:
            if cyc.issubset(indifferenceClass):
                addToRep(rep, cyc, "=", "~")
                indifferenceClass = indifferenceClass - cyc
                break
        addToRep(rep, indifferenceClass, "~")
    
    rep.pop()
    return " ".join(rep)




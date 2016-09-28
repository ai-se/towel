"Synthetic Minority oversampling technique"
from __future__ import print_function, division

def SMOTE(dat, N=1000):
    rows = [d[:-1] for d in dat]
    labels = [d[-1] for d in dat]
    C = Counter(labels)
    k = C.keys()
    M, m = k[1], k[0]
    if C[m] > C[M]:
        m, M = M, m
    minority = [d for d in dat if d[-1] == m]
    majority = [d for d in dat if d[-1] == M]
    SMOTED = []

    def NN(one, pop, k=5):
        from scipy.spatial.distance import euclidean
        theRest = [p for p in pop if not p == one]
        return sorted(theRest, key=lambda F: euclidean(one[:-1], F[:-1]))[:k]


    def FN(one, pop, k=2):
        from scipy.spatial.distance import euclidean
        # theRest = [p for p in pop1 if not p==one]
        order = np.argsort([euclidean(one[:-1], F[:-1]) for F in pop])[::-1]
        return pop[order[0]]

    "Smote 2: Use farthest neighbours"
    for _ in xrange(C[M] - C[m]):
        from scipy.spatial.distance import euclidean
        some = choice(minority)
        other = FN(some, majority)
        same = sorted(minority, key=lambda F: euclidean(F[:-1], other[:-1]), reverse=True)[:2]
        new = [a + random() * np.abs(b - c) for a, b, c in zip(some[:-1]
                                                               , same[0][:-1]
                                                               , same[1][:-1])]
        SMOTED.append(new + [m])

    SMOTED.extend(minority)
    SMOTED.extend(majority)

    return SMOTED


def SMOTE2(dat, N=1000):
    rows = [d[:-1] for d in dat]
    labels = [d[-1] for d in dat]
    C = Counter(labels)
    k = C.keys()
    M, m = k[1], k[0]
    if C[m] > C[M]:
        m, M = M, m
    minority = [d for d in dat if d[-1] == m]
    majority = [d for d in dat if d[-1] == M]
    SMOTED = []

    def NN(one, pop, k=5):
        from scipy.spatial.distance import euclidean
        theRest = [p for p in pop if not p == one]
        return sorted(theRest, key=lambda F: euclidean(one[:-1], F[:-1]))[:k]

    for _ in xrange(int((len(dat) / 2 - C[m]))):
        #  for _ in xrange(C[M]-C[m]):
        some = choice(minority)
        other = choice(NN(some, minority))
        new = [a + random() * (b - a) for a, b in zip(some[:-1], other[:-1])]
        SMOTED.append(new + [m])

    SMOTED.extend(minority)
    shuffle(majority)
    SMOTED.extend(majority[:int(len(dat) / 2)])
    return SMOTED
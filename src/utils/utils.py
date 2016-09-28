# from demos import *
import sys

sys.dont_write_bytecode = True


class Vessel(object):
    id = -1

    def __init__(i, **fields):
        i.override(fields)
        i.newId()

    def newId(i):
        i._id = Vessel.id = Vessel.id + 1

    def also(i, **d):
        return i.override(d)

    def override(i, d):
        i.__dict__.update(d)
        return i

    def __hash__(i):
        return i._id


def flatten(x):
    """
    Takes an N times nested list of list like [[a,b],[c, [d, e]],[f]]
    and returns a single list [a,b,c,d,e,f]
    """
    result = []
    for el in x:
        if hasattr(el, "__iter__") and not isinstance(el, basestring):
            result.extend(flatten(el))
        else:
            result.append(el)
    return result


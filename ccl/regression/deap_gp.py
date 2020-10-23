import sys
import collections
import operator

from deap.gp import Primitive

__type__ = object


def gen_full(pset, min_, max_, rng, type_=None):
    def condition(height, depth):
        """Expression generation stops when the depth is equal to height."""
        return depth == height

    return generate(pset, min_, max_, condition, rng, type_)


def gen_grow(pset, min_, max_, rng, type_=None):
    def condition(height, depth):
        return depth == height or \
               (depth >= min_ and rng.random() < pset.terminalRatio)

    return generate(pset, min_, max_, condition, rng, type_)


def gen_half_and_half(pset, min_, max_, rng, type_=None):
    method = rng.choice((gen_grow, gen_full))
    return method(pset, min_, max_, rng, type_)


def generate(pset, min_, max_, condition, rng, type_=None):
    if type_ is None:
        type_ = pset.ret
    expr = []
    height = rng.randint(min_, max_)
    stack = [(0, type_)]
    while len(stack) != 0:
        depth, type_ = stack.pop()
        if condition(height, depth):
            try:
                term = rng.choice(pset.terminals[type_])
            except IndexError:
                _, _, traceback = sys.exc_info()
                raise IndexError("The generate function tried to add " \
                                  "a terminal of type '%s', but there is " \
                                  "none available." % (type_,)).with_traceback(traceback)
            if isinstance(term, type):
                term = term()
            expr.append(term)
        else:
            try:
                prim = rng.choice(pset.primitives[type_])
            except IndexError:
                _, _, traceback = sys.exc_info()
                raise IndexError("The generate function tried to add " \
                                  "a primitive of type '%s', but there is " \
                                  "none available." % (type_,)).with_traceback(traceback)
            expr.append(prim)
            for arg in reversed(prim.args):
                stack.append((depth + 1, arg))
    return expr


def cx_one_point(ind1, ind2, rng):
    if len(ind1) < 2 or len(ind2) < 2:
        # No crossover on single node tree
        return ind1, ind2

    # List all available primitive types in each individual
    types1 = collections.defaultdict(list)
    types2 = collections.defaultdict(list)
    if ind1.root.ret == __type__:
        # Not STGP optimization
        types1[__type__] = range(1, len(ind1))
        types2[__type__] = range(1, len(ind2))
        common_types = [__type__]
    else:
        for idx, node in enumerate(ind1[1:], 1):
            types1[node.ret].append(idx)
        for idx, node in enumerate(ind2[1:], 1):
            types2[node.ret].append(idx)
        common_types = set(types1.keys()).intersection(set(types2.keys()))

    if len(common_types) > 0:
        type_ = rng.choice(list(common_types))

        index1 = rng.choice(types1[type_])
        index2 = rng.choice(types2[type_])

        slice1 = ind1.searchSubtree(index1)
        slice2 = ind2.searchSubtree(index2)
        ind1[slice1], ind2[slice2] = ind2[slice2], ind1[slice1]

    return ind1, ind2


def mut_uniform(individual, expr, pset, rng):

    index = rng.randrange(len(individual))
    slice_ = individual.searchSubtree(index)
    type_ = individual[index].ret
    individual[slice_] = expr(pset=pset, type_=type_)
    return individual,


def sel_random(individuals, k, rng):
    return [rng.choice(individuals) for i in range(k)]


def sel_double_tournament(individuals, k, fitness_size, parsimony_size, rng, fit_attr="fitness"):
    def _fit_tournament(individuals, k):
        chosen = []
        for i in range(k):
            aspirants = sel_random(individuals, k=fitness_size, rng=rng)
            chosen.append(max(aspirants, key=operator.attrgetter(fit_attr)))
        return chosen

    def _size_tournament(individuals, k):
        chosen = []
        for i in range(k):
            # Select two individuals from the population
            # The first individual has to be the shortest
            prob = parsimony_size / 2.
            ind1, ind2 = _fit_tournament(individuals, k=2)

            if len(ind1) > len(ind2):
                ind1, ind2 = ind2, ind1
            elif len(ind1) == len(ind2):
                # random selection in case of a tie
                prob = 0.5

            # Since size1 <= size2 then ind1 is selected
            # with a probability prob
            chosen.append(ind1 if rng.random() < prob else ind2)
        return chosen

    return _size_tournament(individuals, k)


def mut_shrink(individual, rng):
    # We don't want to "shrink" the root
    if len(individual) < 3 or individual.height <= 1:
        return individual,

    iprims = []
    for i, node in enumerate(individual[1:], 1):
        if isinstance(node, Primitive) and node.ret in node.args:
            iprims.append((i, node))

    if len(iprims) != 0:
        index, prim = rng.choice(iprims)
        arg_idx = rng.choice([i for i, type_ in enumerate(prim.args) if type_ == prim.ret])
        rindex = index + 1
        for _ in range(arg_idx + 1):
            rslice = individual.searchSubtree(rindex)
            subtree = individual[rslice]
            rindex += len(subtree)

        slice_ = individual.searchSubtree(index)
        individual[slice_] = subtree

    return individual,

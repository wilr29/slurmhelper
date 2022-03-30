"""
Miscellaneous helper functions.
"""

# Lil' helper function from stackoverflow
# source: https://stackoverflow.com/questions/752308/split-list-into-smaller-lists-split-in-half
def split_list(alist, wanted_parts=1):
    """
    Split a list into a given number of parts. Used to divvy up jobs evenly.
    :param alist: list o' jobs
    :param wanted_parts: how many chunks we want
    :return: list o' lists
    """
    length = len(alist)
    return [
        alist[i * length // wanted_parts : (i + 1) * length // wanted_parts]
        for i in range(wanted_parts)
    ]

def factors(n):
    '''
    Finds all factors for a given number.
    Copied from https://stackoverflow.com/a/19578818
    :param n: some integer
    :return: set with all factors of n
    '''
    from functools import reduce
    from math import sqrt
    step = 2 if n%2 else 1
    return set(reduce(list.__add__,([i, n//i] for i in range(1, int(sqrt(n))+1, step) if n % i == 0)))

def find_optimal_n_parcels(n:int, p_min:int, par_target=50):
    '''
    Algorithm for parcellating jobs.
    :param n: number of jobs to parcellate
    :param p_min: constraint; minimum number of parcels (e.g., based on max duration per sbatch array element)
    :param par_target: percent to which to attempt to parallelize (vs. serialize). 100 will lead to one array element per job; 0 will lead to the longest possible serial jobs.
    :return:
    '''
    import numpy as np
    import logging
    logger = logging.getLogger('cli')

    if p_min > n:
        raise ValueError("Minimum number of parcels cannot be greater than number of jobs to divvy up!")

    if not isinstance(n,int) and isinstance(p_min,int) and isinstance(par_target,int):
        raise ValueError("All values supplied should be integers!")

    if par_target == 100: # avoid computation; just return n_jobs.
        rv = n
    else:
        fac = {f for f in factors(n) if f >= p_min} # determine viable factors
        if len(fac) == 1 and list(fac)[0] == n:
            logger.warning("There is no way to evenly serialize jobs across an sbatch array given the maximum sbatch "
                           "duration and number of jobs specified. Defaulting to full parallelization.")
            rv = n
        else:
            logger.info(f"Jobs can be evenly divided into sbatch array elements that serialize: {fac} jobs")
            print(sorted(list(fac)))
            rv = np.percentile(sorted(list(fac)), par_target, interpolation='nearest')

    return rv

def unique(l):
    return list(set(l))

from contextlib import contextmanager
from math import sqrt
import optparse
import time

"""
    primes.py: Generate primes using the following sieve algorithms (from slowest to fastest)
        - Brute Force
        - Sieve of Eratosthenes
        - Sieve of Euler
        - Sieve of Sundaram
        - Sieve of Atkin
"""

def timethis(what):
    @contextmanager
    def benchmark():
        start = time.time()
        yield
        end = time.time()
        print("%s : %0.3f seconds" % (what, end-start))
    if hasattr(what, "__call__"):
        def timed(*args, **kwargs):
            with benchmark():
                return what(*args, **kwargs)
        return timed
    else:
        return benchmark()

def brute_force_primes(start, end, verbose=False):
    def is_prime(x):
        """Returns true if x is a prime number, otherwise it returns false"""
        i = 2
        while i < x:
            if x % i == 0:
                return False
            i = i + 1
        return True

    return [i for i in xrange(start, end) if is_prime(i)]

def sieve_of_eratosthenes(start, end, verbose=False):
    """
    Typical usage
    >>> sieve_of_eratosthenes(2, 20)
    [2, 3, 5, 7, 11, 13, 17, 19]

    Test truncated list
    >>> sieve_of_eratosthenes(30, 40)
    [31, 37]

    Bad range returns empty list
    >>> sieve_of_eratosthenes(3, 2)
    []

    Bad input raise a value error
    >>> sieve_of_eratosthenes(0, -1)
    Traceback (most recent call last):
    ...
    ValueError: Start and End values must be positive integers
    """
    #
    # Elmininates all multiples of current primes from list.
    #
    def sieve_eratosthenes(primes, p, end):
        i = 3
        m = i * p
        while m <= end:
            if m in primes:
                primes.remove(m)
            i += 1
            m = i * p
    if start < 0 or end < 0:
        raise ValueError, "Start and End values must be positive integers"
    last = int(sqrt(end))
    primes = range(3, end, 2)
    for p in primes:
        if p > last:
            break
        sieve_eratosthenes(primes, p, end)
    primes = filter(lambda x: x >= start, primes)
    if start < 3:
        primes.insert(0,2)
    return primes

def sieve_of_euler(start, end, verbose=False):
    """
    Typical usage
    >>> sieve_of_euler(2, 20)
    [2, 3, 5, 7, 11, 13, 17, 19]

    Test truncated list
    >>> sieve_of_euler(30, 40)
    [31, 37]

    Bad range returns empty list
    >>> sieve_of_euler(3, 2)
    []

    Bad input raise a value error
    >>> sieve_of_euler(0, -1)
    Traceback (most recent call last):
    ...
    ValueError: Start and End values must be positive integers
    """
    #
    # Elmininate products of current primes and prime candidates from list
    #
    def sieve_euler(primes, p, end):
        delete_list = []
        for n in primes:
            m = p * n
            if m > end:
                break
            if m in primes:
                delete_list.append(m)
        for n in delete_list:
            primes.remove(n)
    if start < 0 or end < 0:
        raise ValueError, "Start and End values must be positive integers"
    last = int(sqrt(end)) + 1
    primes = [2] + range(3, end, 2)
    for p in primes:
        if p > last:
            break
        sieve_euler(primes, p, end)
    primes = filter(lambda x: x >= start, primes)
    return primes

@timethis
def sieve_of_sundaram(start, end, verbose=False):
    """
    >>> sieve_of_sundaram(2, 20)
    [2, 3, 5, 7, 11, 13, 17, 19]
    >>> sieve_of_sundaram(30, 40)
    [31, 37]
    """
    # http://en.wikipedia.org/wiki/Sieve_of_Sundaram
    def sieve_sundaram(primes, end):
        mid = int(end / 2)
        initial = 4
        for step in xrange(3, end+1, 2):
            for i in xrange(initial, mid, step):
                primes[i-1] = 0
            initial += 2 * (step + 1)
            if initial > mid:
                return [2] + filter(None, primes)
    primes = range(3, end+1, 2)
    primes = sieve_sundaram(primes, end)
    primes = filter(lambda x: x >= start, primes)
    return primes

def sieve_of_atkin(start, end, verbose=False):
    """
    Typical usage
    >>> sieve_of_atkin(2, 20)
    [2, 3, 5, 7, 11, 13, 17, 19]

    Test truncated list
    >>> sieve_of_atkin(30, 40)
    [31, 37]

    Bad range returns empty list
    >>> sieve_of_atkin(3, 2)
    []

    Bad input raise a value error
    >>> sieve_of_atkin(0, -1)
    Traceback (most recent call last):
    ...
    ValueError: Start and End values must be positive integers
    """
    #
    # Uses a pre-step to "prime" candidate list,
    # then sieves candidates by eliminating all multiples of the square
    # of known primes.
    #
    # See http://en.wikipedia.org/wiki/Sieve_of_Atkin
    #
    def sieve_atkin(primes_dict, n, end):
        i = 1
        while True:
            m = i * n ** 2
            if m > end:
                break
            primes_dict[m] = False
            i += 1
    if start < 0 or end < 0:
        raise ValueError, "Start and End values must be positive integers"
    last = long(sqrt(end)) + 1
    primes_dict = dict()
    # find candidates
    for x in xrange(1, last):
        for y in xrange(1, last):
            n = 4 * x**2 + y**2
            if (n <= end) and ((n % 12 == 1) or (n % 12 == 5)):
                primes_dict[n] = not primes_dict.get(n, False)

            n = 3 * x**2 + y**2
            if (n <= end) and (n % 12 == 7):
                primes_dict[n] = not primes_dict.get(n, False)

            n = 3 * x**2 - y**2
            if (x > y) and (n <= end) and (n % 12 == 11):
                primes_dict[n] = not primes_dict.get(n, False)
    # sieve primes
    for n in sorted(primes_dict.iterkeys()):
        if n > last:
            break
        if primes_dict[n]:
            sieve_atkin(primes_dict, n, end)

    primes_dict[2] = primes_dict[3] = True
    # convert to list
    primes = filter(lambda k: primes_dict[k] and k >= start and k <= end,
            primes_dict)
    return primes

def get_primes(opts, args):
    primes = []

    start = long(opts.start)
    end = long(opts.end)

    algorithm_dct = {
        'sundaram': ('Sieve of Sundaram', sieve_of_sundaram),
        'euler': ('Sieve of Euler', sieve_of_euler),
        'atkin': ('Sieve of Atkin', sieve_of_atkin),
        'eratosthenes': ('Sieve of Eratosthenes', sieve_of_eratosthenes),
        'brute': ('Brute Force', brute_force_primes),
    }
    desc, prime_func = algorithm_dct.get(opts.algorithm.lower(),
            algorithm_dct['atkin'])
    print "Finding all primes between %d and %d, using %s algorithm..." % (start,
            end, desc)
    primes.extend(prime_func(start, end, opts.verbose))
    print "Found %d primes" % len(primes)
    return primes

def main():
    p = optparse.OptionParser(description=
            'Generate a list of prime numbers using a variety of algorithms',
            version='0.3')
    p.add_option('--start', '-s')
    p.add_option('--end', '-e')
    p.add_option('--nth', '-n', help='print the nth prime number.')
    p.add_option('--algorithm', '-a',
            help="algorithms: euler, atkin, eratosthenes, brute")
    p.add_option('--verbose', '-v', action="store_true")
    p.set_defaults(
         start = 2,
         end = 100,
         algorithm="atkin",
         nth = 0)

    opts, args = p.parse_args()
    if opts.nth != 0:
        opts.end = 1000000

    primes = get_primes(opts, args)
    if opts.verbose:
        print primes
    if opts.nth:
        print primes[int(opts.nth)]

if __name__ == "__main__":
    main()

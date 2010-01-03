#!/usr/bin/python

import sys
import optparse
from datetime import datetime
from random import randint, random

"""
   A simple Python benchmark tool.
"""

__author__  = "Neil (mace033@gmail.com)"
__license__ = "GPLv2"


def get_ms(d):
	return d.microseconds/1000 + d.seconds * 1000 + d.days * 84600

def int_range(count):
	'''Generates a random integer between 0 and sys.maxint.'''
	max_int = sys.maxint
	for i in xrange(count):
		yield randint(0, max_int)

def float_range(count):
	'''Generates a random float between 0 and sys.maxint.'''
	max_int = sys.maxint
	for i in xrange(count):
		yield float(randint(0, max_int) + random())

def time_it(func, *args):
	'''Runs function func with *args and returns the number of 
   millseconds it takes to run func.'''
	start = datetime.now()
	func(*args)
	return get_ms(datetime.now() - start)

def int_tst(int_list):
	total = 0
	for i in int_list:
		total += i

def float_tst(float_list):
	total = 0.0
	for i in float_list:
		total += i

def run_it(name, passes, func, *args):
	global verbose
	print " Running %s bench" % (name)
	start = datetime.now()
	for i in xrange(1, passes+1):
		if verbose:
			print "  pass %d:" % (i) 
		ts = time_it(func, *args)
		if verbose:
			print "  done in %s ms." % (ts)
	print " done in %s ms." % (get_ms(datetime.now() - start))
	
verbose = False
def main():
	global verbose
	parser = optparse.OptionParser()
	parser.add_option("-p", "--passes", default=100)
	parser.add_option("-v", "--verbose", action='store_true', default=False)

	opts, args = parser.parse_args()
	passes = int(opts.passes)
	verbose = opts.verbose

	print "Creating random dataset...",
	int_list = int_range(100)
	float_list = float_range(100)
	print "done"

	start = datetime.now()
	print "Runnng benchmark %d passes..." % (passes)
	run_it("integer", passes, int_tst, int_list)
	run_it("floating point", passes, float_tst, float_list)
	print "done in %s ms." % (get_ms(datetime.now() - start))

if __name__ == "__main__":
	main()

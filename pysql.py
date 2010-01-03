#!/bin/python

import sys
import optparse
from datetime import datetime
import pysqlite2.dbapi2 as sqlite3

"""
   A tool to stress test a SQLite database. Uses 
   the pysqlite3.dbapi2 SQLite inteface.
"""
__author__  = "Neil (mace033@gmail.com)"
__license__ = "GPLv2"

def time_it(desc, func, arg, val_list = None):
	start = datetime.now()
	if val_list:
		ret = func(arg, val_list)
	elif arg:
		ret = func(arg)
	else:
		ret = func()

	print "%s finished in %s" % (desc, datetime.now()-start)
	sys.stdout.flush()
	return ret

def random_str(min, max):
	from random import randint, choice
	'''Returns a random string with min length min and max length'''
	
	length = randint(min, max)
	letters = map(chr, range(97, 123))
	l = []
	for i in xrange(length):
		l.append(choice(letters))

	return "".join(l)

def random_int(min, max):
	from random import randint
	'''Returns a random integer with min value min and max value'''

	return randint(min, max)

def mk_user_seq():
	'''A generator that returns randomized first, middle, and last names'''
	while True:
		yield (random_str(7, 11), random_str(7, 11), random_str(7, 11))

def mk_profile_seq():
	'''A generator that returns randomized first, middle, and last names'''
	while True:
		yield (''.join([str(random_int(1, 9999)), ' ', random_str(10, 16)]), random_str(6, 16), random_int(10000, 99999), random_str(2,2))

def get_create_sql():
	return '''BEGIN;
	DROP TABLE IF EXISTS user;
	DROP TABLE IF EXISTS profile;

	CREATE TABLE  user (id INTEGER PRIMARY KEY NOT NULL, first VARCHAR(64) NOT NULL, middle VARCHAR(64) NOT NULL, last VARCHAR(64) NOT NULL);
	CREATE TABLE  profile (id INTEGER PRIMARY KEY NOT NULL, user_id INTEGER  NOT NULL CONSTRAINT fk_user_id REFERENCES user(id) on DELETE CASCADE, address VARCHAR(32) NOT NULL, city VARCHAR(64) NOT NULL, zip INTEGER NOT NULL, state VARCHAR(2) NOT NULL);

	CREATE INDEX profile_idx ON profile (city, zip, state);
	COMMIT;'''

	# the multi-column index profile_idx would be used for queries containing columns:
	#		city, zip and state
	#		city and zip
	#		city and state but for column city
	#		city

def main():
	p = optparse.OptionParser(description='SQLite stress tester.', version='0.1')
	p.add_option('--create', '-c', action = "store_true")	
	p.add_option('--query', '-q', action = "store_true")
	p.add_option('--indexes', '-x', action = "store_true")
	p.add_option('--inserts', '-i')
	p.add_option('--passes', '-p', default = "1")
	opts, args = p.parse_args()

	if opts.create is None and opts.query is None and opts.inserts is None: 
		p.print_help()
		sys.exit(2)

	# initialize options
	query = opts.query
	inserts = 0
	if opts.inserts:
		inserts = int(opts.inserts) 

	schema = None	
	if opts.create:
		schema  = get_create_sql()

	con = sqlite3.connect("test.db")
	csr = con.cursor()

	if schema:
		time_it("schema creation", csr.executescript, schema)

	if inserts:
		user_sql = 'INSERT INTO user (first, middle, last) VALUES (:first, :middle, :last)'
		user_gen = mk_user_seq()
		profile_sql = 'INSERT INTO profile (user_id, address, city, zip, state) VALUES (:user_id, :address, :city, :zip, :state)'
		profile_gen = mk_profile_seq()
		start = datetime.now()
		for i in xrange(inserts):
			csr.execute(user_sql, user_gen.next())
			user_id = (csr.lastrowid,)
			csr.execute(profile_sql, user_id+profile_gen.next())
		print "%d rows additions finished in %s" % (inserts * 2, datetime.now()-start)
		
		ret = time_it("transaction commit", con.commit, None)

	if query:
		query_list = ["SELECT u.*, p.* FROM user u, profile p WHERE u.id = p.id AND u.first LIKE 'neil%'", 
			"SELECT u.*, p.* FROM user u, profile p WHERE u.id = p.id AND p.state = 'ca'",
			"SELECT u.*, p.* FROM user u, profile p WHERE u.id = p.id AND p.zip = 12345"]
		for sql in query_list:
			print "Runing query '%s'" % (sql)
			csr.execute(sql)
			ret = time_it("query", csr.fetchall, None)
			print "%d rows found" % (len(ret))

	csr.close()
	con.close()

if __name__ == "__main__":
	main()

#!/bin/env python
# -*- coding: utf-8 *-*

from time import strftime
import tempfile
import bz2
import os
import socket
import subprocess
from optparse import OptionParser

parser = OptionParser()

parser.add_option('-a', "--alertemail", action="store", type="string",
                  dest="alertemail", default='admin@pgexperts.com')
parser.add_option('-d', "--destdir", action="store", type="string",
                  dest="backupdir", default='/data/pg/backup/dumps')
parser.add_option('-k', "--keep", action="store", type="int", dest="keep",
                  default=7)
parser.add_option('', "--pghost", action="store", type="string",
                  dest="pghost")
parser.add_option('-U', "--pguser", action="store", type="string",
                  dest="pguser")
parser.add_option('-p', "--port", action="store", type="string",
                  dest="pgport")
parser.add_option('-c', "--compress", action="store", type="int",
                  dest="compress", default=6)
parser.add_option('', "--debug", action="store_const", const=1,
                  dest="debug", default=0)

(options, args) = parser.parse_args()

failed = 0

# set up some environment variables either from the command line arguments,
# from the environment or from reasonable defaults
dbenv = {"PATH": os.environ["PATH"]}

if options.pghost or os.getenv("PGHOST"):
    dbenv["PGHOST"] = options.pghost or os.getenv("PGHOST")

dbenv["PGPORT"] = options.pgport or os.getenv("PGPORT") or "5432"
dbenv["PGUSER"] = options.pguser or os.getenv("PGUSER") or "postgres"

# hostname used for file naming convention
dbhost = options.pghost or os.getenv("PGHOST") or socket.getfqdn()
if options.debug:
    print "DBHOST: " + dbhost
    print "DBENV:" + str(dbenv)

logfile = tempfile.TemporaryFile()

globalsfile = options.backupdir + '/' + dbhost + '-globals-'\
  + strftime('%Y%m%d') + '.sql.bz2'
if options.debug: print "GLOBALSFILE: " + globalsfile

globals_out = bz2.BZ2File(globalsfile, 'wb')
globals_in = subprocess.Popen(["pg_dumpall", "--globals"],
    stdout=subprocess.PIPE, stderr=logfile, env=dbenv)
globals_out.writelines(globals_in.stdout)
globals_out.close()

databases = subprocess.check_output(["psql", "--no-align", "--tuples-only",
    "--command",
    "SELECT datname FROM pg_database WHERE datname NOT IN ('postgres', "
    "'template0','template1')", "postgres"], env=dbenv)


for db in databases.split():
    if options.debug: print "DB: " + db
    dbfile = options.backupdir + '/' + dbhost + '-' + db + '-'\
      + strftime('%Y%m%d') + '.dmp'
    if options.debug: print "DBFILE: " + dbfile
    pg_dump = ['pg_dump', '--format=custom',
        '--compress=' + str(options.compress),
        '--file=' + dbfile, db]
    if options.debug: print "PG_DUMP: " + str(pg_dump)
    dumpreturn = subprocess.call(pg_dump, stderr=logfile, env=dbenv)
    if dumpreturn != 0:
        failed = 1

if failed:
    print "dump failed"
    logfile.seek(0)
    for errorline in logfile:
      print errorline

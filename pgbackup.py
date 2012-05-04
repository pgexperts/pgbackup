#!/bin/env python
# -*- coding: utf-8 *-*

from time import strftime
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

(options, args) = parser.parse_args()

# set up some environment variables either from the command line arguments,
# from the environment or from reasonable defaults
dbenv = {"PATH": os.environ["PATH"]}

if options.pghost or os.getenv("PGHOST"):
    dbenv["PGHOST"] = options.pghost or os.getenv("PGHOST")

dbenv["PGPORT"] = options.pgport or os.getenv("PGPORT") or "5432"
dbenv["PGUSER"] = options.pguser or os.getenv("PGUSER") or "postgres"

# hostname used for file naming convention
dbhost = options.pghost or os.getenv("PGHOST") or socket.getfqdn()
print dbhost
print dbenv

globalsfile = dbhost + '-globals-' + strftime('%Y%m%d') + '.sql.bz2'
print globalsfile

globals_out = bz2.BZ2File(globalsfile, 'wb')
globals_in =  subprocess.Popen(["pg_dumpall", "--globals"],
    stdout=subprocess.PIPE, env=dbenv)
globals_out.writelines(globals_in.stdout)
globals_out.close()

databases = subprocess.check_output(["psql", "--no-align", "--tuples-only",
    "--command",
    "SELECT datname FROM pg_database WHERE datname NOT IN ('postgres',"
    "'template0','template1')","postgres"], env=dbenv)

for db in databases.split():
    print db



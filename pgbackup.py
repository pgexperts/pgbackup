#!/bin/env python
# -*- coding: utf-8 *-*
#
#    pgbackup.py is licensed under the PostgreSQL License:
#
#    Copyright (c) 2012, PostgreSQL, Experts, Inc.
#
#    Permission to use, copy, modify, and distribute this software and its
#    documentation for any purpose, without fee, and without a written
#    agreement is hereby granted, provided that the above copyright notice and
#    this paragraph and the following two paragraphs appear in all copies.
#
#    IN NO EVENT SHALL POSTGRESQL EXPERTS, INC. BE LIABLE TO ANY PARTY FOR
#    DIRECT, INDIRECT, SPECIAL, INCIDENTAL, OR CONSEQUENTIAL DAMAGES, INCLUDING
#    LOST PROFITS, ARISING OUT OF THE USE OF THIS SOFTWARE AND ITS
#    DOCUMENTATION, EVEN IF POSTGRESQL EXPERTS, INC. HAS BEEN ADVISED OF THE
#    POSSIBILITY OF SUCH DAMAGE.
#
#    POSTGRESQL EXPERTS, INC. SPECIFICALLY DISCLAIMS ANY WARRANTIES, INCLUDING,
#    BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
#    FOR A PARTICULAR PURPOSE. THE SOFTWARE PROVIDED HEREUNDER IS ON AN "AS IS"
#    BASIS, AND POSTGRESQL EXPERTS, INC. HAS NO OBLIGATIONS TO PROVIDE
#    MAINTENANCE, SUPPORT, UPDATES, ENHANCEMENTS, OR MODIFICATIONS.

from time import strftime, time
import tempfile
import bz2
import os
import socket
import subprocess
from optparse import OptionParser

parser = OptionParser()

parser.add_option('-a', "--alertemail", action="store", type="string",
                  dest="alertemail", default='nobody@pgexperts.com')
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
if options.debug:
    print "GLOBALSFILE: " + globalsfile

globals_out = bz2.BZ2File(globalsfile, 'wb')
globals_in = subprocess.Popen(["pg_dumpall", "--globals"],
    stdout=subprocess.PIPE, stderr=logfile, env=dbenv)
globals_out.writelines(globals_in.stdout)
globals_out.close()

# Let's get a list of databases to dump
databases = subprocess.check_output(["psql", "--no-align", "--tuples-only",
    "--command",
    "SELECT datname FROM pg_database WHERE datname NOT IN ('postgres', "
    "'template0','template1')", "postgres"], env=dbenv)

# Now that we've got a list, let's get to work
for db in databases.split():
    if options.debug:
        print "DB: " + db
    dbfile = options.backupdir + '/' + dbhost + '-' + db + '-'\
      + strftime('%Y%m%d') + '.dmp'
    if options.debug:
        print "DBFILE: " + dbfile
    pg_dump = ['pg_dump', '--format=custom',
        '--compress=' + str(options.compress),
        '--file=' + dbfile, db]
    if options.debug:
        print "PG_DUMP: " + str(pg_dump)
    dumpreturnvalue = subprocess.call(pg_dump, stderr=logfile, env=dbenv)
    if dumpreturnvalue != 0:
        failed = 1

#Cleanup old backups
now = time()
for dumpfile in os.listdir(options.backupdir):
    if os.stat(os.path.join(options.backupdir, dumpfile)).st_mtime\
      < now - options.keep * 86400:
        if os.path.isfile(os.path.join(options.backupdir, dumpfile)):
            try:
                os.remove(os.path.join(options.backupdir, dumpfile))
            except:
                print "Error deleting " + dumpfile

# Print out the logfile which contains stderr from pg_dump
# if we failed
if failed:
    print "dump failed"
    logfile.seek(0)
    for errorline in logfile:
      print errorline

logfile.close()

pgbackup
========

pgbackup is a python script for automating pg_dumps of all databases in a
PostgreSQL cluster in the pg_dump custom format. It also dumps the globals
as a bzip2'd SQL file.

It will use libpq variables defined in your environment or specified
on the command line.

Requires Python 2.7+

Usage: pgbackup.py [options]

    Options:
      -h, --help            show this help message and exit
      -a ALERTEMAIL, --alertemail=ALERTEMAIL
      -d BACKUPDIR, --destdir=BACKUPDIR
      -k KEEP, --keep=KEEP  
      --pghost=PGHOST       
      -U PGUSER, --pguser=PGUSER
      -p PGPORT, --port=PGPORT
      -c COMPRESS, --compress=COMPRESS
      --debug    

LICENSE
-------

This package is licensed under the PostgreSQL License. See the LICENSE file for 
details.

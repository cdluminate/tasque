from collections import namedtuple
import os

# Data Definition
DB_TABLE_CONFIG = 'config'
CONFIG_FIELDS = 'key, value'
Config = namedtuple('Config', CONFIG_FIELDS)

DB_TABLE_TASQUE = 'tq'
TASK_FIELDS = 'id, pid, cwd, cmd, retval, stime, etime, pri, rsc'
Task = namedtuple('Task', TASK_FIELDS)

DB_TABLE_NOTES = 'notes'
NOTE_FIELDS = 'noteid, id, note'
Note = namedtuple('Note', NOTE_FIELDS)

# TASQUE_DB is the key variable.
if os.getenv('TASQUE_DB') is not None:
    TASQUE_DB = os.path.expanduser(os.getenv('TASQUE_DB'))
else:
    TASQUE_DB = os.path.expanduser('~/.tasque/tasq.db')

# the rest TASQUE_* variables are auto-configured according to TASQUE_DB
TASQUE_DIR = os.path.dirname(TASQUE_DB)
TASQUE_LOG = os.path.join(TASQUE_DIR, 'tasq.log')
TASQUE_PID = os.path.join(TASQUE_DIR, 'tasque.pid')

from collections import namedtuple

DB_TABLE_TASQUE = 'tq'
TASK_FIELDS = 'id, pid, cwd, cmd, retval, stime, etime, pri, rsc'
Task = namedtuple('Task', TASK_FIELDS)

DB_TABLE_NOTES = 'notes'
NOTE_FIELDS = 'noteid, id, note'
Note = namedtuple('Note', NOTE_FIELDS)

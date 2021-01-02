from pprint import pprint
from typing import *
import atexit
import io
import logging as log
import math
import multiprocessing as mp
import os
import re
import select
import shlex
import signal
import socket
import sqlite3
import subprocess
import sys
import time
import random
from . import db
from . import defs
from . import daemon
from . import utils
import rich
c = rich.get_console()

class tqClient:
    '''
    Client functionalities.
    '''

    def __init__(self):
        self.db = db.tqDB(defs.TASQUE_DB)

    def stop(self):
        '''
        Stop the tasque daemon
        '''
        if os.path.exists(defs.TASQUE_PID):
            with open(defs.TASQUE_PID) as f:
                pid = int(f.read())
                os.kill(pid, signal.SIGTERM)
            c.log(f'Tasque daemon <{pid}> has been killed.')
        else:
            c.log(f'Tasque daemon is not running.')

    def kill(self, taskid: int):
        '''
        Kill the worker specified by given task id
        '''
        if not os.path.exists(defs.TASQUE_DB):
            c.log('cannot find the database.')
            return None
        sql = f'select pid from tq where (id = {id_}) limit 1'
        taskpid = self.db[sql][0]
        c.log(f'Requested to kill task {taskid} with pid {taskpid}')
        if utils.checkpid(taskpid):
            os.kill(taskpid, signal.SIGTERM)

    def purge(self):
        '''
        remove the database and the logs
        '''
        # remove all related file if tqd is not running
        if not os.path.exists(defs.TASQUE_PID):
            if os.path.exists(logfile):
                os.unlink(logfile)
            if os.path.exists(dbpath):
                os.unlink(dbpath)
            c.log('Purged TASQUE database and logs...')

    def clear(self):
        '''
        cleanup finished entries in the database
        '''
        results = self.db[f'select id from tq where (retval is not null)']
        for taskid in [x[0] for x in results]:
            self.db(f'delete from notes where (id = {taskid})')
        self.db(f'delete from tq where retval is not null')
        c.log('cleared (either correctly or incorrectly) finished tasks.')

    def enqueue(self, taskid: int = None, pid: int =None,
            cwd: str = None, cmd: str = None, retval: str =None,
            stime: int = None, etime: int = None,
            pri: int = 0, rsc: float = None) -> None:
        '''
        Enqueue a task into tq database. One must provide (cwd, cmd)

        id: must, int, task indicator
        pid: opt, None or int or bool, int for PID, None for waiting, bool True for complete
        cwd: must, str
        cmd: must, str
        retval: opt, None or int
        stime: opt, None or long, seconds since epoch, start time
        etime: opt, None or long, seconds since epoch, end time
        pri: opt, None or int
        rsc: opt, None or float.
        '''
        ids = [t[0] for t in self.db['select id from tq']]
        id_ = max(ids)+1 if len(ids) > 0 else 1
        if cmd is None:
            raise ValueError('must provide a valid cmd')
        task = defs.Task._make([
            'null' if v is None else v for v in
            (id_, pid, cwd, cmd, retval, stime, etime, pri, rsc)])
        with c.status('Adding new task to the queue ...'):
            c.log('Enqueue:', task)
            self.db += task

    def dequeue(self, id_: int):
        '''
        Remove a task specified by id_ from Tq database.
        Do nothing if pid is not empty for sanity.
        '''
        # remove related notes
        self.db(f'delete from notes where (id = {id_})')
        # remove task itself
        self.db(f'delete from tq where ((pid is null) or (pid < 0)) and (id = {id_})')
        c.log(f'Removed task <{id_}> from task queue.')

    def dump(self):
        '''
        Dump database to screen. Raw version of tqLS.
        '''
        self.db.dump()

    def isdaemonalive(self) -> bool:
        '''
        Check if TQD is alive given the pidfile.
        '''
        if os.path.exists(defs.TASQUE_PID):
            with open(defs.TASQUE_PID) as f:
                pid = int(f.read())
            if utils.checkpid(pid):
                return True
            else:
                # process does not exist
                os.remove(defs.TASQUE_PID)
                return False
        else:
            return False

    def start(self):
        tqd = daemon.tqD()
        tqd.Start()

# def tqEdit(pidfile: str, dbpath: str, id_: int, *, pri: int = 0, rsc: int = 10):
#     '''
#     editing Pri and Rsc attributes
#     '''
#     sql = f"update tq set pri = {pri}, rsc = {rsc}" \
#         + f" where (id = {id_}) limit 1"
#     log.debug(f'tqEdit SQL update -- {sql}')
#     dbExec(dbpath, sql)
# 
# 
# def tqNote(pidfile: str, dbpath: str, id_: int, note: str) -> None:
#     '''
#     Take note in specified task entry
#     '''
#     # get a noteid
#     sql = f'select noteid from notes'
#     results = dbQuery(dbpath, sql)
#     noteid = max(x[0] for x in results) + 1 if len(results) > 0 else 1
#     sql = f'insert into notes (noteid, id, note) values ({noteid}, {id_}, {repr(note)})'
#     log.info(f'TQ taking notes ... {sql}')
#     dbExec(dbpath, sql)
# 
# 
# def tqDelNote(pidfile: str, dbpath: str, noteid: int) -> None:
#     '''
#     Remove the note specified by noteid
#     '''
#     sql = f'delete from notes where (noteid = {noteid})'
#     dbExec(dbpath, sql)
# 
# 
# def tqDumpNotes(pidfile: str, dbpath: str) -> None:
#     '''
#     Pretty print of the notes
#     '''
#     sql = f'select noteid, id, note from notes'
#     notes = dbQuery(dbpath, sql)
#     for noteid, id_, note in notes:
#         symbol = random.choice('♩♪♫♬♭♮♯')
#         randcolor = f'\033[{random.randint(0,1)};{random.randint(31,37)}m'
#         print(noteid, randcolor + symbol + '\033[m', f'Task[{id_}]', ':', note)
# 
# def tqLs(pidfile: str, dbpath: str) -> None:
#     '''
#     List items in the tq database in pretty format. Fancy version of tqDumpDB
#     '''
#     if not os.path.exists(dbpath):
#         log.error('Oops! TQ database is not found.')
#         return
#     sql = 'select * from tq'
#     tasks = dbQuery(dbpath, sql)
#     sql = 'select id, note from notes'
#     notes = dbQuery(dbpath, sql)
#     print(yellow('┌───┬'+'─'*73+'┐'))
#     for k, task in enumerate(tasks, 1):
#         id_, pid, cwd, cmd, retval, stime, etime, pri, rsc = task
#         if retval is None and pid is None:  # wait
#             status = white('[♨]')
#         elif retval is not None and pid is None:
#             status = Green('[✓]') if retval == 0 else RedB(White(f'[✗ {retval}]'))
#         elif retval is None and pid is not None:
#             status = Cyan(f'[⚙ {pid}]') if pid > 0 else Yellow(f'[⚠ Accident]')
#         else:
#             status = redB('[???BUG???]')
#         # first line : status
#         print(Yellow(f'│{id_:>3d}│'), 'St', status,
#               f'| Pri {Purple("-" if 0==pri else str(pri))}',
#               f'| Rsc {Purple("-" if 10==rsc else str(rsc))}')
#         # second line : time
#         if all((stime, etime)):
#             print(yellow('│   ├'), Yellow('☀'), Purple(f'{sec2hms(etime-stime)}'),
#                   f'| ({time.ctime(stime)}) ➜ ({time.ctime(etime)})')
#         elif stime:
#             print(yellow('│   ├'), Yellow('☀'), f'Started at ({time.ctime(stime)})',
#                   Purple(f'➜ {sec2hms(time.time() - stime)}'), 'Elapsed.')
#         # third line: cwd
#         print(yellow('│   ├'), Yellow('⚑'), Blue(cwd))
#         prog, args = cmd.split()[0], ' '.join(cmd.split()[1:])
#         # fourth line: cmd
#         print(yellow('│   ├'), Yellow('✒'), purple(underline(prog)), green(underline(args)))
#         # optional fifth+ lines
#         for id_, note in [(k, m) for (k, m) in notes if k == id_]:
#             symbol = random.choice('♩♪♫♬♭♮♯')
#             print(yellow('│   │'), cyan(symbol) + ' ', note)
#         print(yellow('├───┼'+'─'*73+'┤'))
#     # print summary
#     sql = 'select id from tq where not (pid is null) and (pid > 0)'
#     stat_running = len(dbQuery(dbpath, sql))
#     sql = 'select id from tq where (pid is null) and (retval is null)'
#     stat_wait = len(dbQuery(dbpath, sql))
#     sql = 'select id from tq where (pid is null) and not (retval is null)'
#     stat_done = len(dbQuery(dbpath, sql))
#     sql = 'select id from tq where not (pid is null) and (pid < 0)'
#     stat_accident = len(dbQuery(dbpath, sql))
#     sql = f'select rsc from tq where (pid is not null) and (pid > 0)'
#     arsc = 10 - sum(x[0] for x in dbQuery(dbpath, sql))
# 
#     tqdstatus = Green('☘') if _tqCheckAlive(pidfile) else White('❄')
#     print(yellow('│ ') + tqdstatus + yellow(' │'),
#           f'Stat: {stat_running:>2d} Running, {stat_wait:>2d} Waiting,',
#           f'{stat_done:>2d} Done, {stat_accident:>2d} Accident,',
#           f'{arsc:>2d} Rsc Avail.', '    ', yellow(' │'))
#     # last line
#     print(yellow('└───┴'+'─'*73+'┘'))
# 
# 

# def _tqCheckWorkerAlive(dbpath: str) -> bool:
#     '''
#     Check if the "running" workers are alive.
#     Set pid to -1 to indicate abnormal behaviour.
#     '''
#     if os.path.exists(dbpath):
#         sql = 'select id, pid from tq where (not pid is null) and (retval is null)'
#         workers = dbQuery(dbpath, sql)
#         wkstat = [_tqCheckPID(pid) for id_, pid in workers]
#         if all(wkstat):
#             return True
#         else:
#             xids = [workers[i][0] for i, st in enumerate(wkstat) if not st]
#             for id_ in xids:
#                 sql = f'update tq set pid = {-1} where (id = {id_})'
#                 dbExec(dbpath, sql)
#             return False
#     else:
#         return True


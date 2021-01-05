'''
Copyright (C) 2020-2021 Mo Zhou <lumin@debian.org>
License: MIT/Expat
'''

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
from termcolor import colored, cprint
import rich
c = rich.get_console()

class tqClient:
    '''
    Client functionalities.
    '''

    def __init__(self):
        self.db = db.tqDB(defs.TASQUE_DB)
        self._CheckWorkerAlive()

    def _CheckWorkerAlive(self) -> bool:
        '''
        Check if the "running" workers are alive.
        Set their pid field to -1 to indicate abnormal behaviour.
        '''
        workers = self.db['select id, pid from tq where (not pid is null) and (retval is null)']
        wkstat = {taskid: utils.checkpid(int(pid)) for taskid, pid in workers}
        if len(wkstat) == 0 or all(wkstat.values()):
            return True
        else:
            for taskid, check in wkstat.items():
                if check:
                    continue
                self.db(f'UPDATE tq SET pid = -1 WHERE (id = {taskid})')
            return False

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
        sql = f'select pid from tq where (id = {taskid}) limit 1'
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
        results = self.db[f'select id from tq where (retval is not "null")']
        for taskid in [x[0] for x in results]:
            self.db(f'delete from notes where (id = {taskid})')
        self.db(f'delete from tq where (retval is not "null")')
        c.log('cleared (either correctly or incorrectly) finished tasks.')

    def enqueue(self, taskid: int = None, pid: int = None,
            cwd: str = None, cmd: str = None, retval: str = None,
            stime: int = None, etime: int = None,
            pri: int = 0, rsc: float = 1.0) -> None:
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
        taskid = max(ids)+1 if len(ids) > 0 else 1
        if cmd is None:
            raise ValueError('must provide a valid cmd')
        task = defs.Task._make(utils.none2null(
            (taskid, pid, cwd, cmd, retval, stime, etime, pri, rsc)))
        with c.status('Adding new task to the queue ...'):
            c.log('Enqueue:', task)
            self.db += task

    def dequeue(self, taskid: int):
        '''
        Remove a task specified by taskid from Tq database.
        Do nothing if pid is not empty for sanity.
        '''
        # remove related notes
        self.db(f'delete from notes where (id = {taskid})')
        # remove task itself
        self.db(f'delete from tq where ((pid is null) or (pid < 0)) and (id = {taskid})')
        c.log(f'Removed task <{taskid}> from task queue.')

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
        c.log('Starting tqD ...')
        tqd = daemon.tqD()
        tqd.Start()

    def annotate(self, taskid: int, note: str):
        '''
        Take note in a specified task entry
        '''
        # get a noteid
        R = self.db[f'SELECT noteid FROM notes']
        noteid = max(x[0] for x in R) + 1 if len(R) > 0 else 1
        self.db(f'INSERT INTO notes (noteid, id, note) VALUES ({noteid}, {taskid}, {repr(note)})')
        c.log(f'Annotating task<{taskid}>: {note}')

    def delannotation(self, noteid: int) -> None:
        '''
        Remove the note specified by noteid
        '''
        self.db(f'DELETE FROM notes WHERE (noteid = {noteid})')

    def dumpannotation(self) -> None:
        '''
        Pretty print of the notes
        '''
        R = self.db[f'select noteid, id, note from notes']
        for noteid, taskid, note in R:
            symbol = random.choice('♩♪♫♬♭♮♯')
            randcolor = f'\033[{random.randint(0,1)};{random.randint(31,37)}m'
            print(noteid, randcolor + symbol + '\033[m', f'Task[{taskid}]', ':', note)

    def edit(self, taskid: int, *, pri: int = None, rsc: int = None):
        '''
        editing Pri and Rsc attributes
        '''
        if pri is not None:
            self.db(f'UPDATE tq SET pri = {pri} WHERE (id = {taskid}) limit 1')
        if rsc is not None:
            self.db(f'UPDATE tq SET rsc = {rsc} WHERE (id = {taskid}) limit 1')

    def config(self, key: str, value: str):
        '''
        edit config in the database
        '''
        if key in [x[0] for x in self.db['config']]:
            sql = f'UPDATE config SET value = "{value}" WHERE (key = "{key}")'
        else:
            sql = f'INSERT INTO config VALUES ("{key}", "{value}")'
        c.log(sql)
        self.db(sql)

    def tqls(self):
        '''
        List items in the tq database in pretty format.
        This function is bulky ...
        '''
        tasks = self.db['select * from tq']
        notes = self.db['select id, note from notes']
        cprint('╭───┬'+'─'*73+'╮', 'yellow')
        for k, task in enumerate(tasks, 1):
            taskid, pid, cwd, cmd, retval, stime, etime, pri, rsc = task
            taskid, pid, retval, stime, etime, pri = map(
                    lambda x: x if x is None else int(x),
                    (taskid, pid, retval, stime, etime, pri))
            if retval is None and pid is None:  # wait
                status = colored('[♨]', 'white')
            elif retval is not None and pid is None:
                status = colored('[✓]', 'green') if int(retval) == 0 else colored(f'[✗ {retval}]', 'white', 'on_red')
            elif retval is None and pid is not None:
                status = colored(f'[⚙ {pid}]', 'cyan', None, ['bold']) if int(pid) > 0 else colored(f'[⚠ Accident]', 'yellow', None, ['bold'])
            else:
                status = colored('[???BUG???]', None, 'on_red')
            # first line : status
            print(colored(f'│{taskid:>3d}│', 'yellow'), 'St', status,
                  f'| Pri {colored("-" if 0==pri else str(pri), "magenta")}',
                  f'| Rsc {colored("-" if 10==rsc else str(rsc), "magenta")}')
            # second line : time
            if all((stime is not None, etime is not None)):
                print(colored('│   ├', 'yellow'), colored('☀', 'yellow'), colored(f'{utils.sec2hms(float(etime)-float(stime))}', 'magenta'),
                      f'| ({time.ctime(int(stime))}) ➜ ({time.ctime(int(etime))})')
            elif stime:
                print(colored('│   ├', 'yellow'), colored('☀', 'yellow'), f'Started at ({time.ctime(stime)})',
                      colored(f'➜ {utils.sec2hms(time.time() - stime)}', 'magenta'), 'Elapsed.')
            # third line: cwd
            print(colored('│   ├', 'yellow'), colored('⚑', 'yellow'), colored(cwd, 'blue'))
            prog, args = cmd.split()[0], ' '.join(cmd.split()[1:])
            # fourth line: cmd
            print(colored('│   ├', 'yellow'), colored('✒', 'yellow'),
                    colored(prog, 'magenta', None, ['underline']),
                    colored(args, 'green', None, ['underline']))
            # optional fifth+ lines
            for taskid, note in [(k, m) for (k, m) in notes if k == taskid]:
                symbol = random.choice('♩♪♫♬♭♮♯')
                print(colored('│   │', 'yellow'), colored(symbol, 'cyan') + ' ', note)
            print(colored('├───┼'+'─'*73+'┤', 'yellow'))
        # print summary
        sql = 'select id from tq where not (pid is null) and (pid > 0)'
        stat_running = len(self.db[sql])
        sql = 'select id from tq where (pid is null) and (retval is null)'
        stat_wait = len(self.db[sql])
        sql = 'select id from tq where (pid is null) and not (retval is null)'
        stat_done = len(self.db[sql])
        sql = 'select id from tq where not (pid is null) and (pid < 0)'
        stat_accident = len(self.db[sql])

        tqdstatus = colored('☘', 'green') if self.isdaemonalive() else colored('❄', 'white')
        print(colored('│ ', 'yellow') + tqdstatus + colored(' │', 'yellow'),
              f'Stat: {stat_running:>2d} Running, {stat_wait:>2d} Waiting,',
              f'{stat_done:>2d} Done, {stat_accident:>2d} Accident.',
              '                  ', colored(' │', 'yellow'))
        # last line
        cprint('╰───┴'+'─'*73+'╯', 'yellow')

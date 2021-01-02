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

# external dependencies
import zstd


# def daemonize(*, uid, pidfile,
#               stdin='/dev/null', stdout='/dev/null', stderr='/dev/null'):
#     '''
#     Turn into a Daemon
#     '''
# 
#     if os.path.exists(pidfile):
#         raise RuntimeError('Already running')
# 
#     # First fork (detaches from parent)
#     try:
#         if os.fork() > 0:
#             raise SystemExit(0)   # Parent exit
#     except OSError as e:
#         raise RuntimeError('fork #1 failed.')
# 
#     os.chdir('/')
#     os.umask(0)
#     os.setsid()
#     # Second fork (relinquish session leadership)
#     try:
#         if os.fork() > 0:
#             raise SystemExit(0)
#     except OSError as e:
#         raise RuntimeError('fork #2 failed.')
# 
#     # Flush I/O buffers
#     sys.stdout.flush()
#     sys.stderr.flush()
# 
#     # Replace file descriptors for stdin, stdout, and stderr
#     with open(stdin, 'rb', 0) as f:
#         os.dup2(f.fileno(), sys.stdin.fileno())
#     with open(stdout, 'ab', 0) as f:
#         os.dup2(f.fileno(), sys.stdout.fileno())
#     with open(stderr, 'ab', 0) as f:
#         os.dup2(f.fileno(), sys.stderr.fileno())
# 
#     # Write the PID file
#     os.system('touch {}'.format(pidfile))
#     with open(pidfile, 'w+') as f:
#         print(os.getpid(), file=f)
# 
#     # Arrange to have the PID file removed on exit/signal
#     atexit.register(lambda: os.remove(pidfile))
# 
#     # Signal handler for termination (required)
#     def sigterm_handler(signo, frame):
#         log.info(f'TQD[{os.getpid()}] recieved SIGTERM, exit.')
#         raise SystemExit(1)
# 
#     signal.signal(signal.SIGTERM, sigterm_handler)
# 
# 
# def _tqWorker(dbpath: str, task: tuple) -> None:
#     '''
#     Process a task.
#     (id, pid, cwd, cmd, retval, stime, etime, pri, rsc)
#     '''
#     task = (x if x is not None else 'null' for x in task)
#     id_, pid, cwd, cmd, retval, stime, etime, pri, rsc = task
#     pid = os.getpid()
# 
#     # update database before working
#     sql = f"update tq set pid = {pid}, stime = {time.time()}" \
#         + f" where (id = {id_})"
#     log.info(f'Worker[{os.getpid()}]: SQL update -- {sql}')
#     dbExec(dbpath, sql)
# 
#     try:
#         # change directory, fork and execute the task.
#         os.chdir(cwd)
#         proc = subprocess.Popen(
#             shlex.split(cmd), shell=False, stdin=None,
#             stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=cwd)
# 
#         # override TQD's sigaction handler
#         def sigterm_handler(signo, frame):
#             log.info(f'Worker[{os.getpid()}] recieved SIGTERM. Gracefully pulling down task process...')
#             proc.kill()
#             os._exit(0)
#         signal.signal(signal.SIGTERM, sigterm_handler)
# 
#         # If nothing goes wrong, we'll get the content of stdout and stderr
#         tqout, tqerr = proc.communicate()
#         retval = proc.returncode
#     except FileNotFoundError as e:
#         log.error(f'Worker[{os.getpid()}]: {str(e)}')
#         tqout, tqerr, retval = '', '', -1
#     except Exception as e:
#         log.error(f'Worker[{os.getpid()}]: {str(e)}')
#         tqout, tqerr, retval = '', '', -1
#     finally:
#         log.info(f'Worker[{os.getpid()}]: subprocess.Popen() successfully returned without exception.')
# 
#     os.chdir(cwd)
#     timestamp = time.strftime('%Y%m%d.%H%M%S')
#     if len(tqout) > 0:
#         with open(f'tq_id-{id_}_{timestamp}.stdout.zst', 'wb') as f:
#             f.write(zstd.dumps(tqout))
#     if len(tqerr) > 0:
#         with open(f'tq_id-{id_}_{timestamp}.stderr.zst', 'wb') as f:
#             f.write(zstd.dumps(tqerr))
# 
#     # update database after finishing the task
#     sql = f"update tq set retval = {retval}, etime = {time.time()}," \
#         + f"pid = null where (id = {id_})"
#     log.info(f'Worker[{os.getpid()}]: SQL update -- {sql}')
#     dbExec(dbpath, sql)
#     # don't remove pidfile! i.e. don't trigger atexit().
#     os._exit(0)
# 
# 
# def _tqWPrefresh(workerpool: List) -> List:
#     '''
#     Refresh a worker pool, removing dead workers. Return a clean workerpool.
#     '''
#     _wp = []
#     for w in workerpool:
#         if w.is_alive():
#             _wp.append(w)
#         else:
#             w.join(timeout=3)
#             w.terminate()
#     return _wp
# 
# 
# def _tqDaemon(dbpath: str, pidfile: str) -> None:
#     '''
#     Tq's Daemon, the scheduler
#     '''
#     log.info(f'TQD[{os.getpid()}] Here we go! (Start)')
# 
#     if not os.path.exists(dbpath):
#         log.info(f'TQD[{os.getpid()}] is creating a new SQLite3 databse ...')
#         _tqCreateDB(dbpath)
#     log.info(f'TQD[{os.getpid()}] is keeping an eye on SQLite3 databse ...')
# 
#     def _daemonsleep() -> None:
#         time.sleep(1)
# 
#     workerpool = []
#     while True:
# 
#         # Assessment: find the current available resource coefficient
#         sql = f'select rsc from tq where (pid is not null) and (pid > 0)'
#         arsc = 10 - sum(x[0] for x in dbQuery(dbpath, sql))
# 
#         # Assessment: find the current highest priority among running jobs
#         sql = f'select pri from tq where (pid is not null) and (pid > 0)'
#         results = dbQuery(dbpath, sql)
#         curhighpri = max(x[0] for x in results) if len(results)>0 else 0
# 
#         # Tier 1 candidate: is there any high-pri candidate waiting in queue?
#         sql = f'select id from tq where (pid is null) and (retval is null) and (pri > {curhighpri}) order by pri desc'
#         results = dbQuery(dbpath, sql)
#         if len(results) > 0:
#             sql = f'select * from tq where (pid is null) and (retval is null) and (pri > {curhighpri}) and (rsc <= {arsc}) order by pri desc'
#             todolist = dbQuery(dbpath, sql)
#         else:
#             # Tier 2 candidates: equal priority tasks
#             sql = f'select id from tq where (pid is null) and (retval is null) and (pri = {curhighpri}) order by id'
#             results = dbQuery(dbpath, sql)
#             if len(results) > 0:
#                 sql = f'select * from tq where (pid is null) and (retval is null) and (pri = {curhighpri}) and (rsc <= {arsc}) order by id'
#                 todolist = dbQuery(dbpath, sql)
#             else:
#                 # Tier 3 candidates: lower priority
#                 sql = f'select * from tq where (pid is null) and (retval is null) and (rsc <= {arsc}) order by pri desc, id'
#                 todolist = dbQuery(dbpath, sql)
# 
#         if len(todolist) > 0:  # there are works to do
#             task = todolist[0]
#             log.debug(f'TQD[{os.getpid()}]: Next task -- {task}')
#             id_, pid, cwd, cmd, retval, stime, etime, pri, rsc = task
# 
#             # create a new worker process for this task
#             worker = mp.Process(target=_tqWorker, args=(dbpath, task))
#             workerpool.append(worker)
#             worker.start()
# 
#         # domestic stuff
#         _daemonsleep()
#         workerpool = _tqWPrefresh(workerpool)
# 
# 
# def tqStart(pidfile: str, sqlite: str, logfile: str) -> None:
#     '''
#     Start the Tq Daemon for Task scheduling
#     '''
#     log.info('starting Tqd ...')
#     try:
#         daemonize(uid=os.getuid(),
#                   pidfile=pidfile,
#                   stdout=logfile,
#                   stderr=logfile)
#     except RuntimeError as e:
#         print(e, file=sys.stderr)
#         raise SystemExit(1)
#     _tqDaemon(sqlite, pidfile)
# 
# 
# def _tqCheckPID(pid: int) -> bool:
#     '''
#     Check if a given process specified by its PID is alive.
#     '''
#     try:
#         os.kill(pid, 0)  # does nothing
#     except OSError:
#         return False
#     else:
#         return True
# 
# 
# def _tqCheckAlive(pidfile: str) -> bool:
#     '''
#     Check if TQD is alive given the pidfile.
#     '''
#     if os.path.exists(pidfile):
#         with open(pidfile) as f:
#             pid = int(f.read())
#         if _tqCheckPID(pid):
#             return True
#         else:
#             # process does not exist
#             os.remove(pidfile)
#             return False
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

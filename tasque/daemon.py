from pprint import pprint
from typing import *
import atexit
import io
import logging
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
import zstd
from . import defs
from . import db
from . import utils
from . import resources

class tqD:
    '''
    Tasque Daemon. In charge of scheduling and spawning task processes.
    '''
    __name__ = 'tqD'

    def __init__(self, *,
            uid:int=os.getuid(),
            pidfile:str=defs.TASQUE_PID,
            stdin='/dev/null',
            stdout='/dev/null',
            stderr='/dev/null',
            ):
        self.db = db.tqDB(defs.TASQUE_DB)
        self.uid = uid
        self.pidfile = pidfile
        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr
        logging.basicConfig(
                filename=defs.TASQUE_LOG,
                format='%(levelno)s %(asctime)s %(process)d %(filename)s:%(lineno)d] %(message)s',
                level=logging.DEBUG)
        self.log = logging
        self.workerpool = list()
        self.config = dict(self.db['config'])
        self.resource = resources.create(self.config['resource'])
        self.idle = lambda: time.sleep(1)

    def Start(self):
        '''
        Start the Tq Daemon for Task scheduling
        '''
        if os.path.exists(self.pidfile):
           raise RuntimeError('Another process is already running')
        self.log.info(f'starting {self.__name__} ...')
        try:
            self.daemonize()
        except RuntimeError as e:
            print(e, file=sys.stderr)
            raise SystemExit(1)
        self.daemonLoop()

    def daemonize(self):
        '''
        Turn into a Daemon
        '''
        # First fork (detaches from parent)
        try:
           if os.fork() > 0:
               raise SystemExit(0)   # Parent exit
        except OSError as e:
           raise RuntimeError('fork #1 failed.')
        os.chdir('/')
        os.umask(0)
        os.setsid()
        # Second fork (relinquish session leadership)
        try:
           if os.fork() > 0:
               raise SystemExit(0)
        except OSError as e:
           raise RuntimeError('fork #2 failed.')
        # Flush I/O buffers
        sys.stdout.flush()
        sys.stderr.flush()
        # Replace file descriptors for stdin, stdout, and stderr
        with open(self.stdin, 'rb', 0) as f:
           os.dup2(f.fileno(), sys.stdin.fileno())
        with open(self.stdout, 'ab', 0) as f:
           os.dup2(f.fileno(), sys.stdout.fileno())
        with open(self.stderr, 'ab', 0) as f:
           os.dup2(f.fileno(), sys.stderr.fileno())
        # Write the PID file
        os.system('touch {}'.format(self.pidfile))
        with open(self.pidfile, 'w+') as f:
           print(os.getpid(), file=f)
        # Arrange to have the PID file removed on exit/signal
        atexit.register(lambda: os.remove(self.pidfile))
        # Signal handler for termination (required)
        def sigterm_handler(signo, frame):
           self.log.info(f'{self.__name__}[{os.getpid()}] exiting on SIGTERM.')
           raise SystemExit(1)
        signal.signal(signal.SIGTERM, sigterm_handler)

    def refresh_workerpool(self):
        # cleanup the worker pool regularly, removing dead workers
        wp_ = []
        for w in self.workerpool:
            if w.is_alive():
                wp_.append(w)
            else:
                w.join(timeout=3)
                w.terminate()
        self.workerpool = wp_

    def daemonLoop(self):
        '''
        Tasque Daemon (scheduler) main loop
        '''
        self.log.info(f'{self.__name__}[{os.getpid()}] All set. Here we go!')
        self.log.info(f'{self.__name__}[{os.getpid()}] I am watching SQLite3 databse ...')

        while True:
            # Assessment: should I be idle?
            R = self.db[f'select id, pri from tq where (pid is "null") and (retval is "null")']
            if not R:
                self.refresh_workerpool()
                self.idle()
                continue
            # find the highest priority among pending jobs
            hpri = max(x[1] for x in R) if len(R)>0 else 0
            # traverse the task list of priority <pri> that we can run
            R = self.db[f'select * from tq where (pid is "null") and (retval is "null") and (pri = {hpri}) order by id']
            tasks = [defs.Task._make(r) for r in R]
            for task in tasks:
                # can we allocate the required resource?
                if not self.resource.canalloc(task.rsc):
                    continue
                # spawn the worker process
                self.log.info(f'{self.__name__}[{os.getpid}] Next task: {str(task)}')
                # create a new worker process for this task
                worker = mp.Process(target=tasqueWorker,
                        args=(self.db, self.log, self.resource, task))
                self.workerpool.append(worker)
                worker.start()
            # cleanup the worker pool regularly, removing dead workers
            self.refresh_workerpool()
            self.idle()

def tasqueWorker(
        db: db.tqDB,
        log: object,
        resource: resources.AbstractResource,
        task: defs.Task,
        ):
    '''
    worker function for processing a Task.
    (id, pid, cwd, cmd, retval, stime, etime, pri, rsc)
    '''
    pid = os.getpid()
    # allocate resource
    acquire, release = resource.request(pid, task.rsc)
    acquire()
    # update database before working
    sql = f"update tq set pid = {pid}, stime = {time.time()} where (id = {task.id})"
    log.info(f'worker[{os.getpid()}]: SQL(pre) -- {sql}')
    db(sql)
    # trying to start task
    try:
        # change directory, fork and execute the task.
        os.chdir(task.cwd)
        cmd = shlex.split(task.cmd)
        log.info(f'Command: {str(cmd)}')
        proc = subprocess.Popen(
            cmd, shell=False, stdin=None,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=task.cwd)
        # override daemon's sigaction handler
        def sigterm_handler(signo, frame):
            log.info(f'worker[{os.getpid()}] recieved SIGTERM. Gracefully pulling down task process...')
            proc.kill()
            release()
            os._exit(0)
        signal.signal(signal.SIGTERM, sigterm_handler)
        # override daemon's atexit action
        atexit.register(lambda: None)
        # If nothing goes wrong, we'll get the content of stdout and stderr
        stdout, _ = proc.communicate()
        retval = proc.returncode
    except FileNotFoundError as e:
        log.error(f'worker[{os.getpid()}]: {str(e)}')
        stdout, retval = '', '', -1
    except Exception as e:
        log.error(f'worker[{os.getpid()}]: {str(e)}')
        stdout, retval = '', '', -1
    finally:
        log.info(f'worker[{os.getpid()}]: subprocess.Popen() successfully returned.')
    # write the stdout (stderr was redirected here)
    release()
    os.chdir(defs.TASQUE_DIR)
    timestamp = time.strftime('%Y%m%d.%H%M%S')
    if len(stdout) > 0:
        with open(f'tq_id-{task.id}_{timestamp}.stdout.zst', 'wb') as f:
            f.write(zstd.dumps(stdout))
    # update database after finishing the task
    sql = f"update tq set retval = {retval}, etime = {time.time()}, pid = null where (id = {task.id})"
    log.info(f'worker[{os.getpid()}]: SQL(post) -- {sql}')
    db(sql)
    # END
    log.info(f'worker[{os.getpid()}]: end gracefully.')

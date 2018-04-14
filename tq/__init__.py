#!/usr/bin/python3
# @brief Command (Task) Queue Daemon for Linux, together with Client utils
# @author COPYRIGHT (C) 2016-2018 Mo Zhou <cdluminate@gmail.com>
# @license MIT License

import atexit
import io
import logging as log
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
from typing import *
import multiprocessing as mp
import math
from pprint import pprint

# Foreground color, normal
def red(x): return re.sub('^(.*)$', '\033[0;31m\\1\033[;m', x)
def green(x): return re.sub('^(.*)$', '\033[0;32m\\1\033[;m', x)
def yellow(x): return re.sub('^(.*)$', '\033[0;33m\\1\033[;m', x)
def blue(x): return re.sub('^(.*)$', '\033[0;34m\\1\033[;m', x)
def purple(x): return re.sub('^(.*)$', '\033[0;35m\\1\033[;m', x)
def cyan(x): return re.sub('^(.*)$', '\033[0;36m\\1\033[;m', x)
def white(x): return re.sub('^(.*)$', '\033[0;37m\\1\033[;m', x)
# Foreground color, bold
def Red(x): return re.sub('^(.*)$', '\033[1;31m\\1\033[;m', x)
def Green(x): return re.sub('^(.*)$', '\033[1;32m\\1\033[;m', x)
def Yellow(x): return re.sub('^(.*)$', '\033[1;33m\\1\033[;m', x)
def Blue(x): return re.sub('^(.*)$', '\033[1;34m\\1\033[;m', x)
def Purple(x): return re.sub('^(.*)$', '\033[1;35m\\1\033[;m', x)
def Cyan(x): return re.sub('^(.*)$', '\033[1;36m\\1\033[;m', x)
def White(x): return re.sub('^(.*)$', '\033[1;37m\\1\033[;m', x)
# background color
def RedB(x): return re.sub('^(.*)$', '\033[1;41m\\1\033[;m', x)
# other control sequences
def Tset(x): return re.sub('^(.*)$', '\0337\\1', x)  # store location
def Tcls(x): return re.sub('^(.*)$', '\033[K\\1', x)  # clear line
def Tres(x): return re.sub('^(.*)$', '\\1\0338', x)  # restore location 


def sec2hms(s: float) -> str:
    '''
    Convert X seconds into A hour B minute C seconds as a string.
    '''
    sec = math.fmod(s, 60.0)
    mm  = (int(s) // 60) % 60
    hh  = (int(s) // 60) // 60
    return f'{hh}h{mm}m{sec:.3f}s'


def dbExec(dbpath: str, sql: str) -> None:
    '''
    Execute a SQL statement on a given DB file.
    '''
    conn = sqlite3.connect(dbpath)
    conn.execute(sql)
    conn.commit()
    conn.close()


def dbQuery(dbpath: str, sql: str) -> List:
    '''
    Query from DB
    '''
    tq = sqlite3.connect(dbpath)
    cursor = tq.cursor()
    cursor.execute(sql)
    values = cursor.fetchall()  # len(values) may be 0
    cursor.close()
    tq.close()
    return values


def tqCreateDB(dbpath: str) -> None:
    '''
    Create a sqlite3 database for Tq Daemon use.
    '''
    sql = 'create table tq (id, pid, cwd, cmd, retval, stime, etime, pri, rsc)'
    dbExec(dbpath, sql)


def sql_pretty(sql):
    '''
    SQL statement formatter
    '''
    ret = sql
    pre = '    sqlite3 operation ...'
    prompt = '    sqlite3>  '
    prompt2 = '    sqlite3.. '
    ret = ret.replace('select', pre+'\n'+prompt+'select')
    ret = ret.replace('update', pre+'\n'+prompt+'update')
    ret = ret.replace('insert', pre+'\n'+prompt+'insert')
    ret = ret.replace('values', '\n'+prompt2+'values')
    ret = ret.replace('where', '\n'+prompt2+'where')
    ret = ret.replace('and', '\n'+prompt2+'and')
    ret = ret.replace('or', '\n'+prompt2+'or')
    return ret


def daemonize(*, uid, pidfile,
              stdin='/dev/null', stdout='/dev/null', stderr='/dev/null'):
    '''
    Turn into a Daemon
    '''

    if os.path.exists(pidfile):
        raise RuntimeError('Already running')

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
    with open(stdin, 'rb', 0) as f:
        os.dup2(f.fileno(), sys.stdin.fileno())
    with open(stdout, 'ab', 0) as f:
        os.dup2(f.fileno(), sys.stdout.fileno())
    with open(stderr, 'ab', 0) as f:
        os.dup2(f.fileno(), sys.stderr.fileno())

    # Write the PID file
    os.system('touch {}'.format(pidfile))
    with open(pidfile, 'w+') as f:
        print(os.getpid(), file=f)

    # Arrange to have the PID file removed on exit/signal
    atexit.register(lambda: os.remove(pidfile))

    # Signal handler for termination (required)
    def sigterm_handler(signo, frame):
        log.info('recieved SIGTERM, exit.')
        raise SystemExit(1)

    signal.signal(signal.SIGTERM, sigterm_handler)


def _tqWorker(dbpath: str, task: tuple) -> None:
    '''
    Process a task.
    (id, pid, cwd, cmd, retval, stime, etime, pri, rsc)
    '''
    task = (x if x is not None else 'null' for x in task)
    id_, pid, cwd, cmd, retval, stime, etime, pri, rsc = task
    pid = os.getpid()

    # update database before working
    sql = f"update tq set pid = {pid}, stime = {time.time()}" \
        + f" where (id = {id_}) limit 1"
    log.info(f'updating SQL: {sql}')
    dbExec(dbpath, sql)
    log.debug(sql_pretty(sql))

    try:
        os.chdir(cwd)
        proc = subprocess.Popen(
            shlex.split(cmd), shell=False, stdin=None,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=cwd)
        tqout, tqerr = proc.communicate()
        retval = proc.returncode
    except FileNotFoundError as e:
        log.error('    {}'.format(str(e)))
        tqout, tqerr = '', ''
        retval = -1
    except:
        log.error('    {}'.format('Unknown Error!'))
        tqout, tqerr = '', ''
        retval = -1
    finally:
        log.info('    tq_popen done')

    os.chdir(cwd)
    if len(tqout) > 0:
        with open('tq.out', 'a+') as f:
            f.write(tqout.decode())
    if len(tqerr) > 0:
        with open('tq.err', 'a+') as f:
            f.write(tqerr.decode())

    # update database after finishing the task
    sql = f"update tq set retval = {retval}, etime = {time.time()}," \
        + f"pid = null where (id = {id_}) limit 1"
    log.debug(sql_pretty(sql))
    dbExec(dbpath, sql)
    # don't remove pidfile! i.e. don't trigger atexit().
    os._exit(0)


def _tqWPrefresh(workerpool: List) -> List:
    '''
    Refresh a worker pool, removing dead workers. Return a clean workerpool.
    '''
    _wp = []
    for w in workerpool:
        if w.is_alive():
            _wp.append(w)
        else:
            w.join(timeout=3)
            w.terminate()
    return _wp


def _tqDaemon(dbpath: str, pidfile: str) -> None:
    '''
    Tq's Daemon, the scheduler
    '''
    log.info(f'Tqd started with pid {os.getpid()}')

    if not os.path.exists(dbpath):
        tqCreateDB(dbpath)
    log.debug('Tqd keeping an eye on sqlite3')

    workerpool = []
    while True:

        # look for todo task
        sql = f'select rsc from tq where (pid is not null)'
        arsc = 10 - sum(x[0]
                        for x in dbQuery(dbpath, sql))  # available resource

        sql = f'select * from tq where (pid is null) and (retval is null) and (rsc <= {arsc}) order by pri desc, id'
        todolist = dbQuery(dbpath, sql)

        if len(todolist) > 0:  # there are works to do
            #log.info('sqlite3> {}'.format(sql))
            task = todolist[0]
            id_, pid, cwd, cmd, retval, stime, etime, pri, rsc = task

            log.info('new task detected, execute next task')
            log.info('    cwd = {}'.format(cwd))
            log.info('    cmd = {}'.format(cmd))

            log.info(f'working on task: {task}')

            # create a new worker process for this task
            worker = mp.Process(target=_tqWorker, args=(dbpath, task))
            workerpool.append(worker)
            worker.start()

        # domestic stuff
        time.sleep(1)
        workerpool = _tqWPrefresh(workerpool)


def tqStart(uid, pidfile, logfile, sqlite) -> None:
    '''
    Start the Tq Daemon for Task scheduling
    '''
    log.info('starting Tqd ...')
    try:
        daemonize(uid=uid,
                  pidfile=pidfile,
                  stdout=logfile,
                  stderr=logfile)
    except RuntimeError as e:
        print(e, file=sys.stderr)
        raise SystemExit(1)
    _tqDaemon(sqlite, pidfile)


def tqStop(pidfile: str) -> None:
    '''
    Stop the Daemon
    '''
    if os.path.exists(pidfile):
        with open(pidfile) as f:
            os.kill(int(f.read()), signal.SIGTERM)
    else:
        log.info('Tqd is NOT running')
        raise SystemExit(1)


def tqLs(pidfile: str, dbpath: str) -> None:
    '''
    List items in the tq database in pretty format. Fancy version of tqDumpDB
    '''
    if not os.path.exists(dbpath):
        log.error('Oops! tq database is not found.')
        return
    sql = 'select * from tq'
    tasks = dbQuery(dbpath, sql)
    print(yellow('⟵⟵⟵⟵☩⟶⟶⟶⟶⟶⟶⟶⟶⟶⟶⟶⟶⟶⟶⟶⟶⟶⟶⟶⟶⟶⟶⟶⟶⟶⟶⟶⟶⟶⟶⟶⟶⟶⟶⟶⟶⟶⟶⟶⟶⟶⟶⟶⟶⟶⟶⟶⟶⟶⟶⟶⟶⟶⟶⟶⟶⟶⟶⟶⟶⟶⟶⟶⟶⟶⟶⟶⟶⟶⟶⟶⟶⟶'))
    for k, task in enumerate(tasks, 1):
        id_, pid, cwd, cmd, retval, stime, etime, pri, rsc = task
        if retval is None and pid is None:  # wait
            status = white('[♨]')
        elif retval is not None and pid is None:
            status = Green('[✓]') if retval == 0 else RedB(White(f'[✗ {retval}]'))
        elif retval is None and pid is not None:
            status = Cyan(f'[⚙ {pid}]')
        else:
            status = redB('[???]')
        print(Yellow(f'{id_:>3d} |'), 'St', status,
              f'| Pri {Purple("-" if 0==pri else str(pri))}',
              f'| Rsc {Purple("-" if 10==rsc else str(rsc))}')
        if all((stime, etime)):
            print('   ', Yellow('☀'), Purple(f'{sec2hms(etime-stime)}'),
                  f'| ({time.ctime(stime)}) ➜ ({time.ctime(etime)})')
        elif stime:
            print('   ', Yellow('☀'), f'Started at ({time.ctime(stime)})',
                  Purple(f'➜ {sec2hms(time.time() - stime)}'), 'Elapsed.')
        print('   ', Yellow('⚑'), Blue(cwd))
        prog, args = cmd.split()[0], ' '.join(cmd.split()[1:])
        print('   ', Yellow('✒'), purple(prog), green(args))
        print(yellow('⟵⟵⟵⟵☩⟶⟶⟶⟶⟶⟶⟶⟶⟶⟶⟶⟶⟶⟶⟶⟶⟶⟶⟶⟶⟶⟶⟶⟶⟶⟶⟶⟶⟶⟶⟶⟶⟶⟶⟶⟶⟶⟶⟶⟶⟶⟶⟶⟶⟶⟶⟶⟶⟶⟶⟶⟶⟶⟶⟶⟶⟶⟶⟶⟶⟶⟶⟶⟶⟶⟶⟶⟶⟶⟶⟶⟶⟶'))


def tqPurge(pidfile: str, dbpath: str, logfile: str,
            really: bool = False) -> None:
    '''
    Cleanup the database, optionally remove all tq files.
    '''
    # cleanup entries in the database
    if os.path.exists(dbpath):
        sql = 'delete from tq where retval is not null'
        dbExec(dbpath, sql)
    # remove all related file if tqd is not running
    if really and not os.path.exists(pidfile):
        print(Tres(Tset('[..] Purging Tq database and log')), end='')
        if os.path.exists(logfile):
            os.unlink(logfile)
        if os.path.exists(dbpath):
            os.unlink(dbpath)
        print('[OK] Purging Tq database and log')


def tqEnqueue(dbpath: str, *,
              id_: int = 'null', pid='null', cwd: 'null', cmd: str, retval='null',
              stime: int = 'null', etime: int = 'null', pri: int = 0, rsc: int = 10) -> None:
    '''
    Enqueue a task into tq database. One must provide (cwd, cmd)

    id: must, int, task indicator
    pid: opt, None or int or bool, int for PID, None for waiting, bool True for complete
    cwd: must, str
    cmd: must, str
    retval: opt, None or int
    stime: opt, None or long, seconds since epoch, start time
    etime: opt, None or long, seconds since epoch, end time
    pri: opt, None or int, range R_int
    rsc: opt, None or int, range [0-10]
    '''
    ids = [t[0] for t in dbQuery(dbpath, 'select id from tq')]
    id_ = max(ids)+1 if len(ids) > 0 else 1
    sql = f'insert into tq' + \
           ' (id, pid, cwd, cmd, retval, stime, etime, pri, rsc)' + \
           ' values' + \
          f' ({id_}, {pid}, "{cwd}", "{cmd}", {retval}, {stime}, {etime}, {pri}, {rsc})'
    log.info(sql_pretty(sql))
    dbExec(dbpath, sql)


def tqDequeue(dbpath: str, id_: int) -> None:
    '''
    Remove a task specified by id_ from Tq database.
    Do nothing if pid is not empty for sanity.
    '''
    if os.path.exists(dbpath):
        sql = f'delete from tq where (pid is null) and (id = {id_})'
        print(sql)
        dbExec(dbpath, sql)


def tqDumpDB(dbpath: str) -> None:
    '''
    Dump database to screen. Raw version of tqLS.
    '''
    if os.path.exists(dbpath):
        sql = f'select * from tq'
        tasks = dbQuery(dbpath, sql)
        for x in tasks:
            print(x)


def tqEdit():
    '''
    FIXME: support editing Pri and Rsc attributes
    '''
    raise NotImplementedError


def tqUsage(args: List) -> None:
    '''
    Print TQ Usage
    '''
    usage = f'''
Usage: {args[0]} ACTION [COMMAND_ARGS]
       {args[0]} [P R] -- TASK

Description:
    TQ (Task Queue) is a simple Command Line Job Manager. (1) By default TQ
    execute the command lines one by one. (2) A command line with high
    Priority will be processed earlier. (3) When the estimated occupancy
    parameter is specified, TQ will run the commands in parallel if possible.

Available Actions:
    start      start TQ's daemon
    stop       stop TQ's daemon
    log        dump log to screen
    ls         fancy print of task queue
    db         print database content to screen
    rm <ID>    remove task with specified id, see ID with tq ls
    clean      remove finished tasks from queue
    purge      remove log file and sqlite3 db file

Apending Task:
    -- TASK        append TASK to the queue
    P R -- TASK    append TASK with priority P and estimated occupancy R
                   int P default  0 range [INT_MIN, INT_MAX], large=important
                   int R detault 10 range [1,       10],      large=consuming

Examples:
    1. Serial: the two given tasks should be executed one by one
         tq -- sleep 100
         tq -- sleep 100
    2. Parallel: each task occupies 40% of resource.
       In this example two tasks will be active at the same time.
         tq 0 4 -- sleep 100
         tq 0 4 -- sleep 100
         tq 0 4 -- sleep 100
    3. Priority: break the FIFO order of tasks. 1 > default Priority.
         tq 1 10 -- sleep 100
    4. Special Case: run the given task right away ignoring Pri and Rsc
         tq 1 0 -- sleep 100
        '''
    print(usage)


def tqMain():
    '''
    tq's main func. It parses command line argument and invoke specified
    functions of tq.

    FIXME: use a better argument parser e.g. argparse
    '''
    import logging as log
    log.basicConfig(
        format='%(levelno)s %(asctime)s %(process)d %(filename)s:%(lineno)d]'
        + ' %(message)s',
        level=log.DEBUG
    )

    # get some info and paths
    uid, cwd = os.getuid(), os.getcwd()
    sqlite  = os.path.expanduser(f'~/.tqd_{uid}.db')
    logfile = os.path.expanduser(f'~/.tqd_{uid}.log')
    pidfile = os.path.expanduser(f'~/.tqd_{uid}.pid')

    if len(sys.argv) < 2:
        tqUsage(sys.argv)
        if os.path.exists(pidfile):
            print('TQ daemon is \x1b[32;1mrunning\x1b[m.')
        else:
            print('TQ daemon is \x1b[31;1mnot running\x1b[m.')
        raise SystemExit(1)

    if sys.argv[1] == 'start':
        tqStart(uid, pidfile, logfile, sqlite)

    elif sys.argv[1] == 'stop':
        tqStop(pidfile)

    elif sys.argv[1] == 'log':
        if os.path.exists(logfile):
            with open(logfile, 'r') as log:
                print(log.read())

    elif sys.argv[1] == 'clean':
        tqPurge(pidfile, sqlite, logfile, False)

    elif sys.argv[1] == 'purge':
        tqPurge(pidfile, sqlite, logfile, True)

    elif sys.argv[1] == 'ls':
        tqLs(pidfile, sqlite)

    elif sys.argv[1] == 'rm':
        tqDequeue(sqlite, int(sys.argv[2]))

    elif sys.argv[1] == 'db':
        tqDumpDB(sqlite)

    elif len(sys.argv) >= 5 and sys.argv[3] == '--':
        # Special and powerful mode: specify priority and resource requirement
        pri, rsc = int(sys.argv[1]), int(sys.argv[2])
        cwd = os.getcwd()
        cmd = ' '.join(sys.argv[4:])

        if len(cmd) == 0:
            log.error('Task missing')
            raise SystemExit(1)

        if not os.path.exists(pidfile):
            log.error('Tqd is not running, starting tqd ...')
        else:
            tqEnqueue(sqlite, cwd=cwd, cmd=cmd, pri=pri, rsc=rsc)

    elif sys.argv[1] == '--':
        cwd = os.getcwd()
        cmd = ' '.join(sys.argv[2:])

        if len(cmd) == 0:
            log.error('Task missing')
            raise SystemExit(1)

        if not os.path.exists(pidfile):
            log.error('Tqd is not running, starting tqd ...')
        else:
            tqEnqueue(sqlite, cwd=cwd, cmd=cmd)

    else:
        log.error('Unknown command {!r}'.format(sys.argv[1]))
        raise SystemExit(1)


main = tqMain


if __name__ == '__main__':
    tqMain()

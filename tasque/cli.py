'''
Copyright (C) 2020-2021 Mo Zhou <lumin@debian.org>
License: MIT/Expat
'''

import os
import sys
import re
from . import defs
from .client import tqClient
import rich
import time
import rich.markdown
c = rich.get_console()

def usage():
    c.print('[bold]TASQUE :: Zero-Config Single-Node Workload Manager[/bold]')
    USAGE = f'''
Usage: tq <subcommand> \[action] \[arguments]
       tq \[specifiers] -- <command-line-to-submit>
Subcommands:
       d|daemon        Manage the daemon/scheduler (e.g. start/stop)
       t|task          Manage tasks (e.g. add/delete/clear)
       a|annotate      Manage task annotations (e.g. add/delete)
       l|ls|list       List task queue
       log             Dump log
       dump            Dump database
    '''
    c.print(USAGE)
    client = tqClient()
    c.print('TASQUE daemon is running?', client.isdaemonalive())

def shorthand_task_add(argv):
    '''
    special shorthand for task_add
    '''
    client = tqClient()
    uid = os.getuid()
    cwd = os.getcwd()
    cmd = ' '.join(argv[argv.index('--')+1:])
    client.enqueue(cwd=cwd, cmd=cmd)

def task(argv):
    client = tqClient()
    def task_clear(argv):
        client.clear()
    if len(argv) == 0:
        print('usage')
        exit(0)
    if argv[0] == 'clear':
        task_clear(argv[1:])

def annotate(argv):
    client = tqClient()
    def annotate_add(argv):
        client.annotate(int(argv[0]), ' '.join(argv[1:]))
    def annotate_del(argv):
        client.delannotation(int(argv[0]))
    def annotate_dump(argv):
        client.dumpannotation()
    if len(argv) == 0:
        c.print('TODO: annotate usage')
    elif any(x == argv[0] for x in ('a', 'add')):
        annotate_add(argv[1:])
    elif any(x == argv[0] for x in ('d', 'del', 'delete', 'r', 'rm', 'remove')):
        annotate_remove(argv[1:])
    elif argv[0] == 'dump':
        annotate_dump(argv[1:])
    else:
        raise ValueError(argv)


def ls(argv):
    client = tqClient()
    client.tqls()

def dump(argv):
    client = tqClient()
    client.dump()

def log(argv):
    with open(defs.TASQUE_LOG) as f:
        log = f.read()
    c.print(log)

def daemon(argv):
    client = tqClient()
    if not argv:
        c.print('''\
Usage: tq daemon <action> \[arguments]
Actions:
       start         Start daemon
       stop          Stop daemon
       restart       Restart daemon
                ''')
        c.log('TASQUE daemon is running?', client.isdaemonalive())
    elif argv[0] == 'start':
        daemon_start(argv[1:])
    elif argv[0] == 'stop':
        daemon_stop(argv[1:])
    elif argv[0] == 'restart':
        daemon_stop(argv[1:])
        time.sleep(1)
        daemon_start(argv[1:])
    else:
        raise ValueError(argv)

def daemon_start(argv):
    client = tqClient()
    client.start()

def daemon_stop(argv):
    client = tqClient()
    client.stop()

def main(argv = sys.argv[1:]):
    '''
    entrance
    '''
    # dispatch
    if len(argv) == 0:
        usage()
    elif any(argv[0] == x for x in ('-h', '--help')):
        usage()
    elif '--' in argv:
        shorthand_task_add(argv)
    elif any(argv[0] == x for x in ('l', 'ls', 'list')):
        ls(argv[1:])
    elif any(argv[0] == x for x in ('d', 'daemon')):
        daemon(argv[1:])
    elif any(argv[0] == x for x in ('n', 'note', 'a', 'ann', 'annotate')):
        annotate(argv[1:])
    elif any(argv[0] == x for x in ('t', 'task')):
        task(argv[1:])
    elif 'log' == argv[0]:
        log(argv[1:])
    elif 'dump' == argv[0]:
        dump(argv[1:])
    else:
        raise ValueError('unable to understand the given arguments')

#def main():
#    # [[ branchings
#
#    # -- many arguments -- add a task
#    if '--' in sys.argv:
#        # Special and powerful mode: specify priority and resource requirement
#        cmd, cwd = ' '.join(sys.argv[sys.argv.index('--'):][1:]), os.getcwd()
#        if len(cmd) == 0:
#            log.error('Task is Missing!')
#            raise SystemExit(1)
#
#        # parse P and R from arguments (this part is flexible)
#        prspec = ''.join(sys.argv[1:sys.argv.index('--')])
#        pri, rsc = 0, 10  # default numbers
#        if re.match('.*[pP].*', prspec):
#            pri = int(re.findall('[pP]([+-]*\d+)', prspec)[0])
#        if re.match('.*[rR].*', prspec):
#            rsc = int(re.findall('[rR]([+-]*\d+)', prspec)[0])
#
#        if not os.path.exists(sqlite):
#            log.error('TQD SQLite3 databse does not exist. Please start TQD.')
#        else:
#            tqEnqueue(pidfile, sqlite, cwd=cwd, cmd=cmd, pri=pri, rsc=rsc)
#
#    # -- 0 arg actions
#    elif len(sys.argv) == 1 or sys.argv[1] == 'ls':
#        tqLs(pidfile, sqlite)
#
#    elif sys.argv[1] in ('-h', '--help'):
#        tqUsage(sys.argv)
#        if os.path.exists(pidfile):
#            print('TQ daemon is \x1b[32;1mrunning\x1b[m.')
#        else:
#            print('TQ daemon is \x1b[31;1mnot running\x1b[m.')
#        raise SystemExit(1)
#
#    elif sys.argv[1] == 'start':
#        tqStart(pidfile, sqlite, logfile)
#
#    elif sys.argv[1] == 'stop':
#        tqStop(pidfile, sqlite)
#
#    elif sys.argv[1] == 'log':
#        if os.path.exists(logfile):
#            with open(logfile, 'r') as log:
#                print(log.read())
#
#    elif sys.argv[1] == '_check':
#        print('check TQ daemon ...', _tqCheckAlive(pidfile))
#        print('check Workers   ...', _tqCheckWorkerAlive(sqlite))
#
#    elif sys.argv[1] in ('clean', 'purge'):
#        tqPurge(pidfile, sqlite, logfile, False if sys.argv[1] == 'clean' else True)
#
#    elif sys.argv[1] == 'db':
#        tqDumpDB(pidfile, sqlite)
#
#    # -- 1 arg actions
#    elif sys.argv[1] == 'rm':
#        tqDequeue(pidfile, sqlite, int(sys.argv[2]))
#
#    elif sys.argv[1] == 'rmn':
#        tqDelNote(pidfile, sqlite, int(sys.argv[2]))
#
#    elif sys.argv[1] == 'kill':
#        tqKill(pidfile, sqlite, int(sys.argv[2]))
#
#    # -- 1+ arg actions
#    elif sys.argv[1] in ('note', 'n'):
#        if len(sys.argv) == 2:
#            tqDumpNotes(pidfile, sqlite)
#        else:
#            tqNote(pidfile, sqlite, int(sys.argv[2]), ' '.join(sys.argv[3:]))
#
#    # -- 2 arg actions
#    elif len(sys.argv) == 4 and sys.argv[1] in ('pri', 'p'):
#        tqEdit(pidfile, sqlite, int(sys.argv[2]), pri=int(sys.argv[3]))
#
#    elif len(sys.argv) == 4 and sys.argv[1] in ('rsc', 'r'):
#        tqEdit(pidfile, sqlite, int(sys.argv[2]), rsc=int(sys.argv[3]))
#
#    # -- what???
#    else:
#        log.error('Unknown command {!r}'.format(sys.argv[1:]))
#        raise SystemExit(1)
#
#

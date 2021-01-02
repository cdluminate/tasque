import os
import sys
import re
from .client import tqClient
import rich
import rich.markdown
c = rich.get_console()

def usage():
    USAGE = f'''
    TASQUE -- Zero-Config Single-Node Workload Manager

    Usage: tq
    '''
    client = tqClient()
    md = rich.markdown.Markdown(USAGE)
    c.print(md)
    c.print('TASQUE daemon running?', client.isdaemonalive())

def task(argv):
    raise NotImplementedError()

def shorthand_task_add(argv):
    '''
    special shorthand for task_add
    '''
    client = tqClient()
    uid = os.getuid()
    cwd = os.getcwd()
    cmd = ' '.join(argv[argv.index('--')+1:])
    client.enqueue(cwd=cwd, cmd=cmd)

def note(argv):
    raise NotImplementedError()


def dump(argv):
    client = tqClient()
    client.dump()

def main(argv):
    '''
    entrance
    '''
    # dispatch
    if len(argv) == 0:
        usage()
    elif '--' in argv:
        shorthand_task_add(argv)
    elif any(argv[0] == x for x in ('n', 'note')):
        note(argv[1:])
    elif 'dump' == argv[0]:
        dump(argv[1:])
    else:
        raise ValueError('unable to understand the given arguments')

#def main():
#    # get some info and paths
#    uid, cwd = os.getuid(), os.getcwd()
#
#    # check (deal with accidents e.g. powerloss)
#    _tqCheckAlive(pidfile)
#    _tqCheckWorkerAlive(sqlite)
#
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

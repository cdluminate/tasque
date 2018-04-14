TQ -- Simple Command Line Job Manager
===

TQ (Task Queue) is a simple Command Line Job Manager. (1) By default TQ
execute the command lines one by one. (2) A command line with high
Priority will be processed earlier. (3) When the estimated occupancy
parameter is specified, TQ will run the commands in parallel if possible.

This tool is available via PIP: `pip3 install tq1`

## Usage

```
Usage: {args[0]} ACTION [COMMAND_ARGS]
       {args[0]} [P R] -- TASK

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
```

## Examples

```
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
```

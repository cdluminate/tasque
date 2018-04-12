Tq -- Command Line Scheduler
===

```
Usage: tq {COMMAND | -- TASK}

          -> show usage, and tqd status
  start   -> start daemon
  stop    -> stop daemon
  log     -> dump daemon log to screen
  ls      -> fancy print of task queue
  db      -> print database content to screen
  rm ID   -> remove task with specified id, see ID with tq ls
  clean   -> remove log file, clean task queue
  purge   -> remove log file and sqlite3 db file
  -- TASK -> assign TASK (a command line)
  P R -- TASK -> create TASK with priority P and resource req R
           int P range [INT_MIN, INT_MAX], higher = more important
               P is used to tell important tasks
           int R range [0, 10], estimated resource occupation
               R is used for parallel execution

  Tq functionality and feature:
     1. run command one by one in serial
     2. run command in parallel by setting resource parameter
     3. task priority is supported

  Example:
     1. run two tasks in serial
        tq -- sleep 10
        tq -- sleep 10
     2. run three tasks in parallel, each of then takes 40% of resource
        tq 0 4 -- sleep 10
        tq 0 4 -- sleep 10
        tq 0 4 -- sleep 10
     3. add a high priority task, which should run ASAP
        tq 1 10 -- sleep 10
     4. add a high priority task and run it right away
        tq 1 0 -- sleep 10
     5. add a task with even higher priority
        tq 999 10 -- sleep 10

tq version: 0.2
```

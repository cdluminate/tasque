Tasque -- Zero-Config Single-Node Workload Manager
===

[![Latest Version](https://pypip.in/version/tq1/badge.svg)](https://pypi.python.org/pypi/tq1/)

<!-- ![tqls1](tqls1.png) -->

Tasque (Task Queue) is a simple workload manager for single-node usage that can
be used out-of-box. It is resource-aware (e.g. CPU, Memory, GPU, Video Memory),
and can automatically schedule the submitted jobs in a sensible way. It is much
more light-weight compared to cluster workload managers such as Slurm and PBS,
while being much smarter than a casually rushed script using tmux, screen, or
alike. Tasque is written by the author for scheduling batches of machine
learning experiments (e.g. caffe, pytorch, tensorflow).

Tasque has the following characteristics:
1. Submitted jobs (command lines) will be automatically scheduled to run when
there is enough resource to do so.
2. The daemon is resource-aware, namely it is able to plan the usage of either
CPU, Memory, GPU, or Video memory. When resource is aboundant, tasks may be
scheduled to run in parallel.
3. The default behavior is to execute the given commands in the FTFO order.
4. Tasks with high priority values will be scheduled to run prior to the rest.
5. The queue is stored in an SQLite3 database, and will not be lost in case of
powerloss.
6. Users can assign text annotations with the tasks in database.
7. Requires no configuration and can be used out-of-box.

## Example

<!--
TQ can be used to deal with some commands in an async manner. e.g.
```
$ tq -- git push  # Doesn't block. Have it done in async.
$ vim mycode.py
```

TQ can be used to manage a series of computation experiments, such as
deep learning experiments, e.g.
```
$ tq r5 -- caffe train -solver net1forfun.prototxt
$ tq r5 -- caffe train -solver net2forfun.prototxt
$ tq 1 5 -- python3 train.py --lr 1e-2
$ tq 1 5 -- python3 train.py --lr 1e-3
$ tq 1 5 -- python3 train.py --lr 1e-4
$ tq 1 5 -- python3 train.py --lr 1e-5
$ tq p10 -- python3 important_train.py
```
One can just put many computation tasks in the queue, and TQ will smartly
schedule these experiments according to the given priority and resource
occupancy parameters.
-->

## Installation

This tools is available on Pypi. Just issue the following command:
```
pip3 install tq1
```
Note that some new language features may be used in the code.
There is no plan to support older versions of python3.
Hence `python3 >= 3.8` is recommended.

In case you want to install it from source:
```
python3 setup.py install
```

## Usage

<!--
```
Usage: tq ACTION [COMMAND_ARGS]
       tq [P R] -- TASK

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
    p<P> -- TASK   append TASK with priority P to the queue
    r<R> -- TASK   append TASK with resource occupancy R to the queue
    P R -- TASK    append TASK with priority P and estimated occupancy R
                   int P default  0 range [INT_MIN, INT_MAX], large=important
                   int R detault 10 range [1,       10],      large=consuming
```
-->

## Copyright and License

```
Copyright (C) 2016-2021 Mo Zhou <lumin@debian.org>
Released under the MIT/Expat License.
```

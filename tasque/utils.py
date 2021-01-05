import math
import os


def sec2hms(s: float) -> str:
    '''
    Convert X seconds into A hour B minute C seconds as a string.
    '''
    sec = math.fmod(s, 60.0)
    mm  = (int(s) // 60) % 60
    hh  = (int(s) // 60) // 60
    return f'{hh}h{mm}m{sec:.3f}s'


def checkpid(pid: int) -> bool:
    '''
    Check if a given process specified by its PID is alive.
    '''
    try:
        os.kill(pid, 0)  # does nothing
    except OSError:
        return False
    else:
        return True


def null2none(T: tuple) -> tuple:
    '''
    We unify null values into None in the python domain.
    '''
    return tuple(x if x != 'null' else None for x in T)


def none2null(T: tuple) -> tuple:
    '''
    We unify none values into null in the SQL domain.
    '''
    return tuple(x if x is not None else 'null' for x in T)

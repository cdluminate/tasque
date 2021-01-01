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

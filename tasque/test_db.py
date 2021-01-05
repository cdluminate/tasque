'''
Copyright (C) 2016-2021 Mo Zhou <lumin@debian.org>
License: MIT/Expat
'''

import rich
from rich.traceback import install
install()
c = rich.get_console()
import pytest
import os
from tasque.db import *
from tasque.defs import *

def test_db(tmp_path):
    tq = tqDB(os.path.join(tmp_path, 'test.db'))

    t = Task._make(['1', '1', 'test', 'test', '0', '0', '0', '0', '0'])
    tq += t
    c.print(tq['tq'])
    assert(len(tq['tq']) == 1)

    n = Note._make(['1', '1', 'test'])
    tq += n
    c.print(tq['notes'])
    assert(len(tq['tq']) == 1)

    del tq

if __name__ == '__main__':
    test_db('./test.db')

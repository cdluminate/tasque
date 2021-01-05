'''
Copyright (C) 2016-2021 Mo Zhou <lumin@debian.org>
License: MIT/Expat
'''

from tasque.resources import *

def test_virtual_resource():
    R = VirtualResource()
    R.canalloc(1.0)
    R.waitfor(1.0)
    R.request(1.0)()

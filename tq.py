#!/usr/bin/env python3
'''
Copyright (C) 2020-2021 Mo Zhou <lumin@debian.org>
License: MIT/Expat
'''
import rich.traceback
import tasque
import sys
rich.traceback.install()
tasque.cli.main(sys.argv[1:])

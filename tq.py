#!/usr/bin/env python3
import rich.traceback
import tasque
import sys
rich.traceback.install()
tasque.cli.main(sys.argv[1:])

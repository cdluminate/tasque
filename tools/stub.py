import torch as th
import time
import sys
x = th.rand(1000, 1000).cuda()
print(x)
time.sleep(int(sys.argv[1]))

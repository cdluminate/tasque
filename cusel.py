#!/usr/bin/env python3
'''
Blocking CUDA Device Selector

Usage: cusel [-m mem]

Without cusel:

    $ gpustat  # (then manually decide the card to use)
    $ CUDA_VISISBLE_DEVICES=5 python3 train.py

With cusel:

    1. wait for a card with 11000MB idle memory and automatically select it
    $ CUDA_VISIBLE_DEVICES=$(cusel) python3 train.py

    2. wait for a card with 4000MB idle memory and automatically select it
    $ CUDA_VISIBLE_DEVICES=$(cusel -m4000) python3 train.py

Hints:

    1. It is suggested to enable nvidia-persistenced to speed up selection.

Copyright (C) 2020-2021 Mo Zhou <lumin@debian.org>
License: MIT/Expat
'''
import sys
import argparse
import tasque

if __name__ == '__main__':

    ag = argparse.ArgumentParser()
    ag.add_argument('-m', type=int, default=11000, help='how much memory (MB)')
    ag.add_argument('--exclude', type=int, default=[], nargs='+',
                    help='exclude gpu indices')
    ag = ag.parse_args()

    cusel = tasque.cuda_selector.CudaSelector()
    print(cusel.waitforCard(ag.m, ag.exclude))

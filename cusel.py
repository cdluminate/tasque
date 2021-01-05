#!/usr/bin/env python3
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

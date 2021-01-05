from typing import List, Union
from . import utils
import csv
import time
from collections import namedtuple
import subprocess as sp

Card = namedtuple('Card', 'index, memory_total, memory_used, memory_free')

class CudaSelector:
    '''
    Select CUDA device
    '''
    lock: str = '/tmp/cusel.lock'
    interval: int = 15
    avail_threshold: float = 0.97

    def getCards(self) -> List[Card]:
        '''
        Get a list of GPU status tuples.
        '''
        cmd = ['nvidia-smi', '--format=csv,noheader,nounits',
            '--query-gpu=index,memory.total,memory.used,memory.free']
        stat = sp.Popen(cmd, stdout=sp.PIPE, stderr=sp.PIPE
                        ).communicate()[0].decode().strip()
        cards = [Card._make(map(int, line))
                 for line in csv.reader(stat.split('\n'))]
        return cards

    def availCards(self) -> List[Card]:
        '''
        Get a list of AVAILABLE cards.
        '''
        cards = self.getCards()
        return [card for card in cards if
                card.memory_free >= card.memory_total * self.avail_threshold]

    def selectCard(self, mem: int, exclude: list = []) -> Union[int, None]:
        '''
        Select a card. This function does not block.
        '''
        cards = self.getCards()
        if exclude:
            cards = [card for card in cards if card.index not in exclude]
        clist = sorted(cards, key=lambda x: x.memory_used)
        for card in clist:
            if card.memory_free >= mem:
                return card.index
        return None

    def waitforCard(self, mem: int, exclude: list = []) -> int:
        '''
        Blocking version of self.selectCard
        '''
        with utils.openlock(self.lock, 'w+'):
            while True:
                sel = self.selectCard(mem, exclude)
                if sel is None:
                    time.sleep(self.interval)
                else:
                    return(sel)
                    break

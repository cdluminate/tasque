import math
import time
RESOURCE_DEFAULT = 'void'
RESOURCE_TYPES = (RESOURCE_DEFAULT, 'virtual', 'cpu', 'memory', 'gpu', 'vmem')

class AbstractResource:
    def __init__(self):
        '''
        Attributes:
            self.book: tracking resource assignment
        '''
        self.book = dict()
        self.acquire = dict()
        self.release = dict()
    def idle(self):
        '''
        Wait for some time.
        '''
        time.sleep(2)
    def avail(self) -> float:
        '''
        Total amount of available specific <kind> of resource.
        '''
        raise NotImplementedError('how to determine available resource?')
    def canalloc(self, rsc: float) -> bool:
        '''
        check whether <rsc> of resource can be allocated. does not block.
        '''
        raise NotImplementedError(f'can I allocate <{rsc}>?')
    def waitfor(self, rsc: float) -> None:
        '''
        wait until <rsc> of resource can be allocated. does indeed block.
        '''
        raise NotImplementedError(f'is there <{rsc}>?')
    def request(self, pid: int, rsc: float) -> (callable, callable):
        '''
        generate callback functions for allocating the requested resource
        '''
        def acquire():
            raise NotImplementedError('how to allocate resource?')
        def release():
            raise NotImplementedError('how to release resource?')
        return (acquire, release)

class VoidResource(AbstractResource):
    '''
    Void resource / sequential execution. (default)
    '''
    def avail(self) -> float:
        return math.nan
    def canalloc(self, rsc: float) -> bool:
        return (0 == len(self.book))
    def waitfor(self, rsc: float) -> None:
        return None
    def request(self, pid: int, rsc: float) -> None:
        self.acquire[pid] = lambda: self.book.__setitem__(pid, rsc)
        self.release[pid] = lambda: self.book.pop(pid)

class VirtualResource(AbstractResource):
    '''
    Virtual resource. And imagined resource with upper bound as <1.0>.
    Can be used to arrange some taks to run in parallel.
    '''
    def avail(self) -> float:
        return 1.0
    def canalloc(self, rsc: float) -> bool:
        return (rsc <= sum(self.book.values()))
    def waitfor(self, rsc: float) -> None:
        while not self.canalloc(rsc):
            self.idle()
    def request(self, pid: int, rsc: float) -> None:
        self.acquire[pid] = lambda: self.book.__setitem__(pid, rsc)
        self.release[pid] = lambda: self.book.pop(pid)


class GpuResource(AbstractResource):
    '''
    GPU (CUDA) Resource. Allocate cards (as a whole) for the requestors.
    We only consider a card "available" when >=97% video memory is free.
    '''
    def __init__(self):
        super(GpuResource, self).__init__()
        raise NotImplementedError()

class VmemResource(AbstractResource):
    '''
    CUDA Video Memory Resource. Allocate video memories for the requestors.
    In this way we can allocate GPU resources in a fine-grained manner and
    smartly jam various tasks on the GPUs as appropriate. Unlike
    coarse-grained GPU allocation such as Slurm(CUDA) which allocate each
    card as a whole to the requestors.
    '''
    def __init__(self):
        super(VmemResource, self).__init__()
        raise NotImplementedError()

class CpuResource(AbstractResource):
    def __init__(self):
        super(CpuResource, self).__init__()
        raise NotImplementedError()

class MemoryResource(AbstractResource):
    def __init__(self):
        super(MemoryResource, self).__init__()
        raise NotImplementedError()

def create(name: str):
    '''
    factory function
    '''
    mapping = {
            RESOURCE_DEFAULT: VoidResource,
            'virtual': VirtualResource,
            'cpu': CpuResource,
            'memory': MemoryResource,
            'gpu': GpuResource,
            'vmem': VmemResource,
            }
    return mapping[name]()

import math
RESOURCE_DEFAULT = 'virtual'
RESOURCE_TYPES = (RESOURCE_DEFAULT, 'cpu', 'memory', 'gpu', 'vmem')

class AbstractResource:
    def __init__(self):
        '''
        Attributes:
            self.book: tracking resource assignment
        '''
        self.book = dict()
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

class VirtualResource(AbstractResource):
    '''
    Virtual resource. (default)
    '''
    def avail(self) -> float:
        return math.nan
    def canalloc(self, rsc: float) -> bool:
        return not self.book.keys()
    def waitfor(self, rsc: float) -> None:
        return None
    def request(self, pid: int, rsc: float) -> (callable, callable):
        def acquire():
            self.book[pid] = rsc
        def release():
            self.book.pop(pid)
        return (acquire, release)

def create(name: str):
    '''
    factory function
    '''
    mapping = {
            RESOURCE_DEFAULT: VirtualResource,
            'cpu': AbstractResource,
            'memory': AbstractResource,
            'gpu': AbstractResource,
            'vmem': AbstractResource,
            }
    return self.mapping[name]()

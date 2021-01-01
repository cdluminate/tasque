import math
RESOURCE_DEFAULT = 'virtual'
RESOURCE_TYPES = (RESOURCE_DEFAULT, 'cpu', 'memory', 'gpu', 'vmem')

class AbstractResource:
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
    def request(self, rsc: float) -> callable:
        '''
        generate a callback function for allocating the requested resource
        '''
        def alloc():
            raise NotImplementedError('how to allocate resource?')
        return alloc

class VirtualResource(AbstractResource):
    '''
    Virtual resource. (default)
    '''
    def avail(self):
        return math.inf
    def canalloc(self, rsc: float) -> bool:
        return rsc <= self.avail()
    def waitfor(self, rsc: float) -> None:
        return None
    def request(self, rsc: float) -> callable:
        def alloc():
            pass
        return alloc

class Resource:
    '''
    factory class
    '''
    mapping = {
            RESOURCE_DEFAULT: VirtualResource,
            'cpu': AbstractResource,
            'memory': AbstractResource,
            'gpu': AbstractResource,
            'vmem': AbstractResource,
            }
    def __init__(self, name: str = None):
        '''
        create a factory
        '''
        self.name = name
    def create(self, name: str = None):
        if name is not None:
            return self.mapping[name]()
        elif self.name is not None:
            return self.mapping[self.name]()
        else:
            raise ValueError('create what?')


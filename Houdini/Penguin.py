from Houdini.Spheniscidae import Spheniscidae


class Penguin(Spheniscidae):

    __slots__ = ['x', 'y', 'room', 'waddle', 'table', 'data']

    def __init__(self, *args):
        super().__init__(*args)

        self.x, self.y = (0, 0)
        self.room = None
        self.waddle = None
        self.table = None

        self.data = None

        self.logger.debug('New penguin created')

    async def add_inventory(self, item):
        pass

    async def add_igloo(self, igloo):
        pass

    async def add_furniture(self, furniture):
        pass

    async def add_flooring(self, flooring):
        pass

    async def add_buddy(self, buddy):
        pass

    async def add_inbox(self, postcard):
        pass

    def __repr__(self):
        if self.data is not None:
            return '<Penguin ID=\'{}\' Username=\'{}\'>'.format(self.data.ID, self.data.Username)
        return super().__repr__()

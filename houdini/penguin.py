from houdini.spheniscidae import Spheniscidae

from houdini.data.permission import PermissionCrumbsCollection

class Penguin(Spheniscidae):

    __slots__ = ['x', 'y', 'frame','room', 'waddle', 'table', 'data',
                 'login_key', 'member', 'membership_days', 'avatar',
                 'walking_puffle', 'permissions']

    def __init__(self, *args):
        super().__init__(*args)

        self.x, self.y = (0, 0)
        self.frame = 1
        self.room = None
        self.waddle = None
        self.table = None

        self.data = None
        self.login_key = None

        self.member = None
        self.membership_days = 0

        self.avatar = None

        self.walking_puffle = None

        self.permissions = None

        self.logger.debug('New penguin created')

    @property
    def party_state(self):
        return str()

    @property
    def puffle_state(self):
        return str()

    @property
    def penguin_state(self):
        return str()

    @property
    def nickname(self):
        return self.data.nickname if self.data.approval else "P" + self.data.id

    async def load(self):
        if self.data:
            self.permissions = await PermissionCrumbsCollection.get_collection(self.data.id)

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
            return '<Penguin ID=\'{}\' Username=\'{}\'>'.format(self.data.id, self.data.username)
        return super().__repr__()

import time

from houdini.spheniscidae import Spheniscidae


class Penguin(Spheniscidae):

    __slots__ = ['x', 'y', 'frame', 'room', 'waddle', 'table', 'data',
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
        return self.data.safe_nickname(self.server.server_config['Language'])

    async def join_room(self, room):
        await room.add_penguin(self)

    async def add_inventory(self, item, notify=True):
        if item.id in self.data.inventory:
            return False

        await self.data.inventory.set(item.id)
        await self.data.update(coins=self.data.coins - item.cost).apply()

        if notify:
            await self.send_xt('ai', item.id, self.data.coins)

        self.logger.info('{} added \'{}\' to their clothing inventory'.format(
            self.data.username, item.name))

        return True

    async def add_igloo(self, igloo, notify=True):
        if igloo.id in self.data.igloos:
            return False

        await self.data.igloos.set(igloo.id)
        await self.data.update(coins=self.data.coins - igloo.cost).apply()

        if notify:
            await self.send_xt('au', igloo.id, self.data.coins)

        self.logger.info('{} added \'{}\' to their igloos inventory'.format(
            self.data.username, igloo.name))

        return True

    async def add_furniture(self, furniture, quantity=1, notify=True):
        if furniture.id in self.data.furniture:
            penguin_furniture = self.data.furniture[furniture.id]
            if penguin_furniture.quantity >= furniture.max_quantity:
                return False

            await penguin_furniture.update(
                quantity=penguin_furniture.quantity + quantity).apply()
        else:
            await self.data.furniture.set(furniture.id)

        await self.data.update(coins=self.data.coins - furniture.cost).apply()

        if notify:
            await self.send_xt('af', furniture.id, self.data.coins)

        self.logger.info('{} added \'{}\' to their furniture inventory'.format(
            self.data.username, furniture.name))

        return True

    async def add_card(self, card, quantity=1):
        if card.id in self.data.cards:
            penguin_card = self.data.cards[card.id]

            await penguin_card.update(
                quantity=penguin_card.quantity + quantity).apply()
        else:
            await self.data.cards.set(card.id)

        self.logger.info('{} added \'{}\' to their ninja deck'.format(
            self.data.username, card.name))

        return True

    async def add_flooring(self, flooring, notify=True):
        if flooring.id in self.data.flooring:
            return False

        await self.data.flooring.set(flooring.id)
        await self.data.update(coins=self.data.coins - flooring.cost).apply()

        if notify:
            await self.send_xt('ag', flooring.id, self.data.coins)

        self.logger.info('{} added \'{}\' to their flooring inventory'.format(
            self.data.username, flooring.name))

        return True

    async def add_location(self, location, notify=True):
        if location.id in self.data.locations:
            return False

        await self.data.locations.set(location.id)
        await self.data.update(coins=self.data.coins - location.cost).apply()

        if notify:
            await self.send_xt('aloc', location.id, self.data.coins)

        self.logger.info('{} added \'{}\' to their location inventory'.format(
            self.data.username, location.name))

        return True

    async def add_inbox(self, postcard, sender_name="sys", sender_id=None, details=""):
        penguin_postcard = await self.data.postcards.set(penguin_id=self.data.id,
                                                         sender_id=sender_id, postcard_id=postcard.id,
                                                         details=details)

        await self.send_xt('mr', sender_name, 0, postcard.id, details, int(time.time()), penguin_postcard.id)

    async def add_permission(self, permission):
        if permission not in self.data.permissions:
            await self.data.permissions.set(permission)

        self.logger.info('{} was assigned permission \'{}\''.format(
            self.data.username, permission))

        return True

    def _client_connected(self):
        super()._client_connected()

    def __repr__(self):
        if self.data is not None:
            return '<Penguin ID=\'{}\' Username=\'{}\'>'.format(self.data.id, self.data.username)
        return super().__repr__()

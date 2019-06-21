import time

from houdini.spheniscidae import Spheniscidae


class Penguin(Spheniscidae):

    __slots__ = ['x', 'y', 'frame', 'room', 'waddle', 'table', 'data',
                 'login_key', 'member', 'membership_days', 'avatar',
                 'walking_puffle', 'permissions', 'age']

    def __init__(self, *args):
        super().__init__(*args)

        self.x, self.y = (0, 0)
        self.frame = 1
        self.room = None
        self.waddle = None
        self.table = None

        self.data = None
        self.login_key = None

        self.member = 1
        self.membership_days = 1

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
    def string(self):
        return self.server.penguin_string_compiler.compile(self)

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

    async def add_puffle_item(self, care_item, quantity=1, notify=True):
        if care_item.id in self.data.puffle_items:
            penguin_care_item = self.data.puffle_items[care_item.id]
            if penguin_care_item.quantity >= 100:
                return False

            await penguin_care_item.update(
                quantity=penguin_care_item.quantity + quantity).apply()
        else:
            await self.data.puffle_items.set(care_item.id)

        await self.data.update(coins=self.data.coins - care_item.cost).apply()

        if notify:
            await self.send_xt('papi', self.data.coins, care_item.id, quantity)

        self.logger.info('{} added \'{}\' to their puffle care inventory'.format(
            self.data.username, care_item.name))

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

    async def set_color(self, item):
        await self.data.update(color=item.id).apply()
        await self.room.send_xt('upc', self.data.id, item.id)
        self.logger.info('{} updated their color to \'{}\' '.format(
            self.data.username, item.name))

    async def set_head(self, item):
        item_id = None if item is None else item.id
        await self.data.update(head=item_id).apply()
        await self.room.send_xt('uph', self.data.id, item_id or 0)

        self.logger.info('{} updated their head item to \'{}\' '.format(
            self.data.username, item.name) if item else
                         '{} removed their head item'.format(
                             self.data.username))

    async def set_face(self, item):
        item_id = None if item is None else item.id
        await self.data.update(face=item_id).apply()
        await self.room.send_xt('upf', self.data.id, item_id or 0)

        self.logger.info('{} updated their face item to \'{}\' '.format(
            self.data.username, item.name) if item else
                         '{} removed their face item'.format(
                             self.data.username))

    async def set_neck(self, item):
        item_id = None if item is None else item.id
        await self.data.update(neck=item_id).apply()
        await self.room.send_xt('upn', self.data.id, item_id or 0)

        self.logger.info('{} updated their neck item to \'{}\' '.format(
            self.data.username, item.name) if item else
                         '{} removed their neck item'.format(
                             self.data.username))

    async def set_body(self, item):
        item_id = None if item is None else item.id
        await self.data.update(body=item_id).apply()
        await self.room.send_xt('upb', self.data.id, item_id or 0)

        self.logger.info('{} updated their body item to \'{}\' '.format(
            self.data.username, item.name) if item else
                         '{} removed their body item'.format(
                             self.data.username))

    async def set_hand(self, item):
        item_id = None if item is None else item.id
        await self.data.update(hand=item_id).apply()
        await self.room.send_xt('upa', self.data.id, item_id or 0)

        self.logger.info('{} updated their hand item to \'{}\' '.format(
            self.data.username, item.name) if item else
                         '{} removed their hand item'.format(
                             self.data.username))

    async def set_feet(self, item):
        item_id = None if item is None else item.id
        await self.data.update(feet=item_id).apply()
        await self.room.send_xt('upe', self.data.id, item_id or 0)

        self.logger.info('{} updated their feet item to \'{}\' '.format(
            self.data.username, item.name) if item else
                         '{} removed their feet item'.format(
                             self.data.username))

    async def set_flag(self, item):
        item_id = None if item is None else item.id
        await self.data.update(flag=item_id).apply()
        await self.room.send_xt('upl', self.data.id, item_id or 0)

        self.logger.info('{} updated their flag item to \'{}\' '.format(
            self.data.username, item.name) if item else
                         '{} removed their flag item'.format(
                             self.data.username))

    async def set_photo(self, item):
        item_id = None if item is None else item.id
        await self.data.update(photo=item_id).apply()
        await self.room.send_xt('upp', self.data.id, item_id or 0)

        self.logger.info('{} updated their background to \'{}\' '.format(
            self.data.username, item.name) if item else
                         '{} removed their background item'.format(
                             self.data.username))

        
    def __repr__(self):
        if self.data is not None:
            return '<Penguin ID=\'{}\' Username=\'{}\'>'.format(self.data.id, self.data.username)
        return super().__repr__()

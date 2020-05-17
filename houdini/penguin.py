import time

from houdini.data import penguin
from houdini.data.mail import PenguinPostcard
from houdini.handlers.play.pet import get_my_player_walking_puffle
from houdini.spheniscidae import Spheniscidae


class Penguin(Spheniscidae, penguin.Penguin):

    __slots__ = (
        'x', 'y',
        'frame',
        'toy',
        'room',
        'waddle',
        'table',
        'muted',

        'login_key',

        'is_member',
        'membership_days_total',
        'membership_days_remain',

        'avatar',
        'active_quests',
        'legacy_buddy_requests',

        'heartbeat',
        'login_timestamp',
        'egg_timer_minutes'
    )

    def __init__(self, *args):
        super().__init__(*args)

        self.x, self.y = (0, 0)
        self.frame = 1
        self.toy = None
        self.room = None
        self.waddle = None
        self.table = None
        self.muted = False

        self.login_key = None

        self.is_member = False
        self.membership_days_total = 0
        self.membership_days_remain = -1

        self.avatar = None
        self.active_quests = None
        self.legacy_buddy_requests = set()

        self.heartbeat = time.time()

        self.login_timestamp = None
        self.egg_timer_minutes = None

        self.can_dig_gold = False

    @property
    def party_state(self):
        return str()

    @property
    def puffle_state(self):
        return get_my_player_walking_puffle(self)

    @property
    def penguin_state(self):
        return str()

    @property
    def string(self):
        return self.server.penguin_string_compiler.compile(self)

    @property
    def safe_name(self):
        return self.safe_nickname(self.server.config.lang)

    @property
    def member(self):
        return int(self.is_member)

    async def join_room(self, room):
        await room.add_penguin(self)

        self.logger.info(f'{self.username} joined room \'{room.name}\'')

    async def add_inventory(self, item, notify=True, cost=None):
        if item.id in self.inventory:
            return False

        cost = cost if cost is not None else item.cost

        await self.inventory.insert(item_id=item.id)
        await self.update(coins=self.coins - cost).apply()

        if notify:
            await self.send_xt('ai', item.id, self.coins)

        self.logger.info(f'{self.username} added \'{item.name}\' to their clothing inventory')

        self.server.cache.delete(f'pins.{self.id}')
        self.server.cache.delete(f'awards.{self.id}')

        return True

    async def add_epf_inventory(self, item, notify=True, cost=None):
        if not item.epf:
            return False

        if item.id in self.inventory:
            return False

        cost = cost if cost is not None else item.cost

        await self.inventory.insert(item_id=item.id)
        await self.update(agent_medals=self.agent_medals - cost).apply()

        if notify:
            await self.send_xt('epfai', self.agent_medals)

        return True

    async def add_igloo(self, igloo, notify=True, cost=None):
        if igloo.id in self.igloos:
            return False

        cost = cost if cost is not None else igloo.cost

        await self.igloos.insert(igloo_id=igloo.id)
        await self.update(coins=self.coins - cost).apply()

        if notify:
            await self.send_xt('au', igloo.id, self.coins)

        self.logger.info(f'{self.username} added \'{igloo.name}\' to their igloos inventory')

        return True

    async def add_puffle_item(self, care_item, quantity=1, notify=True, cost=None):
        if care_item.type not in ['food', 'head', 'play']:
            return False

        care_item_id = care_item.parent_id
        quantity = quantity * care_item.quantity

        if care_item.type == 'play' and care_item_id in self.puffle_items:
            return False

        if care_item_id in self.puffle_items:
            penguin_care_item = self.puffle_items[care_item_id]
            if penguin_care_item.quantity >= 100:
                return False

            await penguin_care_item.update(
                quantity=penguin_care_item.quantity + quantity).apply()
        else:
            penguin_care_item = await self.puffle_items.insert(item_id=care_item_id,
                                                               quantity=quantity)

        cost = cost if cost is not None else care_item.cost
        await self.update(coins=self.coins - cost).apply()

        if notify:
            await self.send_xt('papi', self.coins, care_item_id, penguin_care_item.quantity)

        self.logger.info(f'{self.username} added \'{care_item.name}\' to their puffle care inventory')

        return True

    async def add_furniture(self, furniture, quantity=1, notify=True, cost=None):
        if furniture.id in self.furniture:
            penguin_furniture = self.furniture[furniture.id]
            if penguin_furniture.quantity >= furniture.max_quantity:
                return False

            await penguin_furniture.update(
                quantity=penguin_furniture.quantity + quantity).apply()
        else:
            await self.furniture.insert(furniture_id=furniture.id)

        cost = cost if cost is not None else furniture.cost
        await self.update(coins=self.coins - cost).apply()

        if notify:
            await self.send_xt('af', furniture.id, self.coins)

        self.logger.info(f'{self.username} added \'{furniture.name}\' to their furniture inventory')

        return True

    async def add_card(self, card, quantity=0, member_quantity=0):
        quantity = max(1, quantity + member_quantity)
        if card.id in self.cards:
            penguin_card = self.cards[card.id]

            await penguin_card.update(
                quantity=penguin_card.quantity + quantity,
                member_quantity=penguin_card.member_quantity + member_quantity).apply()
        else:
            await self.cards.insert(card_id=card.id, quantity=quantity, member_quantity=member_quantity)

        self.logger.info(f'{self.username} added \'{card.name}\' to their ninja deck')

        return True

    async def add_flooring(self, flooring, notify=True, cost=None):
        if flooring.id in self.flooring:
            return False

        cost = cost if cost is not None else flooring.cost

        await self.flooring.insert(flooring_id=flooring.id)
        await self.update(coins=self.coins - cost).apply()

        if notify:
            await self.send_xt('ag', flooring.id, self.coins)

        self.logger.info(f'{self.username} added \'{flooring.name}\' to their flooring inventory')

        return True

    async def add_location(self, location, notify=True, cost=None):
        if location.id in self.locations:
            return False

        cost = cost if cost is not None else location.cost

        await self.locations.insert(location_id=location.id)
        await self.update(coins=self.coins - cost).apply()

        if notify:
            await self.send_xt('aloc', location.id, self.coins)

        self.logger.info(f'{self.username} added \'{location.name}\' to their location inventory')

        return True

    async def add_stamp(self, stamp, notify=True):
        if stamp.id in self.stamps:
            return False

        await self.stamps.insert(stamp_id=stamp.id)

        if notify:
            await self.send_xt('aabs', stamp.id)

        self.logger.info(f'{self.username} earned stamp \'{stamp.name}\'')
        self.server.cache.delete(f'stamps.{self.id}')

        return True

    async def add_inbox(self, postcard, sender_name="sys", sender_id=None, details=""):
        penguin_postcard = await PenguinPostcard.create(penguin_id=self.id, sender_id=sender_id,
                                                        postcard_id=postcard.id, details=details)

        await self.send_xt('mr', sender_name, 0, postcard.id, details, int(time.time()), penguin_postcard.id)

    async def add_permission(self, permission):
        if permission.name not in self.permissions:
            await self.permissions.insert(permission_name=permission.name)

        self.logger.info(f'{self.username} was assigned permission \'{permission.name}\'')

        return True

    async def revoke_permission(self, permission_root):
        for permission in list(self.permissions.values()):
            server_permission = self.server.permissions[permission.permission_name]

            if server_permission.name == permission_root.name or \
                    server_permission.name.startswith(permission_root.name + '.'):
                await self.permissions.delete(server_permission.name)

        self.logger.info(f'{self.username} had permission \'{permission_root.name}\' revoked')

        return True

    def get_custom_attribute(self, name, default=None):
        penguin_attribute = self.attributes.get(name, default)
        if penguin_attribute == default:
            return default
        return penguin_attribute.value

    async def set_custom_attribute(self, name, value):
        if name not in self.attributes:
            await self.attributes.insert(name=name, value=value)
        else:
            attribute = self.attributes[name]
            await attribute.update(value=value).apply()

        self.logger.info(f'{self.username} set custom attribute \'{name}\' to \'{value}\'')

        return True

    async def delete_custom_attribute(self, name):
        if name in self.attributes:
            await self.attributes.delete(name)

        self.logger.info(f'{self.username} deleted attribute \'{name}\'')

        return True

    async def add_coins(self, coins, stay=False):
        if stay:
            await self.join_room(self.room)
        await self.update(coins=self.coins + coins).apply()
        await self.send_xt('zo', self.coins, '', 0, 0, 0)
        return self.coins

    async def set_color(self, item):
        await self.update(color=item.id).apply()
        await self.room.send_xt('upc', self.id, item.id)
        self.logger.info(f'{self.username} updated their color to \'{item.name}\' ')

    async def set_head(self, item):
        item_id = None if item is None else item.id
        await self.update(head=item_id).apply()
        await self.room.send_xt('uph', self.id, item_id or 0)

        self.logger.info(f'{self.username} updated their head item to \'{item.name}\' ' if item else
                         f'{self.username} removed their head item')

    async def set_face(self, item):
        item_id = None if item is None else item.id
        await self.update(face=item_id).apply()
        await self.room.send_xt('upf', self.id, item_id or 0)

        self.logger.info(f'{self.username} updated their face item to \'{item.name}\' ' if item else
                         f'{self.username} removed their face item')

    async def set_neck(self, item):
        item_id = None if item is None else item.id
        await self.update(neck=item_id).apply()
        await self.room.send_xt('upn', self.id, item_id or 0)

        self.logger.info(f'{self.username} updated their neck item to \'{item.name}\' ' if item else
                         f'{self.username} removed their neck item')

    async def set_body(self, item):
        item_id = None if item is None else item.id
        await self.update(body=item_id).apply()
        await self.room.send_xt('upb', self.id, item_id or 0)

        self.logger.info(f'{self.username} updated their body item to \'{item.name}\' ' if item else
                         f'{self.username} removed their body item')

    async def set_hand(self, item):
        item_id = None if item is None else item.id
        await self.update(hand=item_id).apply()
        await self.room.send_xt('upa', self.id, item_id or 0)

        self.logger.info(f'{self.username} updated their hand item to \'{item.name}\' ' if item else
                         f'{self.username} removed their hand item')

    async def set_feet(self, item):
        item_id = None if item is None else item.id
        await self.update(feet=item_id).apply()
        await self.room.send_xt('upe', self.id, item_id or 0)

        self.logger.info(f'{self.username} updated their feet item to \'{item.name}\' ' if item else
                         f'{self.username} removed their feet item')

    async def set_flag(self, item):
        item_id = None if item is None else item.id
        await self.update(flag=item_id).apply()
        await self.room.send_xt('upl', self.id, item_id or 0)

        self.logger.info(f'{self.username} updated their flag item to \'{item.name}\' ' if item else
                         f'{self.username} removed their flag item')

    async def set_photo(self, item):
        item_id = None if item is None else item.id
        await self.update(photo=item_id).apply()
        await self.room.send_xt('upp', self.id, item_id or 0)

        self.logger.info(f'{self.username} updated their background to \'{item.name}\' ' if item else
                         f'{self.username} removed their background item')
        
    def __repr__(self):
        if self.id is not None:
            return f'<Penguin ID=\'{self.id}\' Username=\'{self.username}\'>'
        return super().__repr__()

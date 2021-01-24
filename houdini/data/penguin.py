from datetime import datetime
from functools import cached_property

from houdini.data import db


class Penguin(db.Model):
    __tablename__ = 'penguin'

    id = db.Column(db.Integer, primary_key=True, server_default=db.text("nextval('\"penguin_id_seq\"'::regclass)"))
    username = db.Column(db.String(12), nullable=False, unique=True)
    nickname = db.Column(db.String(30), nullable=False)
    password = db.Column(db.CHAR(60), nullable=False)
    email = db.Column(db.String(255), nullable=False, index=True)
    registration_date = db.Column(db.DateTime, nullable=False, server_default=db.text("now()"))
    active = db.Column(db.Boolean, nullable=False, server_default=db.text("false"))
    safe_chat = db.Column(db.Boolean, nullable=False, server_default=db.text("false"))
    last_paycheck = db.Column(db.DateTime, nullable=False, server_default=db.text("now()"))
    minutes_played = db.Column(db.Integer, nullable=False, server_default=db.text("0"))
    moderator = db.Column(db.Boolean, nullable=False, server_default=db.text("false"))
    stealth_moderator = db.Column(db.Boolean, nullable=False, server_default=db.text("false"))
    character = db.Column(db.ForeignKey('character.id', ondelete='CASCADE', onupdate='CASCADE'))
    igloo = db.Column(db.ForeignKey('penguin_igloo_room.id', ondelete='CASCADE', onupdate='CASCADE'))
    coins = db.Column(db.Integer, nullable=False, server_default=db.text("500"))
    color = db.Column(db.ForeignKey('item.id', ondelete='CASCADE', onupdate='CASCADE'))
    head = db.Column(db.ForeignKey('item.id', ondelete='CASCADE', onupdate='CASCADE'))
    face = db.Column(db.ForeignKey('item.id', ondelete='CASCADE', onupdate='CASCADE'))
    neck = db.Column(db.ForeignKey('item.id', ondelete='CASCADE', onupdate='CASCADE'))
    body = db.Column(db.ForeignKey('item.id', ondelete='CASCADE', onupdate='CASCADE'))
    hand = db.Column(db.ForeignKey('item.id', ondelete='CASCADE', onupdate='CASCADE'))
    feet = db.Column(db.ForeignKey('item.id', ondelete='CASCADE', onupdate='CASCADE'))
    photo = db.Column(db.ForeignKey('item.id', ondelete='CASCADE', onupdate='CASCADE'))
    flag = db.Column(db.ForeignKey('item.id', ondelete='CASCADE', onupdate='CASCADE'))
    permaban = db.Column(db.Boolean, nullable=False, server_default=db.text("false"))
    book_modified = db.Column(db.SmallInteger, nullable=False, server_default=db.text("0"))
    book_color = db.Column(db.SmallInteger, nullable=False, server_default=db.text("1"))
    book_highlight = db.Column(db.SmallInteger, nullable=False, server_default=db.text("1"))
    book_pattern = db.Column(db.SmallInteger, nullable=False, server_default=db.text("0"))
    book_icon = db.Column(db.SmallInteger, nullable=False, server_default=db.text("1"))
    agent_status = db.Column(db.Boolean, nullable=False, server_default=db.text("false"))
    field_op_status = db.Column(db.SmallInteger, nullable=False, server_default=db.text("0"))
    career_medals = db.Column(db.Integer, nullable=False, server_default=db.text("0"))
    agent_medals = db.Column(db.Integer, nullable=False, server_default=db.text("0"))
    last_field_op = db.Column(db.DateTime, nullable=False, server_default=db.text("now()"))
    com_message_read_date = db.Column(db.DateTime, nullable=False, server_default=db.text("now()"))
    ninja_rank = db.Column(db.SmallInteger, nullable=False, server_default=db.text("0"))
    ninja_progress = db.Column(db.SmallInteger, nullable=False, server_default=db.text("0"))
    fire_ninja_rank = db.Column(db.SmallInteger, nullable=False, server_default=db.text("0"))
    fire_ninja_progress = db.Column(db.SmallInteger, nullable=False, server_default=db.text("0"))
    water_ninja_rank = db.Column(db.SmallInteger, nullable=False, server_default=db.text("0"))
    water_ninja_progress = db.Column(db.SmallInteger, nullable=False, server_default=db.text("0"))
    snow_ninja_progress = db.Column(db.SmallInteger, nullable=False, server_default=db.text("0"))
    snow_ninja_rank = db.Column(db.SmallInteger, nullable=False, server_default=db.text("0"))
    ninja_matches_won = db.Column(db.Integer, nullable=False, server_default=db.text("0"))
    fire_matches_won = db.Column(db.Integer, nullable=False, server_default=db.text("0"))
    water_matches_won = db.Column(db.Integer, nullable=False, server_default=db.text("0"))
    rainbow_adoptability = db.Column(db.Boolean, nullable=False, server_default=db.text("false"))
    has_dug = db.Column(db.Boolean, nullable=False, server_default=db.text("false"))
    puffle_handler = db.Column(db.Boolean, nullable=False, server_default=db.text("false"))
    nuggets = db.Column(db.SmallInteger, nullable=False, server_default=db.text("0"))
    walking = db.Column(db.ForeignKey('penguin_puffle.id', ondelete='CASCADE', onupdate='CASCADE'))
    opened_playercard = db.Column(db.Boolean, nullable=False, server_default=db.text("false"))
    special_wave = db.Column(db.Boolean, nullable=False, server_default=db.text("false"))
    special_dance = db.Column(db.Boolean, nullable=False, server_default=db.text("false"))
    special_snowball = db.Column(db.Boolean, nullable=False, server_default=db.text("false"))
    map_category = db.Column(db.SmallInteger, nullable=False, server_default=db.text("0"))
    status_field = db.Column(db.Integer, nullable=False, server_default=db.text("0"))
    timer_active = db.Column(db.Boolean, nullable=False, server_default=db.text("false"))
    timer_start = db.Column(db.Time, nullable=False, server_default=db.text("'00:00:00'::time without time zone"))
    timer_end = db.Column(db.Time, nullable=False, server_default=db.text("'23:59:59'::time without time zone"))
    timer_total = db.Column(db.Interval, nullable=False, server_default=db.text("'01:00:00'::interval"))
    grounded = db.Column(db.Boolean, nullable=False, server_default=db.text("false"))
    approval_en = db.Column(db.Boolean, nullable=False, server_default=db.text("false"))
    approval_pt = db.Column(db.Boolean, nullable=False, server_default=db.text("false"))
    approval_fr = db.Column(db.Boolean, nullable=False, server_default=db.text("false"))
    approval_es = db.Column(db.Boolean, nullable=False, server_default=db.text("false"))
    approval_de = db.Column(db.Boolean, nullable=False, server_default=db.text("false"))
    approval_ru = db.Column(db.Boolean, nullable=False, server_default=db.text("false"))
    rejection_en = db.Column(db.Boolean, nullable=False, server_default=db.text("false"))
    rejection_pt = db.Column(db.Boolean, nullable=False, server_default=db.text("false"))
    rejection_fr = db.Column(db.Boolean, nullable=False, server_default=db.text("false"))
    rejection_es = db.Column(db.Boolean, nullable=False, server_default=db.text("false"))
    rejection_de = db.Column(db.Boolean, nullable=False, server_default=db.text("false"))
    rejection_ru = db.Column(db.Boolean, nullable=False, server_default=db.text("false"))
	

    def __init__(self, *args, **kwargs):
        self.inventory = None
        self.permissions = None
        self.attributes = None
        self.igloos = None
        self.igloo_rooms = None
        self.furniture = None
        self.flooring = None
        self.locations = None
        self.stamps = None
        self.cards = None
        self.puffles = None
        self.puffle_items = None
        self.buddies = None
        self.buddy_requests = None
        self.character_buddies = None
        self.ignore = None

        super().__init__(*args, **kwargs)

    def safe_nickname(self, language_bitmask):
        return self.nickname if self.approval & language_bitmask else "P" + str(self.id)

    async def status_field_set(self, field_bitmask):
        if (self.status_field & field_bitmask) == 0:
            await self.update(status_field=self.status_field ^ field_bitmask).apply()

    def status_field_get(self, field_bitmask):
        return (self.status_field & field_bitmask) != 0

    @cached_property
    def age(self):
        return (datetime.now() - self.registration_date).days

    @cached_property
    def approval(self):
        return int(f'{self.approval_ru * 1}{self.approval_de * 1}0{self.approval_es * 1}'
                   f'{self.approval_fr * 1}{self.approval_pt * 1}{self.approval_en * 1}', 2)

    @cached_property
    def rejection(self):
        return int(f'{self.rejection_ru * 1}{self.rejection_de * 1}0{self.rejection_es * 1}'
                   f'{self.rejection_fr * 1}{self.rejection_pt * 1}{self.rejection_en * 1}', 2)


class ActivationKey(db.Model):
    __tablename__ = 'activation_key'

    penguin_id = db.Column(db.ForeignKey('penguin.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
                           nullable=False)
    activation_key = db.Column(db.CHAR(255), primary_key=True, nullable=False)


class PenguinMembership(db.Model):
    __tablename__ = 'penguin_membership'

    penguin_id = db.Column(db.ForeignKey('penguin.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
                           nullable=False)
    start = db.Column(db.DateTime, primary_key=True, nullable=False)
    expires = db.Column(db.DateTime)
    start_aware = db.Column(db.Boolean, server_default=db.text("false"))
    expires_aware = db.Column(db.Boolean, server_default=db.text("false"))
    expired_aware = db.Column(db.Boolean, server_default=db.text("false"))


class Login(db.Model):
    __tablename__ = 'login'

    id = db.Column(db.Integer, primary_key=True, server_default=db.text("nextval('\"login_id_seq\"'::regclass)"))
    penguin_id = db.Column(db.ForeignKey('penguin.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    date = db.Column(db.DateTime, nullable=False, server_default=db.text("now()"))
    ip_hash = db.Column(db.CHAR(255), nullable=False)
    minutes_played = db.Column(db.Integer, nullable=False, server_default=db.text("0"))


class EpfComMessage(db.Model):
    __tablename__ = 'epf_com_message'

    message = db.Column(db.Text, nullable=False)
    character_id = db.Column(db.ForeignKey('character.id', ondelete='RESTRICT', onupdate='CASCADE'), nullable=False)
    date = db.Column(db.DateTime, nullable=False, server_default=db.text("now()"))


class CfcDonation(db.Model):
    __tablename__ = 'cfc_donation'

    penguin_id = db.Column(db.ForeignKey('penguin.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    coins = db.Column(db.Integer, nullable=False)
    charity = db.Column(db.Integer, nullable=False)
    date = db.Column(db.DateTime, nullable=False, server_default=db.text("now()"))

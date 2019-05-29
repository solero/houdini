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
    permaban = db.Column(db.SmallInteger, nullable=False, server_default=db.text("0"))
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
    ninja_rank = db.Column(db.SmallInteger, nullable=False, server_default=db.text("0"))
    ninja_progress = db.Column(db.SmallInteger, nullable=False, server_default=db.text("0"))
    fire_ninja_rank = db.Column(db.SmallInteger, nullable=False, server_default=db.text("0"))
    fire_ninja_progress = db.Column(db.SmallInteger, nullable=False, server_default=db.text("0"))
    water_ninja_rank = db.Column(db.SmallInteger, nullable=False, server_default=db.text("0"))
    water_ninja_progress = db.Column(db.SmallInteger, nullable=False, server_default=db.text("0"))
    ninja_matches_won = db.Column(db.Integer, nullable=False, server_default=db.text("0"))
    fire_matches_won = db.Column(db.Integer, nullable=False, server_default=db.text("0"))
    water_matches_won = db.Column(db.Integer, nullable=False, server_default=db.text("0"))
    rainbow_adoptability = db.Column(db.SmallInteger, nullable=False, server_default=db.text("0"))
    has_dug = db.Column(db.Boolean, nullable=False, server_default=db.text("false"))
    nuggets = db.Column(db.SmallInteger, nullable=False, server_default=db.text("0"))
    timer_active = db.Column(db.Boolean, nullable=False, server_default=db.text("false"))
    timer_start = db.Column(db.Time, nullable=False, server_default=db.text("'00:00:00'::time without time zone"))
    timer_end = db.Column(db.Time, nullable=False, server_default=db.text("'23:59:59'::time without time zone"))
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

    @property
    def approval(self):
        return int('{}{}0{}{}{}{}'.format(self.approval_ru * 1, self.approval_de * 1, self.approval_es * 1,
                                          self.approval_fr * 1, self.approval_pt * 1, self.approval_en * 1), 2)

    @property
    def rejection(self):
        return int('{}{}0{}{}{}{}'.format(self.rejection_ru * 1, self.rejection_de * 1, self.rejection_es * 1,
                                          self.rejection_fr * 1, self.rejection_pt * 1, self.rejection_en * 1), 2)


class ActivationKey(db.Model):
    __tablename__ = 'activation_key'

    penguin_id = db.Column(db.ForeignKey('penguin.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
                           nullable=False)
    activation_key = db.Column(db.CHAR(255), primary_key=True, nullable=False)


class PuffleQuest(db.Model):
    __tablename__ = 'puffle_quest'

    penguin_id = db.Column(db.ForeignKey('penguin.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
                           nullable=False)
    task_id = db.Column(db.SmallInteger, primary_key=True, nullable=False)
    completion_date = db.Column(db.DateTime)
    item_collected = db.Column(db.Boolean, nullable=False, server_default=db.text("false"))
    coins_collected = db.Column(db.Boolean, nullable=False, server_default=db.text("false"))


class PenguinIgloo(db.Model):
    __tablename__ = 'penguin_igloo'

    penguin_id = db.Column(db.ForeignKey('penguin.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
                           nullable=False)
    igloo_id = db.Column(db.ForeignKey('igloo.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
                         nullable=False)


class PenguinItem(db.Model):
    __tablename__ = 'penguin_item'

    penguin_id = db.Column(db.ForeignKey('penguin.id', ondelete='CASCADE', onupdate='CASCADE'),
                           primary_key=True, nullable=False)
    item_id = db.Column(db.ForeignKey('item.id', ondelete='CASCADE', onupdate='CASCADE'),
                        primary_key=True, nullable=False)


class PenguinLocation(db.Model):
    __tablename__ = 'penguin_location'

    penguin_id = db.Column(db.ForeignKey('penguin.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
                           nullable=False)
    location_id = db.Column(db.ForeignKey('location.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
                            nullable=False)


class PenguinStamp(db.Model):
    __tablename__ = 'penguin_stamp'

    penguin_id = db.Column(db.ForeignKey('penguin.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
                           nullable=False)
    stamp_id = db.Column(db.ForeignKey('stamp.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
                         nullable=False)
    recent = db.Column(db.Boolean, nullable=False, server_default=db.text("true"))


class PenguinRedemption(db.Model):
    __tablename__ = 'penguin_redemption'

    penguin_id = db.Column(db.ForeignKey('penguin.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
                           nullable=False)
    code_id = db.Column(db.ForeignKey('redemption_code.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
                        nullable=False, index=True)
    book_id = db.Column(db.ForeignKey('redemption_book.id', ondelete='CASCADE', onupdate='CASCADE'), index=True)


class PenguinMembership(db.Model):
    __tablename__ = 'penguin_membership'

    penguin_id = db.Column(db.ForeignKey('penguin.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
                           nullable=False)
    start = db.Column(db.DateTime, primary_key=True, nullable=False)
    expires = db.Column(db.DateTime, primary_key=True, nullable=False)


class PenguinPostcard(db.Model):
    __tablename__ = 'penguin_postcard'

    id = db.Column(db.Integer, primary_key=True,
                   server_default=db.text("nextval('\"penguin_postcard_id_seq\"'::regclass)"))
    penguin_id = db.Column(db.ForeignKey('penguin.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False,
                           index=True)
    sender_id = db.Column(db.ForeignKey('penguin.id', ondelete='CASCADE', onupdate='CASCADE'), index=True)
    postcard_id = db.Column(db.ForeignKey('postcard.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    send_date = db.Column(db.DateTime, nullable=False, server_default=db.text("now()"))
    details = db.Column(db.String(255), nullable=False, server_default=db.text("''::character varying"))
    has_read = db.Column(db.Boolean, nullable=False, server_default=db.text("false"))


class PenguinIglooRoom(db.Model):
    __tablename__ = 'penguin_igloo_room'

    id = db.Column(db.Integer, primary_key=True,
                   server_default=db.text("nextval('\"penguin_igloo_room_id_seq\"'::regclass)"))
    penguin_id = db.Column(db.ForeignKey('penguin.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    type = db.Column(db.ForeignKey('igloo.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    flooring = db.Column(db.ForeignKey('flooring.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    music = db.Column(db.SmallInteger, nullable=False, server_default=db.text("0"))
    location = db.Column(db.ForeignKey('location.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    locked = db.Column(db.Boolean, nullable=False, server_default=db.text("false"))


class PenguinLaunchGame(db.Model):
    __tablename__ = 'penguin_launch_game'

    penguin_id = db.Column(db.ForeignKey('penguin.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
                           nullable=False)
    level = db.Column(db.SmallInteger, primary_key=True, nullable=False, server_default=db.text("0"))
    puffle_os = db.Column(db.SmallInteger, nullable=False, server_default=db.text("0"))
    best_time = db.Column(db.SmallInteger, nullable=False, server_default=db.text("600"))
    turbo = db.Column(db.Boolean, nullable=False, server_default=db.text("false"))


class PenguinCard(db.Model):
    __tablename__ = 'penguin_card'

    penguin_id = db.Column(db.ForeignKey('penguin.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
                           nullable=False, index=True)
    card_id = db.Column(db.ForeignKey('card.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
                        nullable=False)
    quantity = db.Column(db.SmallInteger, nullable=False, server_default=db.text("1"))


class PenguinFurniture(db.Model):
    __tablename__ = 'penguin_furniture'

    penguin_id = db.Column(db.ForeignKey('penguin.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
                           nullable=False)
    furniture_id = db.Column(db.ForeignKey('furniture.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
                             nullable=False)
    quantity = db.Column(db.SmallInteger, nullable=False, server_default=db.text("1"))


class PenguinFlooring(db.Model):
    __tablename__ = 'penguin_flooring'

    penguin_id = db.Column(db.ForeignKey('penguin.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
                           nullable=False)
    flooring_id = db.Column(db.ForeignKey('flooring.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
                            nullable=False)


class PenguinPuffle(db.Model):
    __tablename__ = 'penguin_puffle'

    id = db.Column(db.Integer, primary_key=True,
                   server_default=db.text("nextval('\"penguin_puffle_id_seq\"'::regclass)"))
    penguin_id = db.Column(db.ForeignKey('penguin.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    puffle_id = db.Column(db.ForeignKey('puffle.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    name = db.Column(db.String(16), nullable=False)
    adoption_date = db.Column(db.DateTime, nullable=False, server_default=db.text("now()"))
    food = db.Column(db.SmallInteger, nullable=False, server_default=db.text("100"))
    play = db.Column(db.SmallInteger, nullable=False, server_default=db.text("100"))
    rest = db.Column(db.SmallInteger, nullable=False, server_default=db.text("100"))
    clean = db.Column(db.SmallInteger, nullable=False, server_default=db.text("100"))
    walking = db.Column(db.Boolean, server_default=db.text("false"))
    hat = db.Column(db.ForeignKey('puffle_item.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    backyard = db.Column(db.Boolean, server_default=db.text("false"))
    has_dug = db.Column(db.Boolean, server_default=db.text("false"))


class PenguinPuffleItem(db.Model):
    __tablename__ = 'penguin_puffle_item'

    penguin_id = db.Column(db.ForeignKey('penguin.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
                           nullable=False)
    item_id = db.Column(db.Integer, primary_key=True, nullable=False)
    quantity = db.Column(db.SmallInteger, nullable=False)


class PenguinPermission(db.Model):
    __tablename__ = 'penguin_permission'

    penguin_id = db.Column(db.ForeignKey(u'penguin.id', ondelete=u'CASCADE', onupdate=u'CASCADE'), primary_key=True)
    permission_id = db.Column(db.ForeignKey(u'permission.id', ondelete=u'CASCADE', onupdate=u'CASCADE'), nullable=False)


class Login(db.Model):
    __tablename__ = 'login'

    id = db.Column(db.Integer, primary_key=True, server_default=db.text("nextval('\"login_id_seq\"'::regclass)"))
    penguin_id = db.Column(db.ForeignKey('penguin.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    date = db.Column(db.DateTime, nullable=False, server_default=db.text("now()"))
    i_p_address = db.Column(db.CHAR(255), nullable=False)

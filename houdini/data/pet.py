from houdini.data import AbstractDataCollection, db


class Puffle(db.Model):
    __tablename__ = 'puffle'

    id = db.Column(db.Integer, primary_key=True)
    parent_id = db.Column(db.ForeignKey('puffle.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    name = db.Column(db.String(50), nullable=False, server_default=db.text("''::character varying"))
    cost = db.Column(db.Integer, nullable=False, server_default=db.text("0"))
    member = db.Column(db.Boolean, nullable=False, server_default=db.text("false"))
    favourite_food = db.Column(db.ForeignKey('puffle_item.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    favourite_toy = db.Column(db.ForeignKey('puffle_item.id', ondelete='CASCADE', onupdate='CASCADE'))
    runaway_postcard = db.Column(db.ForeignKey('postcard.id', ondelete='CASCADE', onupdate='CASCADE'))


class PuffleItem(db.Model):
    __tablename__ = 'puffle_item'

    id = db.Column(db.Integer, primary_key=True)
    parent_id = db.Column(db.ForeignKey('puffle_item.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    name = db.Column(db.String(50), nullable=False, server_default=db.text("''::character varying"))
    type = db.Column(db.String(10), nullable=False, server_default=db.text("'care'::character varying"))
    play_external = db.Column(db.String(10), nullable=False, server_default=db.text("'none'::character varying"))
    cost = db.Column(db.Integer, nullable=False, server_default=db.text("0"))
    quantity = db.Column(db.SmallInteger, nullable=False, server_default=db.text("1"))
    member = db.Column(db.Boolean, nullable=False, server_default=db.text("false"))
    food_effect = db.Column(db.SmallInteger, nullable=False, server_default=db.text("0"))
    rest_effect = db.Column(db.SmallInteger, nullable=False, server_default=db.text("0"))
    play_effect = db.Column(db.SmallInteger, nullable=False, server_default=db.text("0"))
    clean_effect = db.Column(db.SmallInteger, nullable=False, server_default=db.text("0"))


class PuffleTreasureFurniture(db.Model):
    __tablename__ = 'puffle_treasure_furniture'

    puffle_id = db.Column(db.ForeignKey('puffle.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
                          nullable=False)
    furniture_id = db.Column(db.ForeignKey('furniture.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
                             nullable=False)


class PuffleTreasureItem(db.Model):
    __tablename__ = 'puffle_treasure_item'

    puffle_id = db.Column(db.ForeignKey('puffle.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
                          nullable=False)
    item_id = db.Column(db.ForeignKey('item.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
                        nullable=False)


class PuffleTreasurePuffleItem(db.Model):
    __tablename__ = 'puffle_treasure_puffle_item'

    puffle_id = db.Column(db.ForeignKey('puffle.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
                          nullable=False)
    puffle_item_id = db.Column(db.ForeignKey('puffle_item.id', ondelete='CASCADE', onupdate='CASCADE'),
                               primary_key=True, nullable=False)


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
    hat = db.Column(db.ForeignKey('puffle_item.id', ondelete='CASCADE', onupdate='CASCADE'))
    backyard = db.Column(db.Boolean, server_default=db.text("false"))
    has_dug = db.Column(db.Boolean, server_default=db.text("false"))


class PenguinPuffleItem(db.Model):
    __tablename__ = 'penguin_puffle_item'

    penguin_id = db.Column(db.ForeignKey('penguin.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
                           nullable=False)
    item_id = db.Column(db.ForeignKey('puffle_item.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
                        nullable=False)
    quantity = db.Column(db.SmallInteger, nullable=False, server_default=db.text("1"))


class PuffleCollection(AbstractDataCollection):
    __model__ = Puffle
    __indexby__ = 'id'
    __filterby__ = 'id'


class PenguinPuffleCollection(AbstractDataCollection):
    __model__ = PenguinPuffle
    __indexby__ = 'id'
    __filterby__ = 'penguin_id'


class PuffleItemCollection(AbstractDataCollection):
    __model__ = PuffleItem
    __indexby__ = 'id'
    __filterby__ = 'id'


class PenguinPuffleItemCollection(AbstractDataCollection):
    __model__ = PenguinPuffleItem
    __indexby__ = 'item_id'
    __filterby__ = 'penguin_id'

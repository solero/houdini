from houdini.data import db, BaseCrumbsCollection
from houdini.data.penguin import PenguinPuffle, PenguinPuffleItem


class Puffle(db.Model):
    __tablename__ = 'puffle'

    id = db.Column(db.Integer, primary_key=True)
    parent_id = db.Column(db.ForeignKey('puffle.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    name = db.Column(db.String(50), nullable=False, server_default=db.text("''::character varying"))
    member = db.Column(db.Boolean, nullable=False, server_default=db.text("false"))
    favourite_food = db.Column(db.ForeignKey('puffle_item.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    runaway_postcard = db.Column(db.ForeignKey('postcard.id', ondelete='CASCADE', onupdate='CASCADE'))
    max_food = db.Column(db.SmallInteger, nullable=False, server_default=db.text("100"))
    max_rest = db.Column(db.SmallInteger, nullable=False, server_default=db.text("100"))
    max_clean = db.Column(db.SmallInteger, nullable=False, server_default=db.text("100"))


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


class PuffleCrumbsCollection(BaseCrumbsCollection):

    def __init__(self, inventory_id=None):
        super().__init__(model=Puffle, key='ID', inventory_model=PenguinPuffle,
                         inventory_id=inventory_id)


class PuffleItemCrumbsCollection(BaseCrumbsCollection):

    def __init__(self, inventory_id=None):
        super().__init__(model=PuffleItem, key='ID', inventory_model=PenguinPuffleItem,
                         inventory_id=inventory_id)

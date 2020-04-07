from houdini.data import db, AbstractDataCollection
from functools import cached_property


class Item(db.Model):
    __tablename__ = 'item'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    type = db.Column(db.SmallInteger, nullable=False, server_default=db.text("1"))
    cost = db.Column(db.Integer, nullable=False, server_default=db.text("0"))
    member = db.Column(db.Boolean, nullable=False, server_default=db.text("false"))
    bait = db.Column(db.Boolean, nullable=False, server_default=db.text("false"))
    patched = db.Column(db.Boolean, nullable=False, server_default=db.text("false"))
    legacy_inventory = db.Column(db.Boolean, nullable=False, server_default=db.text("false"))
    vanilla_inventory = db.Column(db.Boolean, nullable=False, server_default=db.text("false"))
    epf = db.Column(db.Boolean, nullable=False, server_default=db.text("false"))
    tour = db.Column(db.Boolean, nullable=False, server_default=db.text("false"))
    release_date = db.Column(db.Date, nullable=False, server_default=db.text("now()"))
    treasure = db.Column(db.Boolean, nullable=False, server_default=db.text("false"))
    innocent = db.Column(db.Boolean, nullable=False, server_default=db.text("false"))

    def is_color(self):
        return self.type == 1

    def is_head(self):
        return self.type == 2

    def is_face(self):
        return self.type == 3

    def is_neck(self):
        return self.type == 4

    def is_body(self):
        return self.type == 5

    def is_hand(self):
        return self.type == 6

    def is_feet(self):
        return self.type == 7

    def is_flag(self):
        return self.type == 8

    def is_photo(self):
        return self.type == 9

    def is_award(self):
        return self.type == 10


class PenguinItem(db.Model):
    __tablename__ = 'penguin_item'

    penguin_id = db.Column(db.ForeignKey('penguin.id', ondelete='CASCADE', onupdate='CASCADE'),
                           primary_key=True, nullable=False)
    item_id = db.Column(db.ForeignKey('item.id', ondelete='CASCADE', onupdate='CASCADE'),
                        primary_key=True, nullable=False)


class ItemCollection(AbstractDataCollection):
    __model__ = Item
    __indexby__ = 'id'
    __filterby__ = 'id'

    @cached_property
    def treasure(self):
        return { item for item in self.values() if item.treasure }

    @cached_property
    def innocent(self):
        return { item for item in self.values() if item.innocent }

    @cached_property
    def legacy_inventory(self):
        return { item for item in self.values() if item.legacy_inventory }

    @cached_property
    def vanilla_inventory(self):
        return { item for item in self.values() if item.vanilla_inventory }


class PenguinItemCollection(AbstractDataCollection):
    __model__ = PenguinItem
    __indexby__ = 'item_id'
    __filterby__ = 'penguin_id'

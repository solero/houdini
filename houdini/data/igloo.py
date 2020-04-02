from houdini.data import AbstractDataCollection, db
from functools import cached_property


class Flooring(db.Model):
    __tablename__ = 'flooring'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    cost = db.Column(db.Integer, nullable=False, server_default=db.text("0"))
    patched = db.Column(db.Boolean, nullable=False, server_default=db.text("false"))
    legacy_inventory = db.Column(db.Boolean, nullable=False, server_default=db.text("false"))
    vanilla_inventory = db.Column(db.Boolean, nullable=False, server_default=db.text("false"))


class Furniture(db.Model):
    __tablename__ = 'furniture'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    type = db.Column(db.SmallInteger, nullable=False, server_default=db.text("1"))
    sort = db.Column(db.SmallInteger, nullable=False, server_default=db.text("1"))
    cost = db.Column(db.Integer, nullable=False, server_default=db.text("0"))
    member = db.Column(db.Boolean, nullable=False, server_default=db.text("false"))
    patched = db.Column(db.Boolean, nullable=False, server_default=db.text("false"))
    legacy_inventory = db.Column(db.Boolean, nullable=False, server_default=db.text("false"))
    vanilla_inventory = db.Column(db.Boolean, nullable=False, server_default=db.text("false"))
    bait = db.Column(db.Boolean, nullable=False, server_default=db.text("false"))
    max_quantity = db.Column(db.SmallInteger, nullable=False, server_default=db.text("100"))
    innocent = db.Column(db.Boolean, nullable=False, server_default=db.text("false"))


class Igloo(db.Model):
    __tablename__ = 'igloo'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    cost = db.Column(db.SmallInteger, nullable=False, server_default=db.text("0"))
    patched = db.Column(db.Boolean, nullable=False, server_default=db.text("false"))
    legacy_inventory = db.Column(db.Boolean, nullable=False, server_default=db.text("false"))
    vanilla_inventory = db.Column(db.Boolean, nullable=False, server_default=db.text("false"))


class IglooFurniture(db.Model):
    __tablename__ = 'igloo_furniture'

    igloo_id = db.Column(db.ForeignKey('penguin_igloo_room.id', ondelete='CASCADE', onupdate='CASCADE'),
                         primary_key=True, nullable=False, index=True)
    furniture_id = db.Column(db.ForeignKey('furniture.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
                             nullable=False)
    x = db.Column(db.SmallInteger, primary_key=True, nullable=False, server_default=db.text("0"))
    y = db.Column(db.SmallInteger, primary_key=True, nullable=False, server_default=db.text("0"))
    frame = db.Column(db.SmallInteger, primary_key=True, nullable=False, server_default=db.text("0"))
    rotation = db.Column(db.SmallInteger, primary_key=True, nullable=False, server_default=db.text("0"))


class IglooLike(db.Model):
    __tablename__ = 'igloo_like'

    igloo_id = db.Column(db.ForeignKey('penguin_igloo_room.id', ondelete='CASCADE', onupdate='CASCADE'),
                         primary_key=True, nullable=False)
    player_id = db.Column(db.ForeignKey('penguin.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
                          nullable=False)
    count = db.Column(db.SmallInteger, nullable=False, server_default=db.text("1"))
    date = db.Column(db.DateTime, nullable=False, server_default=db.text("now()"))


class Location(db.Model):
    __tablename__ = 'location'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    cost = db.Column(db.Integer, nullable=False, server_default=db.text("0"))
    patched = db.Column(db.Boolean, nullable=False, server_default=db.text("false"))
    legacy_inventory = db.Column(db.Boolean, nullable=False, server_default=db.text("false"))
    vanilla_inventory = db.Column(db.Boolean, nullable=False, server_default=db.text("false"))


class PenguinIgloo(db.Model):
    __tablename__ = 'penguin_igloo'

    penguin_id = db.Column(db.ForeignKey('penguin.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
                           nullable=False)
    igloo_id = db.Column(db.ForeignKey('igloo.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
                         nullable=False)


class PenguinLocation(db.Model):
    __tablename__ = 'penguin_location'

    penguin_id = db.Column(db.ForeignKey('penguin.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
                           nullable=False)
    location_id = db.Column(db.ForeignKey('location.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
                            nullable=False)


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


class IglooCollection(AbstractDataCollection):
    __model__ = Igloo
    __indexby__ = 'id'
    __filterby__ = 'id'

    @cached_property
    def legacy_inventory(self):
        return [item for item in self.values() if item.legacy_inventory]

    @cached_property
    def vanilla_inventory(self):
        return [item for item in self.values() if item.vanilla_inventory]


class PenguinIglooCollection(AbstractDataCollection):
    __model__ = PenguinIgloo
    __indexby__ = 'igloo_id'
    __filterby__ = 'penguin_id'


class LocationCollection(AbstractDataCollection):
    __model__ = Location
    __indexby__ = 'id'
    __filterby__ = 'id'

    @cached_property
    def legacy_inventory(self):
        return [item for item in self.values() if item.legacy_inventory]

    @cached_property
    def vanilla_inventory(self):
        return [item for item in self.values() if item.vanilla_inventory]


class PenguinLocationCollection(AbstractDataCollection):
    __model__ = PenguinLocation
    __indexby__ = 'location_id'
    __filterby__ = 'penguin_id'


class FurnitureCollection(AbstractDataCollection):
    __model__ = Furniture
    __indexby__ = 'id'
    __filterby__ = 'id'

    @cached_property
    def innocent(self):
        return [item for item in self.values() if item.innocent]

    @cached_property
    def legacy_inventory(self):
        return [item for item in self.values() if item.legacy_inventory]

    @cached_property
    def vanilla_inventory(self):
        return [item for item in self.values() if item.vanilla_inventory]


class PenguinFurnitureCollection(AbstractDataCollection):
    __model__ = PenguinFurniture
    __indexby__ = 'furniture_id'
    __filterby__ = 'penguin_id'


class FlooringCollection(AbstractDataCollection):
    __model__ = Flooring
    __indexby__ = 'id'
    __filterby__ = 'id'

    @cached_property
    def legacy_inventory(self):
        return [item for item in self.values() if item.legacy_inventory]

    @cached_property
    def vanilla_inventory(self):
        return [item for item in self.values() if item.vanilla_inventory]


class PenguinFlooringCollection(AbstractDataCollection):
    __model__ = PenguinFlooring
    __indexby__ = 'flooring_id'
    __filterby__ = 'penguin_id'

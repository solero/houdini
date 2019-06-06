from houdini.data import db, BaseCrumbsCollection


class Flooring(db.Model):
    __tablename__ = 'flooring'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    cost = db.Column(db.Integer, nullable=False, server_default=db.text("0"))
    patched = db.Column(db.Boolean, nullable=False, server_default=db.text("false"))


class Furniture(db.Model):
    __tablename__ = 'furniture'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    type = db.Column(db.SmallInteger, nullable=False, server_default=db.text("1"))
    sort = db.Column(db.SmallInteger, nullable=False, server_default=db.text("1"))
    cost = db.Column(db.Integer, nullable=False, server_default=db.text("0"))
    member = db.Column(db.Boolean, nullable=False, server_default=db.text("false"))
    patched = db.Column(db.Boolean, nullable=False, server_default=db.text("false"))
    bait = db.Column(db.Boolean, nullable=False, server_default=db.text("false"))
    max_quantity = db.Column(db.SmallInteger, nullable=False, server_default=db.text("100"))


class Igloo(db.Model):
    __tablename__ = 'igloo'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    cost = db.Column(db.SmallInteger, nullable=False, server_default=db.text("0"))
    patched = db.Column(db.Boolean, nullable=False, server_default=db.text("false"))


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
    owner_id = db.Column(db.ForeignKey('penguin.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
                         nullable=False)
    player_id = db.Column(db.ForeignKey('penguin.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
                          nullable=False)
    count = db.Column(db.SmallInteger, nullable=False)
    date = db.Column(db.Date, nullable=False, server_default=db.text("now()"))


class Location(db.Model):
    __tablename__ = 'location'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    cost = db.Column(db.Integer, nullable=False, server_default=db.text("0"))
    patched = db.Column(db.Boolean, nullable=False, server_default=db.text("false"))


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


class IglooCrumbsCollection(BaseCrumbsCollection):

    def __init__(self, inventory_id=None):
        super().__init__(model=Igloo,
                         key='id',
                         inventory_model=PenguinIgloo,
                         inventory_key='penguin_id',
                         inventory_value='igloo_id',
                         inventory_id=inventory_id)


class LocationCrumbsCollection(BaseCrumbsCollection):

    def __init__(self, inventory_id=None):
        super().__init__(model=Location,
                         key='id',
                         inventory_model=PenguinLocation,
                         inventory_key='penguin_id',
                         inventory_value='location_id',
                         inventory_id=inventory_id)


class FurnitureCrumbsCollection(BaseCrumbsCollection):

    def __init__(self, inventory_id=None):
        super().__init__(model=Furniture,
                         key='id',
                         inventory_model=PenguinFurniture,
                         inventory_key='penguin_id',
                         inventory_value='furniture_id',
                         inventory_id=inventory_id)


class FlooringCrumbsCollection(BaseCrumbsCollection):

    def __init__(self, inventory_id=None):
        super().__init__(model=Flooring,
                         key='id',
                         inventory_model=PenguinFlooring,
                         inventory_key='penguin_id',
                         inventory_value='flooring_id',
                         inventory_id=inventory_id)

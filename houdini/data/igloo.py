from houdini.data import db, BaseCrumbsCollection
from houdini.data.penguin import PenguinIgloo, PenguinLocation, PenguinFurniture


class Flooring(db.Model):
    __tablename__ = 'flooring'

    ID = db.Column(db.Integer, primary_key=True)
    Name = db.Column(db.String(50))
    Cost = db.Column(db.Integer, nullable=False, server_default=db.text("0"))
    Patched = db.Column(db.Boolean, nullable=False, server_default=db.text("false"))


class Furniture(db.Model):
    __tablename__ = 'furniture'

    ID = db.Column(db.Integer, primary_key=True)
    Name = db.Column(db.String(50), nullable=False)
    Type = db.Column(db.SmallInteger, nullable=False, server_default=db.text("1"))
    Sort = db.Column(db.SmallInteger, nullable=False, server_default=db.text("1"))
    Cost = db.Column(db.Integer, nullable=False, server_default=db.text("0"))
    Member = db.Column(db.Boolean, nullable=False, server_default=db.text("false"))
    Patched = db.Column(db.Boolean, nullable=False, server_default=db.text("false"))
    Bait = db.Column(db.Boolean, nullable=False, server_default=db.text("false"))
    MaxQuantity = db.Column(db.SmallInteger, nullable=False, server_default=db.text("100"))


class Igloo(db.Model):
    __tablename__ = 'igloo'

    ID = db.Column(db.Integer, primary_key=True)
    Name = db.Column(db.String(50), nullable=False)
    Cost = db.Column(db.SmallInteger, nullable=False, server_default=db.text("0"))
    Patched = db.Column(db.Boolean, nullable=False, server_default=db.text("false"))


class IglooFurniture(db.Model):
    __tablename__ = 'igloo_furniture'

    IglooID = db.Column(db.ForeignKey('penguin_igloo_room.ID', ondelete='CASCADE', onupdate='CASCADE'),
                        primary_key=True, nullable=False, index=True)
    FurnitureID = db.Column(db.ForeignKey('furniture.ID', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
                            nullable=False)
    X = db.Column(db.SmallInteger, primary_key=True, nullable=False, server_default=db.text("0"))
    Y = db.Column(db.SmallInteger, primary_key=True, nullable=False, server_default=db.text("0"))
    Frame = db.Column(db.SmallInteger, primary_key=True, nullable=False, server_default=db.text("0"))
    Rotation = db.Column(db.SmallInteger, primary_key=True, nullable=False, server_default=db.text("0"))


class IglooLike(db.Model):
    __tablename__ = 'igloo_like'

    IglooID = db.Column(db.ForeignKey('penguin_igloo_room.ID', ondelete='CASCADE', onupdate='CASCADE'),
                        primary_key=True, nullable=False)
    OwnerID = db.Column(db.ForeignKey('penguin.ID', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
                        nullable=False)
    PlayerID = db.Column(db.ForeignKey('penguin.ID', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
                         nullable=False)
    Count = db.Column(db.SmallInteger, nullable=False)
    Date = db.Column(db.Date, nullable=False, server_default=db.text("now()"))


class Location(db.Model):
    __tablename__ = 'location'

    ID = db.Column(db.Integer, primary_key=True)
    Name = db.Column(db.String(50), nullable=False)
    Cost = db.Column(db.Integer, nullable=False, server_default=db.text("0"))
    Patched = db.Column(db.Boolean, nullable=False, server_default=db.text("false"))


class IglooCrumbsCollection(BaseCrumbsCollection):

    def __init__(self, inventory_id=None):
        super().__init__(model=Igloo, key='ID', inventory_model=PenguinIgloo,
                         inventory_id=inventory_id)


class LocationCrumbsCollection(BaseCrumbsCollection):

    def __init__(self, inventory_id=None):
        super().__init__(model=Location, key='ID', inventory_model=PenguinLocation,
                         inventory_id=inventory_id)


class FurnitureCrumbsCollection(BaseCrumbsCollection):

    def __init__(self, inventory_id=None):
        super().__init__(model=Furniture, key='ID', inventory_model=PenguinFurniture,
                         inventory_id=inventory_id)


class FlooringCrumbsCollection(BaseCrumbsCollection):

    def __init__(self):
        super().__init__(model=Flooring, key='ID')

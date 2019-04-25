from Houdini.Data import db, BaseCrumbsCollection
from Houdini.Data.Penguin import PenguinPuffle, PenguinPuffleItem


class Puffle(db.Model):
    __tablename__ = 'puffle'

    ID = db.Column(db.Integer, primary_key=True)
    ParentID = db.Column(db.ForeignKey('puffle.ID', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    Name = db.Column(db.String(50), nullable=False, server_default=db.text("''::character varying"))
    Member = db.Column(db.Boolean, nullable=False, server_default=db.text("false"))
    FavouriteFood = db.Column(db.ForeignKey('puffle_item.ID', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    RunawayPostcard = db.Column(db.ForeignKey('postcard.ID', ondelete='CASCADE', onupdate='CASCADE'))
    MaxFood = db.Column(db.SmallInteger, nullable=False, server_default=db.text("100"))
    MaxRest = db.Column(db.SmallInteger, nullable=False, server_default=db.text("100"))
    MaxClean = db.Column(db.SmallInteger, nullable=False, server_default=db.text("100"))


class PuffleItem(db.Model):
    __tablename__ = 'puffle_item'

    ID = db.Column(db.Integer, primary_key=True)
    ParentID = db.Column(db.ForeignKey('puffle_item.ID', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    Name = db.Column(db.String(50), nullable=False, server_default=db.text("''::character varying"))
    Type = db.Column(db.String(10), nullable=False, server_default=db.text("'care'::character varying"))
    PlayExternal = db.Column(db.String(10), nullable=False, server_default=db.text("'none'::character varying"))
    Cost = db.Column(db.Integer, nullable=False, server_default=db.text("0"))
    Quantity = db.Column(db.SmallInteger, nullable=False, server_default=db.text("1"))
    Member = db.Column(db.Boolean, nullable=False, server_default=db.text("false"))
    FoodEffect = db.Column(db.SmallInteger, nullable=False, server_default=db.text("0"))
    RestEffect = db.Column(db.SmallInteger, nullable=False, server_default=db.text("0"))
    PlayEffect = db.Column(db.SmallInteger, nullable=False, server_default=db.text("0"))
    CleanEffect = db.Column(db.SmallInteger, nullable=False, server_default=db.text("0"))


class PuffleTreasureFurniture(db.Model):
    __tablename__ = 'puffle_treasure_furniture'

    PuffleID = db.Column(db.ForeignKey('puffle.ID', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
                         nullable=False)
    FurnitureID = db.Column(db.ForeignKey('furniture.ID', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
                            nullable=False)


class PuffleTreasureItem(db.Model):
    __tablename__ = 'puffle_treasure_item'

    PuffleID = db.Column(db.ForeignKey('puffle.ID', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
                         nullable=False)
    ItemID = db.Column(db.ForeignKey('item.ID', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
                       nullable=False)


class PuffleTreasurePuffleItem(db.Model):
    __tablename__ = 'puffle_treasure_puffle_item'

    PuffleID = db.Column(db.ForeignKey('puffle.ID', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
                         nullable=False)
    PuffleItemID = db.Column(db.ForeignKey('puffle_item.ID', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
                             nullable=False)


class PuffleCrumbsCollection(BaseCrumbsCollection):

    def __init__(self, inventory_id=None):
        super().__init__(model=Puffle, key='ID', inventory_model=PenguinPuffle,
                         inventory_id=inventory_id)


class PuffleItemCrumbsCollection(BaseCrumbsCollection):

    def __init__(self, inventory_id=None):
        super().__init__(model=PuffleItem, key='ID', inventory_model=PenguinPuffleItem,
                         inventory_id=inventory_id)

from Houdini.Data import db, BaseCrumbsCollection
from Houdini.Data.Penguin import PenguinStamp


class Stamp(db.Model):
    __tablename__ = 'stamp'

    ID = db.Column(db.Integer, primary_key=True)
    Name = db.Column(db.String(50), nullable=False)
    GroupID = db.Column(db.ForeignKey('stamp_group.ID', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    Member = db.Column(db.Boolean, nullable=False, server_default=db.text("false"))
    Rank = db.Column(db.SmallInteger, nullable=False, server_default=db.text("1"))
    Description = db.Column(db.String(255), nullable=False, server_default=db.text("''::character varying"))


class StampGroup(db.Model):
    __tablename__ = 'stamp_group'

    ID = db.Column(db.Integer, primary_key=True)
    Name = db.Column(db.String(50), nullable=False)
    ParentID = db.Column(db.ForeignKey('stamp_group.ID', ondelete='CASCADE', onupdate='CASCADE'))


class CoverStamp(db.Model):
    __tablename__ = 'cover_stamp'

    PenguinID = db.Column(db.ForeignKey('penguin.ID', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
                          nullable=False)
    StampID = db.Column(db.ForeignKey('stamp.ID', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
                        nullable=False)
    ItemID = db.Column(db.ForeignKey('item.ID', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    X = db.Column(db.SmallInteger, nullable=False, server_default=db.text("0"))
    Y = db.Column(db.SmallInteger, nullable=False, server_default=db.text("0"))
    Type = db.Column(db.SmallInteger, nullable=False, server_default=db.text("0"))
    Rotation = db.Column(db.SmallInteger, nullable=False, server_default=db.text("0"))
    Depth = db.Column(db.SmallInteger, nullable=False, server_default=db.text("0"))


class StampCrumbsCollection(BaseCrumbsCollection):

    def __init__(self, inventory_id=None):
        super().__init__(model=Stamp, key='ID', inventory_model=PenguinStamp,
                         inventory_id=inventory_id)

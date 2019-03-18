from Houdini.Data import db


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


t_puffle_treasure_furniture = db.Table(
    'puffle_treasure_furniture', db,
    db.Column('PuffleID', db.ForeignKey('puffle.ID', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
              nullable=False),
    db.Column('FurnitureID', db.ForeignKey('furniture.ID', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
              nullable=False)
)


t_puffle_treasure_item = db.Table(
    'puffle_treasure_item', db,
    db.Column('PuffleID', db.ForeignKey('puffle.ID', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
              nullable=False),
    db.Column('ItemID', db.ForeignKey('item.ID', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
              nullable=False)
)


t_puffle_treasure_puffle_item = db.Table(
    'puffle_treasure_puffle_item', db,
    db.Column('PuffleID', db.ForeignKey('puffle.ID', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
              nullable=False),
    db.Column('PuffleItemID', db.ForeignKey('puffle_item.ID', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
              nullable=False)
)
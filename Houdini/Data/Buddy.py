from Houdini.Data import db


class BuddyList(db.Model):
    __tablename__ = 'buddy_list'

    PenguinID = db.Column(db.ForeignKey('penguin.ID', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
                          nullable=False)
    BuddyID = db.Column(db.ForeignKey('penguin.ID', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
                        nullable=False, index=True)
    BestBuddy = db.Column(db.Boolean, nullable=False, server_default=db.text("false"))


t_buddy_request = db.Table(
    'buddy_request', db,
    db.Column('PenguinID', db.ForeignKey('penguin.ID', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
              nullable=False),
    db.Column('RequesterID', db.ForeignKey('penguin.ID', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
              nullable=False)
)


t_ignore_list = db.Table(
    'ignore_list', db,
    db.Column('PenguinID', db.ForeignKey('penguin.ID', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
              nullable=False),
    db.Column('IgnoreID', db.ForeignKey('penguin.ID', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
              nullable=False, index=True)
)


class Character(db.Model):
    __tablename__ = 'character'

    ID = db.Column(db.Integer, primary_key=True)
    Name = db.Column(db.String(30), nullable=False)
    GiftID = db.Column(db.ForeignKey('item.ID', ondelete='CASCADE', onupdate='CASCADE'))
    StampID = db.Column(db.ForeignKey('stamp.ID', ondelete='CASCADE', onupdate='CASCADE'))


t_character_buddy = db.Table(
    'character_buddy', db,
    db.Column('PenguinID', db.ForeignKey('penguin.ID', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
              nullable=False),
    db.Column('CharacterID', db.ForeignKey('character.ID', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
              nullable=False)
)
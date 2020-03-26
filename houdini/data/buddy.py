from houdini.data import AbstractDataCollection, db


class BuddyList(db.Model):
    __tablename__ = 'buddy_list'

    penguin_id = db.Column(db.ForeignKey('penguin.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
                           nullable=False)
    buddy_id = db.Column(db.ForeignKey('penguin.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
                         nullable=False, index=True)
    best_buddy = db.Column(db.Boolean, nullable=False, server_default=db.text("false"))


class BuddyRequest(db.Model):
    __tablename__ = 'buddy_request'
    penguin_id = db.Column(db.ForeignKey('penguin.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
                           nullable=False)
    requester_id = db.Column(db.ForeignKey('penguin.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
                             nullable=False)


class IgnoreList(db.Model):
    __tablename__ = 'ignore_list'
    penguin_id = db.Column(db.ForeignKey('penguin.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
                           nullable=False)
    ignore_id = db.Column(db.ForeignKey('penguin.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
                          nullable=False, index=True)


class Character(db.Model):
    __tablename__ = 'character'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), nullable=False)
    gift_id = db.Column(db.ForeignKey('item.id', ondelete='CASCADE', onupdate='CASCADE'))
    stamp_id = db.Column(db.ForeignKey('stamp.id', ondelete='CASCADE', onupdate='CASCADE'))


class CharacterBuddy(db.Model):
    __tablename__ = 'character_buddy'
    penguin_id = db.Column(db.ForeignKey('penguin.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
                           nullable=False)
    character_id = db.Column(db.ForeignKey('character.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
                             nullable=False)
    best_buddy = db.Column(db.Boolean, nullable=False, server_default=db.text("false"))


class BuddyListCollection(AbstractDataCollection):
    __model__ = BuddyList
    __filterby__ = 'penguin_id'
    __indexby__ = 'buddy_id'


class IgnoreListCollection(AbstractDataCollection):
    __model__ = IgnoreList
    __filterby__ = 'penguin_id'
    __indexby__ = 'ignore_id'


class BuddyRequestCollection(AbstractDataCollection):
    __model__ = BuddyRequest
    __filterby__ = 'penguin_id'
    __indexby__ = 'requester_id'


class CharacterCollection(AbstractDataCollection):
    __model__ = Character
    __filterby__ = 'id'
    __indexby__ = 'id'


class CharacterBuddyCollection(AbstractDataCollection):
    __model__ = CharacterBuddy
    __filterby__ = 'penguin_id'
    __indexby__ = 'character_id'

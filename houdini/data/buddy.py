from houdini.data import db, BaseCrumbsCollection


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


class BuddyListCollection(BaseCrumbsCollection):

    def __init__(self, inventory_id=None):
        super().__init__(model=BuddyList,
                         key='buddy_id',
                         inventory_model=BuddyList,
                         inventory_key='penguin_id',
                         inventory_value='buddy_id',
                         inventory_id=inventory_id)


class IgnoreListCollection(BaseCrumbsCollection):

    def __init__(self, inventory_id=None):
        super().__init__(model=IgnoreList,
                         key='ignore_id',
                         inventory_model=IgnoreList,
                         inventory_key='penguin_id',
                         inventory_value='ignore_id',
                         inventory_id=inventory_id)


class BuddyRequestCollection(BaseCrumbsCollection):

    def __init__(self, inventory_id=None):
        super().__init__(model=BuddyRequest,
                         key='requester_id',
                         inventory_model=BuddyRequest,
                         inventory_key='penguin_id',
                         inventory_value='requester_id',
                         inventory_id=inventory_id)


class CharacterCrumbsCollection(BaseCrumbsCollection):

    def __init__(self):
        super().__init__(model=Character, key='id')


class CharacterBuddyCollection(BaseCrumbsCollection):

    def __init__(self, inventory_id=None):
        super().__init__(model=CharacterBuddy,
                         key='character_id',
                         inventory_model=CharacterBuddy,
                         inventory_key='penguin_id',
                         inventory_value='character_id',
                         inventory_id=inventory_id)
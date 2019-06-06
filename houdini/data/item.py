from houdini.data import db, BaseCrumbsCollection


class Item(db.Model):
    __tablename__ = 'item'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    type = db.Column(db.SmallInteger, nullable=False, server_default=db.text("1"))
    cost = db.Column(db.Integer, nullable=False, server_default=db.text("0"))
    member = db.Column(db.Boolean, nullable=False, server_default=db.text("false"))
    bait = db.Column(db.Boolean, nullable=False, server_default=db.text("false"))
    patched = db.Column(db.Boolean, nullable=False, server_default=db.text("false"))
    epf = db.Column(db.Boolean, nullable=False, server_default=db.text("false"))
    tour = db.Column(db.Boolean, nullable=False, server_default=db.text("false"))
    release_date = db.Column(db.Date, nullable=False, server_default=db.text("now()"))


class PenguinItem(db.Model):
    __tablename__ = 'penguin_item'

    penguin_id = db.Column(db.ForeignKey('penguin.id', ondelete='CASCADE', onupdate='CASCADE'),
                           primary_key=True, nullable=False)
    item_id = db.Column(db.ForeignKey('item.id', ondelete='CASCADE', onupdate='CASCADE'),
                        primary_key=True, nullable=False)


class ItemCrumbsCollection(BaseCrumbsCollection):

    def __init__(self, inventory_id=None):
        super().__init__(model=Item,
                         key='id',
                         inventory_model=PenguinItem,
                         inventory_key='penguin_id',
                         inventory_value='item_id',
                         inventory_id=inventory_id)

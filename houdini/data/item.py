from houdini.data import db, BaseCrumbsCollection
from houdini.data.penguin import PenguinItem


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


class ItemCrumbsCollection(BaseCrumbsCollection):

    def __init__(self, inventory_id=None):
        super().__init__(model=Item, key='ID', inventory_model=PenguinItem,
                         inventory_id=inventory_id)

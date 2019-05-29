from houdini.data import db, BaseCrumbsCollection
from houdini.data.penguin import PenguinPostcard


class Postcard(db.Model):
    __tablename__ = 'postcard'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    cost = db.Column(db.Integer, nullable=False, server_default=db.text("10"))
    enabled = db.Column(db.Boolean, nullable=False, server_default=db.text("false"))


class PostcardCrumbsCollection(BaseCrumbsCollection):

    def __init__(self, inventory_id=None):
        super().__init__(model=Postcard,
                         key='id',
                         inventory_model=PenguinPostcard,
                         inventory_key='recipient_id',
                         inventory_value='postcard_id',
                         inventory_id=inventory_id)

from houdini.data import db, BaseCrumbsCollection
from houdini.data.penguin import PenguinPostcard


class Postcard(db.Model):
    __tablename__ = 'postcard'

    ID = db.Column(db.Integer, primary_key=True)
    Name = db.Column(db.String(50), nullable=False)
    Cost = db.Column(db.Integer, nullable=False, server_default=db.text("10"))
    Enabled = db.Column(db.Boolean, nullable=False, server_default=db.text("false"))


class PostcardCrumbsCollection(BaseCrumbsCollection):

    def __init__(self, inventory_id=None):
        super().__init__(model=Postcard, key='ID', inventory_model=PenguinPostcard,
                         inventory_id=inventory_id)

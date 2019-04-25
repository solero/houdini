from Houdini.Data import db, BaseCrumbsCollection
from Houdini.Data.Penguin import PenguinCard


class Card(db.Model):
    __tablename__ = 'card'

    ID = db.Column(db.Integer, primary_key=True)
    Name = db.Column(db.String(50), nullable=False)
    SetID = db.Column(db.SmallInteger, nullable=False, server_default=db.text("1"))
    PowerID = db.Column(db.SmallInteger, nullable=False, server_default=db.text("0"))
    Element = db.Column(db.CHAR(1), nullable=False, server_default=db.text("'s'::bpchar"))
    Color = db.Column(db.CHAR(1), nullable=False, server_default=db.text("'b'::bpchar"))
    Value = db.Column(db.SmallInteger, nullable=False, server_default=db.text("2"))
    Description = db.Column(db.String(255), nullable=False, server_default=db.text("''::character varying"))


class CardCrumbsCollection(BaseCrumbsCollection):

    def __init__(self, inventory_id=None):
        super().__init__(model=Card, key='ID', inventory_model=PenguinCard,
                         inventory_id=inventory_id)

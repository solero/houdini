from houdini.data import db, BaseCrumbsCollection


class Card(db.Model):
    __tablename__ = 'card'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    set_id = db.Column(db.SmallInteger, nullable=False, server_default=db.text("1"))
    power_id = db.Column(db.SmallInteger, nullable=False, server_default=db.text("0"))
    element = db.Column(db.CHAR(1), nullable=False, server_default=db.text("'s'::bpchar"))
    color = db.Column(db.CHAR(1), nullable=False, server_default=db.text("'b'::bpchar"))
    value = db.Column(db.SmallInteger, nullable=False, server_default=db.text("2"))
    description = db.Column(db.String(255), nullable=False, server_default=db.text("''::character varying"))


class PenguinCard(db.Model):
    __tablename__ = 'penguin_card'

    penguin_id = db.Column(db.ForeignKey('penguin.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
                           nullable=False, index=True)
    card_id = db.Column(db.ForeignKey('card.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
                        nullable=False)
    quantity = db.Column(db.SmallInteger, nullable=False, server_default=db.text("1"))


class CardCrumbsCollection(BaseCrumbsCollection):

    def __init__(self, inventory_id=None):
        super().__init__(model=Card,
                         key='id',
                         inventory_key='penguin_id',
                         inventory_value='card_id',
                         inventory_model=PenguinCard,
                         inventory_id=inventory_id)

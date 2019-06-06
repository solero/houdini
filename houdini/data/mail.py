from houdini.data import db, BaseCrumbsCollection


class Postcard(db.Model):
    __tablename__ = 'postcard'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    cost = db.Column(db.Integer, nullable=False, server_default=db.text("10"))
    enabled = db.Column(db.Boolean, nullable=False, server_default=db.text("false"))


class PenguinPostcard(db.Model):
    __tablename__ = 'penguin_postcard'

    id = db.Column(db.Integer, primary_key=True,
                   server_default=db.text("nextval('\"penguin_postcard_id_seq\"'::regclass)"))
    penguin_id = db.Column(db.ForeignKey('penguin.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False,
                           index=True)
    sender_id = db.Column(db.ForeignKey('penguin.id', ondelete='CASCADE', onupdate='CASCADE'), index=True)
    postcard_id = db.Column(db.ForeignKey('postcard.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    send_date = db.Column(db.DateTime, nullable=False, server_default=db.text("now()"))
    details = db.Column(db.String(255), nullable=False, server_default=db.text("''::character varying"))
    has_read = db.Column(db.Boolean, nullable=False, server_default=db.text("false"))


class PostcardCrumbsCollection(BaseCrumbsCollection):

    def __init__(self, inventory_id=None):
        super().__init__(model=Postcard,
                         key='id',
                         inventory_model=PenguinPostcard,
                         inventory_key='penguin_id',
                         inventory_value='id',
                         inventory_id=inventory_id)

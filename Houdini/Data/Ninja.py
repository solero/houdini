from Houdini.Data import db


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

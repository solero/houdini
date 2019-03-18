from Houdini.Data import db


class Postcard(db.Model):
    __tablename__ = 'postcard'

    ID = db.Column(db.Integer, primary_key=True)
    Name = db.Column(db.String(50), nullable=False)
    Cost = db.Column(db.Integer, nullable=False, server_default=db.text("10"))
    Enabled = db.Column(db.Boolean, nullable=False, server_default=db.text("false"))



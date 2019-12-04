from houdini.data import db


class PenguinGameData(db.Model):
    __tablename__ = 'penguin_game_data'

    penguin_id = db.Column(db.ForeignKey('penguin.id', ondelete='RESTRICT', onupdate='CASCADE'), primary_key=True,
                           nullable=False)
    room_id = db.Column(db.ForeignKey('room.id', ondelete='RESTRICT', onupdate='CASCADE'), primary_key=True,
                        nullable=False, index=True)
    index = db.Column(db.Integer, primary_key=True, index=True)
    data = db.Column(db.Text, nullable=False, server_default=db.text("''"))

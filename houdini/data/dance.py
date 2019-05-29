from houdini.data import db


class DanceSong(db.Model):
    __tablename__ = 'dance_song'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), nullable=False)
    song_length = db.Column(db.Integer, nullable=False, server_default=db.text("100000"))
    millis_per_bar = db.Column(db.Integer, nullable=False, server_default=db.text("2000"))

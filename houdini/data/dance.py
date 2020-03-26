from houdini.data import AbstractDataCollection, db


class DanceSong(db.Model):
    __tablename__ = 'dance_song'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), nullable=False)
    song_length_millis = db.Column(db.Integer, nullable=False)
    song_length = db.Column(db.Integer, nullable=False)
    millis_per_bar = db.Column(db.Integer, nullable=False)


class DanceSongCollection(AbstractDataCollection):
    __model__ = DanceSong
    __indexby__ = 'id'
    __filterby__ = 'id'

from houdini.data import db


class DanceSong(db.Model):
    __tablename__ = 'dance_song'

    ID = db.Column(db.Integer, primary_key=True)
    Name = db.Column(db.String(30), nullable=False)
    SongLength = db.Column(db.Integer, nullable=False, server_default=db.text("100000"))
    MillisPerBar = db.Column(db.Integer, nullable=False, server_default=db.text("2000"))

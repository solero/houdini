from houdini.data import db


class PenguinTrack(db.Model):
    __tablename__ = 'penguin_track'

    id = db.Column(db.Integer, primary_key=True,
                   server_default=db.text("nextval('\"penguin_track_id_seq\"'::regclass)"))
    name = db.Column(db.String(12), nullable=False, server_default=db.text("''::character varying"))
    owner_id = db.Column(db.ForeignKey('penguin.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    sharing = db.Column(db.Boolean, nullable=False, server_default=db.text("false"))
    pattern = db.Column(db.Text, nullable=False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._likes = 0

    @property
    def likes(self):
        return self._likes

    @likes.setter
    def likes(self, like_count):
        self._likes = like_count


class TrackLike(db.Model):
    __tablename__ = 'track_like'

    penguin_id = db.Column(db.ForeignKey('penguin.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
                           nullable=False)
    track_id = db.Column(db.ForeignKey('penguin_track.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
                         nullable=False, index=True)
    date = db.Column(db.DateTime, primary_key=True, nullable=False, server_default=db.text("now()"))

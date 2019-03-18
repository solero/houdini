from Houdini.Data import db


class PenguinTrack(db.Model):
    __tablename__ = 'penguin_track'

    ID = db.Column(db.Integer, primary_key=True,
                   server_default=db.text("nextval('\"penguin_track_ID_seq\"'::regclass)"))
    Name = db.Column(db.String(12), nullable=False, server_default=db.text("''::character varying"))
    OwnerID = db.Column(db.ForeignKey('penguin.ID', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    Sharing = db.Column(db.Boolean, nullable=False, server_default=db.text("false"))
    Pattern = db.Column(db.Text, nullable=False)


class TrackLike(db.Model):
    __tablename__ = 'track_like'

    PenguinID = db.Column(db.ForeignKey('penguin.ID', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
                          nullable=False)
    TrackID = db.Column(db.ForeignKey('penguin_track.ID', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
                        nullable=False, index=True)
    Date = db.Column(db.DateTime, primary_key=True, nullable=False)
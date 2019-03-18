from Houdini.Data import db


class Ban(db.Model):
    __tablename__ = 'ban'

    PenguinID = db.Column(db.ForeignKey('penguin.ID', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
                          nullable=False)
    Issued = db.Column(db.DateTime, primary_key=True, nullable=False, server_default=db.text("now()"))
    Expires = db.Column(db.DateTime, primary_key=True, nullable=False, server_default=db.text("now()"))
    ModeratorID = db.Column(db.ForeignKey('penguin.ID', ondelete='CASCADE', onupdate='CASCADE'), index=True)
    Reason = db.Column(db.SmallInteger, nullable=False)
    Comment = db.Column(db.Text)


class Warning(db.Model):
    __tablename__ = 'warning'

    PenguinID = db.Column(db.ForeignKey('penguin.ID', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
                          nullable=False)
    Issued = db.Column(db.DateTime, primary_key=True, nullable=False)
    Expires = db.Column(db.DateTime, primary_key=True, nullable=False)
    Type = db.Column(db.SmallInteger, nullable=False)
    Comment = db.Column(db.Text, nullable=False)


class Report(db.Model):
    __tablename__ = 'report'

    ID = db.Column(db.Integer, primary_key=True, server_default=db.text("nextval('\"report_ID_seq\"'::regclass)"))
    PenguinID = db.Column(db.ForeignKey('penguin.ID', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    ReporterID = db.Column(db.ForeignKey('penguin.ID', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    ReportType = db.Column(db.SmallInteger, nullable=False, server_default=db.text("0"))
    Date = db.Column(db.DateTime, nullable=False, server_default=db.text("now()"))
    ServerID = db.Column(db.Integer, nullable=False)
    RoomID = db.Column(db.ForeignKey('room.ID', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)


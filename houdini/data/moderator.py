from houdini.data import db


class Ban(db.Model):
    __tablename__ = 'ban'

    penguin_id = db.Column(db.ForeignKey('penguin.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
                           nullable=False)
    issued = db.Column(db.DateTime, primary_key=True, nullable=False, server_default=db.text("now()"))
    expires = db.Column(db.DateTime, primary_key=True, nullable=False, server_default=db.text("now()"))
    moderator_id = db.Column(db.ForeignKey('penguin.id', ondelete='CASCADE', onupdate='CASCADE'), index=True)
    reason = db.Column(db.SmallInteger, nullable=False)
    comment = db.Column(db.Text)


class Warning(db.Model):
    __tablename__ = 'warning'

    penguin_id = db.Column(db.ForeignKey('penguin.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
                           nullable=False)
    issued = db.Column(db.DateTime, primary_key=True, nullable=False)
    expires = db.Column(db.DateTime, primary_key=True, nullable=False)
    type = db.Column(db.SmallInteger, nullable=False)
    comment = db.Column(db.Text, nullable=False)


class Report(db.Model):
    __tablename__ = 'report'

    id = db.Column(db.Integer, primary_key=True, server_default=db.text("nextval('\"report_ID_seq\"'::regclass)"))
    penguin_id = db.Column(db.ForeignKey('penguin.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    reporter_id = db.Column(db.ForeignKey('penguin.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    report_type = db.Column(db.SmallInteger, nullable=False, server_default=db.text("0"))
    date = db.Column(db.DateTime, nullable=False, server_default=db.text("now()"))
    server_id = db.Column(db.Integer, nullable=False)
    room_id = db.Column(db.ForeignKey('room.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)


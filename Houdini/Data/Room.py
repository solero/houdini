from Houdini.Data import db


class Room(db.Model):
    __tablename__ = 'room'

    ID = db.Column(db.Integer, primary_key=True)
    InternalID = db.Column(db.Integer, nullable=False, unique=True,
                           server_default=db.text("nextval('\"room_InternalID_seq\"'::regclass)"))
    Name = db.Column(db.String(50), nullable=False)
    Member = db.Column(db.Boolean, nullable=False, server_default=db.text("false"))
    MaxUsers = db.Column(db.SmallInteger, nullable=False, server_default=db.text("80"))
    RequiredItem = db.Column(db.ForeignKey('item.ID', ondelete='CASCADE', onupdate='CASCADE'))
    Game = db.Column(db.Boolean, nullable=False, server_default=db.text("false"))
    Blackhole = db.Column(db.Boolean, nullable=False, server_default=db.text("false"))
    Spawn = db.Column(db.Boolean, nullable=False, server_default=db.text("false"))
    StampGroup = db.Column(db.ForeignKey('stamp_group.ID', ondelete='CASCADE', onupdate='CASCADE'))


class RoomTable(db.Model):
    __tablename__ = 'room_table'

    ID = db.Column(db.Integer, primary_key=True, nullable=False)
    RoomID = db.Column(db.ForeignKey('room.ID', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
                       nullable=False)
    Game = db.Column(db.String(20), nullable=False)


class RoomWaddle(db.Model):
    __tablename__ = 'room_waddle'

    ID = db.Column(db.Integer, primary_key=True, nullable=False)
    RoomID = db.Column(db.ForeignKey('room.ID', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
                       nullable=False)
    Seats = db.Column(db.SmallInteger, nullable=False, server_default=db.text("2"))
    Game = db.Column(db.String(20), nullable=False)

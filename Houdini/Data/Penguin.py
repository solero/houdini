from Houdini.Data import db


class Penguin(db.Model):
    __tablename__ = 'penguin'

    ID = db.Column(db.Integer, primary_key=True, server_default=db.text("nextval('\"penguin_ID_seq\"'::regclass)"))
    Username = db.Column(db.String(12), nullable=False, unique=True)
    Nickname = db.Column(db.String(30), nullable=False)
    Password = db.Column(db.CHAR(255), nullable=False)
    Email = db.Column(db.String(255), nullable=False, index=True)
    RegistrationDate = db.Column(db.DateTime, nullable=False, server_default=db.text("now()"))
    Active = db.Column(db.Boolean, nullable=False, server_default=db.text("false"))
    SafeChat = db.Column(db.Boolean, nullable=False, server_default=db.text("false"))
    LastPaycheck = db.Column(db.DateTime, nullable=False, server_default=db.text("now()"))
    MinutesPlayed = db.Column(db.Integer, nullable=False, server_default=db.text("0"))
    Moderator = db.Column(db.Boolean, nullable=False, server_default=db.text("false"))
    Character = db.Column(db.ForeignKey('character.ID', ondelete='CASCADE', onupdate='CASCADE'))
    Igloo = db.Column(db.ForeignKey('penguin_igloo_room.ID', ondelete='CASCADE', onupdate='CASCADE'))
    Coins = db.Column(db.Integer, nullable=False, server_default=db.text("500"))
    Color = db.Column(db.ForeignKey('item.ID', ondelete='CASCADE', onupdate='CASCADE'))
    Head = db.Column(db.ForeignKey('item.ID', ondelete='CASCADE', onupdate='CASCADE'))
    Face = db.Column(db.ForeignKey('item.ID', ondelete='CASCADE', onupdate='CASCADE'))
    Neck = db.Column(db.ForeignKey('item.ID', ondelete='CASCADE', onupdate='CASCADE'))
    Body = db.Column(db.ForeignKey('item.ID', ondelete='CASCADE', onupdate='CASCADE'))
    Hand = db.Column(db.ForeignKey('item.ID', ondelete='CASCADE', onupdate='CASCADE'))
    Feet = db.Column(db.ForeignKey('item.ID', ondelete='CASCADE', onupdate='CASCADE'))
    Photo = db.Column(db.ForeignKey('item.ID', ondelete='CASCADE', onupdate='CASCADE'))
    Flag = db.Column(db.ForeignKey('item.ID', ondelete='CASCADE', onupdate='CASCADE'))
    Permaban = db.Column(db.SmallInteger, nullable=False, server_default=db.text("0"))
    BookModified = db.Column(db.SmallInteger, nullable=False, server_default=db.text("0"))
    BookColor = db.Column(db.SmallInteger, nullable=False, server_default=db.text("1"))
    BookHighlight = db.Column(db.SmallInteger, nullable=False, server_default=db.text("1"))
    BookPattern = db.Column(db.SmallInteger, nullable=False, server_default=db.text("0"))
    BookIcon = db.Column(db.SmallInteger, nullable=False, server_default=db.text("1"))
    AgentStatus = db.Column(db.Boolean, nullable=False, server_default=db.text("false"))
    FieldOpStatus = db.Column(db.SmallInteger, nullable=False, server_default=db.text("0"))
    CareerMedals = db.Column(db.Integer, nullable=False, server_default=db.text("0"))
    AgentMedals = db.Column(db.Integer, nullable=False, server_default=db.text("0"))
    LastFieldOp = db.Column(db.DateTime, nullable=False, server_default=db.text("now()"))
    NinjaRank = db.Column(db.SmallInteger, nullable=False, server_default=db.text("0"))
    NinjaProgress = db.Column(db.SmallInteger, nullable=False, server_default=db.text("0"))
    FireNinjaRank = db.Column(db.SmallInteger, nullable=False, server_default=db.text("0"))
    FireNinjaProgress = db.Column(db.SmallInteger, nullable=False, server_default=db.text("0"))
    WaterNinjaRank = db.Column(db.SmallInteger, nullable=False, server_default=db.text("0"))
    WaterNinjaProgress = db.Column(db.SmallInteger, nullable=False, server_default=db.text("0"))
    NinjaMatchesWon = db.Column(db.Integer, nullable=False, server_default=db.text("0"))
    FireMatchesWon = db.Column(db.Integer, nullable=False, server_default=db.text("0"))
    WaterMatchesWon = db.Column(db.Integer, nullable=False, server_default=db.text("0"))
    RainbowAdoptability = db.Column(db.SmallInteger, nullable=False, server_default=db.text("0"))
    HasDug = db.Column(db.Boolean, nullable=False, server_default=db.text("false"))
    Nuggets = db.Column(db.SmallInteger, nullable=False, server_default=db.text("0"))
    TimerActive = db.Column(db.Boolean, nullable=False, server_default=db.text("false"))
    TimerStart = db.Column(db.Time, nullable=False, server_default=db.text("'00:00:00'::time without time zone"))
    TimerEnd = db.Column(db.Time, nullable=False, server_default=db.text("'23:59:59'::time without time zone"))
    ApprovalEn = db.Column(db.Boolean, nullable=False, server_default=db.text("false"))
    ApprovalPt = db.Column(db.Boolean, nullable=False, server_default=db.text("false"))
    ApprovalFr = db.Column(db.Boolean, nullable=False, server_default=db.text("false"))
    ApprovalEs = db.Column(db.Boolean, nullable=False, server_default=db.text("false"))
    ApprovalDe = db.Column(db.Boolean, nullable=False, server_default=db.text("false"))
    ApprovalRu = db.Column(db.Boolean, nullable=False, server_default=db.text("false"))
    RejectionEn = db.Column(db.Boolean, nullable=False, server_default=db.text("false"))
    RejectionPt = db.Column(db.Boolean, nullable=False, server_default=db.text("false"))
    RejectionFr = db.Column(db.Boolean, nullable=False, server_default=db.text("false"))
    RejectionEs = db.Column(db.Boolean, nullable=False, server_default=db.text("false"))
    RejectionDe = db.Column(db.Boolean, nullable=False, server_default=db.text("false"))
    RejectionRu = db.Column(db.Boolean, nullable=False, server_default=db.text("false"))


class ActivationKey(db.Model):
    __tablename__ = 'activation_key'

    PenguinID = db.Column(db.ForeignKey('penguin.ID', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
                          nullable=False)
    ActivationKey = db.Column(db.CHAR(255), primary_key=True, nullable=False)


class PuffleQuest(db.Model):
    __tablename__ = 'puffle_quest'

    PenguinID = db.Column(db.ForeignKey('penguin.ID', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
                          nullable=False)
    TaskID = db.Column(db.SmallInteger, primary_key=True, nullable=False)
    CompletionDate = db.Column(db.DateTime)
    ItemCollected = db.Column(db.Boolean, nullable=False, server_default=db.text("false"))
    CoinsCollected = db.Column(db.Boolean, nullable=False, server_default=db.text("false"))


t_penguin_igloo = db.Table(
    'penguin_igloo', db,
    db.Column('PenguinID', db.ForeignKey('penguin.ID', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
              nullable=False),
    db.Column('IglooID', db.ForeignKey('igloo.ID', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
              nullable=False)
)


t_penguin_item = db.Table(
    'penguin_item', db,
    db.Column('PenguinID', db.ForeignKey('penguin.ID', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
              nullable=False),
    db.Column('ItemID', db.ForeignKey('item.ID', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
              nullable=False)
)


t_penguin_location = db.Table(
    'penguin_location', db,
    db.Column('PenguinID', db.ForeignKey('penguin.ID', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
              nullable=False),
    db.Column('LocationID', db.ForeignKey('location.ID', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
              nullable=False)
)


class PenguinStamp(db.Model):
    __tablename__ = 'penguin_stamp'

    PenguinID = db.Column(db.ForeignKey('penguin.ID', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
                          nullable=False)
    StampID = db.Column(db.ForeignKey('stamp.ID', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
                        nullable=False)
    Recent = db.Column(db.Boolean, nullable=False, server_default=db.text("true"))


class PenguinRedemption(db.Model):
    __tablename__ = 'penguin_redemption'

    PenguinID = db.Column(db.ForeignKey('penguin.ID', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
                          nullable=False)
    CodeID = db.Column(db.ForeignKey('redemption_code.ID', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
                       nullable=False, index=True)
    BookID = db.Column(db.ForeignKey('redemption_book.ID', ondelete='CASCADE', onupdate='CASCADE'), index=True)


class PenguinMembership(db.Model):
    __tablename__ = 'penguin_membership'

    PenguinID = db.Column(db.ForeignKey('penguin.ID', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
                          nullable=False)
    Start = db.Column(db.DateTime, primary_key=True, nullable=False)
    End = db.Column(db.DateTime, primary_key=True, nullable=False)


class PenguinPostcard(db.Model):
    __tablename__ = 'penguin_postcard'

    ID = db.Column(db.Integer, primary_key=True,
                   server_default=db.text("nextval('\"penguin_postcard_ID_seq\"'::regclass)"))
    SenderID = db.Column(db.ForeignKey('penguin.ID', ondelete='CASCADE', onupdate='CASCADE'), index=True)
    RecipientID = db.Column(db.ForeignKey('penguin.ID', ondelete='CASCADE', onupdate='CASCADE'), nullable=False,
                            index=True)
    PostcardID = db.Column(db.ForeignKey('postcard.ID', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    SendDate = db.Column(db.DateTime, nullable=False, server_default=db.text("now()"))
    Details = db.Column(db.String(255), nullable=False, server_default=db.text("''::character varying"))
    HasRead = db.Column(db.Boolean, nullable=False, server_default=db.text("false"))


class PenguinIglooRoom(db.Model):
    __tablename__ = 'penguin_igloo_room'

    ID = db.Column(db.Integer, primary_key=True,
                   server_default=db.text("nextval('\"penguin_igloo_room_ID_seq\"'::regclass)"))
    PenguinID = db.Column(db.ForeignKey('penguin.ID', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    Type = db.Column(db.ForeignKey('igloo.ID', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    Flooring = db.Column(db.ForeignKey('flooring.ID', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    Music = db.Column(db.SmallInteger, nullable=False, server_default=db.text("0"))
    Location = db.Column(db.ForeignKey('location.ID', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    Locked = db.Column(db.Boolean, nullable=False, server_default=db.text("false"))


class PenguinLaunchGame(db.Model):
    __tablename__ = 'penguin_launch_game'

    PenguinID = db.Column(db.ForeignKey('penguin.ID', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
                          nullable=False)
    Level = db.Column(db.SmallInteger, primary_key=True, nullable=False, server_default=db.text("0"))
    PuffleOs = db.Column(db.SmallInteger, nullable=False, server_default=db.text("0"))
    BestTime = db.Column(db.SmallInteger, nullable=False, server_default=db.text("600"))
    Turbo = db.Column(db.Boolean, nullable=False, server_default=db.text("false"))


class PenguinCard(db.Model):
    __tablename__ = 'penguin_card'

    PenguinID = db.Column(db.ForeignKey('penguin.ID', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
                          nullable=False, index=True)
    CardID = db.Column(db.ForeignKey('card.ID', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
                       nullable=False)
    Quantity = db.Column(db.SmallInteger, nullable=False, server_default=db.text("1"))


class PenguinFurniture(db.Model):
    __tablename__ = 'penguin_furniture'

    PenguinID = db.Column(db.ForeignKey('penguin.ID', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
                          nullable=False)
    FurnitureID = db.Column(db.ForeignKey('furniture.ID', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
                            nullable=False)
    Quantity = db.Column(db.SmallInteger, nullable=False, server_default=db.text("1"))


class PenguinPuffle(db.Model):
    __tablename__ = 'penguin_puffle'

    ID = db.Column(db.Integer, primary_key=True,
                   server_default=db.text("nextval('\"penguin_puffle_ID_seq\"'::regclass)"))
    PenguinID = db.Column(db.ForeignKey('penguin.ID', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    Name = db.Column(db.String(16), nullable=False)
    AdoptionDate = db.Column(db.DateTime, nullable=False, server_default=db.text("now()"))
    Type = db.Column(db.ForeignKey('puffle.ID', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    Food = db.Column(db.SmallInteger, nullable=False, server_default=db.text("100"))
    Play = db.Column(db.SmallInteger, nullable=False, server_default=db.text("100"))
    Rest = db.Column(db.SmallInteger, nullable=False, server_default=db.text("100"))
    Clean = db.Column(db.SmallInteger, nullable=False, server_default=db.text("100"))
    Walking = db.Column(db.Boolean, server_default=db.text("false"))
    Hat = db.Column(db.ForeignKey('puffle_item.ID', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    Backyard = db.Column(db.Boolean, server_default=db.text("false"))
    HasDug = db.Column(db.Boolean, server_default=db.text("false"))


class PenguinPuffleItem(db.Model):
    __tablename__ = 'penguin_puffle_item'

    PenguinID = db.Column(db.ForeignKey('penguin.ID', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
                          nullable=False)
    ItemID = db.Column(db.Integer, primary_key=True, nullable=False)
    Quantity = db.Column(db.SmallInteger, nullable=False)


class Login(db.Model):
    __tablename__ = 'login'

    ID = db.Column(db.Integer, primary_key=True, server_default=db.text("nextval('\"login_ID_seq\"'::regclass)"))
    PenguinID = db.Column(db.ForeignKey('penguin.ID', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    Date = db.Column(db.DateTime, nullable=False, server_default=db.text("now()"))
    IPAddress = db.Column(db.CHAR(255), nullable=False)

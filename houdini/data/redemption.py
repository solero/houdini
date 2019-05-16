from houdini.data import db


class RedemptionBook(db.Model):
    __tablename__ = 'redemption_book'

    ID = db.Column(db.Integer, primary_key=True)
    Name = db.Column(db.String(255), nullable=False)


class RedemptionBookWord(db.Model):
    __tablename__ = 'redemption_book_word'

    BookID = db.Column(db.ForeignKey('redemption_book.ID', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
                       nullable=False)
    Page = db.Column(db.SmallInteger, primary_key=True, nullable=False, server_default=db.text("1"))
    Line = db.Column(db.SmallInteger, primary_key=True, nullable=False, server_default=db.text("1"))
    WordNumber = db.Column(db.SmallInteger, primary_key=True, nullable=False, server_default=db.text("1"))
    Answer = db.Column(db.String(20), nullable=False)


class RedemptionCode(db.Model):
    __tablename__ = 'redemption_code'

    ID = db.Column(db.Integer, primary_key=True,
                   server_default=db.text("nextval('\"redemption_code_ID_seq\"'::regclass)"))
    Code = db.Column(db.String(16), nullable=False, unique=True)
    Type = db.Column(db.String(8), nullable=False, server_default=db.text("'BLANKET'::character varying"))
    Coins = db.Column(db.Integer, nullable=False, server_default=db.text("0"))
    Expires = db.Column(db.DateTime)


t_redemption_award_card = db.Table(
    'redemption_award_card', db,
    db.Column('CodeID', db.ForeignKey('redemption_code.ID', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
              nullable=False),
    db.Column('CardID', db.ForeignKey('card.ID', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
              nullable=False)
)

t_redemption_award_flooring = db.Table(
    'redemption_award_flooring', db,
    db.Column('CodeID', db.ForeignKey('redemption_code.ID', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
              nullable=False),
    db.Column('FlooringID', db.ForeignKey('flooring.ID', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
              nullable=False)
)

t_redemption_award_furniture = db.Table(
    'redemption_award_furniture', db,
    db.Column('CodeID', db.ForeignKey('redemption_code.ID', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
              nullable=False),
    db.Column('FurnitureID', db.ForeignKey('furniture.ID', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
              nullable=False)
)

t_redemption_award_igloo = db.Table(
    'redemption_award_igloo', db,
    db.Column('CodeID', db.ForeignKey('redemption_code.ID', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
              nullable=False),
    db.Column('IglooID', db.ForeignKey('igloo.ID', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
              nullable=False)
)

t_redemption_award_item = db.Table(
    'redemption_award_item', db,
    db.Column('CodeID', db.ForeignKey('redemption_code.ID', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
              nullable=False),
    db.Column('ItemID', db.ForeignKey('item.ID', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
              nullable=False)
)

t_redemption_award_location = db.Table(
    'redemption_award_location', db,
    db.Column('CodeID', db.ForeignKey('redemption_code.ID', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
              nullable=False),
    db.Column('LocationID', db.ForeignKey('location.ID', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
              nullable=False)
)

t_redemption_award_puffle = db.Table(
    'redemption_award_puffle', db,
    db.Column('CodeID', db.ForeignKey('redemption_code.ID', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
              nullable=False),
    db.Column('PuffleID', db.ForeignKey('puffle.ID', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
              nullable=False)
)

t_redemption_award_puffle_item = db.Table(
    'redemption_award_puffle_item', db,
    db.Column('CodeID', db.ForeignKey('redemption_code.ID', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
              nullable=False),
    db.Column('PuffleItemID', db.ForeignKey('puffle_item.ID', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
              nullable=False)
)

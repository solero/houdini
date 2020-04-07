from houdini.data import db


class RedemptionCode(db.Model):
    __tablename__ = 'redemption_code'

    id = db.Column(db.Integer, primary_key=True,
                   server_default=db.text("nextval('\"redemption_code_id_seq\"'::regclass)"))
    code = db.Column(db.String(16), nullable=False, unique=True)
    type = db.Column(db.String(8), nullable=False, server_default=db.text("'BLANKET'::character varying"))
    coins = db.Column(db.Integer, nullable=False, server_default=db.text("0"))
    expires = db.Column(db.DateTime)
    uses = db.Column(db.Integer)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._cards = set()
        self._flooring = set()
        self._furniture = set()
        self._igloos = set()
        self._items = set()
        self._locations = set()
        self._puffles = set()
        self._puffle_items = set()

    @property
    def cards(self):
        return self._cards

    @cards.setter
    def cards(self, child):
        if isinstance(child, RedemptionAwardCard):
            self._cards.add(child)

    @property
    def flooring(self):
        return self._flooring

    @flooring.setter
    def flooring(self, child):
        if isinstance(child, RedemptionAwardFlooring):
            self._flooring.add(child)

    @property
    def furniture(self):
        return self._furniture

    @furniture.setter
    def furniture(self, child):
        if isinstance(child, RedemptionAwardFurniture):
            self._furniture.add(child)

    @property
    def igloos(self):
        return self._igloos

    @igloos.setter
    def igloos(self, child):
        if isinstance(child, RedemptionAwardIgloo):
            self._igloos.add(child)

    @property
    def items(self):
        return self._items

    @items.setter
    def items(self, child):
        if isinstance(child, RedemptionAwardItem):
            self._items.add(child)

    @property
    def locations(self):
        return self._locations

    @locations.setter
    def locations(self, child):
        if isinstance(child, RedemptionAwardLocation):
            self._locations.add(child)

    @property
    def puffles(self):
        return self._puffles

    @puffles.setter
    def puffles(self, child):
        if isinstance(child, RedemptionAwardPuffle):
            self._puffles.add(child)

    @property
    def puffle_items(self):
        return self._puffle_items

    @puffle_items.setter
    def puffle_items(self, child):
        if isinstance(child, RedemptionAwardPuffleItem):
            self._puffle_items.add(child)


class RedemptionBook(db.Model):
    __tablename__ = 'redemption_book'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)


class RedemptionBookWord(db.Model):
    __tablename__ = 'redemption_book_word'

    question_id = db.Column(db.Integer, primary_key=True, server_default=db.text("nextval('\"redemption_book_word_question_id_seq\"'::regclass)"))
    book_id = db.Column(db.ForeignKey('redemption_book.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
                        nullable=False)
    page = db.Column(db.SmallInteger, primary_key=True, nullable=False, server_default=db.text("1"))
    line = db.Column(db.SmallInteger, primary_key=True, nullable=False, server_default=db.text("1"))
    word_number = db.Column(db.SmallInteger, primary_key=True, nullable=False, server_default=db.text("1"))
    answer = db.Column(db.String(20), nullable=False)


class RedemptionAwardCard(db.Model):
    __tablename__ = 'redemption_award_card'
    code_id = db.Column(db.ForeignKey('redemption_code.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
                        nullable=False)
    card_id = db.Column(db.ForeignKey('card.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
                        nullable=False)


class RedemptionAwardFlooring(db.Model):
    __tablename__ = 'redemption_award_flooring'
    code_id = db.Column(db.ForeignKey('redemption_code.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
                        nullable=False)
    flooring_id = db.Column(db.ForeignKey('flooring.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
                            nullable=False)


class RedemptionAwardFurniture(db.Model):
    __tablename__ = 'redemption_award_furniture'
    code_id = db.Column(db.ForeignKey('redemption_code.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
                        nullable=False)
    furniture_id = db.Column(db.ForeignKey('furniture.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
                             nullable=False)


class RedemptionAwardIgloo(db.Model):
    __tablename__ = 'redemption_award_igloo'
    code_id = db.Column(db.ForeignKey('redemption_code.id', ondelete='CASCADE', onupdate='CASCADE'),
                        primary_key=True, nullable=False)
    igloo_id = db.Column(db.ForeignKey('igloo.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
                         nullable=False)


class RedemptionAwardItem(db.Model):
    __tablename__ = 'redemption_award_item'
    code_id = db.Column(db.ForeignKey('redemption_code.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
                        nullable=False)
    item_id = db.Column(db.ForeignKey('item.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
                        nullable=False)


class RedemptionAwardLocation(db.Model):
    __tablename__ = 'redemption_award_location'
    code_id = db.Column(db.ForeignKey('redemption_code.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
                        nullable=False)
    location_id = db.Column(db.ForeignKey('location.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
                            nullable=False)


class RedemptionAwardPuffle(db.Model):
    __tablename__ = 'redemption_award_puffle'
    code_id = db.Column(db.ForeignKey('redemption_code.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
                        nullable=False)
    puffle_id = db.Column(db.ForeignKey('puffle.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
                          nullable=False)


class RedemptionAwardPuffleItem(db.Model):
    __tablename__ = 'redemption_award_puffle_item'
    code_id = db.Column(db.ForeignKey('redemption_code.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
                        nullable=False)
    puffle_item_id = db.Column(db.ForeignKey('puffle_item.id', ondelete='CASCADE', onupdate='CASCADE'),
                               primary_key=True, nullable=False)


class PenguinRedemptionCode(db.Model):
    __tablename__ = 'penguin_redemption_code'

    penguin_id = db.Column(db.ForeignKey('penguin.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
                           nullable=False)
    code_id = db.Column(db.ForeignKey('redemption_code.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
                        nullable=False, index=True)


class PenguinRedemptionBook(db.Model):
    __tablename__ = 'penguin_redemption_book'

    penguin_id = db.Column(db.ForeignKey('penguin.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
                           nullable=False)
    book_id = db.Column(db.ForeignKey('redemption_book.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
                        nullable=False, index=True)

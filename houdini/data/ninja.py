from houdini.data import AbstractDataCollection, db


class Card(db.Model):
    __tablename__ = 'card'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    set_id = db.Column(db.SmallInteger, nullable=False, server_default=db.text("1"))
    power_id = db.Column(db.SmallInteger, nullable=False, server_default=db.text("0"))
    element = db.Column(db.CHAR(1), nullable=False, server_default=db.text("'s'::bpchar"))
    color = db.Column(db.CHAR(1), nullable=False, server_default=db.text("'b'::bpchar"))
    value = db.Column(db.SmallInteger, nullable=False, server_default=db.text("2"))
    description = db.Column(db.String(255), nullable=False, server_default=db.text("''::character varying"))

    def get_string(self):
        return f'{self.id}|{self.element}|{self.value}|{self.color}|{self.power_id}'


class CardStarterDeck(db.Model):
    __tablename__ = 'card_starter_deck'

    item_id = db.Column(db.ForeignKey('item.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
                           nullable=False, index=True)
    card_id = db.Column(db.ForeignKey('card.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
                        nullable=False)
    quantity = db.Column(db.SmallInteger, nullable=False, server_default=db.text("1"))


class PenguinCard(db.Model):
    __tablename__ = 'penguin_card'

    penguin_id = db.Column(db.ForeignKey('penguin.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
                           nullable=False, index=True)
    card_id = db.Column(db.ForeignKey('card.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
                        nullable=False)
    quantity = db.Column(db.SmallInteger, nullable=False, server_default=db.text("1"))
    member_quantity = db.Column(db.SmallInteger, nullable=False, server_default=db.text("0"))


class CardCollection(AbstractDataCollection):
    __model__ = Card
    __indexby__ = 'id'
    __filterby__ = 'id'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.starter_decks = {}

    def set_starter_decks(self, starter_deck_cards):
        for card in starter_deck_cards:
            starter_deck = self.starter_decks.get(card.item_id, [])
            starter_deck.append((self.get(card.card_id), card.quantity))
            self.starter_decks[card.item_id] = starter_deck

    @property
    def power_cards(self):
        return [card for card in self.values() if card.power_id > 0]


class PenguinCardCollection(AbstractDataCollection):
    __model__ = PenguinCard
    __indexby__ = 'card_id'
    __filterby__ = 'penguin_id'

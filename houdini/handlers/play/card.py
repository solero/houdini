import random

from houdini import handlers
from houdini.data.ninja import CardCollection, CardStarterDeck, PenguinCardCollection
from houdini.handlers import Priority, XMLPacket, XTPacket


@handlers.boot
async def cards_load(server):
    server.cards = await CardCollection.get_collection()
    server.logger.info(f'Loaded {len(server.cards)} ninja cards')

    starter_deck_cards = await CardStarterDeck.query.gino.all()
    server.cards.set_starter_decks(starter_deck_cards)
    server.logger.info(f'Loaded {len(server.cards.starter_decks)} starter decks')


@handlers.handler(XMLPacket('login'), priority=Priority.Low)
@handlers.allow_once
async def load_card_inventory(p):
    p.cards = await PenguinCardCollection.get_collection(p.id)


@handlers.handler(XTPacket('i', 'ai'))
async def handle_buy_starter_deck(p, deck_id: int):
    if deck_id in p.server.cards.starter_decks:
        starter_deck = p.server.cards.starter_decks[deck_id]
        power_cards = [card for card, qty in starter_deck if card.power_id > 0]
        for card, qty in starter_deck:
            if card.power_id == 0:
                await p.add_card(card, quantity=qty)
        power_card = random.choice(power_cards)
        await p.add_card(power_card, quantity=1)


@handlers.handler(XTPacket('cd', 'gcd'))
async def handle_get_card_data(p):
    await p.send_xt('gcd', '|'.join(f'{card.card_id},{card.quantity},{card.member_quantity}'
                                    for card in p.cards.values()))


@handlers.handler(XTPacket('cd', 'bpc'))
async def handle_buy_power_cards(p):
    if p.coins >= 1500:
        power_cards = random.sample(p.server.cards.power_cards, 3)
        for card in power_cards:
            await p.add_card(card, member_quantity=1)

        await p.update(coins=p.coins - 1500).apply()
        await p.send_xt('bpc', ','.join([str(card.id) for card in power_cards]), p.coins)
    else:
        await p.send_xt('bpc', 401)

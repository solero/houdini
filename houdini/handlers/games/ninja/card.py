import itertools
import math
import random
import enum
from collections import Counter
from dataclasses import dataclass
from typing import Dict, List, Union

from houdini import IWaddle, handlers
from houdini.data.ninja import Card
from houdini.handlers import XTPacket
from houdini.penguin import Penguin

class CardStamp(enum.IntEnum):
    """ID of Card-Jitsu stamps"""
    GRASSHOPPER = 230
    ELEMENTAL_WIN = 242
    FINE_STUDENT = 232
    FLAWLESS_VICTORY = 238
    ONE_ELEMENT = 244
    TRUE_NINJA = 234
    MATCH_MASTER = 240
    NINJA_MASTER = 236
    SENSEI_CARD = 246
    FULL_DOJO = 248


@dataclass
class Played:
    id: int
    card: Card
    player: int
    opponent: int
    value: int
    element: str


@dataclass
class Ninja:
    penguin: Penguin
    deck: Dict[int, Played]
    bank: Dict[str, List[Played]]
    chosen: Union[Played, None]


class CardJitsuLogic(IWaddle):
    room_id = 998

    RuleSet = {'f': 's', 'w': 'f', 's': 'w'}
    DiscardElements = {4: 's', 5: 'w', 6: 'f'}
    DiscardColors = {7: 'r', 8: 'b', 9: 'g', 10: 'y', 11: 'o', 12: 'p'}
    Replacements = {16: ['w', 'f'], 17: ['s', 'w'], 18: ['f', 's']}
    PowerLimiters = {13: 's', 14: 'f', 15: 'w'}

    OnPlayed = {1, 16, 17, 18}
    CurrentRound = {4, 5, 6, 7, 8, 9, 10, 11, 12, 16, 17, 18}
    AffectsOwnPlayer = {2}

    ItemAwards = [4025, 4026, 4027, 4028, 4029, 4030, 4031, 4032, 4033, 104]
    PostcardAwards = {0: 177, 4: 178, 8: 179}
    StampAwards = {
        0: CardStamp.GRASSHOPPER,
        4: CardStamp.FINE_STUDENT,
        8: CardStamp.TRUE_NINJA,
        9: CardStamp.NINJA_MASTER,
    }
    StampGroupId = 38

    def __init__(self, waddle):
        super().__init__(waddle)

        self.ninjas = [Ninja(
            penguin=p,
            deck={},
            bank={'f': [], 'w': [], 's': []},
            chosen=None
        ) for p in waddle.penguins]

        self.card_id = 1
        self.powers = {}
        self.discards = []

    def get_winning_cards(self, seat_id):
        player_cards = self.ninjas[seat_id].bank
        for element, cards in player_cards.items():
            color_cards, colors = [], []
            for card in cards:
                if card.card.color not in colors:
                    color_cards.append(card)
                    colors.append(card.card.color)
                    if len(color_cards) == 3:
                        return color_cards, 0
        elements = player_cards.values()
        for combo in itertools.product(*elements):
            colors = {card.card.color for card in combo}
            if len(colors) == 3:
                return combo, 1
        return False, -1

    def has_cards_to_play(self, seat_id):
        for power_id, element in CardJitsuLogic.PowerLimiters.items():
            if power_id in self.powers:
                power_card = self.powers[power_id]
                if power_card.opponent == seat_id:
                    opponent_deck = self.ninjas[power_card.opponent].deck
                    for card_id, card in opponent_deck.items():
                        if card.card.element != element:
                            return True
                    return False
        return True

    def discard_opponent_card(self, power_id, opponent_seat_id):
        opponent_cards = self.ninjas[opponent_seat_id].bank
        if power_id in self.DiscardElements:
            element_to_discard = self.DiscardElements[power_id]
            if len(opponent_cards[element_to_discard]) > 0:
                card_to_discard = self.ninjas[opponent_seat_id].bank[element_to_discard][-1]
                self.discards.append(card_to_discard.id)
                del self.ninjas[opponent_seat_id].bank[element_to_discard][-1]
                return True
        if power_id in self.DiscardColors:
            color_to_discard = self.DiscardColors[power_id]
            for element, cards in opponent_cards.items():
                for index, card in enumerate(cards):
                    if card.card.color == color_to_discard:
                        card_to_discard = self.ninjas[opponent_seat_id].bank[element][index]
                        self.discards.append(card_to_discard.id)
                        del self.ninjas[opponent_seat_id].bank[element][index]
                        return True
        return False

    def adjust_card_values(self, first_card, second_card):
        for power_id, power_card in self.powers.items():
            if power_card.card.power_id == 1 and first_card.element == second_card.element:
                swap_value = first_card.value
                first_card.value = second_card.value
                second_card.value = swap_value
            if power_card.card.power_id == 2:
                if power_card.player == 0:
                    first_card.value += 2
                else:
                    second_card.value += 2
            if power_card.card.power_id == 3:
                if power_card.player == 0:
                    second_card.value -= 2
                else:
                    first_card.value -= 2

    def on_played_effects(self, first_card, second_card):
        for ninja_seat_id, ninja in enumerate(self.ninjas):
            played_card = ninja.chosen
            power_id = played_card.card.power_id
            if not power_id:
                continue
            on_played = power_id in CardJitsuLogic.OnPlayed
            current_round = power_id in CardJitsuLogic.CurrentRound
            next_round = not current_round
            if on_played:
                if next_round:
                    self.powers[power_id] = played_card
                if current_round:
                    self.replace_cards(power_id, first_card, second_card)

    def on_scored_effects(self, first_card, second_card):
        winner_seat_id = self.get_winner_seat_id(first_card, second_card)
        for ninja_seat_id, ninja in enumerate(self.ninjas):
            power_id = ninja.chosen.card.power_id
            if power_id:
                opponent_seat_id = (ninja_seat_id + 1) % 2
                on_scored = power_id not in CardJitsuLogic.OnPlayed
                current_round = power_id in CardJitsuLogic.CurrentRound
                next_round = not current_round
                if on_scored and ninja_seat_id == winner_seat_id:
                    if next_round:
                        self.powers[power_id] = ninja.chosen
                    if current_round:
                        self.discard_opponent_card(power_id, opponent_seat_id)

    def get_round_winner(self):
        first_card, second_card = self.ninjas[0].chosen, self.ninjas[1].chosen
        self.adjust_card_values(first_card, second_card)
        self.powers = {}
        self.on_played_effects(first_card, second_card)
        self.on_scored_effects(first_card, second_card)
        winner_seat_id = self.get_winner_seat_id(first_card, second_card)
        return winner_seat_id

    @classmethod
    def replace_cards(cls, power_id, first_card, second_card):
        original, replace = cls.Replacements[power_id]
        if first_card.element == original:
            first_card.element = replace
        if second_card.element == original:
            second_card.element = replace

    @classmethod
    def get_winner_seat_id(cls, first_card, second_card):
        if first_card.element != second_card.element:
            return 0 if cls.RuleSet[first_card.element] == second_card.element else 1
        elif first_card.value > second_card.value:
            return 0
        elif second_card.value > first_card.value:
            return 1
        return -1


class CardJitsuMatLogic(CardJitsuLogic):
    pass


class SenseiLogic(CardJitsuLogic):

    def __init__(self, waddle):
        super().__init__(waddle)

        self.ninjas.insert(0, Ninja(
            penguin=waddle.penguins[0],
            deck={},
            bank={'f': [], 'w': [], 's': []},
            chosen=None
        ))

        self.sensei_move = {}
        self.colors = []

    def get_win_card(self, card):
        self.colors = [] if len(self.colors) >= 6 else self.colors

        cards_to_pick = self.penguins[0].server.cards
        cards_iter = cards_to_pick.values()
        cards_end_to_end = itertools.chain(cards_iter, cards_iter)
        start_position = random.randint(0, len(cards_to_pick))
        cards_random_start = itertools.islice(cards_end_to_end, start_position, start_position+len(cards_to_pick))

        for card_check in cards_random_start:
            if card_check.color not in self.colors and self.beats_card(card_check, card):
                self.colors.append(card_check.color)
                return card_check

    @classmethod
    def beats_card(cls, card_check, card_play):
        if card_check.element != card_play.element:
            return True if cls.RuleSet[card_check.element] == card_play.element else False
        elif card_check.value > card_play.value:
            return True
        return False


async def ninja_rank_up(p, ranks=1):
    if p.ninja_rank + ranks > len(CardJitsuLogic.ItemAwards):
        return False
    for rank in range(p.ninja_rank, p.ninja_rank+ranks):
        await p.add_inventory(p.server.items[CardJitsuLogic.ItemAwards[rank]], notify=False)
        if rank in CardJitsuLogic.PostcardAwards:
            await p.add_inbox(p.server.postcards[CardJitsuLogic.PostcardAwards[rank]])
        if rank in CardJitsuLogic.StampAwards:
            await p.add_card_jitsu_stamp(CardJitsuLogic.StampAwards[rank])
    await p.update(ninja_rank=p.ninja_rank + ranks).apply()
    return True

def get_exp_difference_to_next_rank(cur_rank: int) -> int:
    return (cur_rank + 1) * 5

def get_threshold_for_rank(rank: int) -> int:
    # using arithmetic progression sum because the exp structure allows 
    return (rank + 1) * rank // 2 * 5

async def ninja_progress(p, won=False):
    # black belts don't need exp, otherwise it could overflow
    if p.ninja_rank >= 9:
        return
    gained_exp = 5 if won else 1

    previous_progress = p.ninja_progress
    cur_rank_threshold = get_threshold_for_rank(p.ninja_rank)
    next_rank_threshold = get_threshold_for_rank(p.ninja_rank + 1)
    # this is for correcting old versions, where the exp might not be in the proper threshold.
    if previous_progress < cur_rank_threshold or previous_progress > next_rank_threshold:
        # in this case, ninja_progress is the percentage to next belt
        previous_progress = int(cur_rank_threshold + previous_progress * get_exp_difference_to_next_rank(p.ninja_rank) / 100)

    new_progress = previous_progress + gained_exp
    await p.update(ninja_progress=new_progress).apply()
    if new_progress >= next_rank_threshold:
        await ninja_rank_up(p)
        await p.send_xt('cza', p.ninja_rank)


async def ninja_win(winner, loser):
    await ninja_progress(winner.penguin, won=True)
    await ninja_progress(loser.penguin, won=False)
    await winner.penguin.waddle.remove_penguin(winner.penguin)
    await loser.penguin.waddle.remove_penguin(loser.penguin)


@handlers.handler(XTPacket('gz', ext='z'))
@handlers.waddle(CardJitsuLogic, CardJitsuMatLogic)
async def handle_get_game(p):
    seat_id = p.waddle.get_seat_id(p)
    await p.send_xt('gz', p.waddle.seats, len(p.waddle.penguins))
    await p.send_xt('jz', seat_id, p.safe_name, p.color, p.ninja_rank)


@handlers.handler(XTPacket('uz', ext='z'))
@handlers.waddle(CardJitsuLogic, CardJitsuMatLogic)
async def handle_update_game(p):
    players = [f'{seat_id}|{player.safe_name}|{player.color}|{player.ninja_rank}'
               for seat_id, player in enumerate(p.waddle.penguins)]
    await p.send_xt('uz', *players)
    await p.send_xt('sz')


@handlers.handler(XTPacket('lz', ext='z'))
@handlers.waddle(CardJitsuLogic, CardJitsuMatLogic, SenseiLogic)
async def handle_leave_game(p):
    # sending stamp info fixes the game taking a bit to close when quitting
    await p.send_card_jitsu_stamp_info()
    seat_id = p.waddle.get_seat_id(p)
    await p.waddle.send_xt('cz', p.safe_name, f=lambda penguin: penguin is not p)
    await p.waddle.send_xt('lz', seat_id, f=lambda penguin: penguin is not p)
    await p.waddle.remove_penguin(p)


@handlers.handler(XTPacket('zm', ext='z'), match=['deal'])
@handlers.waddle(CardJitsuLogic, CardJitsuMatLogic)
async def handle_send_deal(p, action: str):
    seat_id = p.waddle.get_seat_id(p)
    opponent_seat_id = (seat_id + 1) % 2
    me = p.waddle.ninjas[seat_id]

    deck = Counter((card.card_id for card in p.cards.values() for _ in range(card.quantity + card.member_quantity)))
    dealt = Counter((played.card.id for played in me.deck.values()))
    undealt = random.sample(list((deck - dealt).elements()), 5 - len(me.deck))

    strings = []
    for card_id in undealt:
        card = p.server.cards[card_id]
        me.deck[p.waddle.card_id] = Played(
            id=p.waddle.card_id,
            card=card,
            player=seat_id,
            opponent=opponent_seat_id,
            value=card.value,
            element=card.element
        )
        strings.append(f'{p.waddle.card_id}|{card.get_string()}')
        p.waddle.card_id += 1

    await p.waddle.send_xt('zm', action, seat_id, *strings)


@handlers.handler(XTPacket('zm', ext='z'), match=['pick'])
@handlers.waddle(CardJitsuLogic, CardJitsuMatLogic)
async def handle_send_pick(p, action: str, card_id: int):
    seat_id = p.waddle.get_seat_id(p)
    opponent_seat_id = (seat_id + 1) % 2
    me = p.waddle.ninjas[seat_id]
    opponent = p.waddle.ninjas[opponent_seat_id]

    if card_id not in me.deck or me.chosen is not None:
        return

    me.chosen = me.deck[card_id]
    del me.deck[card_id]
    await p.waddle.send_xt('zm', action, seat_id, card_id)

    if me.chosen and opponent.chosen:
        winner_seat_id = p.waddle.get_round_winner()

        if me.chosen.card.id == 256 or opponent.chosen.card.id == 256:
            await me.penguin.add_card_jitsu_stamp(CardStamp.SENSEI_CARD)
            await opponent.penguin.add_card_jitsu_stamp(CardStamp.SENSEI_CARD)

        if me.chosen.card.power_id and me.chosen.card.power_id in CardJitsuLogic.OnPlayed:
            await p.waddle.send_xt('zm', 'power', seat_id, opponent_seat_id, me.chosen.card.power_id)
        if opponent.chosen.card.power_id and opponent.chosen.card.power_id in CardJitsuLogic.OnPlayed:
            await p.waddle.send_xt('zm', 'power', opponent_seat_id, seat_id, opponent.chosen.card.power_id)

        if winner_seat_id != -1:
            loser_seat_id = (winner_seat_id + 1) % 2
            winner = p.waddle.ninjas[winner_seat_id]
            loser = p.waddle.ninjas[loser_seat_id]
            winning_card = winner.chosen
            winner.bank[winning_card.card.element].append(winning_card)

            if winning_card.card.power_id and winning_card.card.power_id not in CardJitsuLogic.OnPlayed:
                affects_own_player = winning_card.card.power_id in CardJitsuLogic.AffectsOwnPlayer
                sender, recipient = (winner_seat_id, winner_seat_id) if affects_own_player else (winner_seat_id, loser_seat_id)
                await p.waddle.send_xt('zm', 'power', sender, recipient, winning_card.card.power_id, *p.waddle.discards)
                p.waddle.discards = []

            winning_cards, win_method = p.waddle.get_winning_cards(winner_seat_id)
            if winning_cards:
                await p.waddle.send_xt('czo', 0, winner_seat_id, *(card.id for card in winning_cards))

                stamp = [CardStamp.ONE_ELEMENT, CardStamp.ELEMENTAL_WIN][win_method]
                await winner.penguin.add_card_jitsu_stamp(stamp)
                if all(not cards for cards in loser.bank.values()):
                    await winner.penguin.add_card_jitsu_stamp(
                        CardStamp.FLAWLESS_VICTORY
                    )
                if sum(1 for cards in winner.bank.values() for _ in cards) >= 9:
                    await winner.penguin.add_card_jitsu_stamp(CardStamp.FULL_DOJO)

                await winner.penguin.update(ninja_matches_won=winner.penguin.ninja_matches_won+1).apply()
                if winner.penguin.ninja_matches_won == 25:
                    await winner.penguin.add_card_jitsu_stamp(CardStamp.MATCH_MASTER)

                await ninja_win(winner, loser)
            else:
                for seat_id, ninja in enumerate(p.waddle.ninjas):
                    if not p.waddle.has_cards_to_play(seat_id):
                        winner_seat_id = (seat_id + 1) % 2
                        winner = p.waddle.ninjas[winner_seat_id]
                        loser = p.waddle.ninjas[seat_id]

                        await p.waddle.send_xt('czo', 0, winner_seat_id)
                        await ninja_win(winner, loser)
        await me.penguin.send_xt('zm', 'judge', winner_seat_id)
        await opponent.penguin.send_xt('zm', 'judge', winner_seat_id)
        me.chosen = None
        opponent.chosen = None


@handlers.handler(XTPacket('gz', ext='z'))
@handlers.waddle(SenseiLogic)
async def handle_get_sensei_game(p):
    await p.send_xt('gz', 2, 2)
    await p.send_xt('jz', 1, p.safe_name, p.color, p.ninja_rank)


@handlers.handler(XTPacket('uz', ext='z'))
@handlers.waddle(SenseiLogic)
async def handle_update_sensei_game(p):
    await p.send_xt('uz', '0|Sensei|14|10', f'1|{p.safe_name}|{p.color}|{p.ninja_rank}')
    await p.send_xt('sz')


@handlers.handler(XTPacket('zm', ext='z'), match=['deal'])
@handlers.waddle(SenseiLogic)
async def handle_send_sensei_deal(p, action: str):
    can_beat_sensei = p.ninja_rank >= len(CardJitsuLogic.ItemAwards) - 1
    sensei, me = p.waddle.ninjas
    deck = Counter((card.card_id for card in p.cards.values() if
                    can_beat_sensei or p.server.cards[card.card_id].power_id == 0
                    for _ in range(card.quantity + card.member_quantity)))
    dealt = Counter((played.card.id for played in me.deck.values()))
    undealt = random.sample(list((deck - dealt).elements()), 5 - len(me.deck))

    strings = []
    sensei_strings = []
    for card_id in undealt:
        card = p.server.cards[card_id]
        me.deck[p.waddle.card_id] = Played(
            id=p.waddle.card_id,
            card=card,
            player=1,
            opponent=0,
            value=card.value,
            element=card.element
        )
        strings.append(f'{p.waddle.card_id}|{card.get_string()}')
        p.waddle.card_id += 1

        sensei_card = random.choice(list(p.server.cards.values())) if can_beat_sensei else p.waddle.get_win_card(card)

        sensei.deck[p.waddle.card_id] = Played(
            id=p.waddle.card_id,
            card=sensei_card,
            player=0,
            opponent=1,
            value=sensei_card.value,
            element=sensei_card.element
        )

        sensei_strings.append(f'{p.waddle.card_id}|{sensei_card.get_string()}')
        p.waddle.sensei_move[p.waddle.card_id - 1] = p.waddle.card_id
        p.waddle.card_id += 1

    await p.waddle.send_xt('zm', action, 0, *sensei_strings)
    await p.waddle.send_xt('zm', action, 1, *strings)


@handlers.handler(XTPacket('zm', ext='z'), match=['pick'])
@handlers.waddle(SenseiLogic)
async def handle_send_sensei_pick(p, action: str, card_id: int):
    sensei, me = p.waddle.ninjas

    if card_id not in me.deck or me.chosen is not None:
        return

    me.chosen = me.deck[card_id]
    sensei.chosen = sensei.deck[p.waddle.sensei_move[card_id]]

    del me.deck[card_id]
    del sensei.deck[p.waddle.sensei_move[card_id]]
    del p.waddle.sensei_move[card_id]

    await p.send_xt('zm', action, 0, sensei.chosen.id)
    await p.send_xt('zm', action, 1, me.chosen.id)

    winner_seat_id = p.waddle.get_round_winner()

    if me.chosen.card.id == 256 or sensei.chosen.card.id == 256:
        await me.penguin.add_card_jitsu_stamp(CardStamp.SENSEI_CARD)

    if me.chosen.card.power_id and me.chosen.card.power_id in CardJitsuLogic.OnPlayed:
        await p.send_xt('zm', 'power', 1, 0, me.chosen.card.power_id)
    if sensei.chosen.card.power_id and sensei.chosen.card.power_id in CardJitsuLogic.OnPlayed:
        await p.send_xt('zm', 'power', 0, 1, sensei.chosen.card.power_id)

    if winner_seat_id != -1:
        loser_seat_id = (winner_seat_id + 1) % 2
        winner = sensei if winner_seat_id == 0 else me
        winning_card = sensei.chosen if winner_seat_id == 0 else me.chosen
        winner.bank[winning_card.card.element].append(winning_card)

        if winning_card.card.power_id and winning_card.card.power_id not in CardJitsuLogic.OnPlayed:
            affects_own_player = winning_card.card.power_id in CardJitsuLogic.AffectsOwnPlayer
            sender, recipient = (winner_seat_id, winner_seat_id) if affects_own_player else (winner_seat_id, loser_seat_id)
            await p.send_xt('zm', 'power', sender, recipient, winning_card.card.power_id, *p.waddle.discards)
            p.waddle.discards = []

        winning_cards, win_method = p.waddle.get_winning_cards(winner_seat_id)
        if winning_cards:
            await p.waddle.send_xt('czo', 0, winner_seat_id, *(card.id for card in winning_cards))

            if winner == me:
                stamp = [CardStamp.ONE_ELEMENT, CardStamp.ELEMENTAL_WIN][win_method]
                await me.penguin.add_card_jitsu_stamp(stamp)
                if all(not cards for cards in sensei.bank.values()):
                    await me.penguin.add_card_jitsu_stamp(CardStamp.FLAWLESS_VICTORY)
                if sum(1 for cards in me.bank.values() for _ in cards) >= 9:
                    await me.penguin.add_card_jitsu_stamp(CardStamp.FULL_DOJO)

                await p.update(ninja_matches_won=p.ninja_matches_won + 1).apply()
                if p.ninja_matches_won == 25:
                    await me.penguin.add_card_jitsu_stamp(CardStamp.MATCH_MASTER)

                can_rank_up = await ninja_rank_up(p)
                if can_rank_up:
                    await p.send_xt('cza', p.ninja_rank)
            else:
                await ninja_progress(p, False)
        else:
            for seat_id, ninja in enumerate(p.waddle.ninjas):
                if not p.waddle.has_cards_to_play(seat_id):
                    winner_seat_id = (seat_id + 1) % 2
                    winner = p.waddle.ninjas[winner_seat_id]
                    if winner == me:
                        can_rank_up = await ninja_rank_up(p)
                        if can_rank_up:
                            await p.send_xt('cza', p.ninja_rank)
                    await p.waddle.send_xt('czo', 0, winner_seat_id)

    await p.send_xt('zm', 'judge', winner_seat_id)
    me.chosen = None
    sensei.chosen = None

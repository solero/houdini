import itertools
from dataclasses import dataclass
from typing import Dict, List, Union

from houdini import IWaddle
from houdini.data.ninja import Card
from houdini.penguin import Penguin


@dataclass
class Played:
    id: int
    card: Card
    player: int
    opponent: int


@dataclass
class Ninja:
    penguin: Penguin
    deck: Dict[int, Card]
    bank: Dict[str, List[Played]]
    chosen: Union[Played, None]


class CardJitsuLogic(IWaddle):
    room_id = 998
    rule_set = {'f': 's', 'w': 'f', 's': 'w'}
    discard_elements = {4: 's', 5: 'w', 6: 'f'}
    discard_colors = {7: 'r', 8: 'b', 9: 'g', 10: 'y', 11: 'o', 12: 'p'}
    replacements = {16: ['w', 'f'], 17: ['s', 'w'], 18: ['f', 's']}
    rank_speed = 1

    def __init__(self, waddle):
        super().__init__(waddle)

        self.ninjas = [
            Ninja(
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
        power_limiters = {13: 's', 14: 'f', 15: 'w'}
        for power_id, element in power_limiters.items():
            if power_id in self.powers:
                power_card = self.powers[power_id]
                if power_card.opponent == seat_id:
                    opponent_deck = self.ninjas[power_card.opponent].deck
                    for card_id, card in opponent_deck.items():
                        if card.element != element:
                            return True
                    return False
        return True

    def discard_opponent_card(self, power_id, opponent_seat_id):
        opponent_cards = self.ninjas[opponent_seat_id].bank
        if power_id in self.discard_elements:
            element_to_discard = self.discard_elements[power_id]
            if len(opponent_cards[element_to_discard]) > 0:
                card_to_discard = self.ninjas[opponent_seat_id].bank[element_to_discard][-1]
                self.discards.append(card_to_discard.id)
                del self.ninjas[opponent_seat_id].bank[element_to_discard][-1]
                return True
        if power_id in self.discard_colors:
            color_to_discard = self.discard_colors[power_id]
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
            if power_card.card.power_id == 1 and first_card.card.element == second_card.card.element:
                first_card.card.value = 1
                second_card.card.value = 1
            if power_card.card.power_id == 2:
                if power_card.player == 0:
                    first_card.card.value += 2
                else:
                    second_card.card.value += 2
            if power_card.card.power_id == 3:
                if power_card.player == 0:
                    second_card.card.value -= 2
                else:
                    first_card.card.value -= 2

    def get_round_winner(self):
        first_card, second_card = self.ninjas[0].chosen, self.ninjas[1].chosen
        winner_seat_id = self.get_winner_seat_id(first_card, second_card)
        self.adjust_card_values(first_card, second_card)

        for ninja_seat_id, ninja in enumerate(self.ninjas):
            played_card = ninja.chosen
            power_id = played_card.card.power_id
            if not power_id:
                continue

            opponent_seat_id = 1 if ninja_seat_id == 0 else 0

            on_played = power_id in {1, 16, 17, 18}
            on_scored = not on_played
            current_round = power_id in {4, 5, 6, 7, 8, 9, 10, 11, 12, 16, 17, 18}
            next_round = not current_round

            if on_played and next_round:
                self.powers[power_id] = played_card
            if on_scored and ninja_seat_id == winner_seat_id:
                if next_round:
                    self.powers[power_id] = played_card
                if current_round:
                    self.discard_opponent_card(power_id, opponent_seat_id)
            if on_played and current_round:
                self.replace_opponent_card(power_id, first_card, second_card, played_card.player)
        winner_seat_id = self.get_winner_seat_id(first_card, second_card)

        self.ninjas[0].chosen = None
        self.ninjas[1].chosen = None
        return winner_seat_id

    @classmethod
    def replace_opponent_card(cls, power_id, first_card, second_card, seat_id):
        for replace_power_id, replacement in cls.replacements.items():
            if power_id == replace_power_id:
                original, replace = replacement
                if seat_id == 1 and first_card.card.element == original:
                    first_card.card.element = replace
                if seat_id == 0 and second_card.card.element == original:
                    second_card.card.element = replace

    @classmethod
    def get_winner_seat_id(cls, first_card, second_card):
        if first_card.card.element != second_card.card.element:
            return 0 if cls.rule_set[first_card.card.element] == second_card.card.element else 1
        elif first_card.card.value > second_card.card.value:
            return 0
        elif second_card.card.value > first_card.card.value:
            return 1
        return -1


class CardJitsuMatLogic(CardJitsuLogic):
    rank_speed = 0.5


class SenseiLogic(CardJitsuLogic):

    def __init__(self, waddle):
        super().__init__(waddle)

        self.ninja = Ninja(
                penguin=waddle.penguins[0],
                deck={},
                bank={'f': [], 'w': [], 's': []},
                chosen=None
        )

        self.sensei_move = {}
        self.colors = []

    def get_win_card(self, card):
        self.colors = [] if len(self.colors) >= 6 else self.colors
        for card_check in self.ninja.penguin.server.cards.values():
            if self.beats_card(card_check, card) and card_check.color not in self.colors:
                self.colors.append(card_check.color)
                return card_check

    @classmethod
    def beats_card(cls, card_check, card_play):
        if card_check.card.element != card_play.card.element:
            return True if cls.rule_set[card_check.card.element] == card_play.card.element else False
        elif card_check.card.value > card_play.card.value:
            return True
        return False

import asyncio
import itertools
import math
import random
import enum
from collections import Counter
from dataclasses import dataclass, field
from typing import List, Union

from houdini import IWaddle, handlers
from houdini.data.ninja import Card
from houdini.handlers import XTPacket
from houdini.penguin import Penguin

class FireStamp(enum.IntEnum):
    """IDs of Card-Jitsu Fire stamps"""
    WARM_UP = 252
    SCORE_FIRE = 254
    FIRE_MIDWAY = 256
    STRONG_DEFENCE = 260
    FIRE_SUIT = 262
    FIRE_NINJA = 264
    MAX_ENERGY = 266
    FIRE_EXPERT = 268

@dataclass
class FireNinja:
    penguin: Penguin
    seat_id: int
    deck: List[Card] = field(default_factory=list)
    chosen: Union[int, None] = None
    energy: int = 6
    energy_won: int = 0
    state: int = 0
    ready: bool = False


class CardJitsuFireLogic(IWaddle):

    room_id = 997

    Board = ['b', 's', 'w', 'f', 'c',
             's', 'f', 'w', 'b', 's',
             'w', 'f', 'c', 'w', 's', 'f']
    RuleSet = {'f': 's', 'w': 'f', 's': 'w'}
    DefaultTiles = [0, 8, 4, 12]
    AutoBattleTimeout = 22

    ItemAwards = [6025, 4120, 2013, 1086, 3032]
    StampAwards = {1: FireStamp.FIRE_MIDWAY, 3: FireStamp.FIRE_SUIT}

    def __init__(self, waddle):
        super().__init__(waddle)

        self.ninjas = [FireNinja(
            penguin=p,
            seat_id=seat_id
        ) for seat_id, p in enumerate(waddle.penguins)]
        self.battle_ninjas = []

        self.podium = [0]*self.seats
        self.finish_position = self.seats

        self.tile_ids = CardJitsuFireLogic.DefaultTiles[:self.seats].copy()

        self.current_player = None
        self.ninja_circle = itertools.cycle(self.ninjas)

        self.spin_amount = 0
        self.move_clockwise = 0
        self.move_anticlockwise = 0
        self.tab_id = None

        self.current_battle_state = 0
        self.current_battle_element = 0
        self.current_battle_type = 'bt'

        self.choose_card_timeout = None
        self.choose_board_timeout = None

        self.next()
        self.deal()
        self.spin()
        self.set_choose_board_timeout()

    def next(self):
        self.current_player = next(self.ninja_circle)
        while self.current_player not in self.ninjas:
            self.current_player = next(self.ninja_circle)

    def deal(self):
        for ninja in self.ninjas:
            penguin = ninja.penguin
            deck = Counter(penguin.server.cards[card.card_id]
                           for card in penguin.cards.values()
                           for _ in range(card.quantity + card.member_quantity))
            dealt = Counter(ninja.deck)
            can_deal = list((deck - dealt).elements())

            if ninja.chosen is None:
                ninja.deck = random.sample(can_deal, 5)
            else:
                ninja.deck[ninja.chosen] = random.choice(can_deal)

    def spin(self):
        self.tab_id = None
        self.spin_amount = random.randrange(1, 7)

        player_position = self.tile_ids[self.current_player.seat_id]
        self.move_clockwise = (player_position + self.spin_amount) % 16
        self.move_anticlockwise = (player_position - self.spin_amount) % 16

    def set_choose_board_timeout(self):
        loop = asyncio.get_running_loop()
        self.choose_board_timeout = loop.call_later(
            CardJitsuFireLogic.AutoBattleTimeout,
            lambda: asyncio.ensure_future(self.auto_choose_board())
        )

    def set_choose_card_timeout(self):
        loop = asyncio.get_running_loop()
        self.choose_card_timeout = loop.call_later(
            CardJitsuFireLogic.AutoBattleTimeout,
            lambda: asyncio.ensure_future(self.auto_choose_card())
        )

    async def auto_choose_board(self):
        self.tab_id = 1
        await self.current_player.penguin.send_xt('zm', 'tb')
        move = self.move_anticlockwise if random.randint(0, 1) else self.move_clockwise
        await self.choose_board(move, is_auto_play=True)

    async def auto_choose_card(self):
        for ninja in self.battle_ninjas:
            if ninja.chosen is None:
                playable_cards = self.get_playable_cards(ninja)
                await self.choose_card(ninja, random.choice(playable_cards))

    def get_ninja_by_seat_id(self, seat_id):
        return next(ninja for ninja in self.ninjas if ninja.seat_id == seat_id)

    def get_ninja_by_penguin(self, penguin):
        return next(ninja for ninja in self.ninjas if ninja.penguin == penguin)

    def get_ninjas_by_tile_id(self, tile_id):
        return [ninja for ninja in self.ninjas if self.tile_ids[ninja.seat_id] == tile_id]

    def is_card_playable(self, ninja, card_id):
        if self.current_battle_type == 'bt':
            if ninja.deck[card_id].element == self.current_battle_element:
                return True
            return all(card.element != self.current_battle_element for card in ninja.deck)
        return True

    def get_playable_cards(self, ninja):
        return [card_id for card_id in range(len(ninja.deck)) if self.is_card_playable(ninja, card_id)]

    def resolve_battle(self):
        if self.current_battle_type == 'be':
            first_ninja, second_ninja = self.battle_ninjas[:2]
            first_card = first_ninja.deck[first_ninja.chosen]
            second_card = second_ninja.deck[second_ninja.chosen]

            battle_result = CardJitsuFireLogic.get_battle_result(first_card, second_card)

            if battle_result == 0:
                first_ninja.state, second_ninja.state = (4, 1)
                first_ninja.energy += 1
                second_ninja.energy -= 1
                first_ninja.energy_won += 1
            elif battle_result == 1:
                first_ninja.state, second_ninja.state = (1, 4)
                first_ninja.energy -= 1
                second_ninja.energy += 1
                second_ninja.energy_won += 1
            else:
                first_ninja.state, second_ninja.state = (2, 2)

            self.current_battle_element = first_card.element if battle_result == 0 else second_card.element
        elif self.current_battle_type == 'bt':
            battle_card_values = [n.deck[n.chosen].value
                                  if n.deck[n.chosen].element == self.current_battle_element
                                  else 0 for n in self.battle_ninjas]
            highest_battle_card = max(battle_card_values)
            is_battle_tie = battle_card_values.count(highest_battle_card) >= 2
            for ninja in self.battle_ninjas:
                card = ninja.deck[ninja.chosen]
                if card.element != self.current_battle_element:
                    ninja.state = 1
                    ninja.energy -= 1
                elif is_battle_tie and card.value == highest_battle_card:
                    ninja.state = 2
                elif card.value == highest_battle_card:
                    ninja.state = 3
                else:
                    ninja.state = 1
                    ninja.energy -= 1

    async def click_spinner(self, tab_id):
        if self.current_battle_state == 0 and self.tab_id is None and 0 <= tab_id <= 6:
            self.tab_id = tab_id
            await self.send_xt('zm', 'is', self.current_player.seat_id, tab_id)

    async def ready_ninja(self, ninja):
        if self.current_battle_state == 0:
            ninja.ready = True

            if all(n.ready for n in self.ninjas):
                self.next()
                self.spin()
                self.deal()

                for n in self.ninjas:
                    n.chosen = None
                    n.ready = False

                    deck = ','.join(str(card.id) for card in n.deck)
                    spin = f'{self.spin_amount},{self.move_clockwise},{self.move_anticlockwise}'

                    await n.penguin.send_xt('zm', 'nt', self.current_player.seat_id, spin, deck)

                self.set_choose_board_timeout()

    async def choose_board(self, tile_id, is_auto_play=False):
        if self.current_battle_state == 0 and tile_id == self.move_clockwise or tile_id == self.move_anticlockwise:
            if not is_auto_play or self.current_battle_state == 0:
                self.tile_ids[self.current_player.seat_id] = tile_id
                tile_ids = ','.join(map(str, self.tile_ids))

                element = CardJitsuFireLogic.Board[tile_id]

                await self.send_xt('zm', 'ub', self.current_player.seat_id, tile_ids, self.tab_id)

                self.current_battle_type = 'bt'
                self.battle_ninjas = self.ninjas
            else:
                tile_id = self.tile_ids[self.current_player.seat_id]
                element = CardJitsuFireLogic.Board[tile_id]

            ninjas_on_tile = self.get_ninjas_by_tile_id(tile_id)

            if len(ninjas_on_tile) > 1:
                self.current_battle_state = 2
                self.current_battle_element = element

                if is_auto_play:
                    ninjas_on_tile.remove(self.current_player)
                    opponent = random.choice(ninjas_on_tile)
                    await self.choose_opponent(opponent.seat_id)
                else:
                    if len(ninjas_on_tile) > 2:
                        battle_seat_ids = ','.join(str(ninja.seat_id) for ninja in ninjas_on_tile)
                        await self.send_xt('zm', 'co', 0, battle_seat_ids)
                    else:
                        opponent = next(n for n in ninjas_on_tile if n != self.current_player)
                        await self.choose_opponent(opponent.seat_id)
            elif element in CardJitsuFireLogic.Board[1:4]:
                battle_seat_ids = ','.join(str(ninja.seat_id) for ninja in self.ninjas)
                self.current_battle_element = element
                self.current_battle_state = 3

                await self.send_xt('zm', 'sb', self.current_battle_type, battle_seat_ids, element)

                self.choose_board_timeout.cancel()
                self.set_choose_card_timeout()
            elif element == 'c':
                if is_auto_play:
                    battle_seat_ids = ','.join(str(ninja.seat_id) for ninja in self.ninjas)
                    self.current_battle_element = random.choice(CardJitsuFireLogic.Board[1:4])
                    self.current_battle_state = 3

                    await self.send_xt('zm', 'sb', self.current_battle_type, battle_seat_ids,
                                       self.current_battle_element)

                    self.choose_board_timeout.cancel()
                    self.set_choose_card_timeout()
                else:
                    self.current_battle_state = 1
                    await self.send_xt('zm', 'ct')
            elif element == 'b':
                self.current_battle_element = element
                self.current_battle_state = 2

                if is_auto_play:
                    opponent = next(n for n in self.ninjas if n != self.current_player)
                    await self.choose_opponent(opponent.seat_id)
                else:
                    if len(self.ninjas) > 2:
                        battle_seat_ids = ','.join(str(ninja.seat_id) for ninja in self.ninjas)

                        await self.send_xt('zm', 'co', 0, battle_seat_ids)
                    else:
                        opponent = next(n for n in self.ninjas if n != self.current_player)
                        await self.choose_opponent(opponent.seat_id)

    async def choose_card(self, ninja, card_id):
        if ninja.chosen is None and self.is_card_playable(ninja, card_id):
            ninja.chosen = card_id

            await self.send_xt('zm', 'ic', ninja.seat_id, f=lambda p: p != ninja.penguin)

            if all(n.chosen is not None for n in self.battle_ninjas):
                self.choose_card_timeout.cancel()
                self.resolve_battle()

                for n in self.ninjas:
                    if n.energy == 0:
                        self.podium[n.seat_id] = self.finish_position
                        self.finish_position -= 1

                if self.finish_position == 1:
                    winner_seat_id = self.podium.index(0)
                    self.podium[winner_seat_id] = 1

                battle_seat_ids = ','.join(str(n.seat_id) for n in self.battle_ninjas)
                battle_card_ids = ','.join(str(n.deck[n.chosen].id) for n in self.battle_ninjas)
                battle_energy = ','.join(str(n.energy) for n in self.battle_ninjas)
                battle_states = ','.join(str(n.state) for n in self.battle_ninjas)
                finish_positions = ','.join(str(position) for position in self.podium)
                battle = f'{self.current_battle_type},{self.current_battle_element}'

                for n in self.ninjas.copy():
                    deck = ','.join(str(card.id) for card in n.deck)

                    await n.penguin.send_xt(
                        'zm', 'rb',
                        battle_seat_ids,
                        battle_card_ids,
                        battle_energy,
                        battle_states,
                        battle,
                        deck,
                        finish_positions
                    )

                    if n.energy == 0 or self.finish_position == 1:
                        player_finish_position = self.podium[n.seat_id]

                        await end_game_stamps(n, player_finish_position)
                        await fire_ninja_progress(n.penguin, self.podium[n.seat_id], len(self.podium))

                        finish_positions = ','.join(str(max(position, 1)) for position in self.podium)
                        await n.penguin.send_xt('zm', 'zo', finish_positions)
                        await self.remove_penguin(n.penguin, quit_early=False)

                self.current_battle_state = 0

    async def choose_opponent(self, seat_id):
        if self.current_battle_state == 2 and seat_id != self.current_player.seat_id:
            opponent = self.get_ninja_by_seat_id(seat_id)
            self.battle_ninjas = [self.current_player, opponent]

            self.current_battle_type = 'be'
            self.current_battle_state = 3

            battle_seat_ids = ','.join(str(ninja.seat_id) for ninja in self.battle_ninjas)
            await self.send_xt('zm', 'sb', self.current_battle_type, battle_seat_ids, self.current_battle_element)

            self.choose_board_timeout.cancel()
            self.set_choose_card_timeout()

    async def choose_trump(self, element):
        if self.current_battle_state == 1 and element in CardJitsuFireLogic.Board[1:4]:
            self.current_battle_element = element
            self.current_battle_state = 3

            battle_seat_ids = ','.join(str(ninja.seat_id) for ninja in self.ninjas)
            await self.send_xt('zm', 'sb', self.current_battle_type, battle_seat_ids, self.current_battle_element)

            self.choose_board_timeout.cancel()
            self.set_choose_card_timeout()

    async def remove_penguin(self, p, quit_early=True):
        await super().remove_penguin(p)
        ninja = self.get_ninja_by_penguin(p)
        self.ninjas.remove(ninja)

        if quit_early:
            self.podium[ninja.seat_id] = self.finish_position
            self.finish_position -= 1
            await self.send_xt('zm', 'cz', ninja.seat_id)

            if len(self.ninjas) == 1:
                opponent = next(n for n in self.ninjas if n != ninja)
                await opponent.penguin.send_xt('cz')

                await self.remove_penguin(opponent.penguin)
            elif len(self.ninjas) >= 2:
                if ninja == self.current_player and 0 <= self.current_battle_state <= 2:
                    self.choose_board_timeout.cancel()
                    await self.auto_choose_board()
                elif ninja.chosen is None and self.current_battle_state == 3:
                    playable_cards = self.get_playable_cards(ninja)
                    await self.choose_card(ninja, random.choice(playable_cards))

    @classmethod
    def get_battle_result(cls, first_card, second_card):
        if first_card.element != second_card.element:
            return 0 if cls.RuleSet[first_card.element] == second_card.element else 1
        elif first_card.value > second_card.value:
            return 0
        elif second_card.value > first_card.value:
            return 1
        return -1


class FireMatLogic(CardJitsuFireLogic):
    pass


class FireSenseiLogic(CardJitsuFireLogic):

    def __init__(self, waddle):
        super().__init__(waddle)

        sensei = FireNinja(
            penguin=waddle.penguins[0],
            seat_id=1
        )
        self.ninjas.append(sensei)
        self.tile_ids.append(CardJitsuFireLogic.DefaultTiles[1])

    async def auto_choose_card(self):
        ninja = self.ninjas[0]
        playable_cards = self.get_playable_cards(ninja)
        await self.choose_card(ninja, random.choice(playable_cards))

    async def ready_ninja(self, ninja):
        if self.current_battle_state == 0:
            self.next()
            self.spin()
            self.deal()

            ninja.chosen = None

            deck = ','.join(str(card.id) for card in ninja.deck)
            spin = f'{self.spin_amount},{self.move_clockwise},{self.move_anticlockwise}'

            await ninja.penguin.send_xt('zm', 'nt', self.current_player.seat_id, spin, deck)

            if self.current_player == ninja:
                self.set_choose_board_timeout()
            else:
                await self.auto_choose_board()

    async def choose_card(self, ninja, card_id):
        if ninja.chosen is None and self.is_card_playable(ninja, card_id):
            self.choose_card_timeout.cancel()

            sensei = self.ninjas[1]
            ninja.chosen = card_id
            card = ninja.deck[ninja.chosen]

            can_beat_sensei = ninja.penguin.fire_ninja_rank >= 4
            sensei_card = random.choice(list(ninja.penguin.server.cards.values())) \
                if can_beat_sensei else self.get_win_card(card)
            sensei.chosen = 0
            sensei.deck = [sensei_card]

            await ninja.penguin.send_xt('zm', 'ic', 1)

            self.resolve_battle()

            if ninja.energy == 0:
                self.podium = [2, 1]
            if sensei.energy == 0:
                self.podium = [1, 2]

            battle_seat_ids = ','.join(str(n.seat_id) for n in self.battle_ninjas)
            battle_card_ids = ','.join(str(n.deck[n.chosen].id) for n in self.battle_ninjas)
            battle_energy = ','.join(str(n.energy) for n in self.battle_ninjas)
            battle_states = ','.join(str(n.state) for n in self.battle_ninjas)
            finish_positions = ','.join(str(position) for position in self.podium)
            deck = ','.join(str(card.id) for card in ninja.deck)
            battle = f'{self.current_battle_type},{self.current_battle_element}'

            await ninja.penguin.send_xt(
                'zm', 'rb',
                battle_seat_ids,
                battle_card_ids,
                battle_energy,
                battle_states,
                battle,
                deck,
                finish_positions
            )

            player_finish_position = self.podium[ninja.seat_id]
            if player_finish_position > 0:
                await end_game_stamps(ninja, player_finish_position)
                await fire_ninja_progress(ninja.penguin, player_finish_position, len(self.podium))

                await ninja.penguin.send_xt('zm', 'zo', finish_positions)
                await self.remove_penguin(ninja.penguin, quit_early=False)

            self.current_battle_state = 0

    def get_win_card(self, card):
        cards_to_pick = self.penguins[0].server.cards
        cards_iter = cards_to_pick.values()
        cards_end_to_end = itertools.chain(cards_iter, cards_iter)
        start_position = random.randint(0, len(cards_to_pick))
        cards_random_start = itertools.islice(cards_end_to_end, start_position, start_position+len(cards_to_pick))

        if self.current_battle_type == 'bt':
            return next(card_check for card_check in cards_random_start
                        if card_check.element == self.current_battle_element
                        and card_check.value >= card.value)
        elif self.current_battle_type == 'be':
            return next(card_check for card_check in cards_random_start
                        if FireSenseiLogic.beats_card(card_check, card))

    async def remove_penguin(self, p, quit_early=True):
        ninja = self.get_ninja_by_penguin(p)
        await super().remove_penguin(p, False)

        if ninja == self.current_player and 0 <= self.current_battle_state <= 2:
            self.choose_board_timeout.cancel()
        elif ninja.chosen is None and self.current_battle_state == 3:
            self.choose_card_timeout.cancel()

    @classmethod
    def beats_card(cls, card_check, card_play):
        if card_check.element != card_play.element:
            return True if cls.RuleSet[card_check.element] == card_play.element else False
        elif card_check.value > card_play.value:
            return True
        return False


async def fire_ninja_rank_up(p, ranks=1):
    if p.fire_ninja_rank + ranks > len(CardJitsuFireLogic.ItemAwards):
        return False
    for rank in range(p.fire_ninja_rank, p.fire_ninja_rank+ranks):
        await p.add_inventory(p.server.items[CardJitsuFireLogic.ItemAwards[rank]], notify=False)
        if rank in CardJitsuFireLogic.StampAwards:
            await p.add_card_jitsu_stamp(CardJitsuFireLogic.StampAwards[rank])
    await p.update(
        fire_ninja_rank=p.fire_ninja_rank + ranks
    ).apply()
    return True

# exp required to reach this rank
def get_fire_rank_threshold(rank):
    try:
        return [0, 25, 75, 175, 325][rank]
    except:
        return

async def fire_ninja_progress(p, finish_position, players_number):
    has_suit = p.fire_ninja_rank >= 4
    is_sensei = type(p.waddle) == FireSenseiLogic
    beat_sensei = is_sensei and p.fire_ninja_rank == 4 and finish_position == 1
    
    cur_rank_threshold = get_fire_rank_threshold(p.fire_ninja_rank)
    next_rank_threshold = get_fire_rank_threshold(p.fire_ninja_rank + 1)
    # scenarios you are allowed to earn XP
    if not has_suit and not is_sensei:
        previous_progress = p.fire_ninja_progress
        # for older versions where the progress was the percentage
        if previous_progress < cur_rank_threshold or previous_progress > next_rank_threshold:
            previous_progress = int(cur_rank_threshold + previous_progress / 100 * (next_rank_threshold - cur_rank_threshold))
        points = [
            [9, 3],
            [12, 6, 3],
            [15, 9, 6, 3],
        ][players_number - 2][finish_position - 1]
        await p.update(fire_ninja_progress=previous_progress+points).apply()
    
    got_new_item = not has_suit and p.fire_ninja_progress >= next_rank_threshold
    if beat_sensei or got_new_item:
        await fire_ninja_rank_up(p)
        await p.send_xt('zm', 'nr', 0, p.fire_ninja_rank)


async def end_game_stamps(ninja, finish_position):
    if finish_position == 1:
        await ninja.penguin.update(fire_matches_won=ninja.penguin.fire_matches_won + 1).apply()
        if ninja.penguin.fire_matches_won >= 10:
            await ninja.penguin.add_card_jitsu_stamp(FireStamp.WARM_UP)
        if ninja.penguin.fire_matches_won >= 50:
            await ninja.penguin.add_card_jitsu_stamp(FireStamp.FIRE_EXPERT)
        if ninja.energy >= 6:
            await ninja.penguin.add_card_jitsu_stamp(FireStamp.STRONG_DEFENCE)
        if type(ninja.penguin.waddle) == FireSenseiLogic:
            await ninja.penguin.add_card_jitsu_stamp(FireStamp.FIRE_NINJA)

    if ninja.energy_won >= 1:
        await ninja.penguin.add_card_jitsu_stamp(FireStamp.SCORE_FIRE)
    if ninja.energy_won >= 3:
        await ninja.penguin.add_card_jitsu_stamp(FireStamp.MAX_ENERGY)


@handlers.handler(XTPacket('gz', ext='z'))
@handlers.waddle(CardJitsuFireLogic, FireMatLogic)
async def handle_get_game(p):
    seat_id = p.waddle.get_seat_id(p)
    await p.send_xt('gz', p.waddle.seats, len(p.waddle.penguins))
    await p.send_xt('jz', seat_id)

    nicknames = ','.join(penguin.safe_name for penguin in p.waddle.penguins)
    colors = ','.join(str(penguin.color) for penguin in p.waddle.penguins)
    energy = ','.join(str(ninja.energy) for ninja in p.waddle.ninjas)
    tile_ids = ','.join(map(str, p.waddle.tile_ids))
    deck = ','.join(str(card.id) for card in p.waddle.ninjas[seat_id].deck)
    spin = f'{p.waddle.spin_amount},{p.waddle.move_clockwise},{p.waddle.move_anticlockwise}'
    ninja_ranks = ','.join(str(penguin.fire_ninja_rank) for penguin in p.waddle.penguins)

    await p.send_xt('sz', 0, nicknames, colors, energy, tile_ids, deck, spin, ninja_ranks)


@handlers.handler(XTPacket('gz', ext='z'))
@handlers.waddle(FireSenseiLogic)
async def handle_get_sensei_game(p):
    await p.send_xt('gz', p.waddle.seats, len(p.waddle.penguins))
    await p.send_xt('jz', 0)

    nicknames = f'{p.safe_name},Sensei'
    colors = f'{p.color},-1'
    energy = ','.join(str(ninja.energy) for ninja in p.waddle.ninjas)
    tile_ids = ','.join(map(str, p.waddle.tile_ids))
    deck = ','.join(str(card.id) for card in p.waddle.ninjas[0].deck)
    spin = f'{p.waddle.spin_amount},{p.waddle.move_clockwise},{p.waddle.move_anticlockwise}'
    ninja_ranks = ','.join(str(penguin.fire_ninja_rank) for penguin in p.waddle.penguins)

    await p.send_xt('sz', 0, nicknames, colors, energy, tile_ids, deck, spin, ninja_ranks)


@handlers.handler(XTPacket('zm', ext='z'), match=['is'])
@handlers.waddle(CardJitsuFireLogic, FireMatLogic, FireSenseiLogic)
async def handle_info_click_spinner(p, *, tab_id: int):
    seat_id = p.waddle.get_seat_id(p)

    if seat_id == p.waddle.current_player.seat_id:
        await p.waddle.click_spinner(tab_id)


@handlers.handler(XTPacket('zm', ext='z'), match=['cb'])
@handlers.waddle(CardJitsuFireLogic, FireMatLogic, FireSenseiLogic)
async def handle_choose_board(p, *, tile_id: int):
    seat_id = p.waddle.get_seat_id(p)
    if seat_id == p.waddle.current_player.seat_id:
        await p.waddle.choose_board(tile_id)


@handlers.handler(XTPacket('zm', ext='z'), match=['co'])
@handlers.waddle(CardJitsuFireLogic, FireMatLogic, FireSenseiLogic)
async def handle_choose_opponent(p, *, opponent_seat_id: int):
    seat_id = p.waddle.get_seat_id(p)
    if seat_id == p.waddle.current_player.seat_id:
        await p.waddle.choose_opponent(opponent_seat_id)


@handlers.handler(XTPacket('zm', ext='z'), match=['ct'])
@handlers.waddle(CardJitsuFireLogic, FireMatLogic, FireSenseiLogic)
async def handle_choose_trump(p, *, element: str):
    seat_id = p.waddle.get_seat_id(p)
    if seat_id == p.waddle.current_player.seat_id:
        await p.waddle.choose_trump(element)


@handlers.handler(XTPacket('zm', ext='z'), match=['cc'])
@handlers.waddle(CardJitsuFireLogic, FireMatLogic, FireSenseiLogic)
async def handle_choose_card(p, *, card_id: int):
    ninja = p.waddle.get_ninja_by_penguin(p)
    await p.waddle.choose_card(ninja, card_id)


@handlers.handler(XTPacket('zm', ext='z'), match=['ir'])
@handlers.waddle(CardJitsuFireLogic, FireMatLogic, FireSenseiLogic)
async def handle_info_ready_sync(p):
    ninja = p.waddle.get_ninja_by_penguin(p)
    await p.waddle.ready_ninja(ninja)


@handlers.handler(XTPacket('lz', ext='z'))
@handlers.player_in_room(CardJitsuFireLogic.room_id)
async def handle_leave_game(p: Penguin):
    await p.send_card_jitsu_stamp_info()

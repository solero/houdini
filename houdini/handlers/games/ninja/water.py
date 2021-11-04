# made by: allinol, dote, diamondfire, adamson

from houdini import IWaddle, handlers
from houdini.data.ninja import Card
from houdini.handlers import XTPacket
from houdini.handlers.games.ninja.card import ninja_stamps_earned
from houdini.penguin import penguin
from dataclasses import dataclass, field
from typing import List, Union
from random import choice, shuffle, sample, randint
from collections import deque
import asyncio
import numpy as np
import math
import sys


class WaterCard:
    __slots__ = ("id", "card", "index", "element", "value")

    def __init__(self, card, index):
        self.card = card
        self.id = self.card.id
        self.element = self.card.element
        self.value = self.card.value
        self.index = index
        
    def __str__(self):
        return f"{self.id}-{self.index}"

class Cells:
    __slots__ = ("id", "type", "value", "penguin")

    def __init__(self, cell_id, _type, value):
        self.id = cell_id
        self.type = _type if value != 0 else 3
        self.value = min(value, 20) if self.type != 3 else 0
        self.penguin = None

    def penguin_jump(self, ninja):
        self.type = 3
        self.penguin = ninja
        ninja.cell = self
        
        
    def update_value(self, dv):
        self.value = max(0, min(self.value + dv, 20))
        if self.value == 0:
            self.type = 3
        
    def can_jump(self):
        return self.type != 4 and self.penguin is None
     
    def __str__(self):
        return f"{self.id}-{self.type}-{self.value}"
        
        
@dataclass
class Rows:
    n_col: int
    index: int
    empty: bool = False
    cells: List[Cells] = field(default_factory=list)
    
    def __post_init__(self):
        self.cell_generator()
        
    def __getitem__(self, i):
        return self.cells[i]
        
    def cell_generator(self):
        self.cells = [Cells(
        cell_id = int("{}{}".format(self.index, i)), 
        _type = randint(0, 2) if not self.empty else 3,
        value = randint(1, 20/2)) for i in range(self.n_col)]
        
    def __str__(self):
        return ",".join(map(str, self.cells))
   
@dataclass
class WaterNinja:
    penguin: penguin
    ready: bool
    seat_id: int
    cell: Union[Cells, None]
    deck: List[Card] = field(default_factory=list)
    chosen: Union[Card, None] = None
    cards: dict = field(default_factory=dict)
    two_close: int = 0
    jumps: int = 0
    position: int = 0
    winner: bool = False
    joined: bool = False
    
    def __hash__(self):
        return self.penguin

        
class CardJitsuWaterLogic(IWaddle):
    room_id = 995
    RankSpeed = 1
    rule_set = {'f' : 1, 'w' : 2, 's' : 3}
    timer_task = None
    started = False
    card_amount = 5
    AVAILABLE_CARDS = {*range(1,114), *range(201, 261), *range(301, 428), *range(501, 596)}
    ItemAwards = [6026, 4121, 2025, 1087, 3032]
    StampAwards = {2: 278, 4: 282}
    def __init__(self, waddle):
        super().__init__(waddle)
        self.timer = 60
        self.in_battle = False
        self.columns = 5 if len(waddle.penguins) <= 2 else 7
        self.x_vals = [1, 3, 5] if len(waddle.penguins) <= 3 else [1, 2, 4, 5]
        self.ninjas = [WaterNinja(
            penguin=p,
            ready=False,
            cell=None,
            seat_id=seat_id
        ) for seat_id, p in enumerate(waddle.penguins)]
        
        
        
            
    async def card_selected(self, ninja, card):
        card_id = int(card)
        card = self.get_player_card(ninja, card_id)
        if card is None:
            return await self.send_zm_client(ninja, 'cp')
            
        ninja.chosen = card
        await self.send_zm_client(ninja, 'cp', card)
        return 
        
        
    async def cycle_card(self):
        for ninja in self.ninjas:
            if ninja.deck is None:
                continue
            self.card_amount += 1
            card = WaterCard(
            card=next(ninja.cards),
            index=self.card_amount)
            
            if len(ninja.deck) > 9:
                pop_card = ninja.deck.popleft()

                if ninja.chosen is not None and \
                   pop_card.index == ninja.chosen.index:

                   ninja.chosen = None

            ninja.deck.append(card)
            await self.send_zm_client(ninja, 'ca', card)
            
    async def cycle_row(self):
        def two_close(row):
            players_in_row = [self.rows_by_id[row][i].penguin for i in range(self.columns) if self.rows_by_id[row][i].penguin is not None] if row in self.rows_by_id else []
            for p in players_in_row:
                p.two_close += 1
        async def edge_users_slip(row):
            players_in_row = [self.rows_by_id[row][i].penguin for i in range(self.columns) if self.rows_by_id[row][i].penguin is not None] if row in self.rows_by_id else []
            position = len(self.ninjas)
            for p in players_in_row:
                p.position = position
                await p.penguin.add_stamp(p.penguin.server.stamps[274])  
            return await self.send_zm(":".join(map(lambda p: 'pk&{}&{}&00&false'.format(p.seat_id, position), players_in_row)))

        dropped, drop_row = self.row_generator()
        if dropped:
            players_in_row = [drop_row[i].penguin for i in range(self.columns) if drop_row[i].penguin is not None]
            
            asyncio.create_task(edge_users_slip(drop_row.index + 1))
            two_close(drop_row.index + 2)
            [(await self.game_over(p)) for p in players_in_row]
        return await self.send_zm("br", self.board_array[-1])


    async def game_over(self, ninja = None):
        if ninja is not None:
            if ninja in self.ninjas:
                self.ninjas.remove(ninja)
            if len(self.ninjas) < 1:
                await self.game_over()
            return

            if hasattr(self, 'velocity_loop') == True:
                if self.velocity_loop is not None:
                    self.velocity_loop.cancel()
                    
            if hasattr(self, 'sensei_loop') == True:
                if self.sensei_loop is not None:
                    self.sensei_loop.cancel()
                    
            if hasattr(self, 'timer_task') == True:
                if self.timer_task is not None:
                    self.timer_task.cancel()

        self.started = False
        players = self.ninjas
        position = len(self.ninjas)
        for p in players:
            if not p.winner:
                progress, rank = await water_ninja_progress(p.penguin, p.position)
                if(progress == 1):
                    await self.send_zm('pd', p.seat_id, position, f'{progress}{rank}', 'false')
                else:
                    await self.send_zm('pd', p.seat_id, position, f'{progress}{0}', 'false')

    def get_cell(self, y, x):
        return self.board_array[y][x]

    def get_nearby_cells(self, row, col):
        if row not in self.rows_by_id:
            return set()

        row_ref = self.rows_by_id[row]
        playable_cells = set()
      
        for i in range(max(0, col-1), min(self.columns, col+2)):
            if row+1 in self.rows_by_id:
                playable_cells.add(self.rows_by_id[row+1][i])

            if row-1 in self.rows_by_id:
                playable_cells.add(self.rows_by_id[row-1][i])

            if i != col:
                playable_cells.add(self.rows_by_id[row][i])

        return list(playable_cells)


    def generate_card(self, ninja):
        cards = list(filter(lambda x: x.card_id in self.AVAILABLE_CARDS, list(ninja.penguin.cards.values())))
        while True:
            yield ninja.penguin.server.cards[choice(cards).card_id]

    def get_playable_cells(self, ninja):
        cell = ninja.cell
        row, col = cell.id//10, cell.id%10

        return self.get_nearby_cells(row, col)

    def get_ninja_by_penguin(self, penguin):
        return next(ninja for ninja in self.ninjas if ninja.penguin == penguin)

    def get_player_card(self, ninja, card_index):
        return next(card for card in ninja.deck if card.index == card_index)
        

    async def initiate_vector(self):
        self.board_array = deque()
        self.rows_by_id = {}
        self.cards_by_id = {}

        self.rows = 0

        [self.row_generator(empty=True) for _ in range(2)]
        [self.row_generator() for _ in range(6)]
        
        await self.initiate_velocity()
        await self.send_zm("bi", self.columns, self.serialize_board())
        [self.get_cell(1, self.x_vals[i]).penguin_jump(self.ninjas[i]) for i in range(len(self.ninjas))]
            
        
    async def initiate_velocity(self):
        self.board_velocity_delta = 100.0
        self.board_velocity = 3000.0 - self.board_velocity_delta
        self.board_velocity_slope = 0.5
        self.card_velocity = np.array((60000.0, 0.0))
        self.card_position = 0
        self.board_position = 278
        self.row_destroy_time = -1

        await self.send_zm("bv", self.board_velocity / self.board_velocity_slope, self.board_velocity)
        await self.send_zm("cv", *self.card_velocity)
    
    async def initiate_player_cards(self):
        for ninja in self.ninjas:
            index = ninja.seat_id

            ninja.cards = self.generate_card(ninja)
            ninja.deck = deque([WaterCard(
            card=next(ninja.cards),
            index=i)
            for i in range(self.card_amount)])
            
            await self.send_zm_client(ninja, "ci", '|'.join(map(str, ninja.deck)))
    
    async def player_initiate(self):
        pi_data = []
        available_pos = range(self.columns)
        '''anti twink
        for ninja in self.ninjas:
            for ninja_ip in self.ninjas:
                if(ninja_ip.penguin.id != ninja.penguin.id and ninja_ip.penguin.peer_name[0] == ninja.penguin.peer_name[0]):
                    await self.send_zm("ge")
                    await self.game_over()
                    return
        ''' 
        for ninja in self.ninjas:        
            cellId = ninja.cell.id
            row, col = 6, cellId%10

            pi_data.append("|".join([str(ninja.seat_id), ninja.penguin.safe_name, str(ninja.penguin.color), "{},{}".format(col, row)]))

        await self.send_zm("pi", *pi_data)

    async def remove_penguin(self, p, isQuit=True):
        if p.waddle is None or p.waddle.room_id != self.room_id:
            return
        for ninja in self.ninjas:
            if ninja.penguin == p:
                self.ninjas.remove(ninja)            
        await super().remove_penguin(p)
        if len(self.ninjas) < 1:
            if hasattr(self, 'velocity_loop') == True:
                if self.velocity_loop is not None:
                    self.velocity_loop.cancel()
                    
            if hasattr(self, 'sensei_loop') == True:
                if self.sensei_loop is not None:
                    self.sensei_loop.cancel()

            if hasattr(self, 'timer_task') == True:
                if self.timer_task is not None:
                    self.timer_task.cancel()

        await ninja_stamps_earned(p)

    def row_generator(self, empty = False):
        self.rows += 1
        row = Rows(self.columns,self.rows, empty=empty)
        self.board_array.append(row)
        self.rows_by_id[row.index] = row
        
        if len(self.board_array) > 9:
            pop_row = self.board_array.popleft()
            if pop_row.index in self.rows_by_id:
                del self.rows_by_id[pop_row.index]

            return True, pop_row
            
        return False, None
    
    async def send_zm(self, *args):
        await self.send_xt("zm", "&".join(map(str, args)))

    async def send_zm_client(self, ninja, *args):
        await ninja.penguin.send_xt("zm", "&".join(map(str, args)))
        
    async def set_velocity(self):
        try:
            while self.started:

                self.board_velocity += self.board_velocity_delta
                self.card_velocity[0] += self.board_velocity_delta / 2.0
                velocity_vector = (self.board_velocity / self.board_velocity_slope, self.board_velocity)

                '''
                  R: y = 0.5x + 186
                  T: y = -2x + 1226
                  int: (416, 394) => R(9)
                  time = (Y - y) / updateF  * 0.05
                '''
                updateFreq = self.update_velocity_vector(velocity_vector)[1]
                pos_delta = 394 - self.board_position
                
                if pos_delta <= 0:
                    await self.cycle_row()
                    self.board_position = 278
                    
                updateCardFreq = self.update_velocity_vector(self.card_velocity)[0]
                cardPos_delta = 256 - self.card_position
                if cardPos_delta <= 0:
                    await self.cycle_card()
                    self.card_position = 0

                self.board_position += updateFreq * 100
                self.card_position += updateCardFreq * 75
                await self.send_zm("bv", *velocity_vector)
                await self.send_zm("cv", *self.card_velocity)
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            pass

    def serialize_board(self):
        return '|'.join(map(str, self.board_array))
            
    async def tick_timer(self):
        try:
            while True:
                await self.send_zm("tt", self.timer)
                self.timer -= 1
                if self.timer < 1:
                    self.timer_task.cancel()
                    self.started = True
                    await self.player_initiate()
                    self.velocity_loop = asyncio.create_task(self.set_velocity())
                 
                elif self.timer < 0:
                    await self.send_zm("ge")
                    await self.game_over()
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            pass
        
    def update_velocity_vector(self, vel, f=50):      
        vel = np.array(vel)

        a = np.linalg.norm(vel) / 1000.0
        b = 1000.0 / f
        vel *= a / vel.max()
        b = np.linalg.norm(vel) / b
        vel *= b / vel.max()

        return vel

class WaterMatLogic(CardJitsuWaterLogic):
    RankSpeed = 0.5

class WaterSenseiLogic(CardJitsuWaterLogic):
    RankSpeed = 0
    
    def __init__(self, waddle):
        super().__init__(waddle)
        sensei = WaterNinja(
            penguin=waddle.penguins[0],
            joined=True,
            ready=True,
            cell=None,
            seat_id=1
        )
        self.ninjas.append(sensei)
        
    async def cycle_card(self):
        ninja = self.ninjas[0]

        self.card_amount += 1
        card = WaterCard(
        card=next(ninja.cards),
        index=self.card_amount)
        
        if len(ninja.deck) > 9:
            pop_card = ninja.deck.popleft()

            if ninja.chosen is not None and \
               pop_card.index == ninja.chosen.index:

               ninja.chosen = None

        ninja.deck.append(card)
        await self.send_zm_client(ninja, 'ca', card)
        
    async def game_over(self, ninja = None):
        if ninja is not None:
            if ninja in self.ninjas:
                self.ninjas.remove(ninja)
            if len(self.ninjas) <= 1:
                await self.game_over()
            return

            if hasattr(self, 'velocity_loop') == True:
                if self.velocity_loop is not None:
                    self.velocity_loop.cancel()

            if hasattr(self, 'sensei_loop') == True:
                if self.sensei_loop is not None:
                    self.sensei_loop.cancel()

            if hasattr(self, 'timer_task') == True:
                if self.timer_task is not None:
                    self.timer_task.cancel()

        self.started = False
        players = self.ninjas
        for p in players:
            await end_game_stamps(p)
            if not p.winner:
                await self.send_zm('pd', p.seat_id, 2, '00', 'false')
        
    async def initiate_player_cards(self):
        ninja = self.ninjas[0]
        ninja.cards = self.generate_card(ninja)
        ninja.deck = deque([WaterCard(
        card=next(ninja.cards),
        index=i)
        for i in range(self.card_amount)])
        
        await self.send_zm_client(ninja, "ci", '|'.join(map(str, ninja.deck)))
        
    async def player_initiate(self):
        available_pos = range(self.columns)
        
        ninja = self.ninjas[0]
        sensei = self.ninjas[1]
        cellId = int(ninja.cell.id)
        sensei_cellId = int(sensei.cell.id)
        row, player_col, sensei_col = 6, cellId%10, sensei_cellId%10
        pi_data =  f'{ninja.seat_id}|{ninja.penguin.safe_name}|{ninja.penguin.color}|{player_col},{row}&{sensei.seat_id}|Sensei|14|{sensei_col},{row}'

        await self.send_zm_client(ninja, "pi", pi_data)
        
    async def sensei_ai(self):
        try:
            while self.started:
                ninja = self.ninjas[0]
                sensei = self.ninjas[1]
                row, cell = sensei.cell.id//10, sensei.cell.id % 10
                available_cells = self.get_playable_cells(sensei)
                available_cells_by_id = {i.id: i for i in available_cells}
                sensei_move = [i for i in available_cells_by_id.values() if i.id//10 > row and not i.penguin]

                sensei_move = choice(sensei_move)
                possible_cards = [1,2,0,3]
                card = possible_cards[sensei_move.type]
                sensei_move.update_value(sensei_move.value * -1)
                row, cell = sensei_move.id//10, sensei_move.id % 10
                cells = [i for i in self.get_nearby_cells(row, cell)[:6] if i.can_jump() and i.id != sensei.cell.id]
                for i in cells:
                    i.type = sensei_move.type if i.type == 3 else i.type
                    i.update_value(i.value * -1) 

                cells.insert(0, sensei_move)
                sensei.cell.penguin = None
                sensei.cell = None
                sensei_move.penguin_jump(sensei)
                await self.send_zm('pt', sensei.seat_id, '{}-{}'.format(card-1, sensei_move.id), '|'.join(map(str, cells)))
                await self.send_zm('pm', f'{sensei.seat_id}-{sensei_move.id}') 
                row = sensei_move.id // 10
                last_row = self.board_array[-1]
                if last_row.index - 2 == row:
                    await self.send_zm("gw", sensei.seat_id, 0,  00, 'false')
                    sensei.winner = True
                    self.started = False
                    await self.game_over()
                if ninja.penguin.water_ninja_rank < 4:  
                    await asyncio.sleep(0.5)
                else:   
                    await asyncio.sleep(2)
        except asyncio.CancelledError:
            pass
        
    async def tick_timer(self):
        try:
            while True:
                await self.send_zm("tt", self.timer)
                self.timer -= 1
                if self.timer < 1:
                    self.timer_task.cancel()
                    self.started = True
                    await self.player_initiate()
                    self.velocity_loop = asyncio.create_task(self.set_velocity())
                    self.sensei_loop = asyncio.create_task(self.sensei_ai())
                elif self.timer < 0:
                    await self.send_zm("ge")
                    await self.game_over()
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            pass

@handlers.handler(XTPacket('gz', ext='z'))
@handlers.waddle(CardJitsuWaterLogic, WaterMatLogic)
async def handle_get_game(p):
    seat_id = p.waddle.get_seat_id(p)
    ninja = p.waddle.get_ninja_by_penguin(p)
    await p.send_xt('gz')
    await p.send_xt('jz')
    await p.waddle.send_zm_client(ninja, "po", seat_id)
    ninja.joined = True
    if all(map(lambda ninja: ninja.joined, p.waddle.ninjas)):
        await p.waddle.initiate_vector()
        await p.waddle.initiate_player_cards()

@handlers.handler(XTPacket('gz', ext='z'))
@handlers.waddle(WaterSenseiLogic)
async def handle_get_sensei_game(p):
    seat_id = p.waddle.get_seat_id(p)
    ninja = p.waddle.get_ninja_by_penguin(p)
    await p.send_xt('gz')
    await p.send_xt('jz')
    await p.waddle.send_zm_client(ninja, "po", seat_id)
    await p.waddle.initiate_vector()
    await p.waddle.initiate_player_cards()

async def end_game_stamps(ninja):
    if ninja.jumps >= 28:
        await ninja.penguin.add_stamp(ninja.penguin.server.stamps[288])  
    if ninja.position == 1:
        await ninja.penguin.update(water_matches_won=ninja.penguin.water_matches_won + 1).apply()
        await ninja.penguin.add_stamp(ninja.penguin.server.stamps[270])
        if ninja.penguin.water_matches_won >= 100:
            await ninja.penguin.add_stamp(ninja.penguin.server.stamps[276])
        if ninja.two_close >= 2:
            await ninja.penguin.add_stamp(ninja.penguin.server.stamps[286])
        if type(ninja.penguin.waddle) == WaterSenseiLogic and ninja.penguin.water_ninja_rank >= 4:
            await ninja.penguin.add_stamp(ninja.penguin.server.stamps[284])
            

async def water_ninja_progress(p, position):
    position = len(p.waddle.penguins) if position <=0 else position
    if p.water_ninja_rank < 4:
        speed = p.waddle.RankSpeed
        points = math.floor((25 / (p.water_ninja_rank+1) / position) * speed)
        await p.update(water_ninja_progress=p.water_ninja_progress+points).apply()
    elif type(p.waddle) == WaterSenseiLogic and p.water_ninja_rank == 4 and position == 1:
        await p.update(water_ninja_progress=100).apply()
    if p.water_ninja_progress >= 100:
        rankup = await water_ninja_rank_up(p)
        return int(rankup), p.water_ninja_rank
    return 0, p.water_ninja_rank
    
async def water_ninja_rank_up(p, ranks=1):
    if p.water_ninja_rank + ranks > len(CardJitsuWaterLogic.ItemAwards):
        return False
    for rank in range(p.water_ninja_rank, p.water_ninja_rank+ranks):
        await p.add_inventory(p.server.items[CardJitsuWaterLogic.ItemAwards[rank]], cost=0, notify=False)
        if rank in CardJitsuWaterLogic.StampAwards:
            await p.add_stamp(p.server.stamps[CardJitsuWaterLogic.StampAwards[rank]])
    await p.update(
        water_ninja_rank=p.water_ninja_rank + ranks,
        water_ninja_progress=p.water_ninja_progress % 100
    ).apply()
    return True

@handlers.handler(XTPacket('zm', ext='z'), match=['103'])
@handlers.waddle(CardJitsuWaterLogic, WaterMatLogic, WaterSenseiLogic)
async def handle_start_game(p):
    ninja = p.waddle.get_ninja_by_penguin(p)
    ninja.ready = True
    if not p.waddle.timer_task:
        p.waddle.timer_task = asyncio.create_task(p.waddle.tick_timer())
    if all(map(lambda ninja: ninja.ready, p.waddle.ninjas)):
        p.waddle.timer = 3

@handlers.handler(XTPacket('jw', ext='z'))
async def handle_update_waddle(p, waddle_id: int):
    uz_string = list()
    waddle = p.room.waddles[waddle_id]
    for seat_id, player in enumerate(waddle.penguins):
        if player is None:
            continue
        uz_string.append('|'.join(map(str, [seat_id, player.safe_name, player.color, player.water_ninja_rank])))

    await p.send_xt('uz', len(uz_string), '%'.join(uz_string))


@handlers.handler(XTPacket('zm', ext='z'), match=['110'])
@handlers.waddle(CardJitsuWaterLogic, WaterMatLogic, WaterSenseiLogic)
async def handle_choose_card(p, *, card_id: int):
    ninja = p.waddle.get_ninja_by_penguin(p)
    await p.waddle.card_selected(ninja, card_id)


@handlers.handler(XTPacket('zm', ext='z'), match=['120'])
@handlers.waddle(CardJitsuWaterLogic, WaterMatLogic, WaterSenseiLogic)
async def handle_player_move(p, action: str, cell_id: int):
    ninja = p.waddle.get_ninja_by_penguin(p)
    available_cells = p.waddle.get_playable_cells(ninja)
    available_cells_by_id = {i.id: i for i in available_cells}

    if cell_id not in available_cells_by_id:
        return await p.waddle.send_zm_client(ninja, 'pf', '{}-{}'.format(ninja.seat_id, cell_id), 'lmao')

    cell = available_cells_by_id[cell_id]
    
    if cell.type != 3 or cell.penguin is not None:
        return await p.waddle.send_zm_client(ninja, 'pf', '{}-{}'.format(ninja.seat_id, cell_id), 'not empty?')

    ninja.cell.penguin = None
    ninja.cell = None
    cell.penguin_jump(ninja)

    await p.waddle.send_zm('pm', '{}-{}'.format(ninja.seat_id, cell.id))

    last_row = p.waddle.board_array[-1]
    row = cell.id // 10
    if last_row.index - 2 == row:
       
        ninja.position = 1
        progress, rank = await water_ninja_progress(ninja.penguin, ninja.position)
        if(progress == 1):
            await p.waddle.send_zm("gw", ninja.seat_id, 1,  '{}{}'.format(int(progress), rank), 'false')
        else:
            await p.waddle.send_zm("gw", ninja.seat_id, 1,  '{}{}'.format(int(progress), 0), 'false')
        ninja.winner = True
        p.waddle.started = False
        return await p.waddle.game_over()


@handlers.handler(XTPacket('lz', ext='z'))
@handlers.waddle(CardJitsuWaterLogic, WaterMatLogic, WaterSenseiLogic)
async def handle_leave_match(p):
    ninja = p.waddle.get_ninja_by_penguin(p)
    await end_game_stamps(ninja)
 
@handlers.handler(XTPacket('zm', ext='z'), match=['121'])
@handlers.waddle(CardJitsuWaterLogic, WaterMatLogic, WaterSenseiLogic)
async def handle_throw_card(p, *, cell_id: int):
    ninja = p.waddle.get_ninja_by_penguin(p)
    available_cells = p.waddle.get_playable_cells(ninja)
    available_cells_by_id = {i.id: i for i in available_cells}

    if cell_id not in available_cells_by_id:
        
        return await p.waddle.send_zm_client(ninja, 'pf', '{}-{}'.format(ninja.seat_id, cell_id))

    cell = available_cells_by_id[cell_id]
    if (ninja.chosen is None) or not cell.can_jump():
        return await p.waddle.send_zm_client(ninja, 'pf', '{}-{}'.format(ninja.seat_id, cell_id))
            
    card = ninja.chosen
    won = ((3 + p.waddle.rule_set[card.element] - (cell.type+1)) % 3 - 1) if cell.type != 3 else -1

    if won > 0:
        return await p.waddle.send_zm_client(ninja, 'pf', '{}-{}'.format(ninja.seat_id, cell_id))

    ninja.chosen = None

    value_del = card.value * (-1 if won != -1 else 1)
    cell.update_value(value_del)
    if cell.type == 3 and cell.value > 0:
        cell.type = p.waddle.rule_set[card.element]-1
        ninja.jumps += 1

    row, col = cell.id//10, cell.id%10
    cells = [i for i in p.waddle.get_nearby_cells(row, col)[:6] if i.can_jump() and i.id != ninja.cell.id]
    for i in cells:
        cell_win = ((3 + p.waddle.rule_set[card.element] - (i.type+1)) % 3 - 1) if i.type != 3 else -1
        if cell_win < 1 and card.value >= 9:
            i.type = cell.type if i.type == 3 else i.type
            i.update_value(card.value * (-1 if cell_win == -1 else 1) if cell.type == p.waddle.rule_set[card.element] else 0) 

    cells.insert(0, cell)
        
    await p.waddle.send_zm('pt', ninja.seat_id, '{}-{}'.format(p.waddle.rule_set[card.element]-1, cell.id), '|'.join(map(str, cells)))

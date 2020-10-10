# Created by Allinol, Dote & DiamondFire.
from houdini import IWaddle, handlers
from houdini.data.ninja import Card
from houdini.handlers import XTPacket
from houdini.handlers.games.ninja.card import ninja_stamps_earned
from houdini.penguin import penguin
from dataclasses import dataclass, field
from typing import List, Union
from random import choice, shuffle, sample, randint
from collections import deque
from concurrent.futures import ProcessPoolExecutor
import asyncio
import numpy as np
import math

executor = ProcessPoolExecutor()


class WaterCard:
    __slots__ = ("id", "card", "index", "element", "value")

    def __init__(self, card, index):
        self.card = card
        print(card)
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
    slipped: int = 0
    jumps: int = 0
    position: int = 0
    winner: bool = False
    joined: bool = False
    
    def __hash__(self):
        return self.penguin

        
class CardJitsuWaterLogic(IWaddle):
    room_id = 995
    rule_set = {'f' : 1, 'w' : 2, 's' : 3}
    timer_task = None
    started = False
    Sensei = False
    card_amount = 7
    AVAILABLE_CARDS = {*range(1,114), *range(201, 261), *range(301, 428), *range(501, 596)}
    ItemAwards = [6026, 4121, 2025, 1087, 3032]
    StampAwards = {2: 278, 4: 282}
    def __init__(self, waddle):
        super().__init__(waddle)
        self.timer = 60
        self.in_battle = False
        self.rows = 0
        self.columns = 5 if len(waddle.penguins) <= 2 else 7
        self.ninjas = [WaterNinja(
            penguin=p,
            ready=False,
            cell=None,
            seat_id=seat_id
        ) for seat_id, p in enumerate(waddle.penguins)]
        
        
    async def initiate_player_cards(self):
        for ninja in self.ninjas:
            index = ninja.seat_id

            ninja.cards = self.generate_card(ninja)
            ninja.deck = deque([WaterCard(
            card=next(ninja.cards),
            index=i)
            for i in range(self.card_amount)])
            
            await self.send_zm_client(ninja, "ci", '|'.join(map(str, ninja.deck)))
            
    async def game_over(self, ninja_dead = None):
        if ninja_dead is not None:
            await end_game_stamps(ninja_dead)
            if ninja_dead in self.ninjas:
                self.ninjas.remove(ninja_dead)
            if len(self.ninjas) < 1:
                await self.game_over()
            return

        if self.velocity_loop is not None:
            self.velocity_loop.cancel()

        self.started = False
        players = self.ninjas
        position = len(players)
        for p in players:
            if not p.winner:
                progress, rank = await water_ninja_progress(p.penguin, p.position)
                await self.send_zm('pd', p.seat_id, position, f'{int(progress)}{rank}', 'false')
                
    def get_playable_cells(self, ninja):
        cell = ninja.cell
        row, col = cell.id//10, cell.id%10

        return self.get_nearby_cells(row, col)

    async def cycle_row(self):
        loop = asyncio.get_running_loop()
        async def edge_users_slip(row):
            players_in_row = [self.rows_by_id[row][i].penguin for i in range(self.columns) if self.rows_by_id[row][i].penguin is not None] if row in self.rows_by_id else []
            position = len(self.ninjas)
            return await self.send_zm(":".join(map(lambda p: 'pk&{}&{}&00&false'.format(p.seat_id, position), players_in_row)))

        dropped, drop_row = self.row_generator()
        if dropped:
            
            players_in_row = [drop_row[i].penguin for i in range(self.columns) if drop_row[i].penguin is not None]
            print('lazy penguins', players_in_row)
            position = len(self.ninjas)
            loop = asyncio.get_running_loop()
            await edge_users_slip(drop_row.index+1)
            [(await self.send_zm_client(p, 'gf'), await self.game_over(p)) for p in players_in_row]

        await self.send_zm("br", self.board_array[-1])

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
        i = 0
        while True:
            i += 1
            yield ninja.penguin.server.cards[choice(cards).card_id]
    
    async def tick_timer(self):
        await self.send_zm("tt", self.timer)
        self.timer -= 1
            
       
        if self.timer < 1 or all(map(lambda ninja: ninja.ready, self.ninjas)):
            self.timer_task.cancel()

            if all(map(lambda ninja: ninja.ready, self.ninjas)):
                self.in_battle = True
                await self.player_initiate()
                self.velocity_loop = asyncio.create_task(set_interval(1,self.set_velocity))
             
            elif self.timer < 1:
                await self.send_zm("ge")
                await self.game_over()

    async def card_selected(self, ninja, card):
        card_id = int(card)
        card = self.get_player_card(ninja, card_id)
        if card is None:
            return await self.send_zm_client(ninja, 'cp')
            
        print(card)
        ninja.chosen = card
        await self.send_zm_client(ninja, 'cp', card)
        return 
        
    def get_player_card(self, ninja, card_index):
        return next(card for card in ninja.deck if card.index == card_index)
        

    async def initiate_vector(self):
        self.board_array = deque()
        self.rows_by_id = {}
        self.cards_by_id = {}

        self.rows = 0

        [self.row_generator(empty=True) for i in range(2)]
        [self.row_generator() for i in range(6)]

        await self.initiate_velocity()
        await self.send_zm("bi", self.columns, self.serialize_board())
        [self.get_cell(1, i*2).penguin_jump(self.ninjas[i]) for i in range(len(self.ninjas))]
            
        
    async def initiate_velocity(self):
        self.board_velocity_delta = 200.0 
        self.board_velocity = 3000.0 - self.board_velocity_delta 
        self.board_velocity_slope = 0.5
        self.card_velocity = np.array((60000.0, 0.0))
        self.card_position = 0

        self.board_position = 278 
        self.row_destroy_time = -1

        await self.send_zm("bv", self.board_velocity / self.board_velocity_slope, self.board_velocity)
        await self.send_zm("cv", *self.card_velocity)
    
    async def player_initiate(self):
        pi_data = []
        available_pos = range(self.columns)
        
        for ninja in self.ninjas:
            cellId = int(ninja.cell.id)
            row, col = 6, cellId%10

            pi_data.append("|".join([str(ninja.seat_id), ninja.penguin.safe_name, str(ninja.penguin.color), "{},{}".format(col, row)]))

        await self.send_zm("pi", *pi_data)
    


    def row_generator(self, empty = False):
        if len(self.board_array) > 9:
            pop_row = self.board_array.popleft()
            if pop_row.index in self.rows_by_id:
                del self.rows_by_id[pop_row.index]

            return True, pop_row
            
        self.rows += 1
        row = Rows(
        n_col=self.columns,
        index=self.rows, 
        empty=empty)

        self.board_array.append(row)
        self.rows_by_id[row.index] = row

        return False, None
       
    async def send_zm(self, *args):
        await super().send_xt("zm", "&".join(map(str, args)))

    async def send_zm_client(self, ninja, *args):
        await ninja.penguin.send_xt("zm", "&".join(map(str, args)))

    def update_velocity_vector(self, vel, f=50):      
        vel = np.array(vel)

        a = np.linalg.norm(vel) / 1000.0
        b = 1000.0 / f
        vel *= a / vel.max()
        b = np.linalg.norm(vel) / b
        vel *= b / vel.max()

        return vel

    async def set_velocity(self):

        self.board_velocity += self.board_velocity_delta
        self.card_velocity[0] += self.board_velocity_delta / 2.0
        velocity_vector = (self.board_velocity / self.board_velocity_slope, self.board_velocity)
        loop = asyncio.get_running_loop()

        '''
          R: y = 0.5x + 186
          T: y = -2x + 1226
          int: (416, 394) => R(9)
          time = (Y - y) / updateF  * 0.05
        '''
        updateFreq = (await loop.run_in_executor(executor, self.update_velocity_vector, velocity_vector))[1]
        pos_delta = 394 - self.board_position
        
        if pos_delta <= 0:
            await self.cycle_row()
            self.board_position = 278
            
        updateCardFreq = (await loop.run_in_executor(executor, self.update_velocity_vector, self.card_velocity))[0]
        cardPos_delta = 128 - self.card_position
        if cardPos_delta <= 0:
            await self.cycle_card()
            self.card_position = 0

        self.board_position += updateFreq * 100
        self.card_position  += updateCardFreq * 100

        await self.send_zm("bv", *velocity_vector)
        await self.send_zm("cv", *self.card_velocity)
       
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



    def serialize_board(self):
        return '|'.join(map(str, self.board_array))

    def get_ninja_by_penguin(self, penguin):
        return next(ninja for ninja in self.ninjas if ninja.penguin == penguin)

    

class WaterMatLogic(CardJitsuWaterLogic):
    RankSpeed = 0.5


class WaterSenseiLogic(CardJitsuWaterLogic):
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
        
    async def player_initiate(self):
        available_pos = range(self.columns)
        
        ninja = self.ninjas[0]
        sensei = self.ninjas[1]
        cellId = int(ninja.cell.id)
        sensei_cellId = int(sensei.cell.id)
        row, player_col, sensei_col = 6, cellId%10, sensei_cellId%10
        pi_data =  f'{ninja.seat_id}|{ninja.penguin.safe_name}|{ninja.penguin.color}|{player_col},{row}&{sensei.seat_id}|Sensei|14|{sensei_col},{row}'

        await self.send_zm_client(ninja, "pi", pi_data)
        
    async def initiate_player_cards(self):
        ninja = self.ninjas[0]
        ninja.cards = self.generate_card(ninja)
        ninja.deck = deque([WaterCard(
        card=next(ninja.cards),
        index=i)
        for i in range(self.card_amount)])
        
        await self.send_zm_client(ninja, "ci", '|'.join(map(str, ninja.deck)))
        
        
    async def game_over(self, ninja_dead = None):
        if ninja_dead is not None:
            if ninja_dead in self.ninjas:
                self.ninjas.remove(ninja_dead)
            if len(self.ninjas) <= 1:
                await self.game_over()

            return

        if self.velocity_loop is not None:
            self.sensei_loop.cancel()
            self.velocity_loop.cancel() 

        self.started = False
        players = self.ninjas
        position = len(players)
        for p in players:
            await end_game_stamps(p)
            if not p.winner:
                await self.send_zm('pd', p.seat_id, position, '00', 'false')
        
    async def tick_timer(self):
        await self.send_zm("tt", self.timer)
        self.timer -= 1
            
     
        if self.timer < 1 or all(map(lambda ninja: ninja.ready, self.ninjas)):
            self.timer_task.cancel()

            if all(map(lambda ninja: ninja.ready, self.ninjas)):
                self.in_battle = True
                await self.player_initiate()
                self.velocity_loop = asyncio.create_task(set_interval(1,self.set_velocity))
                ninja = self.ninjas[0]
                if ninja.penguin.water_ninja_rank < 4:
                    self.sensei_loop = asyncio.create_task(set_interval(1.7,self.sensei_ai))
                else:
                    self.sensei_loop = asyncio.create_task(set_interval(3.5,self.sensei_ai))
             
            elif self.timer < 1:
                await self.send_zm("ge")
                await self.game_over()

        
    async def sensei_ai(self):
        sensei = self.ninjas[1]
        row, cell = sensei.cell.id//10, sensei.cell.id % 10
        available_cells = self.get_playable_cells(sensei)
        available_cells_by_id = {i.id: i for i in available_cells}
        sensei_move = [i for i in available_cells_by_id.values() if i.id//10 > row]
        
        print("sensei's shit", repr(sensei_move))
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
            return await self.game_over()
            
            
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


async def set_interval(timeout, stuff):
    while True:
        await asyncio.sleep(timeout)
        await stuff()

async def end_game_stamps(ninja):
    if ninja.jumps >= 4:
        await ninja.penguin.add_stamp(ninja.penguin.server.stamps[288])  
    if ninja.position == 1:
        await ninja.penguin.update(water_matches_won=ninja.penguin.water_matches_won + 1).apply()
        await ninja.penguin.add_stamp(ninja.penguin.server.stamps[270])
        if ninja.penguin.water_matches_won >= 100:
            await ninja.penguin.add_stamp(ninja.penguin.server.stamps[276])
        if ninja.slipped >= 2:
            await ninja.penguin.add_stamp(ninja.penguin.server.stamps[286])
        if type(ninja.penguin.waddle) == WaterSenseiLogic:
            await ninja.penguin.add_stamp(ninja.penguin.server.stamps[284])
            

async def water_ninja_progress(p, position):
    position = len(p.waddle.penguins) if position <=0 else position
    if p.water_ninja_rank < 4:
        rankup = await water_ninja_rank_up(p)
        speed = p.waddle.RankSpeed
        points = math.floor((25 / (p.water_ninja_rank+1) / position) * speed)
        await p.update(water_ninja_progress=p.water_ninja_progress+points).apply()
        return rankup, p.water_ninja_rank
    elif p.water_ninja_rank == 4 and position == 1:
        await p.update(water_ninja_progress=100).apply()
        return False, p.water_ninja_rank

async def water_ninja_rank_up(p, ranks=1):
    if p.water_ninja_rank + ranks > len(CardJitsuWaterLogic.ItemAwards):
        return False
    for rank in range(p.water_ninja_rank, p.water_ninja_rank+ranks):
        await p.add_inventory(p.server.items[CardJitsuWaterLogic.ItemAwards[rank]], notify=False)
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
        p.waddle.timer_task = asyncio.create_task(set_interval(1, p.waddle.tick_timer))


@handlers.handler(XTPacket('zm', ext='z'), match=['110'])
@handlers.waddle(CardJitsuWaterLogic, WaterMatLogic, WaterSenseiLogic)
async def handle_choose_card(p, *, card_id: int):
    print(f"Player Card Data{card_id}")
    ninja = p.waddle.get_ninja_by_penguin(p)
    await p.waddle.card_selected(ninja, card_id)


@handlers.handler(XTPacket('zm', ext='z'), match=['120'])
@handlers.waddle(CardJitsuWaterLogic, WaterMatLogic, WaterSenseiLogic)
async def handle_player_move(p, action: str, cell_id: int):
    ninja = p.waddle.get_ninja_by_penguin(p)
    available_cells = p.waddle.get_playable_cells(ninja)
    available_cells_by_id = {i.id: i for i in available_cells}

    if cell_id not in available_cells_by_id:
        print(cell_id, available_cells_by_id.keys(), ninja.cell.id)
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
       
        print("ROWS:",last_row.index, row)
        ninja.position = 1
        progress, rank = await water_ninja_progress(ninja.penguin, ninja.position)
        print("Penguin Progress", progress, rank)
        await p.waddle.send_zm("gw", ninja.seat_id, 1,  '{}{}'.format(int(progress), rank), 'false')
        ninja.winner = True
        p.waddle.started = False
        return await p.waddle.game_over()



@handlers.handler(XTPacket('lz', ext='z'))
@handlers.waddle(CardJitsuWaterLogic, WaterMatLogic, WaterSenseiLogic)
async def handle_leave_match(p):
    p.waddle.started = False
 
@handlers.handler(XTPacket('zm', ext='z'), match=['121'])
@handlers.waddle(CardJitsuWaterLogic, WaterMatLogic, WaterSenseiLogic)
async def handle_throw_card(p, *, cell_id: int):
    ninja = p.waddle.get_ninja_by_penguin(p)
    available_cells = p.waddle.get_playable_cells(ninja)
    available_cells_by_id = {i.id: i for i in available_cells}

    if cell_id not in available_cells_by_id:
        print(cell_id, available_cells_by_id.keys(), ninja.cell.id)
        
        return await p.waddle.send_zm_client(ninja, 'pf', '{}-{}'.format(ninja.seat_id, cell_id))

    cell = available_cells_by_id[cell_id]
    if (ninja.chosen is None) or not cell.can_jump():
        print(ninja.chosen, cell.can_jump())
        return await p.waddle.send_zm_client(ninja, 'pf', '{}-{}'.format(ninja.seat_id, cell_id))
            
    card = ninja.chosen
    won = ((3 + p.waddle.rule_set[card.element] - (cell.type+1)) % 3 - 1) if cell.type != 3 else -1

    print("CJ WIN:", card.element, cell.type, won)

    if won > 0:
        return await p.waddle.send_zm_client(ninja, 'pf', '{}-{}'.format(ninja.seat_id, cell_id))

    ninja.chosen = None

    value_del = card.value * (-1 if won != -1 else 1)
    cell.update_value(value_del)
    if cell.type == 3 and cell.value > 0:
        cell.type = p.waddle.rule_set[card.element]-1
        ninja.jumps += 1

    print("ValDel:", value_del, cell.value)

    row, col = cell.id//10, cell.id%10
    cells = [i for i in p.waddle.get_nearby_cells(row, col)[:6] if i.can_jump() and i.id != ninja.cell.id]
    for i in cells:
        cell_win = ((3 + p.waddle.rule_set[card.element] - (i.type+1)) % 3 - 1) if i.type != 3 else -1
        if cell_win < 1 and card.value >= 9:
            i.type = cell.type if i.type == 3 else i.type
            i.update_value(card.value * (-1 if cell_win == -1 else 1) if cell.type == p.waddle.rule_set[card.element] else 0) 

    cells.insert(0, cell)
        
    await p.waddle.send_zm('pt', ninja.seat_id, '{}-{}'.format(p.waddle.rule_set[card.element]-1, cell.id), '|'.join(map(str, cells)))

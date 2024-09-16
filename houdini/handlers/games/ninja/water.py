"""Module for all the logic of the Card-Jitsu Water game"""

import enum
import asyncio
from dataclasses import dataclass, field
from random import choice, randint, shuffle
from typing import List, Generator, Union
from collections import deque

from houdini import IWaddle, handlers
from houdini.handlers import XTPacket
from houdini.penguin import Penguin
from houdini.data.ninja import Card


@dataclass
class WaterCard:
    """Interface for a card used in Card-Jitsu Water"""

    card: Card
    """Reference to the Card-Jitsu card"""

    hand_id: int
    """ID which must be unique from all other cards in the player's hand"""

    def serialize(self) -> str:
        """Serialize data for the client"""
        return f"{self.card.id}-{self.hand_id}"


class CellType(enum.IntEnum):
    """
    All valid types for a cell.
    The exact numbers are important and match the values used by the client
    """
    FIRE = 0
    WATER = 1
    SNOW = 2
    EMPTY = 3
    OBSTACLE = 4  # Unused normally


class Cell:
    """Represents a cell or "stone" in a board of Card-Jitsu Water"""

    AMOUNT_DISTRIBUTION = [
        *([2] * 2),
        *([3] * 3),
        *([4] * 4),
        *([5] * 6),
        *([6] * 3),
        7,
        8,
    ]
    """
    Distribution which corresponds to how the vanilla game
    generated the element amounts randomly
    """

    @classmethod
    def get_random_amount(cls) -> int:
        """Generate a random amount of element using the amount distribution"""
        return choice(cls.AMOUNT_DISTRIBUTION)

    uid: int
    """
    Unique ID which must be different from all other cells in the board

    It follows the format: Row ID * 10 + Column index
    """

    cell_type: CellType

    amount: int
    """A number between 0 and 20 including that describes the amount of element in it"""

    has_player: bool = False
    """If a player is in this cell"""

    def __init__(self, uid: int, cell_type: CellType, start: bool = False):
        """
        start being True generates all elements being 2, which matches the original's game
        behavior for the first row with elements
        """
        self.uid = uid
        self.cell_type = cell_type

        if cell_type == CellType.EMPTY:
            self.amount = 0
        elif start:
            self.amount = 2
        else:
            self.amount = self.get_random_amount()

    def can_jump(self) -> bool:
        """Check if a penguin can jump to this cell"""
        return self.cell_type == CellType.EMPTY and not self.has_player

    def update_amount(self, delta: int):
        """Update the amount of element given an incoming delta"""
        self.amount = max(0, min(self.amount + delta, 20))
        if self.amount == 0:
            self.cell_type = CellType.EMPTY

    def serialize(self) -> str:
        """Serialize data for the client"""
        return f"{self.uid}-{self.cell_type}-{self.amount}"


@dataclass
class Row:
    """Class for a row of stones of a Card-Jitsu Water game board"""

    uid: int
    """
    Unique row ID which must be different from other rows
    (and > 0, and incrementing for each new row, other parts rely on this behavior)
    """

    cells: List[Cell] = field(default_factory=list)

    def __getitem__(self, i):
        return self.cells[i]

    def generate_cells(self, columns: int, empty=False, start=False):
        """
        Generate all cells in the row

        empty should be True if all cells must be empty

        start should be True if this is to be generated as the first row with elements
        """
        self.cells = [
            Cell(
                # specific format used by cell ids
                int(f"{self.uid}{i}"),
                # element chance is uniform
                randint(CellType.FIRE, CellType.SNOW) if not empty else CellType.EMPTY,
                start=start,
            )
            for i in range(columns)
        ]

    def serialize(self) -> str:
        """Serialize for the client"""
        return ",".join([cell.serialize() for cell in self.cells])


@dataclass
class Board:
    """Class for the board of stones in a Card-Jitsu Water game"""

    columns: int
    """Number of columns in the board"""

    row_cumulative: int = 0
    """
    Total rows ever added to this board, not the number of rows in the board
    (for that use len(rows))
    """

    rows: deque[Row] = field(default_factory=deque)

    rows_by_id: dict = field(default_factory=dict)
    """Map of the row IDs to their row instance"""

    def __getitem__(self, i):
        return self.rows[i]

    def generate_row(self, empty=False, start=False) -> tuple[bool, Union[None, Row]]:
        """Generate a new row, remove extra rows"""
        self.row_cumulative += 1
        row = Row(uid=self.row_cumulative)
        row.generate_cells(self.columns, empty=empty, start=start)
        self.rows.append(row)
        self.rows_by_id[row.uid] = row

        # 9 is the max number in vanilla (there are always 2 offscreen rows)
        if len(self.rows) > 9:
            pop_row = self.rows.popleft()
            if pop_row.uid in self.rows_by_id:
                del self.rows_by_id[pop_row.uid]

            return True, pop_row

        return False, None

    def get_cell(self, row: int, col: int) -> Cell:
        """Get a cell in a given row and column INDEX (not ID)"""
        return self[row][col]

    def get_nearby_cells(self, cell: Cell) -> List[Cell]:
        """Get all cells adjacent to a cell"""
        row_id, col_index = cell.uid // 10, cell.uid % 10
        if row_id not in self.rows_by_id:
            return []

        playable_cells = set()
        for i in range(max(0, col_index - 1), min(self.columns, col_index + 2)):
            for j in [-1, 1]:
                other_row_id = row_id + j
                if other_row_id in self.rows_by_id:
                    playable_cells.add(self.rows_by_id[other_row_id][i])

            if i != col_index:
                playable_cells.add(self.rows_by_id[row_id][i])

        return list(playable_cells)

    def serialize(self) -> str:
        """Serialize data for the client"""
        return "|".join([row.serialize() for row in self.rows])


@dataclass
class WaterPlayerHand:
    """Organizes the card information for a player"""

    card_generator: Generator[WaterCard, None, None]
    """Generator that gives the next card when called"""

    chosen_card: Union[WaterCard, None] = None
    """Card the player is ready to throw or None"""

    cards: deque[WaterCard] = field(default_factory=deque)
    """Cards currently on hand"""


@dataclass
class WaterPlayer:
    """Interface for a player of Card-Jitsu Water"""

    penguin: Penguin
    """The player's penguin"""

    seat_id: int
    """Index of the order that they entered in the match"""

    hand: WaterPlayerHand
    """Player card info"""

    joined: bool = False

    ready: bool = False

    cell: Union[Cell, None] = None
    """Cell this penguin is standing on"""

    two_close: int = 0
    """Number of times that almost slipped (for Two Close stamp)"""

    cleared: int = 0
    """Number of stones cleared in the match"""

    def get_card(self, hand_id: int) -> WaterCard:
        """Get the card given its hand ID"""
        return next((card for card in self.hand.cards if card.hand_id == hand_id), None)

    def jump(self, cell: Cell):
        """Jump to a given cell"""
        if self.cell is not None:
            self.cell.has_player = False
        cell.has_player = True
        self.cell = cell


class WaterSensei(WaterPlayer):
    """Class for the player that controls Sensei"""


class WaterCycleHandler:
    """
    Class handles the tasks that happen in cycles with objects moving in Card-Jitsu Water

    The cards and stones moving work with a velocity in an odd unit system which this class
    takes care off
    """

    period: float
    """The time between cycles in second (eg, two new rows being spawned)"""

    progress: float
    """From 0 to 1, how far into the current cycle we are"""

    update_frequency: float
    """The value used by the client for the update frequency of the cycle"""

    distance: int
    """The distance traveled by the object, in pixels, throughout the cycle"""

    TICKS_PER_SECOND: float = 1000
    """Constant value from the client"""

    FRAME_RATE: int = 24
    """Constant value from the client"""

    def __init__(self, period: float, update_frequency: float, distance: int):
        self.period = period
        self.update_frequency = update_frequency
        self.distance = distance
        self.progress = 0

    def get_client_velocity(self) -> int:
        """
        The value for the "velocity" of the object to be sent to the client

        It has very specific units of pixel tick^2 frame^-1 second^-1
        and it is unknown why the original club penguin handled it this way

        If one wishes to change the speed, they should not mess with this, and instead
        should use the change_period method
        """
        return int(
            (self.distance * self.TICKS_PER_SECOND ** 2)
            / (self.update_frequency * self.FRAME_RATE * self.period)
        )

    def update(self, time_delta: float) -> bool:
        """
        Update the cycle based on how much time passed since the last one

        Return True if the cycle was met this update
        """
        updated = False
        # epsilon to avoid possible jittering due to float imprecision
        if self.progress + 1e-6 > 1:
            updated = True
            # avoid negative from epsilon
            self.progress = max(0, self.progress - 1)
        self.progress += time_delta / self.period
        return updated

    def change_period(self, new_period: float):
        """Change the period of the cycle"""
        self.progress *= self.period / new_period
        self.period = new_period


class Amulet:
    """Amulet is a value the client uses to know when to award ranks"""

    amulet_state: int
    """
    Uses bit operations to know which elements you have mastered for the water gem cutscene
    
    This number should not be supplied if someone is a water ninja, otherwise it will assume
    they are gaining the water gem every game

    Otherwise it does not matter if you give it or not
    """

    rank_awarded: int
    """Rank being given, or 0 if did not rank up this match"""

    def __init__(self, penguin: Penguin, is_ranking_up: bool):
        if is_ranking_up:
            self.amulet_state = Amulet.get_amulet_state(penguin)
            self.rank_awarded = penguin.water_ninja_rank
        else:
            self.amulet_state = 0
            self.rank_awarded = 0

    @staticmethod
    def get_amulet_state(p: Penguin) -> int:
        """Gets the proper amulet state based on how the client does the operations"""
        amulet = 0
        if p.fire_ninja_rank >= 5:
            amulet += 1
        if p.water_ninja_rank >= 5:
            amulet += 2
        if p.snow_ninja_rank >= 13:
            amulet += 4
        return amulet

    def serialize(self) -> str:
        """Serialize for the client"""
        return f"{self.amulet_state}{self.rank_awarded}"


class CardJitsuWaterLogic(IWaddle):
    """Logic for a Card-Jitsu Water match"""

    room_id = 995

    AVAILABLE_CARDS = {
        *range(1, 114),
        *range(201, 261),
        *range(301, 428),
        *range(501, 596),
    }
    """
    The modern client only accepts these cards, any other ID is displayed as undefined
    """

    SLEEP_TIME = 0.1
    """
    How fast (in seconds) the server sends data to the client

    Anything greater than 1 second is at great risk of deteriorating the player experience

    If 0.1 is too low for your server, 1 should be fine under normal settings
    """

    CARD_ELEMENTS = {"f": CellType.FIRE, "w": CellType.WATER, "s": CellType.SNOW}
    """Maps the card element from the Card class onto the element for the cell"""

    ITEM_AWARDS = [6026, 4121, 2025, 1087, 3032]
    """All the items gained from ranking, indexed by their rank"""

    STAMP_AWARDS = {1: 278, 3: 282, 4: 284}
    """Map rank and the stamp you gain from LEAVING the rank"""

    board_cycle_handler: WaterCycleHandler
    """Handles the cycle of new rows spawning/disappearing"""

    card_cycle_handler: WaterCycleHandler
    """Handles the cycle of cards being added to the hand"""

    BOARD_VELOCITY_SLOPE: float = 0.5
    """
    The slope of the line that connects the cells in the board
    (in flash's coordinate orientation, so increasing y means going down)

    This is a constant value obtained from the client
    """

    player_total: int
    """Number of players at the start of the game"""

    card_amount = 5
    """
    Number of cards picked by each player (eg, 5 is everyone has picked 5)

    5 matches how many cards you had at the start in original
    """

    countdown_task: Union[asyncio.Task, None] = None
    """Task that updates the countdown at the start"""

    timer: int = 60
    """Timer to start the match (in original starts at 60)"""

    started: bool = False

    board: Board

    game_loop: Union[asyncio.Task, None] = None
    """Loop that handles updating the game"""

    players: List[WaterPlayer]

    def __init__(self, waddle):
        super().__init__(waddle)

        self.players = [
            WaterPlayer(p, seat_id, WaterPlayerHand(self.get_card_generator(p)))
            for seat_id, p in enumerate(waddle.penguins)
        ]

        self.player_total = len(self.players)

        # The last two values are from the client, so one should not change them
        # The time period was determined from reverse engineering videos, and it looks
        # very reasonable, but can be tweaked if desired
        self.board_cycle_handler = WaterCycleHandler(7.0, 50.0, 58)
        self.card_cycle_handler = WaterCycleHandler(2.0, 42.0, 128)

        # number of columns depends on number of players (this is how it was in
        # original)
        self.board = Board(columns=5 if len(waddle.penguins) <= 2 else 7)

    async def send_zm(self, *args):
        """Send a "zm" packet, used for various commands, to the clients"""
        await self.send_xt("zm", "&".join(map(str, args)))

    async def send_zm_client(self, player: WaterPlayer, *args):
        """Send a "zm" packet, used for various commands, to a specific client"""
        await player.penguin.send_xt("zm", "&".join(map(str, args)))

    def get_player_by_penguin(self, penguin: Penguin) -> WaterPlayer:
        """Get the player instance associated with a penguin"""
        return next(player for player in self.players if player.penguin == penguin)

    def get_card_generator(self, p: Penguin) -> Generator[WaterCard, None, None]:
        """Get a generator for a player's cards"""
        cards = list(
            filter(lambda x: x.card_id in self.AVAILABLE_CARDS, list(p.cards.values()))
        )
        current_queue = []

        while True:
            if len(current_queue) == 0:
                current_queue = list(cards)
                shuffle(current_queue)
            yield p.server.cards[current_queue.pop().card_id]

    async def initiate_board(self):
        """Send initial board configuration to client"""
        # vanilla board structure
        # (only 6 rows are actually visible but 8 need to be on the client's memory):
        # 2 empty rows
        for _ in range(2):
            self.board.generate_row(empty=True)

        # 1 row with rigged rng
        self.board.generate_row(start=True)

        # 5 random rows
        for _ in range(5):
            self.board.generate_row()

        # CMD_BOARD_INIT
        await self.send_zm("bi", self.board.columns, self.board.serialize())

        # matching how the penguins start in original
        start_x_pos = [1, 3, 5] if len(self.penguins) <= 3 else [1, 2, 4, 5]
        for i, player in enumerate(self.players):
            player.jump(self.board.get_cell(1, start_x_pos[i]))

    async def update_board_velocity(self):
        """Update the client's board velocity"""
        # CMD_BOARD_VELOCITY
        speed_x = self.board_cycle_handler.get_client_velocity()
        await self.send_zm("bv", speed_x, speed_x * self.BOARD_VELOCITY_SLOPE)

    async def update_card_velocity(self):
        """Update the client card's velocity"""
        # CMD_CARD_VELOCITY
        await self.send_zm("cv", self.card_cycle_handler.get_client_velocity(), 0)

    async def initiate_player_cards(self):
        """Send player card data to the client at the start of the game"""
        for player in self.players:
            if isinstance(player, WaterSensei):
                continue

            player.hand.cards = deque(
                [
                    WaterCard(card=next(player.hand.card_generator), hand_id=i)
                    for i in range(self.card_amount)
                ]
            )

            # CMD_CARD_INIT
            # cards parameter format is as defined in water.swf
            # GameCardCollection.build
            await self.send_zm_client(
                player, "ci", "|".join([card.serialize() for card in player.hand.cards])
            )

    async def initiate_player(self):
        """Send player data to the client at the start of the game"""
        player_init_data = []
        for player in self.players:
            # players are in the "6th" row at the start
            # can do this modulus because of how the id is calculated
            row, col = 6, player.cell.uid % 10
            name, color = "", ""

            if isinstance(player, WaterSensei):
                name, color = "Sensei", "14"  # Gray
            else:
                name, color = player.penguin.safe_name, str(player.penguin.color)

            player_init_data.append(
                "|".join([str(player.seat_id), name, color, f"{col},{row}"])
            )

        # PLAYER_INIT
        await self.send_zm("pi", *player_init_data)

    def shutdown(self):
        """Shut down all tasks in progress"""
        if self.game_loop is not None:
            self.game_loop.cancel()
        if self.countdown_task is not None:
            self.countdown_task.cancel()

    async def update_player_progress(
        self,
        player: WaterPlayer,
        fell: bool = False,
        position: Union[int, None] = None
    ) -> Amulet:
        """
        Update the Card-Jitsu Water progress for a player after they reach the end
        """
        penguin = player.penguin
        if player in self.players:
            if position is None:
                position = len(self.players)
            self.players.remove(player)

            if penguin.water_ninja_rank < 4:
                # points obtained from heavy research from youtube videos
                points = [[48, 16], [56, 40, 16], [64, 48, 40, 0]][
                    self.player_total - 2
                ][position - 1]

                # in original you get ~62.5% of the exp if you fall
                points = points * 5 // 8 if fell else points

                await penguin.update(
                    water_ninja_progress=penguin.water_ninja_progress + points
                ).apply()

                if penguin.water_ninja_progress >= get_water_rank_threshold(
                    penguin.water_ninja_rank + 1
                ):
                    await self.water_ninja_rank_up(penguin)
                    return Amulet(penguin, True)

        return Amulet(penguin, False)

    async def gong_game_over(self, winner: WaterPlayer):
        """When someone hits the gong"""
        self.started = False  # end loop

        # game won needs to be sent first as to force the game to stop for the clients
        # CMD_GAME_WON
        amulet = await self.update_player_progress(winner, position=1)

        await self.send_zm(
            "gw",
            winner.seat_id,
            1,
            amulet.serialize(),
            "false",
        )

        if not isinstance(winner, WaterSensei):
            await winner.penguin.update(
                water_matches_won=winner.penguin.water_matches_won + 1
            ).apply()

            if winner.penguin.water_matches_won >= 100:
                # Water Expert stamp
                await winner.penguin.add_stamp(winner.penguin.server.stamps[276])

            # Gong! stamp
            await winner.penguin.add_stamp(winner.penguin.server.stamps[270])

            if winner.two_close >= 2:
                # Two Close stamp
                await winner.penguin.add_stamp(winner.penguin.server.stamps[286])

        # iterate over all players that drowned from the last place order
        for row in self.board.rows:
            if len(self.players) < 1:
                break
            players_in_row = self.get_players_in_row(row)
            for player in players_in_row:
                if isinstance(player, WaterSensei):
                    continue

                # because winner has already been removed
                position = len(self.players) + 1
                amulet = await self.update_player_progress(
                    player, position=position
                )

                # CMD_PLAYER_DROWNED (players who lose without falling)
                await self.send_zm(
                    "pd",
                    player.seat_id,
                    position,
                    amulet.serialize(),
                    "false",
                )

        self.shutdown()

    @classmethod
    async def water_ninja_rank_up(cls, p: Penguin, ranks: int = 1) -> bool:
        """
        Updates a Card-Jitsu Water rank for a penguin

        Returns whether or not the player was able to rank up
        """
        if p.water_ninja_rank + ranks > len(cls.ITEM_AWARDS):
            return False
        for rank in range(p.water_ninja_rank, p.water_ninja_rank + ranks):
            await p.add_inventory(
                p.server.items[cls.ITEM_AWARDS[rank]], cost=0, notify=False
            )
            if rank in cls.STAMP_AWARDS:
                await p.add_stamp(p.server.stamps[cls.STAMP_AWARDS[rank]])

        await p.update(water_ninja_rank=p.water_ninja_rank + ranks).apply()
        return True

    def get_players_in_row(self, row: Row) -> List[WaterPlayer]:
        """Get list of all players in row"""
        return [player for player in self.players if row.uid == player.cell.uid // 10]

    async def cycle_row(self):
        """Adds a new row, removing any extra rows"""
        dropped, drop_row = self.board.generate_row()
        if dropped:
            players_in_row = self.get_players_in_row(drop_row)
            position = len(self.players)
            for player in players_in_row:
                if player.penguin is not None:
                    # Watery Fall stamp
                    await player.penguin.add_stamp(player.penguin.server.stamps[274])

            # CMD_PLAYER_KILL, meant for players who lose from falling
            player_kill_data = []
            for player in players_in_row:
                amulet = await self.update_player_progress(
                    player, fell=True, position=position
                )
                player_kill_data.append(
                    f"pk&{player.seat_id}&{position}&{amulet.serialize()}&false"
                )

            await self.send_zm(":".join(player_kill_data))

        # for Two Close stamp
        # it starts at 8 rows, and then stagnates at 9
        # so if there still aren't 9 rows you can't possibly
        # be close to slipping
        if len(self.board.rows) == 9:
            slipping_row = self.board.rows[0]
            players_nearly_slipping = self.get_players_in_row(slipping_row)
            for player in players_nearly_slipping:
                player.two_close += 1

        # CMD_BOARD_NEWROW
        await self.send_zm("br", self.board[-1].serialize())

    async def cycle_card(self):
        """Adds a new card to the hand of all players, removing any extras"""
        self.card_amount += 1
        for player in self.players:
            if isinstance(player, WaterSensei):
                continue

            card = WaterCard(
                card=next(player.hand.card_generator),
                hand_id=self.card_amount
            )

            # a bit of a magic number (9) but it's the correct one
            if len(player.hand.cards) > 9:
                pop_card = player.hand.cards.popleft()

                if (
                    player.hand.chosen_card is not None
                    and pop_card.hand_id == player.hand.chosen_card.hand_id
                ):
                    player.hand.chosen_card = None

            player.hand.cards.append(card)

            # CMD_CARD_ADD
            await self.send_zm_client(player, "ca", card.serialize())

    async def game_loop_task(self):
        """Task that sends game information to the players"""
        await asyncio.gather(self.update_board_velocity(), self.update_card_velocity())
        while self.started:
            # all players disconnected
            if all([penguin is None for penguin in self.penguins]):
                self.shutdown()
                return

            if self.board_cycle_handler.update(CardJitsuWaterLogic.SLEEP_TIME):
                await self.cycle_row()
            if self.card_cycle_handler.update(CardJitsuWaterLogic.SLEEP_TIME):
                await self.cycle_card()

            await asyncio.sleep(CardJitsuWaterLogic.SLEEP_TIME)

    def get_playable_cells(self, player: WaterPlayer) -> dict[int, Cell]:
        """Get a map of all the cells around a player"""
        available_cells = self.board.get_nearby_cells(player.cell)
        available_cells_by_id = {i.uid: i for i in available_cells}
        return available_cells_by_id

    def start_game_loop(self):
        """Starts the loop that handles the game"""
        self.game_loop = asyncio.create_task(self.game_loop_task())

    async def tick_count_down(self):
        """Task that counts down the waiting timer at the start of the game"""
        while True:
            # tt = COUNT_DOWN_TICK
            await self.send_zm("tt", self.timer)
            self.timer -= 1

            if self.timer < -1:
                self.started = True
                await self.initiate_player()
                self.start_game_loop()
                self.countdown_task.cancel()
                return

            # should not be possible
            elif self.timer < -2:
                # GAME_CONNECTION_ERROR
                await self.send_zm("ge")
                await self.shutdown()
            await asyncio.sleep(1)

    async def select_card(self, player: WaterPlayer, card_id: int):
        """A player selects (clicks) a card and make it ready to throw"""
        player.hand.chosen_card = player.get_card(card_id)

    def get_card_result_on_cell(self, cell: Cell, card: Card) -> int:
        """
        To be applied in non-empty cell, returns:

        0 if card element = cell element
        1 if card element beats cell element
        2 if card element can't beat cell element
        """
        return (self.CARD_ELEMENTS[card.element] - (cell.cell_type) + 3) % 3

    def affect_neighbor_cells(self, cell: Cell, card: Card, affected: List[Cell]):
        """
        Uses a card on a cell and add all neighbor cells that are affected
        to a given list
        """
        # power cards (which have value > 9) deal 4 value to neighbors
        # as it was in vanilla club penguin
        POWER_CARD_AMOUNT = 4

        if card.value < 9:
            return

        neighbor_cells = self.board.get_nearby_cells(cell)
        for neighbor_cell in neighbor_cells:
            if (
                neighbor_cell.has_player
                or neighbor_cell.cell_type == CellType.EMPTY
            ):
                continue

            result = self.get_card_result_on_cell(neighbor_cell, card)
            if result != 2:
                affected.append(neighbor_cell)
                neighbor_cell.update_amount(
                    POWER_CARD_AMOUNT * (-1 if result == 1 else 1)
                )


class WaterSenseiLogic(CardJitsuWaterLogic):
    """Logic for a Card-Jitsu Water match against Sensei"""

    sensei_loop: Union[asyncio.Task, None] = None
    """Loop that controls Sensei's AI"""

    def __init__(self, waddle):
        super().__init__(waddle)

        self.players.append(WaterSensei(None, 1, None, joined=True, ready=True))

    async def sensei_ai(self):
        """Task that controls Sensei's moves"""
        penguin = self.players[0].penguin
        element_decks = {}

        for element in ["f", "w", "s"]:
            element_decks[element] = [
                card for card in penguin.server.cards.values()
                if card.element == element
            ]

        sensei = self.players[1]
        previous_move = None  # for object permanence

        while self.started:
            if penguin.water_ninja_rank < 4:  # make sensei lock in
                await asyncio.sleep(0.5)
            else:
                await asyncio.sleep(3)

            row_id, col_index = sensei.cell.uid // 10, sensei.cell.uid % 10
            next_row_id = row_id + 1

            move = None
            if previous_move is not None and not previous_move.has_player:
                move = previous_move
            else:
                possible_moves = [
                    i for i in filter(
                        lambda cell: not cell.has_player,
                        [
                            self.board.rows_by_id[next_row_id][i]
                            for i in range(
                                max(0, col_index - 1),
                                min(self.board.columns, col_index + 2),
                            )
                        ],
                    )
                ]
                empty_moves = [
                    move for move in possible_moves if move.cell_type == CellType.EMPTY
                ]
                move = (
                    choice(possible_moves)
                    if len(empty_moves) == 0
                    else choice(empty_moves)
                )
                previous_move = None

            use_card = move.cell_type != CellType.EMPTY
            affected_cells = []
            opposite_element = ""

            if use_card:
                opposite_element = {
                    CellType.FIRE: "w",
                    CellType.WATER: "s",
                    CellType.SNOW: "f",
                }[move.cell_type]

                used_card = choice(element_decks[opposite_element])
                move.update_amount(-used_card.value)
                affected_cells.append(move)
                self.affect_neighbor_cells(move, used_card, affected_cells)

            # technically, this algo doesnt account for the novel case
            # in which a cell adjacent is freed up, but the main one doesnt
            do_move = move.cell_type == CellType.EMPTY
            if do_move:
                sensei.jump(move)
            else:
                # save so sensei will try this one next time again
                previous_move = move

            if use_card:
                await self.send_zm(
                    "pt",
                    sensei.seat_id,
                    f"{opposite_element}-{move.uid}",
                    "|".join([cell.serialize() for cell in affected_cells]),
                )

            if do_move:
                await self.send_zm("pm", f"{sensei.seat_id}-{move.uid}")

            # - 2 because two rows are off-screen
            if self.board.rows[-1].uid - 2 == next_row_id:
                await self.gong_game_over(sensei)

    def start_game_loop(self):
        super().start_game_loop()
        self.sensei_loop = asyncio.create_task(self.sensei_ai())

    def shutdown(self):
        super().shutdown()

        if self.sensei_loop is not None:
            self.sensei_loop.cancel()

    async def update_player_progress(
        self,
        player: WaterPlayer,
        position=None,
        fell: bool = False
    ) -> Amulet:
        self.players.remove(player)
        if isinstance(player, WaterSensei):
            return Amulet(player.penguin, False)

        if position == 1 and player.penguin.water_ninja_rank == 4:
            await self.water_ninja_rank_up(player.penguin)
            return Amulet(player.penguin, True)

        return Amulet(player.penguin, False)


def get_water_rank_threshold(rank):
    """Get the amount of experience needed to reach this rank"""
    try:
        return [0, 128, 512, 1536, 3584][rank]
    except:
        return


@handlers.handler(XTPacket("gz", ext="z"))
@handlers.waddle(CardJitsuWaterLogic, WaterSenseiLogic)
async def handle_get_game(p: Penguin):
    """Handle the client entering the game"""
    seat_id = p.waddle.get_seat_id(p)
    player = p.waddle.get_player_by_penguin(p)

    # needs to send these or the client dies
    await p.send_xt("gz")
    await p.send_xt("jz")

    # CMD_PLAYER_INDEX
    await p.waddle.send_zm_client(player, "po", seat_id)

    start_game = False
    if isinstance(p.waddle, CardJitsuWaterLogic):
        # to wait until all have joined
        player.joined = True
        start_game = all(player.joined for player in p.waddle.players)
    elif isinstance(p.waddle, WaterSenseiLogic):
        start_game = True

    if start_game:
        await p.waddle.initiate_board()
        await p.waddle.initiate_player_cards()


@handlers.handler(XTPacket("zm", ext="z"), match=["103"])
@handlers.waddle(CardJitsuWaterLogic, WaterSenseiLogic)
async def handle_start_game(p: Penguin):
    """Handle the client being ready to play"""
    player = p.waddle.get_player_by_penguin(p)
    player.ready = True

    if not p.waddle.countdown_task:
        p.waddle.countdown_task = asyncio.create_task(p.waddle.tick_count_down())

    if all(map(lambda player: player.ready, p.waddle.players)):
        p.waddle.timer = 3


@handlers.handler(XTPacket("zm", ext="z"), match=["110"])
@handlers.waddle(CardJitsuWaterLogic, WaterSenseiLogic)
async def handle_choose_card(p: Penguin, *, card_id: str):
    """Handle a player clicking on a card (which leaves it on a state where it is ready to use)"""
    player = p.waddle.get_player_by_penguin(p)
    await p.waddle.select_card(player, int(card_id))


@handlers.handler(XTPacket("zm", ext="z"), match=["120"])
@handlers.waddle(CardJitsuWaterLogic, WaterSenseiLogic)
async def handle_player_move(p: Penguin, *, cell_id: str):
    """Handle a player moving to a different cell/stone"""
    player = p.waddle.get_player_by_penguin(p)
    available_cells_by_id = p.waddle.get_playable_cells(player)
    cell_id = int(cell_id)

    async def send_fail():
        # CMD_PLAYER_INVALID_THROW
        await p.waddle.send_zm_client(player, "pf", f"{player.seat_id}-{cell_id}")

    if cell_id not in available_cells_by_id:
        return await send_fail()

    cell = available_cells_by_id[cell_id]

    if not cell.can_jump():
        return await send_fail()

    player.jump(cell)

    # CMD_PLAYER_MOVE
    await p.waddle.send_zm("pm", f"{player.seat_id}-{cell.uid}")

    last_row = p.waddle.board[-1]
    row_id = cell.uid // 10

    # -2 because there are always two off-screen rows
    if last_row.uid - 2 == row_id:
        return await p.waddle.gong_game_over(player)


@handlers.handler(XTPacket("lz", ext="z"))
@handlers.waddle(CardJitsuWaterLogic, WaterSenseiLogic)
async def handle_leave_match(p: Penguin):
    """Sent by the players if they close the game"""


@handlers.handler(XTPacket("zm", ext="z"), match=["121"])
@handlers.waddle(CardJitsuWaterLogic, WaterSenseiLogic)
async def handle_throw_card(p: Penguin, *, cell_id: str):
    """Handle client using/throwing a card on a cell"""
    player: WaterPlayer = p.waddle.get_player_by_penguin(p)
    available_cells_by_id = p.waddle.get_playable_cells(player)
    cell_id = int(cell_id)

    async def send_fail():
        # CMD_PLAYER_INVALID_THROW
        await p.waddle.send_zm_client(player, "pf", f"{player.seat_id}-{cell_id}")

    if cell_id not in available_cells_by_id:
        return await send_fail()

    cell = available_cells_by_id[cell_id]
    if (player.hand.chosen_card is None) or cell.has_player:
        return await send_fail()

    card = player.hand.chosen_card

    if cell.cell_type != CellType.EMPTY:
        result = p.waddle.get_card_result_on_cell(cell, card.card)
        if result == 2:
            return await send_fail()
        else:
            value_delta = card.card.value * (-1 if result == 1 else 1)
            cell.update_amount(value_delta)

    player.hand.chosen_card = None

    affected_cells = [cell]

    p.waddle.affect_neighbor_cells(cell, card.card, affected_cells)

    # all cleared cells count for stamp (from og club penguin)
    player.cleared += sum(
        [1 if c.cell_type == CellType.EMPTY else 0 for c in affected_cells]
    )

    if player.cleared >= 28:
        # Skipping Stones stamp
        await player.penguin.add_stamp(player.penguin.server.stamps[288])

    # CMD_PLAYER_THROW
    await p.waddle.send_zm(
        "pt",
        player.seat_id,
        f"{p.waddle.CARD_ELEMENTS[card.card.element]}-{cell.uid}",
        "|".join([cell.serialize() for cell in affected_cells]),
    )


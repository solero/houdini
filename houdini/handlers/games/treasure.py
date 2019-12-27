from houdini import handlers
from houdini.handlers import XTPacket
from houdini.handlers.games.table import table_handler
from houdini.data.room import TreasureHuntLogic


@handlers.handler(XTPacket('gz', ext='z'))
@table_handler(TreasureHuntLogic)
async def handle_get_game(p):
    if len(p.table.penguins) == 2:
        player_one = p.table.penguins[0]
        await p.send_xt('gz', player_one.safe_name, str())
    else:
        await p.send_xt('gz', p.table.get_string())


@handlers.handler(XTPacket('jz',  ext='z'))
@table_handler(TreasureHuntLogic)
async def handle_join_game(p):
    game_full = len(p.table.penguins) > 2
    if not game_full:
        seat_id = p.table.get_seat_id(p)
        await p.send_xt('jz', seat_id)
        await p.table.send_xt('uz', seat_id, p.safe_name)
        if len(p.table.penguins) == 2:
            await p.table.send_xt('sz', p.table.get_string())

@handlers.handler(XTPacket('zm', ext='z'))
@table_handler(TreasureHuntLogic)
async def handle_send_move(p, movie: str, direction: str, spade: int):
    try:
        seat_id = p.table.get_seat_id(p)
        is_player = seat_id < 2
        game_ready = len(p.table.penguins) > 1
        if is_player and game_ready:
            current_player = p.table.penguins[p.table.logic.current_player - 1]
            if current_player != p:
                return
            if not p.table.logic.is_valid_move(movie, direction, spade):
                return
            p.table.logic.make_move(movie, direction, spade)
            await p.table.send_xt('zm', movie, direction, spade)
            opponent = p.table.penguins[1 if p.table.logic.current_player == 1 else 0]
            if p.table.logic.turns == 0:
                winnings = p.table.logic.determine_winnings()
                await p.add_coins(winnings)
                await opponent.add_coins(winnings)
                await p.table.reset()
                return
            p.table.logic.current_player = 2 if p.table.logic.current_player == 1 else 1
    except (KeyError, ValueError):
        p.logger.warn(f'Invalid treasure hunt move made by {p}')

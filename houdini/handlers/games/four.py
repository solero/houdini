from houdini import handlers
from houdini.handlers import XTPacket
from houdini.handlers.games.table import table_handler
from houdini.data.room import ConnectFourLogic


@handlers.handler(XTPacket('gz', ext='z'))
@table_handler(ConnectFourLogic)
async def handle_get_game(p):
    await p.send_xt('gz', p.table.get_string())


@handlers.handler(XTPacket('jz',  ext='z'))
@table_handler(ConnectFourLogic)
async def handle_join_game(p):
    game_full = len(p.table.penguins) > 2
    if not game_full:
        seat_id = p.table.get_seat_id(p)
        await p.send_xt('jz', seat_id)
        await p.table.send_xt('uz', seat_id, p.safe_name)

        if len(p.table.penguins) == 2:
            await p.table.send_xt('sz')


@handlers.handler(XTPacket('zm', ext='z'))
@table_handler(ConnectFourLogic)
async def handle_send_move(p, col: int, row: int):
    try:
        seat_id = p.table.get_seat_id(p)
        is_player = seat_id < 2
        game_ready = len(p.table.penguins) > 1
        if is_player and game_ready:
            current_player = p.table.penguins[p.table.logic.current_player - 1]
            if current_player != p:
                return
            if not p.table.logic.is_valid_move(col, row):
                return
            await p.table.send_xt('zm', p.table.logic.current_player - 1, col, row)
            p.table.logic.place_chip(col, row)
            opponent = p.table.penguins[1 if p.table.logic.current_player == 1 else 0]
            if p.table.logic.is_position_win(col, row):
                await p.add_coins(10)
                await opponent.add_coins(5)
                await p.table.reset()
                return
            if p.table.logic.is_board_full():
                await p.add_coins(5)
                await opponent.add_coins(5)
                await p.table.reset()
                return
            p.table.logic.current_player = 2 if p.table.logic.current_player == 1 else 1
    except (KeyError, ValueError):
        p.logger.warn(f'Invalid connect four move made by {p}')

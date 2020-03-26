from houdini import ITable, handlers
from houdini.handlers import XTPacket




@handlers.handler(XTPacket('gz', ext='z'))
@table_handler(MancalaLogic)
async def handle_get_game(p):
    await p.send_xt('gz', p.table.get_string())


@handlers.handler(XTPacket('jz',  ext='z'))
@table_handler(MancalaLogic)
async def handle_join_game(p):
    game_full = len(p.table.penguins) > 2
    if not game_full:
        seat_id = p.table.get_seat_id(p)
        await p.send_xt('jz', seat_id)
        await p.table.send_xt('uz', seat_id, p.safe_name)

        if len(p.table.penguins) == 2:
            await p.table.send_xt('sz', 0)


@handlers.handler(XTPacket('zm', ext='z'))
@table_handler(MancalaLogic)
async def handle_send_move(p, hollow: int):
    try:
        seat_id = p.table.get_seat_id(p)
        is_player = seat_id < 2
        game_ready = len(p.table.penguins) > 1

        if is_player and game_ready:
            current_player = p.table.penguins[p.table.logic.current_player - 1]

            if current_player != p:
                return
            if not p.table.logic.is_valid_move(hollow):
                return

            move_result = p.table.logic.make_move(hollow)
            await p.table.send_xt('zm', seat_id, hollow, move_result)
            opponent = p.table.penguins[1 if p.table.logic.current_player == 1 else 0]

            if p.table.logic.is_position_win():
                await p.add_coins(10)
                await opponent.add_coins(5)
                await p.table.reset()
                return
            elif p.table.logic.is_position_tie():
                await p.add_coins(5)
                await opponent.add_coins(5)
                await p.table.reset()
                return

            p.table.logic.current_player = 2 if p.table.logic.current_player == 1 else 1
    except (KeyError, ValueError):
        p.logger.warn(f'Invalid mancala move made by {p}')

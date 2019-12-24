from houdini import handlers
from houdini.handlers import XTPacket
from houdini.handlers.games.table import table_handler
from houdini.data.room import MancalaLogic


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
            await p.table.send_xt('sz', 0) # Todo: Is this 0 needed?


@handlers.handler(XTPacket('zm', ext='z'))
@table_handler(MancalaLogic)
async def handle_send_move(p, hollow: int):
  pass # Todo

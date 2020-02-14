from houdini import handlers
from houdini.handlers import XTPacket
from houdini.handlers.games.waddle import waddle_handler
from houdini.games.sled import SledRacingLogic


@handlers.handler(XTPacket('jz', ext='z'))
@waddle_handler(SledRacingLogic)
async def handle_join_game(p):
    await p.send_xt('uz', p.waddle.seats, *(f'{penguin.safe_name}|{penguin.color}|'
                                            f'{penguin.hand or 0}|{penguin.nickname}' for penguin in p.waddle.penguins))


@handlers.handler(XTPacket('zm', ext='z'))
@waddle_handler(SledRacingLogic)
async def handle_send_move(p, player_id: int, x: float, y: float, time: float):
    await p.waddle.send_xt('zm', player_id, x, y, time)


@handlers.handler(XTPacket('zo', ext='z'))
@waddle_handler(SledRacingLogic)
async def handle_game_over(p):
    coins = p.waddle.get_payout()
    await p.add_coins(coins)

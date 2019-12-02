from houdini import handlers
from houdini.handlers import XTPacket
from houdini.data.penguin import Penguin

import random


@handlers.handler(XTPacket('r', 'cdu'))
@handlers.cooldown(1)
async def handle_get_coin_reward(p):
    if random.random() < 0.3:
        coins = random.choice([1, 2, 5, 10, 20, 50, 100])
        await p.update(coins=Penguin.coins + coins).apply()
        await p.send_xt('cdu', coins, p.coins)

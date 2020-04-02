from houdini import handlers
from houdini.handlers import XTPacket
from houdini.data.penguin import CfcDonation


@handlers.handler(XTPacket('e', 'dc'))
async def handle_donate_to_charity(p, charity: int, coins: int):
    if p.coins >= coins and 0 <= charity <= 4:
        await p.update(coins=p.coins-coins).apply()
        await CfcDonation.create(penguin_id=p.id, coins=coins, charity=charity)
        await p.send_xt('dc', p.coins)


@handlers.handler(XTPacket('e', 'sig'))
async def handle_igloo_contest_entry(p):
    if p.room.igloo and p.room.penguin_id == p.id and not p.room.competition:
        await p.room.update(competition=True).apply()

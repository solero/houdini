from houdini import IWaddle, handlers
from houdini.handlers import XTPacket


class SledRacingLogic(IWaddle):

    room_id = 999

    def __init__(self, waddle):
        super().__init__(waddle)

        self.payouts = [20, 10, 5, 5]

    async def remove_penguin(self, p):
        await super().remove_penguin(p)
        await self.send_xt('uz', self.seats, *(f'{penguin.safe_name}|{penguin.color}|'
                                               f'{penguin.hand}|{penguin.safe_name}' for penguin in self.penguins))

    def get_payout(self):
        return self.payouts.pop(0)


@handlers.handler(XTPacket('jz', ext='z'))
@handlers.waddle(SledRacingLogic)
async def handle_join_game(p):
    await p.send_xt('uz', p.waddle.seats, *(f'{penguin.safe_name}|{penguin.color}|'
                                            f'{penguin.hand or 0}|{penguin.nickname}' for penguin in p.waddle.penguins))


@handlers.handler(XTPacket('zm', ext='z'))
@handlers.waddle(SledRacingLogic)
async def handle_send_move(p, player_id: int, x: float, y: float, time: float):
    await p.waddle.send_xt('zm', player_id, x, y, time)


@handlers.handler(XTPacket('zo', ext='z'))
@handlers.waddle(SledRacingLogic)
async def handle_game_over(p):
    coins = p.waddle.get_payout()
    await p.add_coins(coins)

from houdini.games import IWaddle


class SledRacingLogic(IWaddle):

    __room_id__ = 999

    def __init__(self, waddle):
        super().__init__(waddle)

        self.payouts = [20, 10, 5, 5]

    async def remove_penguin(self, p):
        await super().remove_penguin(p)
        await self.send_xt('uz', self.seats, *(f'{penguin.safe_name}|{penguin.color}|'
                                               f'{penguin.hand}|{penguin.safe_name}' for penguin in self.penguins))

    def get_payout(self):
        return self.payouts.pop(0)

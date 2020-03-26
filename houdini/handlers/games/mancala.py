from houdini import ITable, handlers
from houdini.handlers import XTPacket


class MancalaLogic(ITable):

    def __init__(self):
        self.current_player = 1
        self.board = [
            4, 4, 4, 4, 4, 4, 0,
            4, 4, 4, 4, 4, 4, 0
        ]

    def make_move(self, hollow):
        capture = False
        hand = self.board[hollow]
        self.board[hollow] = 0

        while hand > 0:
            hollow = (hollow + 1) % len(self.board)
            my_mancala, opponent_mancala = (6, 13) if self.current_player == 1 else (13, 6)

            if hollow == opponent_mancala:
                continue
            opposite_hollow = 12 - hollow

            if hand == 1 and self.board[hollow] == 0:
                if (self.current_player == 1 and hollow in range(0, 6)) or (self.current_player == 2 and hollow in range(7, 13)):
                    self.board[my_mancala] += self.board[opposite_hollow] + 1
                    self.board[opposite_hollow] = 0
                    capture = True
                    break

            self.board[hollow] += 1
            hand -= 1

        if (self.current_player == 1 and hollow != 6) or (self.current_player == 2 and hollow != 13):
            return 'c' if capture else str()
        else:
            self.current_player = 2 if self.current_player == 1 else 1
            return 'f'

    def is_valid_move(self, hollow):
        if self.current_player == 1 and hollow not in range(0, 6):
            return False
        elif self.current_player == 2 and hollow not in range(7, 13):
            return False
        return True

    def get_string(self):
        return ','.join(map(str, self.board))

    def is_position_win(self):
        if sum(self.board[0:6]) == 0 or sum(self.board[7:-1]) == 0:
            if sum(self.board[0:6]) > sum(self.board[7:-1]):
                return self.current_player == 1
            return self.current_player == 2
        return False

    def is_position_tie(self):
        if sum(self.board[0:6]) == 0 or sum(self.board[7:-1]) == 0:
            if sum(self.board[0:6]) == sum(self.board[7:-1]):
                return True
        return False


@handlers.handler(XTPacket('gz', ext='z'))
@handlers.table(MancalaLogic)
async def handle_get_game(p):
    await p.send_xt('gz', p.table.get_string())


@handlers.handler(XTPacket('jz',  ext='z'))
@handlers.table(MancalaLogic)
async def handle_join_game(p):
    game_full = len(p.table.penguins) > 2
    if not game_full:
        seat_id = p.table.get_seat_id(p)
        await p.send_xt('jz', seat_id)
        await p.table.send_xt('uz', seat_id, p.safe_name)

        if len(p.table.penguins) == 2:
            await p.table.send_xt('sz', 0)


@handlers.handler(XTPacket('zm', ext='z'))
@handlers.table(MancalaLogic)
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

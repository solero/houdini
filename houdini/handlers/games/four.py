from houdini import ITable, handlers
from houdini.handlers import XTPacket


class ConnectFourLogic(ITable):

    def __init__(self):
        self.current_player = 1
        self.board = [[0 for _ in range(6)] for _ in range(7)]

    def make_move(self, col, row):
        self.board[col][row] = self.current_player

    def is_valid_move(self, col, row):
        if 0 <= row <= 5 and 0 <= col <= 6:
            if row == 5 or (self.board[col][row] == 0 and self.board[col][row + 1]):
                return True
        return False

    def get_string(self):
        return ','.join(str(item) for row in self.board for item in row)

    def is_position_win(self, col, row):
        for delta_row, delta_col in [(1, 0), (0, 1), (1, 1), (1, -1)]:
            streak = 1
            for delta in (1, -1):
                delta_row *= delta
                delta_col *= delta
                next_row = row + delta_row
                next_col = col + delta_col
                while 0 <= next_row < 6 and 0 <= next_col < 7:
                    if self.board[next_col][next_row] == self.current_player:
                        streak += 1
                    else:
                        break
                    if streak == 4:
                        return True
                    next_row += delta_row
                    next_col += delta_col
        return False

    def is_board_full(self):
        for col in self.board:
            if not col[0]:
                return False
        return True


@handlers.handler(XTPacket('gz', ext='z'))
@handlers.table(ConnectFourLogic)
async def handle_get_game(p):
    await p.send_xt('gz', p.table.get_string())


@handlers.handler(XTPacket('jz',  ext='z'))
@handlers.table(ConnectFourLogic)
async def handle_join_game(p):
    game_full = len(p.table.penguins) > 2
    if not game_full:
        seat_id = p.table.get_seat_id(p)
        await p.send_xt('jz', seat_id)
        await p.table.send_xt('uz', seat_id, p.safe_name)

        if len(p.table.penguins) == 2:
            await p.table.send_xt('sz')


@handlers.handler(XTPacket('zm', ext='z'))
@handlers.table(ConnectFourLogic)
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
            p.table.logic.make_move(col, row)
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

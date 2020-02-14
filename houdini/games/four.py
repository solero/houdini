from houdini.games import ITable


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

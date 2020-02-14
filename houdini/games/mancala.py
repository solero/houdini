from houdini.games import ITable


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

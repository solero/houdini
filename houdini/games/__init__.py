from abc import ABC
from abc import abstractmethod


class ITable(ABC):
    """
    All table game logic classes must implement this interface.
    """

    @abstractmethod
    def make_move(self, *args):
        """Tells logic a move has been made."""

    @abstractmethod
    def is_valid_move(self, *args):
        """Returns true if the move is valid."""

    @abstractmethod
    def get_string(self):
        """Returns string representation of the game."""


class IWaddle(ABC):
    """
    All waddle game logic classes must implement this interface.
    """

    @property
    @abstractmethod
    def __room_id__(self):
        """External ID of waddle game room."""

    def __init__(self, waddle):
        self.penguins = list(waddle.penguins)
        self.seats = waddle.seats

    async def start(self):
        room_id = type(self).__room_id__
        for penguin in self.penguins:
            penguin.waddle = self
            await penguin.join_room(penguin.server.rooms[room_id])

    async def remove_penguin(self, p):
        self.penguins.remove(p)
        p.waddle = None

    async def send_xt(self, *data):
        for penguin in self.penguins:
            await penguin.send_xt(*data)

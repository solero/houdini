import asyncio
import importlib
import logging
import pkgutil
from abc import ABC, abstractmethod
from collections import OrderedDict
from types import FunctionType


def get_package_modules(package):
    package_modules = []
    for importer, module_name, is_package in pkgutil.iter_modules(package.__path__):
        full_module_name = f'{package.__name__}.{module_name}'
        subpackage_object = importlib.import_module(full_module_name, package=package.__path__)
        if is_package:
            sub_package_modules = get_package_modules(subpackage_object)

            package_modules = package_modules + sub_package_modules
        package_modules.append(subpackage_object)
    return package_modules


class _AbstractManager(dict):
    def __init__(self, server):
        self.server = server
        self.logger = logging.getLogger('houdini')

        super().__init__()

    @abstractmethod
    async def setup(self, module):
        """Setup manager class"""

    @abstractmethod
    async def load(self, module):
        """Loads entries from module"""


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
    def room_id(self):
        """External ID of waddle game room."""

    def __init__(self, waddle):
        self.penguins = list(waddle.penguins)
        self.seats = waddle.seats

    async def start(self):
        room_id = type(self).room_id
        for penguin in self.penguins:
            penguin.waddle = self
            await penguin.join_room(penguin.server.rooms[room_id])

    async def remove_penguin(self, p):
        self.penguins[self.penguins.index(p)] = None
        p.waddle = None

    async def send_xt(self, *data, f=None):
        for penguin in filter(f, self.penguins):
            if penguin is not None:
                await penguin.send_xt(*data)

    def get_seat_id(self, p):
        return self.penguins.index(p)


class PenguinStringCompiler(OrderedDict):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __setitem__(self, key, compiler_method):
        assert type(compiler_method) == FunctionType
        super().__setitem__(key, compiler_method)

    async def compile(self, p):
        compiler_method_results = []

        for compiler_method in self.values():
            if asyncio.iscoroutinefunction(compiler_method):
                compiler_method_result = await compiler_method(p)
            else:
                compiler_method_result = compiler_method(p)
            compiler_method_results.append(str(compiler_method_result))

        compiler_result = '|'.join(compiler_method_results)
        return compiler_result

    @classmethod
    def attribute_by_name(cls, attribute_name):
        async def attribute_method(p):
            return getattr(p, attribute_name) or 0
        return attribute_method

    @classmethod
    def custom_attribute_by_name(cls, attribute_name):
        async def attribute_method(p):
            return p.get_custom_attribute(attribute_name, '')
        return attribute_method

    @classmethod
    def setup_default_builder(cls, string_builder):
        string_builder.update({
            'ID': PenguinStringCompiler.attribute_by_name('id'),
            'Nickname': PenguinStringCompiler.attribute_by_name('nickname'),
            'Approval': PenguinStringCompiler.attribute_by_name('approval'),
            'Color': PenguinStringCompiler.attribute_by_name('color'),
            'Head': PenguinStringCompiler.attribute_by_name('head'),
            'Face': PenguinStringCompiler.attribute_by_name('face'),
            'Neck': PenguinStringCompiler.attribute_by_name('neck'),
            'Body': PenguinStringCompiler.attribute_by_name('body'),
            'Hand': PenguinStringCompiler.attribute_by_name('hand'),
            'Feet': PenguinStringCompiler.attribute_by_name('feet'),
            'Flag': PenguinStringCompiler.attribute_by_name('flag'),
            'Photo': PenguinStringCompiler.attribute_by_name('photo'),
            'X': PenguinStringCompiler.attribute_by_name('x'),
            'Y': PenguinStringCompiler.attribute_by_name('y'),
            'Frame': PenguinStringCompiler.attribute_by_name('frame'),
            'Member': PenguinStringCompiler.attribute_by_name('member'),
            'MemberDays': PenguinStringCompiler.attribute_by_name('membership_days_total'),
            'Avatar': PenguinStringCompiler.attribute_by_name('avatar'),
            'PenguinState': PenguinStringCompiler.attribute_by_name('penguin_state'),
            'PartyState': PenguinStringCompiler.attribute_by_name('party_state'),
            'PuffleState': PenguinStringCompiler.attribute_by_name('puffle_state')
        })

    @classmethod
    def setup_anonymous_default_builder(cls, string_builder):
        string_builder.update({
            'ID': PenguinStringCompiler.attribute_by_name('id'),
            'Nickname': PenguinStringCompiler.attribute_by_name('nickname'),
            'Approval': PenguinStringCompiler.attribute_by_name('approval'),
            'Color': PenguinStringCompiler.attribute_by_name('color'),
            'Head': PenguinStringCompiler.attribute_by_name('head'),
            'Face': PenguinStringCompiler.attribute_by_name('face'),
            'Neck': PenguinStringCompiler.attribute_by_name('neck'),
            'Body': PenguinStringCompiler.attribute_by_name('body'),
            'Hand': PenguinStringCompiler.attribute_by_name('hand'),
            'Feet': PenguinStringCompiler.attribute_by_name('feet'),
            'Flag': PenguinStringCompiler.attribute_by_name('flag'),
            'Photo': PenguinStringCompiler.attribute_by_name('photo')
        })

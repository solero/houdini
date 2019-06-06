from collections import OrderedDict
from aiocache import cached
from types import FunctionType
from abc import abstractmethod

import asyncio
import enum
import logging
import copy


class ConflictResolution(enum.Enum):
    Silent = 0
    Append = 1
    Exception = 2


class Language(enum.IntEnum):
    En = 1
    Pt = 2
    Fr = 4
    Es = 8
    De = 32
    Ru = 64


class _AbstractManager(dict):
    def __init__(self, server):
        self.server = server
        self.logger = logging.getLogger('houdini')

        self.__backup = None
        super().__init__()

    @abstractmethod
    def load(self, module):
        """Loads entries from module"""

    @abstractmethod
    def remove(self, module):
        """Removes all entries by module"""

    def backup(self):
        self.__backup = copy.copy(self)

    def restore(self):
        if self.__backup is not None:
            self.update(self.__backup)
            self.__backup = None


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
    def data_attribute_by_name(cls, attribute_name):
        async def attribute_method(p):
            return getattr(p.data, attribute_name) or 0
        return attribute_method

    @classmethod
    def setup_default_builder(cls, string_builder):
        string_builder.update({
            'ID': PenguinStringCompiler.data_attribute_by_name('id'),
            'Nickname': PenguinStringCompiler.attribute_by_name('nickname'),
            'Approval': PenguinStringCompiler.data_attribute_by_name('approval'),
            'Color': PenguinStringCompiler.data_attribute_by_name('color'),
            'Head': PenguinStringCompiler.data_attribute_by_name('head'),
            'Face': PenguinStringCompiler.data_attribute_by_name('face'),
            'Neck': PenguinStringCompiler.data_attribute_by_name('neck'),
            'Body': PenguinStringCompiler.data_attribute_by_name('body'),
            'Hand': PenguinStringCompiler.data_attribute_by_name('hand'),
            'Photo': PenguinStringCompiler.data_attribute_by_name('photo'),
            'X': PenguinStringCompiler.attribute_by_name('x'),
            'Y': PenguinStringCompiler.attribute_by_name('y'),
            'Frame': PenguinStringCompiler.attribute_by_name('frame'),
            'Member': PenguinStringCompiler.attribute_by_name('member'),
            'MemberDays': PenguinStringCompiler.attribute_by_name('membership_days'),
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
            'Hand': PenguinStringCompiler.attribute_by_name('name'),
            'Photo': PenguinStringCompiler.attribute_by_name('photo')
        })

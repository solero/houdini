from collections import OrderedDict
from aiocache import cached
from types import FunctionType
import asyncio


class PenguinStringCompiler(OrderedDict):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __setitem__(self, key, compiler_method):
        assert type(compiler_method) == FunctionType
        super().__setitem__(key, compiler_method)

    @cached(namespace='houdini')
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
            return getattr(p, attribute_name)
        return attribute_method

    @classmethod
    def data_attribute_by_name(cls, attribute_name):
        async def attribute_method(p):
            return getattr(p.data, attribute_name)
        return attribute_method

    @classmethod
    def setup_default_builder(cls, string_builder):
        string_builder.update({
            'ID': PenguinStringCompiler.data_attribute_by_name('ID'),
            'Nickname': PenguinStringCompiler.data_attribute_by_name('Nickname'),
            'Approval': PenguinStringCompiler.attribute_by_name('approval'),
            'Color': PenguinStringCompiler.data_attribute_by_name('Color'),
            'Head': PenguinStringCompiler.data_attribute_by_name('Head'),
            'Face': PenguinStringCompiler.data_attribute_by_name('Face'),
            'Neck': PenguinStringCompiler.data_attribute_by_name('Neck'),
            'Body': PenguinStringCompiler.data_attribute_by_name('Body'),
            'Hand': PenguinStringCompiler.data_attribute_by_name('Name'),
            'Photo': PenguinStringCompiler.data_attribute_by_name('Photo'),
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
            'ID': PenguinStringCompiler.attribute_by_name('ID'),
            'Nickname': PenguinStringCompiler.attribute_by_name('Nickname'),
            'Approval': PenguinStringCompiler.attribute_by_name('approval'),
            'Color': PenguinStringCompiler.attribute_by_name('Color'),
            'Head': PenguinStringCompiler.attribute_by_name('Head'),
            'Face': PenguinStringCompiler.attribute_by_name('Face'),
            'Neck': PenguinStringCompiler.attribute_by_name('Neck'),
            'Body': PenguinStringCompiler.attribute_by_name('Body'),
            'Hand': PenguinStringCompiler.attribute_by_name('Name'),
            'Photo': PenguinStringCompiler.attribute_by_name('Photo')
        })

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

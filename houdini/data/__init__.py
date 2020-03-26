from collections.abc import Mapping

from gino import Gino

db = Gino()


class AbstractDataCollection(Mapping):

    def __init__(self, filter_lookup=None):
        self.__collection = dict()

        self.__model = getattr(self.__class__, '__model__')
        self.__indexby = getattr(self.__class__, '__indexby__')

        self.__filterby = getattr(self.__class__, '__filterby__')
        self.__filter_lookup = getattr(self.__model, self.__filterby)
        self.__filter_lookup = filter_lookup or self.__filter_lookup

    def __delitem__(self, key):
        raise TypeError(f'Use {self.__class__.__name__}.delete to remove an item from this collection')

    def __setitem__(self, key, value):
        raise TypeError(f'Use {self.__class__.__name__}.insert to add an item to this collection')

    def __len__(self):
        return len(self.__collection)

    def __iter__(self):
        return iter(self.__collection)

    def __getitem__(self, item):
        return self.__collection[item]

    async def insert(self, **kwargs):
        kwargs = {self.__filterby: self.__filter_lookup, **kwargs}
        model_instance = await self.__model.create(**kwargs)
        key = getattr(model_instance, self.__indexby)

        self.__collection[key] = model_instance
        return model_instance

    async def delete(self, key):
        model_instance = self.__collection.pop(key)
        await model_instance.delete()

    async def __collect(self):
        filter_column = getattr(self.__model, self.__filterby)
        query = self.__model.query.where(filter_column == self.__filter_lookup)

        async with db.transaction():
            collected = query.gino.iterate()
            async for model_instance in collected:
                collection_index = getattr(model_instance, self.__indexby)
                self.__collection[collection_index] = model_instance

    @classmethod
    async def get_collection(cls, *args, **kwargs):
        cc = cls(*args, **kwargs)
        await cc.__collect()
        return cc

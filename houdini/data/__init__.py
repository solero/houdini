from gino import Gino

db = Gino()


class BaseCrumbsCollection(dict):

    def __init__(self, *args, **kwargs):
        super().__init__()

        self._db = db
        self._model = kwargs.get('model')
        self._key = kwargs.get('key')
        self._inventory_model = kwargs.get('inventory_model')
        self._inventory_key = kwargs.get('inventory_key')
        self._inventory_value = kwargs.get('inventory_value')
        self._inventory_id = kwargs.get('inventory_id')

        self._model_key_column = getattr(self._model, self._key)

        self._is_inventory = self._inventory_model is not None and self._inventory_id is not None

        if self._is_inventory:
            self._inventory_key_column = getattr(self._inventory_model, self._inventory_key)
            self._inventory_value_column = getattr(self._inventory_model, self._inventory_value)

    async def get(self, k):
        try:
            return self[k]
        except KeyError as e:
            query = self._model.load(parent=self._inventory_model).where(
                (self._inventory_key_column == self._inventory_id) & (self._inventory_value_column == k)
            ) if self._is_inventory else self._model.query.where(self._model_key_column == k)
            result = await query.gino.first()
            if result:
                self[k] = result
                return result
            raise e

    async def set(self, k=None, **kwargs):
        if self._is_inventory and k:
            kwargs = {self._inventory_key: self._inventory_id, self._inventory_value: k}
            self[k] = await self._inventory_model.create(**kwargs)
        else:
            model_instance = await self._model.create(**kwargs)
            k = getattr(model_instance, self._key)
            self[k] = model_instance
        return self[k]

    async def __collect(self):
        query = self._model.load(parent=self._inventory_model).where(
            self._inventory_key_column == self._inventory_id
        ) if self._is_inventory else self._model.query

        async with db.transaction():
            collected = query.gino.iterate()
            self.update(
                {getattr(model_instance, self._key): model_instance async for model_instance in collected}
            )

    @classmethod
    async def get_collection(cls, *args, **kwargs):
        cc = cls(*args, **kwargs)
        await cc.__collect()
        return cc

from gino import Gino

db = Gino()


class BaseCrumbsCollection(dict):

    def __init__(self, *args, **kwargs):
        super().__init__()

        self._db = db
        self._model = kwargs.get('model')
        self._key = kwargs.get('key')
        self._inventory_model = kwargs.get('inventory_model')
        self._inventory_id = kwargs.get('inventory_id')

        self._is_inventory = self._inventory_model is not None and self._inventory_id is not None

    async def get(self, k):
        if self._is_inventory:
            return self[k]
        try:
            return self[k]
        except KeyError as e:
            result = await self._model.query.where(getattr(self._model, self._key) == k).gino.first()
            if result:
                self[k] = result
                return result
            raise e

    async def __collect(self):
        query = self._model.load(parent=self._inventory_model).where(
            self._inventory_model.PenguinID == self._inventory_id
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

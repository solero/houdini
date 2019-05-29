from houdini.data import db, BaseCrumbsCollection
from houdini.data.penguin import PenguinPermission


class Permission(db.Model):
    __tablename__ = 'permission'

    id = db.Column(db.Integer, primary_key=True, server_default=db.text("nextval('\"permission_id_seq\"'::regclass)"))
    name = db.Column(db.String(50), nullable=False, unique=True)
    enabled = db.Column(db.Boolean, nullable=False, server_default=db.text("true"))


class PermissionCrumbsCollection(BaseCrumbsCollection):

    def __init__(self, inventory_id=None):
        super().__init__(model=Permission,
                         key='name',
                         inventory_model=PenguinPermission,
                         inventory_key='penguin_id',
                         inventory_value='permission_id',
                         inventory_id=inventory_id)

    async def register(self, permission_name):
        try:
            permission = await self.get(permission_name)
        except KeyError:
            permission = await self.set(name=permission_name)
        return permission

from houdini.data import AbstractDataCollection, db


class Permission(db.Model):
    __tablename__ = 'permission'

    name = db.Column(db.String(50), nullable=False, primary_key=True)
    enabled = db.Column(db.Boolean, nullable=False, server_default=db.text("true"))


class PenguinPermission(db.Model):
    __tablename__ = 'penguin_permission'

    penguin_id = db.Column(db.ForeignKey(u'penguin.id', ondelete=u'CASCADE', onupdate=u'CASCADE'), primary_key=True)
    permission_name = db.Column(db.ForeignKey(u'permission.name', ondelete=u'CASCADE', onupdate=u'CASCADE'),
                                nullable=False, primary_key=True)


class PermissionCollection(AbstractDataCollection):
    __model__ = Permission
    __indexby__ = 'name'
    __filterby__ = 'name'

    async def register(self, permission_name):
        permission_parts = permission_name.split('.')
        for permission_index in range(1, len(permission_parts) + 1):
            permission_name = '.'.join(permission_parts[:permission_index])
            if permission_name not in self:
                await self.insert(name=permission_name)

    async def unregister(self, permission_name):
        for permission in self.values():
            if permission.name == permission_name or permission.name.startswith(permission_name):
                await self.delete(permission.name)


class PenguinPermissionCollection(AbstractDataCollection):
    __model__ = PenguinPermission
    __indexby__ = 'permission_name'
    __filterby__ = 'penguin_id'

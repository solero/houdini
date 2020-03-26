from houdini.data import AbstractDataCollection, db


class Permission(db.Model):
    __tablename__ = 'permission'

    id = db.Column(db.Integer, primary_key=True, server_default=db.text("nextval('\"permission_id_seq\"'::regclass)"))
    name = db.Column(db.String(50), nullable=False, unique=True)
    enabled = db.Column(db.Boolean, nullable=False, server_default=db.text("true"))


class PenguinPermission(db.Model):
    __tablename__ = 'penguin_permission'

    penguin_id = db.Column(db.ForeignKey(u'penguin.id', ondelete=u'CASCADE', onupdate=u'CASCADE'), primary_key=True)
    permission_id = db.Column(db.ForeignKey(u'permission.id', ondelete=u'CASCADE', onupdate=u'CASCADE'), nullable=False)


class PermissionCollection(AbstractDataCollection):
    __model__ = Permission
    __indexby__ = 'name'
    __filterby__ = 'name'


class PenguinPermissionCollection(AbstractDataCollection):
    __model__ = PenguinPermission
    __indexby__ = 'permission_id'
    __filterby__ = 'penguin_id'

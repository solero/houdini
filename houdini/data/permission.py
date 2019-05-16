from houdini.data import db, BaseCrumbsCollection
from houdini.data.penguin import PenguinPermission


class Permission(db.Model):
    __tablename__ = 'permission'

    ID = db.Column(db.Integer, primary_key=True, server_default=db.text("nextval('\"permission_ID_seq\"'::regclass)"))
    Name = db.Column(db.String(50), nullable=False, unique=True)
    Enabled = db.Column(db.Boolean, nullable=False, server_default=db.text("true"))


class PermissionCrumbsCollection(BaseCrumbsCollection):

    def __init__(self, inventory_id=None):
        super().__init__(model=Permission, key='ID', inventory_model=PenguinPermission,
                         inventory_id=inventory_id)

from houdini.data import db, AbstractDataCollection


class PluginAttribute(db.Model):
    __tablename__ = 'plugin_attribute'

    plugin_name = db.Column(db.Text, primary_key=True, nullable=False)
    name = db.Column(db.Text, primary_key=True, nullable=False)
    value = db.Column(db.Text)


class PenguinAttribute(db.Model):
    __tablename__ = 'penguin_attribute'

    penguin_id = db.Column(db.ForeignKey('penguin.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
                           nullable=False)
    name = db.Column(db.Text, primary_key=True, nullable=False)
    value = db.Column(db.Text)


class PenguinAttributeCollection(AbstractDataCollection):
    __model__ = PenguinAttribute
    __indexby__ = 'name'
    __filterby__ = 'penguin_id'


class PluginAttributeCollection(AbstractDataCollection):
    __model__ = PluginAttribute
    __indexby__ = 'name'
    __filterby__ = 'plugin_name'

from hashlib import sha1
from uuid import uuid4 as uuid

from sqlalchemy.schema import ForeignKey, Table, Column, Index, UniqueConstraint, ForeignKeyConstraint
from sqlalchemy import event

from batteries.model import Model
from batteries.model.types import Ascii

class Hashable(object):
    key_name = 'key'
    keyed_on = 'uuid'

    @property
    def key(self):
        colname = '_' + self.key_name
        if getattr(self, colname) is None:
            setattr(self, colname, self.make_key())
        return getattr(self, colname)

    @classmethod
    def make_key(cls, instance=None, **values):
        if instance is not None:
            h = sha1()

            if isinstance(instance.keyed_on, tuple):
                for p in instance.keyed_on:
                    h.update(str(getattr(instance, p)))

            elif instance.keyed_on == 'uuid':
                h.update(uuid().hex)

            return h.hexdigest()

        else:
            h = sha1()

            if isinstance(cls.keyed_on, tuple):
                for p in cls.keyed_on:
                    h.update(values[p])

            elif cls.keyed_on == 'uuid':
                h.update(uuid().hex)

            return h.hexdigest()

    def update_key(self):
        colname = '_' + self.key_name
        if getattr(self, colname) is None:
            setattr(self, colname, Hashable.make_key(instance=self))

@event.listens_for(Hashable, 'before_insert', propagate=True)
def on_before_insert(mapper, connection, target):
    target.update_key()

@event.listens_for(Hashable, 'before_update', propagate=True)
def on_before_update(mapper, connection, target):
    target.update_key()

def HashableAssociation(left_table, right_table, left_key_name=None, right_key_name=None, left_foreign_key_name='key', right_foreign_key_name='key', name=None, **kwargs):
    if name is None:
        name = "{0}_{1}".format(left_table, right_table)

    if left_key_name is None:
        left_key_name = "{0}_key".format(left_table)

    if right_key_name is None:
        right_key_name = "{0}_key".format(right_table)

    return Table(name, Model.metadata,
            Column(left_key_name, Ascii(40), ForeignKey("{0}.{1}".format(left_table, left_foreign_key_name)), primary_key=True),
            Column(right_key_name, Ascii(40), ForeignKey("{0}.{1}".format(right_table, right_foreign_key_name)), primary_key=True),
            **kwargs)

def HashableReference(foreign_table, foreign_key_name='key', **kwargs):
    return Column(Ascii(40), ForeignKey("{0}.{1}".format(foreign_table, foreign_key_name)), **kwargs)

def HashableKey(name=None):
    if name is None:
        name = 'key'

    return Column(name, Ascii(40), primary_key=True)

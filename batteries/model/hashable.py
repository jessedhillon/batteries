from hashlib import sha1
from uuid import uuid4 as uuid

from batteries.model.types import Ascii

from sqlalchemy import event

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
                    h.update(getattr(instance, p))

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

    @staticmethod
    def on_before_insert(mapper, connection, target):
        target.update_key()

    @staticmethod
    def on_before_update(mapper, connection, target):
        target.update_key()

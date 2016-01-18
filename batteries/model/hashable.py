from hashlib import sha1
from uuid import uuid4 as uuid
import warnings

from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import event
from sqlalchemy.schema import ForeignKey, Table, Column, Index,\
        UniqueConstraint, ForeignKeyConstraint

from batteries.model import Model
from batteries.model.types import Ascii


def Key(len=40):
    return Ascii(len)


class Hashable(object):
    keyed_on = 'uuid'

    @classmethod
    def make_key(cls, instance=None, **values):
        if instance is not None:
            h = sha1()

            if isinstance(instance.keyed_on, tuple):
                for p in instance.keyed_on:
                    h.update(str(getattr(instance, p)))

            elif instance.keyed_on == 'uuid':
                h.update(uuid().hex)

            return unicode(h.hexdigest())

        else:
            h = sha1()

            if isinstance(cls.keyed_on, tuple):
                for p in cls.keyed_on:
                    h.update(values[p])

            elif cls.keyed_on == 'uuid':
                h.update(uuid().hex)

            return unicode(h.hexdigest())

    def update_key(self):
        colname = _get_key_name(self.__class__)
        if getattr(self, colname) is None:
            setattr(self, colname, Hashable.make_key(self))


def _get_key_name(cls):
    if getattr(cls, 'key_name', False):
        return '_{}'.format(cls.key_name)
    return '_{}_key'.format(cls.__tablename__)


def _get_key_attr(cls):
    return getattr(cls, _get_key_name(cls))


def _get_key_column(cls):
    return getattr(_get_key_attr(cls).parent.columns, _get_key_name(cls))


def key_fget(instance):
    colname = _get_key_name(instance.__class__)
    if getattr(instance, colname) is None:
        setattr(instance, colname, instance.make_key())
    return getattr(instance, colname)


def key_fset(instance, value):
    colname = _get_key_name(instance.__class__)
    setattr(instance, colname, value)


def key_expr(cls):
    return getattr(cls, _get_key_name(cls))


@event.listens_for(Hashable, 'instrument_class', propagate=True)
def instrument_class(mapper, cls):
    prop = hybrid_property(key_fget, key_fset, expr=key_expr)
    if getattr(cls, 'key_name', False):
        propname = cls.key_name
    else:
        propname = '{}_key'.format(cls.__tablename__)
    setattr(cls, '_{}'.format(propname), getattr(cls, propname))
    setattr(cls, propname, prop)

    keycol = getattr(mapper.mapped_table.columns, propname)
    keycol.key = '_{}'.format(propname)
    keycol.name = propname
    return object.__new__(cls)


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
            Column(left_key_name, Key(40), ForeignKey("{0}.{1}".format(left_table, left_foreign_key_name)), primary_key=True),
            Column(right_key_name, Key(40), ForeignKey("{0}.{1}".format(right_table, right_foreign_key_name)), primary_key=True),
            **kwargs)


def HashableReference(foreign_table, key_name='key', name=None, **kwargs):
    if hasattr(Model.metadata, 'naming_convention'):
        return Column(Key(40), ForeignKey("{0}.{1}".format(foreign_table, key_name)), name=name, **kwargs)

    if name is None:
        name = key_name + '_constraint'
    return Column(Key(40), ForeignKey("{0}.{1}".format(foreign_table, key_name)), name=name, **kwargs)


def HashableKey(name=None):
    if name is None:
        name = 'key'
    return Column(name, Key(40), primary_key=True)

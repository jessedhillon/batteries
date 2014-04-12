from batteries.model import Model
from batteries.model.types import Ascii
from batteries.util import slugify

from sqlalchemy import event
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm.exc import NoResultFound


class Identifiable(object):
    slug_name = 'slug'

    @classmethod
    def make_slug(cls, instance=None, *values):
        if instance is None:
            col = _get_slug_column(cls)

        else:
            col = _get_slug_column(instance.__class__)

            values = []
            for key in instance.named_with:
                v = getattr(instance, key)
                if v is None:
                    raise ValueError(
                            "{}.{} cannot be None and provide slug input".\
                            format(instance.__class__.__name__, key))
                values.append(getattr(instance, key))

        seed = slugify(u'-'.join(values))
        return seed[:col.type.length]

    def update_slug(self):
        colname = _get_slug_name(self.__class__)
        if getattr(self, colname) is None:
            slug = find_available_slug(self.__class__, Identifiable.make_slug(self))
            setattr(self, colname, slug)


def _get_slug_name(cls):
    return '_' + cls.slug_name


def _get_slug_attr(cls):
    return getattr(cls, _get_slug_name(cls))


def _get_slug_column(cls):
    return getattr(_get_slug_attr(cls).parent.columns, _get_slug_name(cls))


def find_available_slug(cls, root, tries=100):
    s = root
    for i in range(1, tries):
        try:
            attr = _get_slug_attr(cls)
            col = _get_slug_column(cls)
            length = col.type.length

            cls.query.filter(attr == s).one()
            suffix = "-{0}".format(i)
            s = root[:length - len(suffix)] + suffix
            s = s[:length]
        except NoResultFound:
            return s

    raise Exception(
        "{cls.__name__} exceeded 100 iterations searching for available slug on input: {0!r}".format(
            seeds, cls=cls))


def slug_fget(instance):
    colname = '_' + instance.slug_name
    if getattr(instance, colname) is None:
        setattr(instance, colname, instance.make_slug())
    return getattr(instance, colname)


def slug_fset(instance, value):
    colname = '_' + instance.slug_name
    setattr(instance, colname, value)


def slug_expr(cls):
    colname = '_' + cls.slug_name
    return getattr(cls, colname)


@event.listens_for(Identifiable, 'instrument_class', propagate=True)
def instrument_class(mapper, cls):
    prop = hybrid_property(slug_fget, slug_fset, expr=slug_expr)
    setattr(cls, cls.slug_name, prop)
    return object.__new__(cls)


@event.listens_for(Identifiable, 'before_insert', propagate=True)
def on_before_insert(mapper, connection, target):
    target.update_slug()

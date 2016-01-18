import logging
import re
import enum
from collections import namedtuple

from sqlalchemy.orm.interfaces import EXT_CONTINUE, EXT_STOP
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.ext.declarative import declarative_base, DeclarativeMeta, declared_attr
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
from sqlalchemy import event
from sqlalchemy.orm.session import Session
import sqlalchemy.dialects.postgresql as postgresql

from batteries.util import metaproperty

session = None
logger = logging.getLogger('batteries.model')
enum_types = [
    postgresql.base.ENUM,
]


def initialize_model(s, engine, debug=False):
    global session
    session = s
    if not isinstance(session, Session):
        session.configure(bind=engine)
    Model.metadata.bind = engine

    logger.info('model configured')


class MetaModel(DeclarativeMeta):
    @metaproperty
    def query(cls):
        return session.query(cls)

    def delete(cls, instance):
        session.delete(instance)

    def get(cls, *v, **kwargs):
        try:
            if v:
                return cls.query.get(v)
            if kwargs:
                q = cls.query
                for k, v in kwargs.items():
                    q = q.filter_by(**{k: v})
                return q.one()

        except NoResultFound:
            return None


class Model(object):
    identifiers = None

    @declared_attr
    def __tablename__(cls):
        return camelcase_to_underscore(cls.__name__)

    def __unicode__(self):
        keys = format_identifiers(self)
        return u"{cls}({keys})".format(cls=self.__class__.__name__,
                                       keys=', '.join(keys))
    __str__ = __unicode__

    def __repr__(self):
        keys = format_identifiers(self)
        return "<{cls}({keys})>".format(cls=self.__class__.__name__,
                                        keys=', '.join(keys))


def camelcase_to_underscore(s):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', s)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower() 


def format_identifiers(instance):
    ids = []
    if not instance.identifiers:
        ids = instance.__mapper__.primary_key
    else:
        ids = instance.identifiers

    s = []
    for col in ids:
        if hasattr(col, 'key'):
            col = col.key

        if isinstance(col, tuple):
            col, fmt = col
        else:
            fmt = u"{v!r}"

        fmt = u"{col}=" + unicode(fmt)
        s.append(fmt.format(col=col, v=getattr(instance, col)))

    return s


@event.listens_for(Model, 'mapper_configured', propagate=True)
def on_after_configured(mapper, cls):
    events = ('after_configured', 'after_delete', 'after_insert',
              'after_update', 'append_result', 'before_delete',
              'before_insert', 'before_update', 'create_instance',
              'instrument_class', 'mapper_configured', 'populate_instance',
              'translate_row', 'expire', 'first_init', 'init', 'init_failure',
              'load', 'pickle', 'refresh', 'resurrect', 'unpickle')

    do_mapper_configure = False

    for ev in events:
        mname = 'on_{}'.format(ev)
        if mname in cls.__dict__:
            if ev == 'mapper_configured':
                do_mapper_configure = True
            event.listen(cls, ev, getattr(cls, mname))

    if do_mapper_configure:
        cls.on_mapper_configured(mapper, cls)


@event.listens_for(Model, 'instrument_class', propagate=True)
def on_instrument_class(mapper, cls):
    for col in mapper.mapped_table.columns:
        if col.default is not None:
            default = col.default

            if col.name is None:
                col.name = key
                key = col.key
            else:
                key = col.name

            context = namedtuple('context', ['current_parameters'])

            def default_get(self):
                if getattr(self, '_{}'.format(key)) is None:
                    params = context(current_parameters=self.__dict__)
                    setattr(self, '_{}'.format(key), default.arg(params))
                return getattr(self, '_{}'.format(key))

            def default_set(self, v):
                setattr(self, '_{}'.format(key), v)

            def default_expr(cls):
                return getattr(cls, '_{}'.format(key))

            prop = hybrid_property(default_get, default_set, expr=default_expr)
            col.key = '_{}'.format(key)
            col.name = key
            setattr(cls, '_{}'.format(key), getattr(cls, key))
            setattr(cls, key, prop)
    return object.__new__(cls)


Model = declarative_base(cls=Model, metaclass=MetaModel)

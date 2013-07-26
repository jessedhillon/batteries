import logging

from sqlalchemy.orm.interfaces import EXT_CONTINUE, EXT_STOP
from sqlalchemy.ext.declarative import declarative_base, DeclarativeMeta, declared_attr
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
from sqlalchemy import event

from batteries.util import metaproperty

Session = None
logger = logging.getLogger('batteries.model')

def initialize_model(session, engine, debug=False):
    global Session
    Session = session
    Session.configure(bind=engine)
    Model.metadata.bind = engine

    logger.info('model configured')

class MetaModel(DeclarativeMeta):
    @metaproperty
    def query(cls):
        return Session.query(cls)

    def delete(cls, instance):
        Session.delete(instance)

    def get(cls, *v):
        try:
            return cls.query.get(v)

        except NoResultFound:
            return default

class Model(object):
    __table_args__ =    {'mysql_engine': 'InnoDB',
                         'mysql_charset': 'utf8'}

    def __str__(self):
        pk = self.__mapper__.primary_key

        s = []
        for col in pk:
            s.append("{0}={1!r}".format(col.key, getattr(self, col.key)))

        return "{cls}({pk})".format(cls=self.__class__.__name__, pk=', '.join(s))

    def __repr__(self):
        pk = self.__mapper__.primary_key

        s = []
        for col in pk:
            s.append("{0}={1!r}".format(col.key, getattr(self, col.key)))

        return "<{cls}({pk})>".format(cls=self.__class__.__name__, pk=', '.join(s))

@event.listens_for(Model, 'mapper_configured', propagate=True)
def on_after_configured(mapper, cls):
    events = ('after_configured', 'after_delete', 'after_insert', 'after_update',\
              'append_result', 'before_delete', 'before_insert', 'before_update',\
              'create_instance', 'instrument_class', 'mapper_configured',\
              'populate_instance', 'translate_row', 'expire', 'first_init',\
              'init', 'init_failure', 'load', 'pickle', 'refresh', 'resurrect',\
              'unpickle')

    for ev in events:
        mname = 'on_{0}'.format(ev)
        if mname in cls.__dict__:
            event.listen(cls, ev, getattr(cls, mname))

Model = declarative_base(cls=Model, metaclass=MetaModel)

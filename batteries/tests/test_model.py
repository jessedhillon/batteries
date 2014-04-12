import os
import warnings
import json
import logging
from unittest import TestCase
from datetime import datetime, timedelta
from dateutil.tz import tzutc

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker, relationship
from sqlalchemy.schema import Column, ForeignKey
from sqlalchemy.types import Unicode
from batteries.path import AssetResolver

from batteries.model.types import Ascii
from batteries.model import Model, initialize_model
from batteries.model.hashable import Hashable
from batteries.model.recordable import Recordable
from batteries.model.serializable import Serializable
from batteries.model.storable import Storable, LocalStorage
from batteries.model.loggable import Loggable, LogMessage
from batteries.model.deletable import Deletable


class MyLogMessage(LogMessage):
    __tablename__ = 'my_log_message'

    model_key = Column(Ascii(40), ForeignKey('my_model.key'))


class MyModel(Hashable, Serializable, Storable, Model, Recordable, Loggable):
    __tablename__ = 'my_model'
    serializable = ('key', 'name', 'ctime', 'mtime')
    logging_class = MyLogMessage

    _key = Column('key', Ascii(40), primary_key=True)
    name = Column(Unicode(100))
    attachment = Column(LocalStorage('batteries.tests:fixtures/'))
    log_messages = relationship('MyLogMessage',
                                order_by='MyLogMessage.timestamp.asc()')


class MyDeletableModel(Hashable, Deletable, Model):
    __tablename__ = 'my_deletable_model'
    serializable = ('key', 'name')

    _key = Column('key', Ascii(40), primary_key=True)
    name = Column(Unicode(100))


class TestCase(TestCase):
    def setUp(self):
        self.engine = create_engine('sqlite://')
        self.session = scoped_session(sessionmaker())
        self.logger = logging.getLogger('batteries.tests')
        initialize_model(self.session, self.engine)

        warnings.filterwarnings('error')
        Model.metadata.create_all(self.engine)

        MyModel.logging_required = False

    def tearDown(self):
        MyModel.logging_required = False
        Model.metadata.drop_all(self.engine)
        self.session.rollback()
        self.session.close()

    def test_create_model(self):
        m = MyModel()
        self.session.add(m)

    def test_fetch_model(self):
        m = MyModel(key='foobar', name=u'Foo Bar')
        self.session.add(m)
        self.session.flush()

        m = MyModel.query.limit(1).all()[0]
        assert m.key == 'foobar'

        try:
            assert MyModel.get('foobar') is not None
            assert MyModel.query.filter(MyModel.key == 'foobar').one() is not None

        except Exception as e:
            self.fail("Unexpected exception raised: {0!s}".format(e))

    def test_hashable_key(self):
        m = MyModel()
        self.session.add(m)
        self.session.flush()

        m = MyModel.query.limit(1).all()[0]

        try:
            assert m.key is not None

        except Exception as e:
            self.fail("Unexpected exception raised: {0!s}".format(e))

    def test_recordable_timestamps(self):
        start = datetime.utcnow().replace(tzinfo=tzutc())

        m = MyModel()
        self.session.add(m)
        self.session.flush()

        m = MyModel.query.limit(1).all()[0]

        assert m.ctime >= start
        assert m.mtime >= start

    def test_serializable(self):
        m = MyModel(name=u'Foo Bar')
        self.session.add(m)
        self.session.flush()

        m = MyModel.query.limit(1).all()[0]
        s = m.serialize()

        assert 'key' in s
        assert s['name'] == u'Foo Bar'
        assert s['mtime'] == int(m.mtime.strftime('%s'))
        assert s['ctime'] == int(m.ctime.strftime('%s'))

    def test_local_storage_field(self):
        m = MyModel(name=u'storable')

        resolver = AssetResolver()
        path = resolver.resolve('batteries.tests:fixtures/test_image.png')
        m.attachment.filename = 'test_local_storage_field.png'

        with open(path.abspath(), 'r') as f:
            with m.attachment.open('w+') as a:
                a.write(f.read())

        self.session.add(m)
        self.session.flush()

        m = MyModel.query.one()
        with open(path.abspath(), 'r') as f:
            with m.attachment.open('r') as a:
                assert f.read() == a.read()

        MyModel.delete(m)
        self.session.flush()
        path = m.attachment.abspath

        assert not os.path.isfile(path)

    def test_loggable(self):
        MyModel.logging_required = True

        try:
            m = MyModel(name=u"Foo Bar")
            self.session.add(m)
            self.session.flush()
        except Exception:
            self.session.rollback()
        else:
            assert False, "Loggable inserted without a log message"

        start = datetime.utcnow().replace(tzinfo=tzutc())
        m = MyModel(name=u"Foo Bar")
        m.log('info', __name__, u"test_loggable", u"{0!r}".format({'name': u"Foo Bar"}))
        self.session.add(m)
        self.session.flush()
        end = datetime.utcnow().replace(tzinfo=tzutc())

        assert len(m.log_messages) == 1
        assert m.log_messages[0].qualifier == __name__
        assert m.log_messages[0].message == u"test_loggable"
        assert m.log_messages[0].data == repr({'name': u"Foo Bar"})
        assert start <= m.log_messages[0].timestamp <= end

        start = datetime.utcnow().replace(tzinfo=tzutc())
        m.name = u"Foo Bar Baz"
        m.log('info', __name__, u"name change", u"Foo Bar Baz")
        self.session.add(m)
        self.session.flush()
        end = datetime.utcnow().replace(tzinfo=tzutc())

        assert len(m.log_messages) == 2
        assert m.log_messages[1].level == 'info'
        assert m.log_messages[1].qualifier == __name__
        assert m.log_messages[1].message == u"name change"
        assert m.log_messages[1].data == u"Foo Bar Baz"
        assert start <= m.log_messages[1].timestamp <= end

        for message in m.log_messages:
            self.logger.info(unicode(message))
            if message.data:
                self.logger.info("  --@ {0}".format(message.data))

    def test_deletable(self):
        m = MyDeletableModel(name=u"Foo Bar")
        assert m.is_deleted is False

        m.delete()
        assert m.is_deleted is not False

        self.session.add(m)
        self.session.flush()

    def test_deprecated_key(self):
        """should not fail if the old `_key` reference is used"""
        m = MyModel(_key='foobar', name=u'Foo Bar')
        self.session.add(m)
        self.session.flush()

        m = MyModel.query.limit(1).all()[0]
        assert m._key == 'foobar'

        try:
            assert MyModel.get('foobar') is not None
            assert MyModel.query.filter(MyModel._key == 'foobar').one() is not None

        except Exception as e:
            self.fail("Unexpected exception raised: {0!s}".format(e))

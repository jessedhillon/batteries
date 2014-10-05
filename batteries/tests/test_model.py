import os
import warnings
import json
import logging
from unittest import TestCase, skip
from datetime import datetime, timedelta
from dateutil.tz import tzutc
import string
import random

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker, relationship
from sqlalchemy.schema import Column, ForeignKey
from sqlalchemy.types import Unicode, Numeric
from sqlalchemy.exc import SAWarning
from batteries.path import AssetResolver

from batteries.model.types import Ascii
from batteries.model import Model, initialize_model
from batteries.model.hashable import Hashable
from batteries.model.identifiable import Identifiable
from batteries.model.recordable import Recordable
from batteries.model.serializable import Serializable
from batteries.model.storable import Storable, LocalStorage
from batteries.model.deletable import Deletable


class MyModel(Hashable, Identifiable, Serializable, Storable, Model, Recordable):
    serializable = ('key', 'name', 'number', 'string', 'ctime', 'mtime')
    named_with = ('name',)

    _key = Column('key', Ascii(40), primary_key=True)
    _slug = Column('slug', Ascii(40), unique=True)
    name = Column(Unicode(100), nullable=False)
    number = Column(Numeric(10, scale=2))
    string = Column(Unicode(100))
    attachment = Column(LocalStorage('batteries.tests:fixtures/'))

    @property
    def nonce(self):
        s = ""
        for i in range(40):
            s += random.choice(string.ascii_letters + string.digits)
        return s


class MyDeletableModel(Hashable, Deletable, Model):
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
        warnings.filterwarnings(
            'ignore',
            r"^Dialect sqlite\+pysqlite does \*not\* support Decimal objects natively\, "
            "and SQLAlchemy must convert from floating point - rounding errors and other "
            "issues may occur\. Please consider storing Decimal numbers as strings or "
            "integers on this platform for lossless storage\.$",
            SAWarning, r'^sqlalchemy\.sql\.type_api$')
        Model.metadata.create_all(self.engine)

    def tearDown(self):
        MyModel.logging_required = False
        Model.metadata.drop_all(self.engine)
        self.session.rollback()
        self.session.close()

    def test_create_model(self):
        m = MyModel(name=u'test')
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
        m = MyModel(name=u'test')
        self.session.add(m)
        self.session.flush()

        m = MyModel.query.limit(1).all()[0]

        try:
            assert m.key is not None

        except Exception as e:
            self.fail("Unexpected exception raised: {0!s}".format(e))

    def test_recordable_timestamps(self):
        start = datetime.utcnow().replace(tzinfo=tzutc())

        m = MyModel(name=u'test')
        self.session.add(m)
        self.session.flush()

        m = MyModel.query.limit(1).all()[0]

        assert m.ctime >= start
        assert m.mtime >= start

    def test_serializable(self):
        m = MyModel(name=u'Foo Bar', number=3.14, string=None)
        self.session.add(m)
        self.session.flush()

        m = MyModel.query.limit(1).all()[0]
        s = m.serialize()

        assert 'key' in s
        assert s['name'] == u'Foo Bar'
        assert s['number'] == 3.14
        assert s['string'] == None
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

    @skip("forget Loggable")
    def test_loggable(self):
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

    def test_identifiable(self):
        m1 = MyModel(key='first', name=u'test 1')
        m2 = MyModel(key='second', name=u'test')
        m3 = MyModel(key='third', name=u'test')

        for m in m1, m2, m3:
            self.session.add(m)
            self.session.flush()

        m1 = MyModel.get('first')
        m2 = MyModel.get('second')
        m3 = MyModel.get('third')
        assert m1.slug == 'test-1'
        assert m2.slug == 'test'
        assert m3.slug == 'test-2'

    def test_identifiable_with_nonce(self):
        m1 = MyModel(key='first', name=u'test 1')
        m2 = MyModel(key='second', name=u'test')
        m3 = MyModel(key='third', name=u'test')

        for m in m1, m2, m3:
            m.named_with = ('name', 'nonce')
            self.session.add(m)
            self.session.flush()

        m1 = MyModel.get('first')
        m2 = MyModel.get('second')
        m3 = MyModel.get('third')
        assert m1.slug.startswith('test-1')
        assert m2.slug.startswith('test')
        assert m3.slug.startswith('test')

        for m in m1, m2, m3:
            assert len(m.slug) == 40

    def test_tablename(self):
        assert MyModel.__table__.name == 'my_model'

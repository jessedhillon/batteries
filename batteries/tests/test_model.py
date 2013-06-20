import os
import warnings
import json
import transaction
from unittest import TestCase
from datetime import datetime, timedelta
from dateutil.tz import tzutc

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.schema import Column
from sqlalchemy.types import Unicode
from zope.sqlalchemy import ZopeTransactionExtension
from pyramid.path import AssetResolver

from batteries.model.types import Ascii
from batteries.model import Model, initialize_model
from batteries.model.hashable import Hashable
from batteries.model.recordable import Recordable
from batteries.model.serializable import Serializable
from batteries.model.storable import Storable, LocalStorage

class MyModel(Hashable, Serializable, Storable, Model, Recordable):
    __tablename__ = 'my_model'
    serializable = ('key', 'name', 'ctime', 'mtime')

    _key =  Column('key', Ascii(40), primary_key=True)
    name =  Column(Unicode(100))

    attachment = Column(LocalStorage('batteries.tests:fixtures/'))

class TestCase(TestCase):
    def setUp(self):
        self.engine = create_engine('sqlite://')
        self.session = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))
        initialize_model(self.session, self.engine)

        warnings.filterwarnings('error')
        Model.metadata.create_all(self.engine)

        from batteries.model import Session
        assert Session == self.session

    def tearDown(self):
        Model.metadata.drop_all(self.engine)
        self.session.close()

    def test_create_model(self):
        m = MyModel()
        self.session.add(m)
        transaction.commit()

    def test_fetch_model(self):
        from batteries.model import Session
        assert Session == self.session

        m = MyModel(_key='foobar', name=u'Foo Bar')
        self.session.add(m)

        transaction.commit()
        transaction.begin()

        m = MyModel.query.limit(1).all()[0]
        assert m.key == 'foobar'

        try:
            assert MyModel.get('foobar') is not None
            assert MyModel.query.filter(MyModel._key == 'foobar').one() is not None

        except Exception as e:
            self.fail("Unexpected exception raised: {0!s}".format(e))

        transaction.commit()

    def test_hashable_key(self):
        m = MyModel()
        self.session.add(m)

        transaction.commit()
        transaction.begin()

        m = MyModel.query.limit(1).all()[0]

        try:
            assert m.key is not None

        except Exception as e:
            self.fail("Unexpected exception raised: {0!s}".format(e))

        transaction.commit()

    def test_recordable_timestamps(self):
        start = datetime.utcnow().replace(tzinfo=tzutc())

        m = MyModel()
        self.session.add(m)

        transaction.commit()
        transaction.begin()

        m = MyModel.query.limit(1).all()[0]

        assert m.ctime >= start
        assert m.mtime >= start

        transaction.commit()

    def test_serializable(self):
        m = MyModel(name=u'Foo Bar')
        self.session.add(m)

        transaction.commit()
        transaction.begin()

        m = MyModel.query.limit(1).all()[0]
        s = m.serialize()

        assert 'key' in s
        assert s['name'] == u'Foo Bar'
        assert s['mtime'] == int(m.mtime.strftime('%s'))
        assert s['ctime'] == int(m.ctime.strftime('%s'))

        transaction.commit()

    def test_local_storage_field(self):
        m = MyModel(name=u'storable')

        resolver = AssetResolver()
        path = resolver.resolve('batteries.tests:fixtures/test_image.png')
        m.attachment.filename = 'test_local_storage_field.png'

        with open(path.abspath(), 'r') as f:
            with m.attachment.open('w+') as a:
                a.write(f.read())

        self.session.add(m)

        transaction.commit()
        transaction.begin()

        m = MyModel.query.one()
        with open(path.abspath(), 'r') as f:
            with m.attachment.open('r') as a:
                assert f.read() == a.read()

        MyModel.delete(m)
        path = m.attachment.abspath
        transaction.commit()

        assert not os.path.isfile(path)

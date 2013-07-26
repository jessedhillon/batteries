from datetime import date, datetime
from dateutil.tz import tzutc
from uuid import uuid4

from sqlalchemy.types import TypeDecorator, DateTime, String
import sqlalchemy.dialects.mysql as mysql
import sqlalchemy.dialects.sqlite as sqlite

from pyramid.path import AssetResolver

class UTCDateTime(TypeDecorator):
    impl = DateTime

    def process_bind_param(self, value, engine):
        if value is not None:
            if value.tzinfo is None:
                # TODO: do we want to assume that unqualified datetimes are UTC?
                return value.replace(tzinfo=tzutc())
            else:
                return value.astimezone(tzutc())

    def process_result_value(self, value, engine):
        if value is not None:
            return datetime(value.year, value.month, value.day,
                                        value.hour, value.minute, value.second,
                                        value.microsecond, tzinfo=tzutc())

class UUID(TypeDecorator):
    impl = String

    def __init__(self):
        self.impl.length = 32
        TypeDecorator.__init__(self, length=self.impl.length)

    def process_bind_param(self, value, dialect=None):
        if value is not None:
            if type(value) is uuid.UUID:
                return value.hex

            raise ValueError("Value {0!r} is not a valid UUID".format(value))

        else:
            return uuid4().hex

    def process_result_value(self,value,dialect=None):
        if value:
            return uuid.UUID(hex=value)

        else:
            return None

    def is_mutable(self):
        return False

class Ascii(TypeDecorator):
    impl = String

    def __init__(self, *args, **kwargs):
        if 'charset' in kwargs:
            del kwargs['charset']

        TypeDecorator.__init__(self, *args, **kwargs)

    def load_dialect_impl(self, dialect):
        if dialect.name == 'mysql':
            return dialect.type_descriptor(mysql.VARCHAR(length=self.length, charset='latin1'))

        else:
            return dialect.type_descriptor(String(self.length))

from datetime import date, datetime
from dateutil.tz import tzutc
from uuid import uuid4

from sqlalchemy.types import TypeDecorator, DateTime, String
from sqlalchemy import func
import sqlalchemy.dialects.mysql as mysql
import sqlalchemy.dialects.sqlite as sqlite
import sqlalchemy.dialects.postgresql as postgresql

from batteries.path import AssetResolver


class Enumeration(TypeDecorator):
    impl = postgresql.ENUM

    def __init__(self, enum):
        super(Enumeration, self).__init__()
        self.enum = enum

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            col = postgresql.ENUM(self.enum.__members__.keys(),
                                  name=self.enum.__name__)
            return dialect.type_descriptor(col)
        raise NotImplementedError()

    def process_bind_param(self, value, dialect):
        return value.name

    def process_result_value(self, value, dialect):
        return getattr(self.enum, value)


class UTCDateTime(TypeDecorator):
    impl = DateTime

    def __init__(self, *args, **kwargs):
        kwargs['timezone'] = True
        super(UTCDateTime, self).__init__(*args, **kwargs)

    def process_bind_param(self, value, engine):
        if value is not None:
            if isinstance(value, basestring) and value == 'UTC':
                return value

            if value.tzinfo is None:
                # TODO: do we want to assume that unqualified datetimes are UTC?
                return value.replace(tzinfo=tzutc())
            else:
                return value.astimezone(tzutc())

    def process_result_value(self, value, engine):
        if value is not None:
            return value.astimezone(tzutc())


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

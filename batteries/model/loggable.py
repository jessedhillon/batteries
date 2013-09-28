from datetime import datetime
from dateutil.tz import tzutc

from batteries.model import Model
from batteries.model import Model
from batteries.model.types import Ascii, UTCDateTime
import batteries.util as util

from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import deferred
from sqlalchemy.schema import Column
from sqlalchemy.types import Unicode, BigInteger, Integer, LargeBinary, Enum
from sqlalchemy import event

class Loggable(object):
    logging_required = True

    def log(self, level, qualifier, message, data=None):
        self._logged = True
        m = self.logging_class(
            level=level,
            timestamp=datetime.utcnow().replace(tzinfo=tzutc()),
            qualifier=qualifier,
            message=message,
            data=data
        )
        self.log_messages.append(m)
        return m

    def debug(self, qualifier, message, data=None):
        return self.log('debug', qualifier, message, data)

    def info(self, qualifier, message, data=None):
        return self.log('info', qualifier, message, data)

    def warn(self, qualifier, message, data=None):
        return self.log('warn', qualifier, message, data)

    def error(self, qualifier, message, data=None):
        return self.log('error', qualifier, message, data)

@event.listens_for(Loggable, 'init', propagate=True)
def on_loggable_init(target, args, kwargs):
    target._logged = False

@event.listens_for(Loggable, 'load', propagate=True)
def on_loggable_load(target, context):
    target._logged = False

@event.listens_for(Loggable, 'before_insert', propagate=True)
def on_loggable_before_insert(mapper, connection, target):
    if target.logging_required and not target._logged:
        raise Exception("Attempting to insert {0!r} instance without log "
                        "message".format(target.__class__.__name__))

@event.listens_for(Loggable, 'before_update', propagate=True)
def on_loggable_before_update(mapper, connection, target):
    if target.logging_required and not target._logged:
        raise Exception("Attempting to update {0!r} without log message".\
                        format(target))

@event.listens_for(Loggable, 'after_insert', propagate=True)
def on_loggable_after_insert(mapper, connection, target):
    target._logged = False

@event.listens_for(Loggable, 'after_update', propagate=True)
def on_loggable_after_update(mapper, connection, target):
    target._logged = False

class LogMessage(Model):
    __abstract__ = True
    __identifiers__ = ('level', 'qualifier', ('timestamp', "[{v!s}]"), 'message')
    timestamp_fmt = None

    id =                Column(Integer, primary_key=True, autoincrement=True)
    level =             Column(Enum('debug', 'info', 'warn', 'error'), nullable=False, index=True)
    timestamp =         Column(UTCDateTime, nullable=False)
    qualifier =         Column(Ascii(100), nullable=False)
    message =           Column(Unicode(500), nullable=False)

    @declared_attr
    def data(cls):
        return deferred(Column(LargeBinary(length=2**20)))

    @property
    def formatted_timestamp(self):
        if self.timestamp_fmt:
            return unicode(self.timestamp.strftime(self.timestamp_fmt))
        return unicode(self.timestamp)

    def __unicode__(self):
        s = u"{level!s:>7} [{l.formatted_timestamp}] <{l.qualifier}> {l.message}".\
                format(level=self.level.upper(), l=self)
        if self.data:
            size = util.format_bytes(len(self.data))
            s += u" @{{{0}}}".format(size)
        return s
    __str__ = __unicode__

@event.listens_for(LogMessage, 'before_insert', propagate=True)
def on_log_message_before_insert(mapper, connection, target):
    if target.timestamp is None:
        target.timestamp = datetime.utcnow().replace(tzinfo=tzutc())

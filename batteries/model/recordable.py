import sys
from datetime import datetime
from dateutil.tz import tzutc

from sqlalchemy.schema import Column
from sqlalchemy import event, func

from batteries.model.types import UTCDateTime


class Recordable(object):
    ctime = Column(UTCDateTime, index=True, server_default=func.clock_timestamp())
    mtime = Column(UTCDateTime, index=True, server_onupdate=func.clock_timestamp())

    ctime._creation_order = sys.maxsize - 1
    mtime._creation_order = sys.maxsize


@event.listens_for(Recordable.ctime, 'before_parent_attach', propagate=True)
def on_ctime_before_parent_attach(column, table):
    column.doc = "creation timestamp for {t.name}".format(t=table)


@event.listens_for(Recordable.mtime, 'before_parent_attach', propagate=True)
def on_mtime_before_parent_attach(column, table):
    column.doc = "modification timestamp for {t.name}".format(t=table)


@event.listens_for(Recordable, 'before_insert', propagate=True)
def on_before_insert(mapper, connection, target):
    target.ctime = datetime.utcnow().replace(tzinfo=tzutc())
    target.mtime = datetime.utcnow().replace(tzinfo=tzutc())


@event.listens_for(Recordable, 'before_update', propagate=True)
def on_before_update(mapper, connection, target):
    target.mtime = datetime.utcnow().replace(tzinfo=tzutc())

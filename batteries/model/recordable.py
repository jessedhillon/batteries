from datetime import datetime
from dateutil.tz import tzutc

from sqlalchemy.schema import Column

from batteries.model.types import UTCDateTime

class Recordable(object):
    ctime = Column(UTCDateTime)
    mtime = Column(UTCDateTime)

    @staticmethod
    def on_before_insert(mapper, connection, target):
        target.ctime = datetime.utcnow().replace(tzinfo=tzutc())
        target.mtime = datetime.utcnow().replace(tzinfo=tzutc())

    @staticmethod
    def on_before_update(mapper, connection, target):
        target.mtime = datetime.utcnow().replace(tzinfo=tzutc())

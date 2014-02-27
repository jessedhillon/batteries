import sys
from datetime import datetime
from dateutil.tz import tzutc

from sqlalchemy.schema import Column
from sqlalchemy import event

from batteries.model.types import UTCDateTime


class Deletable(object):
    delete_time = Column(UTCDateTime)
    delete_time._creation_order = sys.maxsize - 1

    @property
    def is_deleted(self):
        return self.delete_time is not None

    def delete(self):
        self.delete_time = datetime.utcnow().replace(tzinfo=tzutc())

@event.listens_for(Deletable.delete_time, 'before_parent_attach', propagate=True)
def on_is_deleted_before_parent_attach(column, table):
    column.doc = "tracks deletion time for {t.name}".format(t=table)

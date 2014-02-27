import sys
from datetime import datetime
from dateutil.tz import tzutc

from sqlalchemy.schema import Column
from sqlalchemy import event
from sqlalchemy.ext.hybrid import hybrid_property

from batteries.model.types import UTCDateTime


class Deletable(object):
    rmtime = Column(UTCDateTime)
    rmtime._creation_order = sys.maxsize - 1

    @hybrid_property
    def is_deleted(self):
        return self.rmtime is not None

    @is_deleted.expression
    def is_deleted(self):
        return (self.rmtime != None)

    def delete(self):
        self.rmtime = datetime.utcnow().replace(tzinfo=tzutc())

@event.listens_for(Deletable.rmtime, 'before_parent_attach', propagate=True)
def on_is_deleted_before_parent_attach(column, table):
    column.doc = "tracks deletion time for {t.name}".format(t=table)

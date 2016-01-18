from collections import Sequence

from sqlalchemy import event


class Sequenceable(object):
    pass


@event.listens_for(Sequenceable, 'mapper_configured', propagate=True)
def on_mapper_configured(mapper, cls):
    for col, relname in cls.sequence_by.items():
        if isinstance(relname, basestring):
            relation = getattr(mapper.relationships, relname)
            backref = relation.backref or relation.back_populates
        elif isinstance(relname, Sequence):
            relname, backref = relname

        def update_sequence(mapper, connection, self):
            parent = getattr(self, relname)
            if parent is not None:
                for i, obj in enumerate(getattr(parent, backref)):
                    if obj == self:
                        setattr(self, col, i)

        def append(target, value, initiator):
            relname
            import pdb; pdb.set_trace()

        update_sequence.__name__ = 'update_{}_{}'.format(col, relname)
        event.listen(cls, 'before_insert', update_sequence, propagate=True)
        event.listen(cls, 'before_update', update_sequence, propagate=True)

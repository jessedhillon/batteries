from sqlalchemy import event


class Orderable(object):
    pass


@event.listens_for('instrument_class')
def instrument_class(mapper, cls):
    order_col, relation = cls.order_on
    def update_order(mapper, connection, self):
        parent = getattr(self, self.order_by)
        for i, obj in getattr(parent, relation.backref):
            if obj == self:
                setattr(self, order_col, i)

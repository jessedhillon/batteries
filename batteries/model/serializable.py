class Serializer(object):
    datetime_format = '%s'
    date_format = '%Y-%m%d'

def serialize_datetime(dt, opts):
    v = dt.strftime(opts.get('datetime_format', '%s'))
    try:
        return int(v)

    except ValueError:
        return v

def serialize_date(d, opts):
    return d.strftime(opts.get('date_format', '%Y-%m-%d'))

def serialize_Decimal(d, opts):
    return float(d)

def serialize_set(s, opts):
    return list(s)

class Serializable(object):
    __serializable_args__ = {
        'opts': {
            'date_format': '%Y-%m-%d',
        },
        'serializers': {
            'datetime': serialize_datetime,
            'date': serialize_date,
            'Decimal': serialize_Decimal,
            'set': serialize_set
        }
    }

    @classmethod
    def define_serializer(cls, target_cls, serializer):
        if isinstance(target_cls, type):
            target_cls == target_cls.__name__
        self.__serializable_args__['serializers'][target] = serializer

    @classmethod
    def set_serializer_option(cls, name, value):
        self.__serializable_args__['opts'][name] = value

    def serialize(self, *props):
        obj = {}

        for prop in self.__class__.serializable + props:
            v = getattr(self, prop)
            serializer_name = 'serialize_' + prop
            clsname = type(v).__name__

            if hasattr(v, 'serialize'):
                obj[prop] = v.serialize()

            elif hasattr(self, serializer_name):
                obj[prop] = getattr(self, serializer_name)(v)

            elif clsname in self.__serializable_args__.get('serializers'):
                serializer = self.__serializable_args__.get('serializers').get(clsname)
                obj[prop] = serializer(v, self.__serializable_args__.get('opts'))

            else:
                obj[prop] = getattr(self, prop)

        return obj

import collections
import numbers

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

def serialize(v, serializers, opts):
    if isinstance(v, basestring) or isinstance(v, numbers.Number):
        return v

    if hasattr(v, 'serialize'):
        return v.serialize()

    elif isinstance(v, (collections.Sequence, collections.Set)):
        return [serialize(w, serializers, opts) for w in v]

    elif isinstance(v, collections.Mapping):
        return {k: serialize(w, serializers, opts) for k, w in v.items()}

    elif type(v).__name__ in serializers:
        return serializers[type(v).__name__](v, opts)

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

    def serialize(self, fields=None, include=None, exclude=None):
        obj = {}

        if fields is None:
            fields = set(self.__class__.serializable)

            if include is not None:
                fields += set(include)

            if exclude is not None:
                fields -= set(exclude)

        for prop in fields:
            serializer_name = 'serialize_' + prop
            if hasattr(self, serializer_name):
                obj[prop] = getattr(self, serializer_name)()

            else:
                v = getattr(self, prop)
                serializers = self.__serializable_args__['serializers']
                opts = self.__serializable_args__['opts']
                obj[prop] = serialize(v, serializers, opts)

        return obj

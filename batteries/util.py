import unicodedata
import re


class metaproperty(object):
    def __init__(self, getter=None, setter=None):
        self.getter = getter
        self.setter = setter

    def __get__(self, cls, owner):
        return self.getter(cls)

    def __set__(self, cls, value):
        self.setter(value)


def unique_values(seq, idfn=None):
    # order preserving
    if idfn is None:
        def idfn(x): return x

    seen = {}
    result = []
    for item in seq:
        marker = idfn(item)

        if marker not in seen:
            seen.setdefault(marker, True)
            result.append(item)

    return result


def format_bytes(bytes, precision=1):
    bytes = int(bytes)

    abbrevs = (
        (1<<50L, 'PB'),
        (1<<40L, 'TB'),
        (1<<30L, 'GB'),
        (1<<20L, 'MB'),
        (1<<10L, 'kB'),
        (1, 'bytes')
    )
    if bytes == 1:
        return '1 byte'

    for factor, suffix in abbrevs:
        if bytes >= factor:
            break

    return '%.*f %s' % (precision, bytes / factor, suffix)


def prefixed_keys(d, prefix):
    return dict([(k.replace(prefix, ''), v) for k, v in d.items() if k.startswith(prefix)])


def parse_uri(s):
    uri_pattern = re.compile(r'^(?P<scheme>[A-Za-z]+)://(?P<username>[^:]+):(?P<password>[^@]*)@(?P<host>[^:]+):(?P<port>[0-9]+)(?P<urn>.*)')
    return re.match(uri_pattern, s).groupdict()


def slugify(value, sep='-'):
    """https://code.djangoproject.com/browser/django/trunk/django/template/defaultfilters.py#L207"""
    value = unicode(value)
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore')
    value = unicode(re.sub('[^\w\s-]', '', value).strip().lower())
    return re.sub('[-\s]+', sep, value)


def is_sequence(l, strings=False):
    if not strings and isinstance(l, basestring):
        return False

    return hasattr(l, '__getitem__')

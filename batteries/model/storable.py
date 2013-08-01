import os

from sqlalchemy.ext.mutable import Mutable
from sqlalchemy.orm.interfaces import MapperExtension, EXT_CONTINUE, EXT_STOP
from sqlalchemy.types import TypeDecorator, String
from sqlalchemy import event

from batteries.path import AssetResolver

class FileProxy(object):
    def __init__(self, path, filename='', file=None):
        self.path = path
        self.file = file
        self.filename = filename
        self.dirty = False

    def close(self):
        self.file.close()
        self.file = None
        self.dirty = False

    def flush(self):
        self.file.flush()
        self.dirty = False

    def read(self, size=-1):
        return self.file.read(size)

    def readline(self, size=-1):
        return self.file.readline(size)

    def readlines(self, sizehint=None):
        return self.file.readlines(sizehint)

    def seek(self, offset, whence=os.SEEK_SET):
        return self.file.seek(offset, whence)

    def tell(self):
        return self.file.tell()

    def write(self, s):
        self.dirty = True
        return self.file.write(s)

    def writelines(self, seq):
        self.dirty = True
        return self.file.writelines(seq)

class LocalFileProxy(FileProxy):
    def __init__(self, path, filename='', file=None):
        self.resolver = AssetResolver()
        super(LocalFileProxy, self).__init__(path, filename, file)

        if file is not None:
            if isinstance(file, LocalFileProxy):
                self.file = file.file
            else:
                self.open('w+')
                self.write(file.read())

    @property
    def abspath(self):
        assert self.filename, "{0}.filename must be set before calling open()".format(self.__class__.__name__)
        base = self.resolver.resolve(self.path).abspath()
        return os.path.join(base, self.filename)

    def open(self, mode='r'):
        self.file = open(self.abspath, mode)
        return self

    def remove(self):
        os.unlink(self.abspath)

    def __enter__(self):
        return self

    def __exit__(self, type, value, tb):
        self.close()
        return value is None


class LocalStorageType(TypeDecorator):
    impl = String

    def __init__(self, pathspec, *args, **kwargs):
        self.resolver = AssetResolver()
        self.pathspec = pathspec

        TypeDecorator.__init__(self, *args, **kwargs)

    def process_bind_param(self, value, dialect=None):
        return value.filename

    def process_result_value(self, value, dialect=None):
        return MutableLocalFileProxy(self.pathspec, filename=value)

class MutableLocalFileProxy(Mutable, LocalFileProxy):
    @classmethod
    def coerce(cls, key, value):
        if isinstance(value, LocalFileProxy):
            return value

        return LocalFileProxy(file=value)

    def write(self, s):
        super(MutableLocalFileProxy, self).write(s)
        self.changed()

    def writelines(self, s):
        super(MutableLocalFileProxy, self).writelines(s)
        self.changed()

LocalStorage = lambda *args: MutableLocalFileProxy.as_mutable(LocalStorageType(*args))

class Storable(object):
    @property
    def storage_fields(self):
        storage_fields = []
        for k, v in self.__mapper__.columns.items():
            if isinstance(v.type, LocalStorageType):
                storage_fields.append(k)

        return storage_fields

@event.listens_for(Storable, 'init', propagate=True)
def on_init(self, target, context):
    cls = self.__class__

    for f in self.storage_fields:
        column = self.__mapper__.columns[f].type
        path = column.pathspec
        filename = getattr(self, f)
        setattr(self, f, MutableLocalFileProxy(path, filename))

@event.listens_for(Storable, 'before_insert', propagate=True)
def on_before_insert(mapper, connection, target):
    for f in target.storage_fields:
        proxy = getattr(target, f)
        if proxy.dirty:
            proxy.flush()

@event.listens_for(Storable, 'before_delete', propagate=True)
def on_before_delete(mapper, connection, target):
    for f in target.storage_fields:
        proxy = getattr(target, f)
        proxy.remove()

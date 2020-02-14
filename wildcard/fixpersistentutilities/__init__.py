from wildcard.fixpersistentutilities import classfactory
import pickle
from io import StringIO
from ZODB.serialize import ObjectReader
import os


def NewObjectReader_get_class(self, module, name):
    return classfactory.ClassFactory(self._conn, module, name)


def NewObjectReader_get_unpickler(self, pickle):
    file = StringIO.StringIO(pickle)
    unpickler = pickle.Unpickler(file)
    unpickler.persistent_load = self._persistent_load
    factory = classfactory.ClassFactory
    conn = self._conn

    def find_global(modulename, name):
        return factory(conn, modulename, name)

    unpickler.find_global = find_global

    return unpickler


def NewObjectReader_load_multi_persistent(self, database_name, oid, klass):
    conn = self._conn.get_connection(database_name)
    # TODO, make connection _cache attr public
    reader = ObjectReader(conn, conn._cache, classfactory.ClassFactory)
    return reader.load_persistent(oid, klass)


def NewObjectReader_load_multi_oid(self, database_name, oid):
    conn = self._conn.get_connection(database_name)
    # TODO, make connection _cache attr public
    reader = ObjectReader(conn, conn._cache, classfactory.ClassFactory)
    return reader.load_oid(oid)


if os.environ.get('FPU_GENERATE_MISSING_CLASSES') == 'true':
    ObjectReader._get_class = NewObjectReader_get_class
    ObjectReader._get_unpickler = NewObjectReader_get_unpickler
    ObjectReader.load_multi_persistent = NewObjectReader_load_multi_persistent
    ObjectReader.load_multi_oid = NewObjectReader_load_multi_oid


def initialize(context):
    """Initializer called when used as a Zope 2 product."""

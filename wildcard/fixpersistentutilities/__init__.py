# -*- extra stuff goes here -*-
from wildcard.fixpersistentutilities import classfactory
import cPickle
import cStringIO

#Zope2.DB.classFactory = classfactory.ClassFactory

from ZODB.serialize import ObjectReader


def NewObjectReader_get_class(self, module, name):
    return classfactory.ClassFactory(self._conn, module, name)


def NewObjectReader_get_unpickler(self, pickle):
    file = cStringIO.StringIO(pickle)
    unpickler = cPickle.Unpickler(file)
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

ObjectReader._get_class = NewObjectReader_get_class
ObjectReader._get_unpickler = NewObjectReader_get_unpickler
ObjectReader.load_multi_persistent = NewObjectReader_load_multi_persistent
ObjectReader.load_multi_oid = NewObjectReader_load_multi_oid


def initialize(context):
    """Initializer called when used as a Zope 2 product."""

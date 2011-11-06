from zope.interface import Interface
import imp
import sys
import string

_generated_classes = {}
_generated_modules = {}
_auto_gen_enabled = False


def toggleAutoGenClasses():
    global _auto_gen_enabled
    _auto_gen_enabled = not _auto_gen_enabled


class FakeClass(object):
    pass


class IFakeInterface(Interface):
    pass


def create_module(module, name, _globals={}, _silly=('__doc__',)):
    modules = module.split('.')
    current_module_repr = ''
    current_module_obj = None
    for module in modules:
        if current_module_repr:
            current_module_repr += '.'
        current_module_repr += module
        try:
            current_module_obj = __import__(
                current_module_repr, _globals, _globals, _silly)
        except ImportError:
            mod = imp.new_module(module)
            if current_module_obj:
                setattr(current_module_obj, module, mod)
            sys.modules[current_module_repr] = mod
            current_module_obj = mod
            _generated_modules[current_module_repr] = mod
    if not hasattr(current_module_obj, name):
        key = current_module_repr + '.' + name
        if name[0] == "I" and name[1] in string.uppercase:
            # interface class, so let's make an ad-hoc interface class here.
            _generated_classes[key] = IFakeInterface
        else:
            _generated_classes[key] = FakeClass
        setattr(current_module_obj, name, _generated_classes[key])

    return current_module_obj, getattr(current_module_obj, name)


def ClassFactory(jar, module, name, _silly=('__doc__',), _globals={}):
    try:
        m = __import__(module, _globals, _globals, _silly)
        return getattr(m, name)
    except:
        # create the modules
        realmodule, obj = create_module(
            module, name, _globals=_globals, _silly=_silly)
        # don't want to save this object...
        import transaction
        transaction.doom()
        return obj

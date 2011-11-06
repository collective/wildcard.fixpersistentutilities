from Products.Five.browser import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from OFS.interfaces import IApplication
from Products.CMFPlone.interfaces.siteroot import IPloneSiteRoot
from zope.interface import noLongerProvides
from wildcard.fixpersistentutilities import classfactory
from zope.component import getGlobalSiteManager
from urllib import urlencode
from zope.dottedname.resolve import resolve
import inspect
from base64 import b64encode, b64decode

EXPERT_ONLY_NAMESPACES = [
     'plone.',
     'Products.CMFPlone',
     'Products.CMFCore',
     'Products.CMFActionIcons',
     'Products.CMFDiffTool',
     'Products.PortalTransforms',
     'Products.MimetypesRegistry',
     'five.customerize',
     'Products.CMFUid',
     'Products.MailHost',
     'Products.ATContentTypes',
     'Products.SecureMailHost',
     'zope.',
     'five.localsitemanager',
     'Products.TinyMCE'
]


def undoom_transaction():
    import transaction
    if transaction.isDoomed():
        tns = transaction.get()
        tns.status = "Active"


def find_object_or_class(objs, klass, oid):
    if type(objs) not in [list, tuple, set]:
        objs = [objs]
    for obj in objs:
        if (klass == obj or \
                (obj.__class__.__name__ == klass.__name__ and \
                    oid == getattr(obj, '_p_oid', ''))) and \
                        obj.__module__ == klass.__module__:
            return obj

    return None


class FixPersistentUtilities(BrowserView):
    cookie_expired = False
    expert_activated = False

    template = ViewPageTemplateFile('templates/manage-utilities.pt')
    confirm_template = ViewPageTemplateFile('templates/confirm.pt')

    @property
    def auto_gen_missing_classes(self):
        return classfactory._generated_classes

    def sitemanager(self):
        if IApplication.providedBy(self.context):
            return getGlobalSiteManager()
        elif IPloneSiteRoot.providedBy(self.context):
            return self.context.getSiteManager()

    def utilities(self):
        sm = self.sitemanager()
        return {
            'adapters': sm.utilities._adapters[0],
            'subscribers': sm.utilities._subscribers[0],
            'provided': sm.utilities._provided
        }

    def set_utilities(self, utilities, _type):
        if _type in ['adapters', 'subscribers']:
            utilities = [utilities]

        setattr(self.sitemanager().utilities, '_' + _type, utilities)

    def deletable(self, klass):
        if not hasattr(klass, '__module__'):
            return False
        elif self.expert:
            return True
        else:
            for namespace in EXPERT_ONLY_NAMESPACES:
                if klass.__module__.startswith(namespace):
                    return False
            return True

    def delete_utility_reg(self):
        if not self.request.get('submit', self.request.get('cancel')):
            return self.confirm_template(
                msg="Are you sure you want to delete %s -- %s : %s" % (
                    self.request.get('util_dottedname'),
                    self.request.get('reg_name'),
                    self.request.get('reg_dottedname')
                ),
                action='/delete-persistent-utility-reg',
                params=self.request.form.items()
            )
        elif self.request.get('cancel') == 'No':
            return self.request.response.redirect(
                self.context.absolute_url() + '/@@fix-persistent-utilities')

        undoom_transaction()

        utilities = self.utilities()
        _type = self.request.get('type')
        utility_registrations = utilities[_type]
        util_klass = resolve(self.request.get('util_dottedname'))
        reg_name = self.request.get('reg_name')
        reg_klass = resolve(self.request.get('reg_dottedname'))
        if not self.deletable(reg_klass):
            raise Exception("I'm not going to allow you to delete that!")
        oid = b64decode(self.request.get('reg_obj_oid'))
        for x in utility_registrations.keys():
            if x.__module__ == util_klass.__module__ and x == util_klass:
                for name, klass in utility_registrations[x].items():
                    found = find_object_or_class(klass, reg_klass, oid)
                    if name == reg_name and found:
                        if type(utility_registrations[x][name]) in \
                                                        [list, tuple, set]:
                            regs = list(utility_registrations[x][name])
                            regs.remove(found)
                            utility_registrations[x][name] = tuple(regs)
                        else:
                            del utility_registrations[x][name]

        self.set_utilities(utility_registrations, _type)
        self.request.response.redirect(
            self.context.absolute_url() + '/@@fix-persistent-utilities')

    def delete_utility(self):
        if not self.request.get('submit', self.request.get('cancel')):
            return self.confirm_template(
                msg="Are you sure you want to delete %s" % \
                                self.request.get('util_dottedname'),
                action='/delete-persistent-utility',
                params=self.request.form.items()
            )
        elif self.request.get('cancel') == 'No':
            return self.request.response.redirect(
                self.context.absolute_url() + '/@@fix-persistent-utilities')

        undoom_transaction()

        utilities = self.utilities()
        _type = self.request.get('type')
        utility_registrations = utilities[_type]
        klass = resolve(self.request.get('util_dottedname'))
        if not self.deletable(klass):
            raise Exception("I'm not going to allow you to delete that!")
        for x in utility_registrations.keys():
            if x.__module__ == klass.__module__ and x == klass:
                del utility_registrations[x]
                break
        self.set_utilities(utility_registrations, _type)

        self.request.response.redirect(
            self.context.absolute_url() + '/@@fix-persistent-utilities')

    def __call__(self):

        return self.template(utilities=self.utilities())

    def utility_data(self, klass, _type):
        return {
            'util_dottedname': klass.__module__ + '.' + klass.__name__,
            'type': _type
        }

    def utility_reg_data(self, util_klass, _type, reg_name, reg_klass):
        data = self.utility_data(util_klass, _type)
        dottedname = reg_klass.__module__ + '.' + (inspect.isclass(reg_klass) \
                        and reg_klass.__name__ or reg_klass.__class__.__name__)
        oid = b64encode(hasattr(reg_klass, '_p_oid') and \
                reg_klass._p_oid or '')
        data.update({
            'reg_name': reg_name,
            'reg_dottedname': dottedname,
            'reg_obj_oid': oid
        })
        return data

    def remove_utility_url(self, klass, _type):
        data = urlencode(self.utility_data(klass, _type))
        return '%s/@@delete-persistent-utility?%s' % (
            self.context.absolute_url(), data)

    def remove_utility_reg_url(self, util, _type, reg_name, reg_klass):
        data = self.utility_reg_data(util, _type, reg_name, reg_klass)
        data = urlencode(data)
        return '%s/@@delete-persistent-utility-reg?%s' % (
            self.context.absolute_url(), data)

    def name(self, m):
        return str(m)

    def activate_expert_mode(self):
        self.request.response.setCookie('expert-mode', 'yes')
        self.expert_activated = True
        return self()

    def deactivate_expert_mode(self):
        self.request.response.expireCookie('expert-mode')
        self.cookie_expired = True
        return self()

    @property
    def expert(self):
        expert = self.request.cookies.get('expert-mode', 'no') == 'yes'
        return not self.cookie_expired and expert or self.expert_activated


class RemoveInterfaces(BrowserView):

    def obj_path(self, obj):
        if hasattr(obj, 'getPhysicalPath'):
            return '/'.join(obj.getPhysicalPath())
        else:
            return getattr(obj, 'id')

    def check_folder(self, context, iface, dryrun):
        for id in context.objectIds():
            obj = context[id]
            if iface.providedBy(obj):
                if not dryrun:
                    noLongerProvides(obj, iface)
                self.request.response.write('Removed from %s\n' % \
                    self.obj_path(obj))

            if hasattr(obj, 'objectIds'):
                self.check_folder(obj, iface, dryrun)

    def __call__(self):
        if self.request.get('submitted'):
            dryrun = self.request.get('dryrun', False) == 'true' or False
            try:
                iface = resolve(self.request.get('dottedname'))
            except ImportError:
                # can't find, let's create it and maybe we can still fix it..
                module, name = self.request.get('dottedname').rsplit('.', 1)
                _, iface = classfactory.create_module(module, name)

            self.request.response.write('Removing %s\n' % \
                self.request.get('dottedname'))

            obj = self.context
            if iface.providedBy(obj):
                if not dryrun:
                    noLongerProvides(obj, iface)
                self.request.response.write('Removed from %s\n' % \
                    self.obj_path(obj))
            if not dryrun:
                undoom_transaction()
            self.check_folder(obj, iface, dryrun)
            self.request.response.write('done.')
        else:
            return super(RemoveInterfaces, self).__call__()

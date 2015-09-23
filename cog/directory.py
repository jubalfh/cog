# -*- coding: utf-8 -*-

# Copyright (c) 2013, Activision Publishing, Inc.

# the cog project is free software under 3-clause BSD licence
# see the LICENCE file in the project root for copying terms

# lightweight wrapper over python-ldap functions

import os, sys
import time
import ldif
import ldap
import ldap.dn
import ldap.sasl
import ldap.schema
import ldap.modlist as modlist
import cog.util.passwd as passwd

from pprint import pprint
from functools import wraps
from ldapurl import ldapUrlEscape as ldap_uri_escape
from StringIO import StringIO
from cog.cidict import cidict
from cog.util.misc import get_current_uid, loop_on, Singleton
from cog.config.settings import Profiles
from cog.config.templates import Templates


accounts, groups, netgroups = (Templates().get(section) for section in ['accounts', 'groups', 'netgroups'])
settings = Profiles()

# Exceptions
class DirectoryException(Exception):
    """Base class for all directory exceptions"""

class MultipleObjectsFound(DirectoryException):
    """
    Multiple objects found, single item expected.
    """

class ObjectNotFound(DirectoryException):
    """
    No objects found, single item expected.
    """

class ServerUnavailable(DirectoryException):
    """
    LDAP server is not available.
    """


# misc things
def get_probably_unique_uidnumber():
    tree = Tree()
    # FIXME: use limits stored within directory, fall back to the full
    # directory search only if there is no other option available.
    # return tree.increment_atomically(settings.user_defaults_dn, 'uidNext')
    max_uidnumber = settings.max_uidnumber
    min_uidnumber = settings.min_uidnumber
    return str(max([int(x['uidNumber'][0]) for x in
                    tree.search(search_filter=('(&(objectClass=posixAccount)(uidNumber<=%s))' % max_uidnumber),
                                attributes=['uidNumber'])] + [min_uidnumber]) + 1)


def get_probably_unique_gidnumber():
    tree = Tree()
    # FIXME: use limits stored within directory!
    max_gidnumber = settings.max_gidnumber
    min_gidnumber = settings.min_gidnumber
    return str(max([int(x['gidNumber'][0]) for x in
                    tree.search(search_filter=('(&(objectClass=posixGroup)(gidNumber<=%s))' % max_gidnumber),
                                attributes=['gidNumber'])] + [min_gidnumber]) + 1)

def path2rdn(path):
    path_list = ["ou=%s," % x for x in path.strip('/').split('/')[::-1] if x]
    return "".join(path_list)

def get_account_base(name):
    return path2rdn(accounts.get(name).get('path')) + settings.user_dn

def get_group_base(name):
    return path2rdn(groups.get(name).get('path')) + settings.group_dn

def get_netgroup_base(name):
    return path2rdn(netgroups.get(name).get('path')) + settings.netgroup_dn

def find_dn_for_uid(uid=None):
    if not uid:
        uid = get_current_uid()
    tree = Tree()
    base_dn = settings.user_dn
    query = '(&(objectClass=posixAccount)(uid=%s))' % uid
    users = tree.search(base_dn, search_filter=query, attributes=['dn'])
    if len(users) > 1:
        raise MultipleObjectsFound("The uid is not unique in the directory tree")
    elif not users:
        user_dn = None
    else:
        user_dn = users[0].dn
    return user_dn

# a few schema helper functions
def get_object_class(oc):
    _, schema = ldap.schema.urlfetch(settings.ldap_uri)
    return schema.get_obj(ldap.schema.ObjectClass, oc)

def is_structural(oc):
    return get_object_class(oc).kind == 0

def is_abstract(oc):
    return get_object_class(oc).kind == 1

def is_auxiliary(oc):
    return get_object_class(oc).kind == 2

def has_rfc2307bis():
    oc = settings.rfc2307bis_group_object_class
    return (is_auxiliary('posixGroup') and is_structural(oc))

# Classes

# Directory entry
class Entry(cidict):
    """
    case-aware case-insensitive LDAP entry dictionary with basic editing
    functions
    """
    def __init__(self, dn, attrs=None, use_dn=False):
        super(Entry, self).__init__()
        if attrs:
            for attr, values in attrs.items():
                self.append(attr, values)
        if use_dn:
            for rdn_elements in ldap.dn.explode_rdn(dn):
                rdn_attr, rdn_value = rdn_elements.split('=')
                self.replace(rdn_attr, rdn_value)
        self.dn = dn

    def replace(self, attr, values):
        self[attr] = list(loop_on(values))

    def append(self, attr, values):
        if attr in self:
            for value in loop_on(values):
                if value not in self[attr]:
                    self[attr].append(value)
        else:
            self.replace(attr, values)

    def remove(self, attr, values):
        if self.has_key(attr):
            for value in loop_on(values):
                if value in self[attr]:
                    self[attr].remove(value)
            if not self[attr]:
                del(self[attr])

    def to_ldif(self):
        out = StringIO()
        ldif_out = ldif.LDIFWriter(out, None, 1000)
        ldif_out.unparse(self.dn, self)
        return out.getvalue()


# wrapper over LDAPObject
class Tree(object):
    __metaclass__ = Singleton


    def __init__(self):
        """
        Get an LDAP directory handle, open (preferably) encrypted connection.
        """
        self.base_dn = settings.base_dn
        self.bind_dn = settings.bind_dn
        self.bind_pass = settings.bind_pass
        self.ldap_encryption = settings.ldap_encryption
        self.ldap_uri = settings.ldap_uri
        self.bound = False
        self._bind = self._simple_bind
        if self.ldap_uri.startswith('ldapi'):
            self.ldap_uri = 'ldapi://%s/' % ldap_uri_escape(settings.ldapi_path)
            self._bind = self._sasl_bind
        self._connect()
        return

    def _connect(self):
        cacertfile = settings.ldap_cacertfile
        self.bound = False
        self.ldap_handle = ldap.initialize(self.ldap_uri, trace_level=0, trace_file=sys.stderr)
        self.ldap_handle.set_option(ldap.OPT_PROTOCOL_VERSION, 3)
        #self.ldap_handle.set_option(ldap.OPT_DEBUG_LEVEL, 255)

        if not self.ldap_uri.startswith('ldaps') and self.ldap_encryption:
            if cacertfile:
                self.ldap_handle.set_option(ldap.OPT_X_TLS_CACERTFILE, cacertfile)
            self.ldap_handle.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_DEMAND)
            self.ldap_handle.set_option(ldap.OPT_X_TLS_NEWCTX, 0)
            self.ldap_handle.start_tls_s()

    def _simple_bind(self):
        """
        Make non-anonymous directory bind. (And let the python-ldap implementation
        handle the fallout.)
        """
        if not self.bound:
            if not self.bind_dn:
                self.bind_dn = find_dn_for_uid()
            if not self.bind_pass:
                self.bind_pass = passwd.get_passwd(self.bind_dn,
                                              settings.keyring_service,
                                              "enter your LDAP password: ",
                                              use_keyring=settings.use_keyring)
                self._reconnect()
            self.ldap_handle.simple_bind_s(self.bind_dn, self.bind_pass)
            self.bound = True

    def _sasl_bind(self):
        """
        Make non-anonymous directory bind using SASL EXTERNAL mechanism.
        """
        if not self.bound:
            self.ldap_handle.sasl_external_bind_s()
            self.bound = True

    def _is_connected(self):
        """
        Check if the connection is live.
        """
        try:
            data = self.ldap_handle.search_s(self.base_dn, ldap.SCOPE_BASE, 'objectClass=*', [])
        except ldap.LDAPError:
            return False
        return True

    def _reconnect(self, tries=3, timeout=2):
        """
        Try to reconnect if the LDAP connection is down.
        """
        for i in range(tries):
            if not self._is_connected():
                time.sleep(i * timeout)
                self._connect()
            else:
                return
        raise ServerUnavailable("LDAP server not available.")

    # decorators
    def keep_connected(method):
        """
        Make sure that the the LDAP connection is live
        """
        @wraps(method)
        def _keep_connected(self, *args, **kwargs):
            self._reconnect()
            return method(self, *args, **kwargs)
        return _keep_connected

    def readwrite(method):
        """
        Make sure that a non-anonymous bind is used before trying directory updates
        """
        @wraps(method)
        def _readwrite(self, *args, **kwargs):
            self._bind()
            return method(self, *args, **kwargs)
        return _readwrite

    # methods
    def get_connection(self):
        """
        Convenience function returning a handle to a naked LDAPObject.
        """
        return self.ldap_handle

    def bind_as(self, dn, password=None):
        """
        Set the LDAP DN that will be used for binds.
        """
        self.bind_dn = dn
        self.bind_pass = password
        self.bound = False

    @keep_connected
    def search(self, base=None, search_filter='objectClass=*',
               scope=ldap.SCOPE_SUBTREE, attributes=None, bind=False):
        """
        Simple wrapper on python-ldap's search_s(). Returns list of
        Entry objects.
        """
        if bind:
            self._bind()
        if not base:
            base = self.base_dn
        if not attributes:
            attributes = []
        data = self.ldap_handle.search_s(base, scope, search_filter, attributes)
        if data:
            return [Entry(entry[0], entry[1]) for entry in data]
        else:
            return []

    def get(self, dn, bind=False):
        """
        Return _ONE_ Entry object of given DN. Or None.
        """
        data = self.search(dn, scope=ldap.SCOPE_BASE, attributes=[], bind=bind)
        if data:
            return data[0]
        else:
            return None

    @keep_connected
    @readwrite
    def add(self, new_entry):
        """
        Add new entry to the LDAP directory.
        """
        dn = new_entry.dn
        entry_modlist = modlist.addModlist(new_entry)
        self.ldap_handle.add_s(dn, entry_modlist)

    @keep_connected
    @readwrite
    def modify(self, changed_entry):
        """
        Modify contents of an LDAP entry.
        """
        dn = changed_entry.dn
        old_entry = self.get(dn)
        entry_modlist = modlist.modifyModlist(old_entry, changed_entry,
                ignore_oldexistent=0)
        self.ldap_handle.modify_s(dn, entry_modlist)

    @keep_connected
    @readwrite
    def replace(self, new_entry):
        """
        Replace an existing LDAP entry with a new one.
        """
        dn = new_entry.dn
        self.remove(dn)
        self.add(dn, new_entry)

    @keep_connected
    @readwrite
    def remove(self, dn):
        """
        Remove an entry from the LDAP directory.
        """
        self.ldap_handle.delete_s(dn)

    @keep_connected
    @readwrite
    def move(self, dn, new_parent, new_rdn=None):
        """
        Move and/or rename an LDAP entry.
        """
        if not new_rdn:
            new_rdn = ldap.explode_dn(dn)[0]
        self.ldap_handle.rename_s(dn, new_rdn, newsuperior=new_parent, delold=1)

    @keep_connected
    @readwrite
    def rename(self, dn, new_rdn):
        """
        Rename an LDAP entry.
        """
        self.ldap_handle.rename_s(dn, new_rdn, delold=1)

    @keep_connected
    @readwrite
    def increment_atomically(self, dn, attr):
        """
        Increment value of an attribute, atomically. A special case.
        """
        while True:
            try:
                val = int(self.get(dn)[attr][0])
                mod_list = [ (ldap.MOD_DELETE, attr, str(val)),
                    (ldap.MOD_ADD, attr, str(val + 1)) ]
                self.ldap_handle.modify_s(dn, mod_list)
            except ldap.NO_SUCH_ATTRIBUTE:
                pass
            else:
                break
        return val

# -*- coding: utf-8 -*-

# Copyright (c) 2013, Activision Publishing, Inc.
# Copyright (c) 2014, 2015 Miroslaw Baran <miroslaw+p+cog@makabra.org>

# the cog project is free software under 3-clause BSD licence
# see the LICENCE file in the project root for copying terms

# process configuration files

import os
import sys
import shutil

from pprint import pprint
from click import get_app_dir
from os.path import join as pathjoin, dirname, isdir
from cog.util.io import merge_data
from cog.util.misc import dict_merge, Singleton


defaults = {
    'ldap_uri': 'ldap://ldap/',
    'ldap_encryption': True,
    'bind_dn': None,
    'bind_pass': None,
    'keyring_service': 'org.makabra.cog',
    'use_keyring': False,
    'user_rdn': 'uid',
    'user_query': '(&(%s=%s)(|(objectClass=posixAccount)(objectClass=inetOrgPerson)))',
    'group_query': '(&(cn=%s)(objectClass=posixGroup))',
    'netgroup_query': '(&(cn=%s)(objectClass=nisNetgroup))',
    'min_uidnumber': 420000,
    'max_uidnumber': 1000000,
    'min_gidnumber': 420000,
    'max_gidnumber': 1000000,
    'rfc2307bis_group_object_class': 'groupOfMembers',
    'rfc2307bis_group_member_attribute': 'member',
    'use_memberuid': True,
}


class Profiles(object):
    __metaclass__ = Singleton

    def __init__(self, user_config=True):

        progpath = dirname(sys.argv[0])

        self.progname = 'cog'
        self.profiles = dict()
        self.store = dict()
        self.cfg_dirs = [pathjoin(dirname(progpath), 'etc', self.progname)]
        if user_config:
            self.make_conf()
            self.cfg_dirs.append(get_app_dir(self.progname, force_posix=True))
        self.cfg_files = [pathjoin(cfg_dir, 'settings')
                          for cfg_dir in self.cfg_dirs if isdir(cfg_dir)]

        self.profiles = merge_data(*self.cfg_files)
        self.current = self.profiles.pop('profile')
        for name, profile in self.profiles.items():
            self.profiles[name] = dict_merge(defaults, profile)
        self.use(self.current)

    def __getattr__(self, key):
        return self.store.get(key, None)

    def make_conf(self):
        appdir = get_app_dir(self.progname, force_posix=True)
        if not os.path.exists(appdir):
            os.makedirs(appdir, mode=0750)
            os.makedirs(pathjoin(appdir, 'templates.d'), mode=0750)
            shutil.copyfile(
                pathjoin(self.cfg_dirs[0], 'examples/settings.local'),
                pathjoin( appdir, 'settings'))

    def list(self):
        return self.profiles.keys()

    def use(self, name):
        if name in self.list():
            self.current = name
            self.store = self.profiles.get(self.current)


if __name__ == "__main__":
    a = Profiles()
    pprint(a.description)
    b = Profiles()
    b.use('test')
    pprint(a.description)
    pprint(b.description)

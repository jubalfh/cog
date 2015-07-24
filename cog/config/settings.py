# -*- coding: utf-8 -*-

# Copyright (c) 2013, Activision Publishing, Inc.
# Copyright (c) 2014, 2015 Miroslaw Baran <miroslaw+p+cog@makabra.org>

# the cog project is free software under 3-clause BSD licence
# see the LICENCE file in the project root for copying terms

# process configuration files

import os
import sys

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
    'rfc2307bis_group_sync_attributes': True,
}


class Profiles(dict):
    __metaclass__ = Singleton

    def __init__(self, user_config=True):
        super(self.__class__, self).__init__({})

        progpath = dirname(sys.argv[0])

        self.progname = 'cog'
        self.profiles = dict()
        self.cfg_dirs = [pathjoin(dirname(progpath), 'etc', self.progname)]
        if user_config:
            self.cfg_dirs.append(get_app_dir(self.progname, force_posix=True))
        self.cfg_files = [pathjoin(cfg_dir, 'settings')
                          for cfg_dir in self.cfg_dirs if isdir(cfg_dir)]

        self.profiles = merge_data(*self.cfg_files)
        self.profile = self.profiles.pop('profile')

    def list(self):
        return self.profiles.keys()

    def current(self, name=None):
        return dict_merge(defaults, self.profiles.get(name or self.profile))

    def use(self, name):
        if name in self.list():
            self.profile = name

if __name__ == "__main__":
    pprint(Profiles().current())

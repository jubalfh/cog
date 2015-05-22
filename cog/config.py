# -*- coding: utf-8 -*-

# Copyright (c) 2013, Activision Publishing, Inc.

# the cog project is free software under 3-clause BSD licence
# see the LICENCE file in the project root for copying terms

# process configuration files

import os
import sys
import yaml
import shutil
import cog.util as util


user_config_dir = os.path.join(os.path.expandvars('${HOME}'), '.cog')
config_dirs = []
config_files = []
template_files = []
for config_dir in ['/etc/cog', os.path.join(sys.argv[0].partition('/bin/')[0], "etc/cog")]:
    if os.path.exists(config_dir):
        config_dirs.append(config_dir)
        config_files.append(os.path.join(config_dir, "settings"))
        template_files.append(os.path.join(config_dir, "templates.yaml"))


def read_yaml(filename):
    data = dict()
    try:
        with open(filename) as fh:
            data = yaml.safe_load(fh)
    except (IOError, yaml.YAMLError), e:
        print e
    return data


def merge_data(*files):
    data = dict()
    for file in files:
        if os.path.exists(file):
            data = util.merge(data, read_yaml(file))
    return data


def expand_inheritances(template_data, section):
    template = dict()
    for k, v in template_data.get(section).iteritems():
        if 'inherits' in v:
            base = v.get('inherits')
            template[k] = util.merge(template_data.get(section).get(base).get('default'), v.get('default'))
        else:
            template[k] = v.get('default')
    return template


def make_user_config():
    if not os.path.exists(user_config_dir):
        os.makedirs(user_config_dir, mode=0750)
        shutil.copyfile(os.path.join(config_dirs[0], 'examples/settings.local'),
                        os.path.join(user_config_dir, 'settings'))


class Profiles(dict):
    __metaclass__ = util.Singleton

    def __init__(self):
        super(self.__class__, self).__init__({})

        user_settings_file = os.path.join(user_config_dir, 'settings')

        self.defaults = {
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
            'user_config': read_yaml(config_files[0]).get('user_config', True),
        }

        if self.defaults.get('user_config'):
            config_files.append(user_settings_file)
        settings_data = merge_data(*config_files)
        self.user_config = settings_data.pop('user_config')
        self.profile = settings_data.pop('profile')
        for k, v in settings_data.iteritems():
            self[k] = v

    def list(self):
        return self.keys()

    def current(self, name=None):
        return util.merge(self.defaults, self.get(name or self.profile))

    def use(self, name):
        if name in self.keys():
            self.profile = name

template_files.append(os.path.join(user_config_dir, 'templates.yaml'))
template_data = merge_data(*template_files)

objects = dict()
for object in ['accounts', 'groups', 'netgroups']:
    objects[object] = expand_inheritances(template_data, object)

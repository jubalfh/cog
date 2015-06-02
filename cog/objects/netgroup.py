# -*- coding: utf-8 -*-

# Copyright (c) 2013, Activision Publishing, Inc.

# the cog project is free software under 3-clause BSD licence
# see the LICENCE file in the project root for copying terms

# netgroup object handling

from functools import wraps

import cog.directory as dir
from cog.config import Profiles

settings = Profiles().current()


def make_triple(host, uid, domain):
    return '(%s,%s,%s)' % (host or '', uid or '', domain or '')


class Netgroup(object):
    def __init__(self, netgroupname, netgroup_data=None):
        self.tree = dir.Tree()
        self.netgroupname = netgroupname
        self.base_dn = settings.get('group_dn')
        self.ldap_query = settings.get('netgroup_query') % (self.netgroupname)
        self.exists = True
        netgroups = self.tree.search(self.base_dn, search_filter=self.ldap_query)
        if len(netgroups) > 1:
            raise dir.MultipleObjectsFound
        if len(netgroups) == 1:
            self.data = netgroups[0]
        else:
            self.exists = False
            self.data = netgroup_data
        print self.data

    def netgroup_exists(method):
        """
        Make sure that you're operating on an existing object."
        """
        @wraps(method)
        def _netgroup_exists(self, *args, **kwargs):
            if not self.exists:
                raise dir.ObjectNotFound("Netgroup ‘%s’ cannot be found." % self.netgroupname)
            return method(self, *args, **kwargs)
        return _netgroup_exists

    def add(self):
        self.tree.add(self.data)
        self.exists = True

    @netgroup_exists
    def commit_changes(self):
        self.tree.modify(self.data)

    @netgroup_exists
    def set_description(self, description):
        self.data.replace('description', description)

    @netgroup_exists
    def rename(self, new_netgroupname):
        self.tree.rename(self.dn, new_netgroupname)

    @netgroup_exists
    def remove(self):
        self.tree.remove(self.data.dn)

    @netgroup_exists
    def add_triple(self, triple):
        if ('nisNetgroupTriple' not in self.data or
           triple not in self.data['nisNetgroupTriple']):
            self.data.append('nisNetgroupTriple', triple)

    @netgroup_exists
    def del_triple(self, triple):
        self.data.remove('nisNetgroupTriple', triple)

    @netgroup_exists
    def add_member(self, member):
        if ('memberNisNetgroup' not in self.data or
           member not in self.data['memberNisNetgroup']):
            self.data.append('memberNisNetgroup', member)

    @netgroup_exists
    def del_member(self, member):
        self.data.remove('memberNisNetgroup', member)

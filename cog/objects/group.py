# -*- coding: utf-8 -*-

# Copyright (c) 2013, Activision Publishing, Inc.
# Copyright (c) 2014, 2015 Miroslaw Baran <miroslaw+p+cog@makabra.org>

# the cog project is free software under 3-clause BSD licence
# see the LICENCE file in the project root for copying terms

# user group object handling

import os
import sys
from functools import wraps

import ldap
import ldap.modlist as modlist

import cog.directory as dir
from cog.util.misc import loop_on
from cog.config.settings import Profiles
from cog.directory import has_rfc2307bis

settings = Profiles()
rfc2307bis_object_class = settings.rfc2307bis_group_object_class
rfc2307bis_member_attribute = settings.rfc2307bis_group_member_attribute
rfc2307bis = True


class Group(object):
    def __init__(self, gid, group_data=None):
        self.tree = dir.Tree()
        self.gid = gid
        self.base_dn = settings.group_dn
        self.ldap_query = settings.group_query % (self.gid)
        self.exists = True
        if has_rfc2307bis():
            rfc2307bis = True
        else:
            settings.use_memberuid = True
            rfc2307bis = False
        groups = self.tree.search(self.base_dn, search_filter=self.ldap_query)
        if len(groups) > 1:
            raise dir.MultipleObjectsFound
        elif len(groups) == 1:
            self.data = groups[0]
        else:
            self.exists = False
            self.data = group_data

    def group_exists(method):
        """
        Make sure that you're operating on an existing object."
        """
        @wraps(method)
        def _group_exists(self, *args, **kwargs):
            if not self.exists:
                raise dir.ObjectNotFound("Group ‘%s’ cannot be found." % self.gid)
            return method(self, *args, **kwargs)
        return _group_exists

    def add(self):
        if rfc2307bis:
            self.data.append('objectClass', rfc2307bis_object_class)
        self.tree.add(self.data)
        self.exists = True

    @group_exists
    def set_description(self, description):
        self.data.replace('description', description)
        self.tree.modify(self.data)

    @group_exists
    def rename(self, new_cn):
        self.tree.rename(self.data.dn, new_rdn='cn=%s' % new_cn)

    @group_exists
    def remove(self):
        self.tree.remove(self.data.dn)

    @group_exists
    def add_uid(self, uids):
        for uid in loop_on(uids):
            if settings.use_memberuid and ('memberUid' not in self.data or
                    uid not in self.data['memberUid']):
                self.data.append('memberUid', uid)
            if rfc2307bis:
                uid_dn = dir.find_dn_for_uid(uid)
                if not uid_dn:
                    raise dir.ObjectNotFound("User object not found.")
                if (rfc2307bis_member_attribute not in self.data or
                      uid_dn not in self.data[rfc2307bis_member_attribute]):
                    self.data.append(rfc2307bis_member_attribute, uid_dn)

    @group_exists
    def del_uid(self, uids):
        for uid in loop_on(uids):
            if settings.use_memberuid:
                self.data.remove('memberUid', uid)
            if rfc2307bis:
                uid_dn = dir.find_dn_for_uid(uid)
                if not uid_dn:
                    raise dir.ObjectNotFound("User object not found.")
                self.data.remove(rfc2307bis_member_attribute, uid_dn)

    @group_exists
    def commit_changes(self):
        self.tree.modify(self.data)


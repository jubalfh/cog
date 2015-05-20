# -*- coding: utf-8 -*-

# Copyright (c) 2013 Activision Publishing, Inc.
# Copyright (c) 2014, 2015 Miroslaw Baran <miroslaw+p+cog@makabra.org>

# the cog project is free software under 3-clause BSD licence
# see the LICENCE file in the project root for copying terms


import sys
import getpass
import argparse
import cog.util as util
import cog.directory as dir
from cog.objects.netgroup import Netgroup, make_triple
from cog.config import objects, Profiles

from access_argparser import tool_parser, arg_no

netgroups = objects.get('netgroups')
settings = Profiles().current()
access_levels = dict(zip(['denied', 'granted', 'admin'],
                         ['denied', 'granted', 'privileged']))

def get_access_group(name, priv_level='granted'):
    """
    Gets a netgroup handle. Creates the group when necessary.
    """
    group_type = 'security'
    group_data = util.merge(netgroups.get(group_type), {})
    path = group_data.pop('path')
    requires = group_data.pop('requires')
    group_name = '%s-%s' % (name, priv_level)
    description = 'Users with %s access to %s.' % (access_levels[priv_level], name)

    dn = 'cn=%s,%s' % (group_name, dir.get_netgroup_base(group_type))
    access_group = Netgroup(group_name, dir.Entry(dn=dn,
                                                  attrs=group_data,
                                                  use_dn=True))
    if not access_group.exists:
        access_group.add()
        access_group.set_description(description)
    return access_group


def manage_access(args, priv_level='granted'):
    for access_object in util.flatten_list(args.get('services', [])):
        access_group = get_access_group(access_object.lower(), priv_level)
        for uid in util.flatten_list(args.get('uid')):
            access_group.add_triple([make_triple(None, uid, None)])
        access_group.commit_changes()


def revoke_access(args):
    revoke_levels = args.pop('revoke_levels', ['granted'])
    for priv_level in access_levels.keys():
        if access_levels[priv_level] in revoke_levels:
            for access_object in util.flatten_list(args.get('services', [])):
                access_group = get_access_group(access_object.lower(), priv_level)
                for uid in util.flatten_list(args.get('uid')):
                    access_group.del_triple(make_triple(None, uid, None))
                    access_group.commit_changes()


def show_access(args):
    tree = dir.Tree()
    if args.get('query_type') in ['host', 'cluster', 'service']:
        # make sure that the netgroup actually contains any triples:
        query = '(&(objectClass=nisNetgroup)(cn=%s-%s)(nisNetgroupTriple=*))'
        for priv_level in access_levels.keys():
            for access_object in args.get('query'):
                search = tree.search(search_filter=(query % (access_object, priv_level)),
                                     attributes=['cn', 'nisNetgroupTriple'])
                if search:
                    users = [x.strip('(-,)') for x in search[0]['nisNetgroupTriple']]
                    print '%s at %s: %s' % (access_levels[priv_level], access_object, ', '.join(users))
    elif args.get('query_type') == 'user':
        uids = args.get('query')
        access_list = dict((k, { key: set([]) for key in access_levels.keys() }) for k in uids)
        query_uids = ''.join(['(nisNetgroupTriple=*,%s,*)' % uid for uid in uids])
        if len(uids) > 1:
            query_uids = '(|' + query_uids + ')'
        query = '(&(objectClass=nisNetgroup)(cn=*-*)%s)' % query_uids
        for netgroup_entry in tree.search(search_filter = query, attributes=['cn', 'nisNetgroupTriple']):
            access_object, priv_level = netgroup_entry.get('cn')[0].rsplit('-', 1)
            access_uids = [x.strip('(-,)') for x in netgroup_entry.get('nisNetgroupTriple')]
            for uid in uids:
                if uid in access_uids:
                    access_list[uid][priv_level].add(access_object)
        for uid, access_object in access_list.items():
            for priv_level in sorted(access_levels.keys()):
                if access_object[priv_level]:
                    print "%s: %s access at %s" % (uid, access_levels[priv_level], ", ".join(sorted(access_object[priv_level])))


def main():
    if arg_no < 2 or sys.argv[1] in ['-h', '--help']:
        print tool_parser.format_help()
        sys.exit(1)

    args = dict((k, v) for k, v in vars(tool_parser.parse_args()).items() if v is not None)
    command = args.pop('command')
    is_privileged = args.pop('privileged', False)
    netgroup_type = args.pop('netgroup_type', 'generic')

    if command in ['grant', 'deny']:
        priv_level = 'denied'
        if command == 'grant':
            priv_level = 'admin' if is_privileged else 'granted'
        manage_access(args, priv_level=priv_level)
    elif command == 'revoke':
        revoke_access(args)
    elif command == 'show':
        show_access(args)

    sys.exit(0)

if __name__ == '__main__':
    main()

# -*- coding: utf-8 -*-

# Copyright (c) 2013 Activision Publishing, Inc.
# Copyright (c) 2014, 2015 Miroslaw Baran <miroslaw+p+cog@makabra.org>

# the cog project is free software under 3-clause BSD licence
# see the LICENCE file in the project root for copying terms


import os
import sys
import click
import cog.directory as dir
from cog.objects.netgroup import Netgroup, make_triple
from cog.util.misc import dict_merge
from cog.config.templates import Templates
from cog.cmd import pass_context, prep_args, CogCLI

netgroups = Templates().get('netgroups')
access_levels = dict(zip(['denied', 'granted', 'admin'],
                         ['denied', 'granted', 'privileged']))


def get_access_group(name, priv_level):
    """
    Gets a netgroup handle. Creates the group when necessary.
    """
    group_type = 'security'
    group_data = dict_merge(netgroups.get(group_type), {})
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


def manage_access(args, priv_level):
    for access_object in args.get('services'):
        access_group = get_access_group(access_object.lower(), priv_level)
        for uid in args.get('uid'):
            access_group.add_triple([make_triple(None, uid, None)])
        access_group.commit_changes()


@click.group()
@pass_context
def cli(ctx):
    """access policy management"""


@cli.command(name="grant", help="grant access to users")
@click.option("-P", "--privileged", "privileged", is_flag=True,
        help="make the access privileged")
@click.option("-h", "--on-host", "services", multiple=True,
        metavar="[name]", help="host name")
@click.option("-c", "--on-cluster", "services", multiple=True,
        metavar="[name]", help="cluster name")
@click.option("-s", "--on-service", "services", multiple=True,
        metavar="[name]", help="service name")
@click.option("-t", "--to-tagged", "services", multiple=True,
        metavar="[name]", help="tag name")
@click.option("-u", "--to-user", "uid", multiple=True,
        metavar="[name]", help="user name")
@pass_context
@prep_args
def grant(ctx, **args):
    """access grants"""
    priv_level = 'admin' if args.pop('privileged', None) else 'granted'
    manage_access(args, priv_level)


@cli.command(name="deny", help="deny access to users")
@click.option("-h", "--on-host", "services", multiple=True,
        metavar="[name]", help="host name")
@click.option("-c", "--on-cluster", "services", multiple=True,
        metavar="[name]", help="cluster name")
@click.option("-s", "--on-service", "services", multiple=True,
        metavar="[name]", help="service name")
@click.option("-t", "--to-tagged", "services", multiple=True,
        metavar="[name]", help="tag name")
@click.option("-u", "--to-user", "uid", multiple=True,
        metavar="[name]", help="user name")
@pass_context
@prep_args
def deny(ctx, **args):
    """access denials"""
    priv_level = 'denied'
    manage_access(args, priv_level)


@cli.command(name="revoke", help="revoke access grant or denial")
@click.option("-l", "--revoke-level", "revoke_levels", multiple=True,
        type=click.Choice(['granted', 'denied', 'privileged']))
@click.option("-h", "--on-host", "services", multiple=True,
        metavar="[name]", help="host name")
@click.option("-c", "--on-cluster", "services", multiple=True,
        metavar="[name]", help="cluster name")
@click.option("-s", "--on-service", "services", multiple=True,
        metavar="[name]", help="service name")
@click.option("-t", "--from-tagged", "services", multiple=True,
        metavar="[name]", help="tag name")
@click.option("-u", "--from-user", "uid", multiple=True,
        metavar="[name]", help="user name")
@pass_context
@prep_args
def revoke(ctx, **args):
    """revoke access grant or denial"""
    revoke_levels = args.pop('revoke_levels', ['granted'])
    for priv_level in access_levels.keys():
        if access_levels[priv_level] in revoke_levels:
            for access_object in args.get('services'):
                access_group = get_access_group(access_object.lower(), priv_level)
                for uid in args.get('uid'):
                    access_group.del_triple(make_triple(None, uid, None))
                    access_group.commit_changes()


@cli.command(name="show", help="show access details for users or systems")
@click.argument("query", nargs=-1, metavar="[name (name...)]", required=1)
@click.option("-t", "--type", "query_type", default='user',
        type=click.Choice(['user', 'host', 'service', 'cluster', 'tag']))
@pass_context
@prep_args
def show(ctx, **args):
    """show access details"""
    tree = dir.Tree()
    if args.get('query_type') in ['host', 'cluster', 'service', 'tag']:
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

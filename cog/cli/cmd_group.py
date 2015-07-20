# -*- coding: utf-8 -*-

# Copyright (c) 2013, Activision Publishing, Inc.
# Copyright (c) 2014, 2015 Miroslaw Baran <miroslaw+p+cog@makabra.org>

# the cog project is free software under 3-clause BSD licence
# see the LICENCE file in the project root for copying terms

import os
import sys
import yaml
import click
import cog.util as util
import cog.directory as dir
#from cog.objects.group import Group
from cog.config import objects, Profiles
from cog.cmd import pass_context, prep_args, CogCLI

groups = objects.get('groups')
#settings = Profiles().current()


# dispatcher
@click.group()
@pass_context
def cli(ctx):
    """Does things."""


@cli.command(name="add", help="add a POSIX group")
@click.argument("cn", metavar="[group name]")
@click.option("-t", "--type", "groupType", metavar="[type of group]",
        default="generic", type=click.Choice(['generic', 'resource']))
@click.option("--gid-number", "gidNumber", metavar="[group id number]")
@click.option("-u", "--with-uid", "memberUid", multiple=True, metavar="[users to add]")
@click.option("--description", "description", metavar="[group description]")
@pass_context
@prep_args
def add(ctx, **args):
    """add a POSIX group"""
    group_data = util.merge(groups.get(args.pop('groupType')), args)

    if groupType in groups.keys():
        cn = group_data.get('cn')
        path = group_data.pop('path', None)
        requires = group_data.pop('requires', None)
        if not group_data.get('gidNumber') and 'gidNumber' in requires:
            group_data['gidNumber'] = dir.get_probably_unique_gidnumber()
        dn = "cn=%s,%s" % (cn, dir.get_group_base(groupType))
        group_entry = dir.Entry(dn=dn, attrs=group_data)
        newgroup = Group(cn, group_entry)
        newgroup.add()
    else:
        print "group type %s is not exactly known." % groupType
        sys.exit(1)


@cli.command(name="edit", help="edit a POSIX group")
@click.argument("cn", metavar="[group name]", required=1)
@click.option("--add-uid", "addMemberUid", multiple=True,
        metavar="[users to add]")
@click.option("--del-uid", "delMemberUid", multiple=True,
        metavar="[users to remove]")
@click.option("--gid-number", "gidNumber", metavar="[new group ID]")
@click.option("--description", "description", metavar="[group description]")
@pass_context
@prep_args
def edit(ctx, **args):
    """edit a POSIX group"""
    group = Group(args.pop('cn'))
    for attr, val in args.items():
        attr = attr.lower()
        if attr == 'description':
            group.set_description(val)
        elif attr == 'addmemberuid':
            group.add_uid(val)
        elif attr == 'delmemberuid':
            group.del_uid(val)
    group.commit_changes()


@cli.command(name="rename", help="change group name")
@click.argument("cn", metavar="[group name]", required=1)
@click.option("-n", "--new-name", "newCn", metavar="[new group name]",
        required=1)
@pass_context
@prep_args
def rename(ctx, **args):
    """change group name"""
    group = Group(args.get('cn'))
    group.rename(args.get('newCn'))


@cli.command(name="remove", help="remove group from directory")
@click.argument("cn", metavar="[group name]", required=1)
@pass_context
@prep_args
def remove(ctx, **args):
    """remove group from directory"""
    group = Group(cn)
    group.remove()


@cli.command(name="show", help="show group details")
@click.argument("cn", metavar="[group name]", required=1)
@pass_context
@prep_args
def show(ctx, **args):
    """show group details"""
    group = Group(cn)
    if group.exists:
        del(group.data['objectClass'])
        data = dict(group.data)
        print yaml.safe_dump({ cn: data }, allow_unicode=True, default_flow_style=False)


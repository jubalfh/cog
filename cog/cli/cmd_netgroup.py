# coding: utf-8

# Copyright (c) 2013, Activision Publishing, Inc.
# Copyright (c) 2014, 2015 Miroslaw Baran <miroslaw+p+cog@makabra.org>

# the cog project is free software under 3-clause BSD licence
# see the LICENCE file in the project root for copying terms


import os
import sys
import click
import cog.util as util
import cog.directory as dir
#from cog.objects.netgroup import Netgroup
#from cog.config import objects, Profiles
from cog.cmd import pass_context, prep_args, CogCLI


#netgroups = objects.get('netgroups')
#settings = Profiles().current()


@click.group()
@pass_context
def cli(ctx):
    """Does things."""


@cli.command(name="add", help="add a netgroup")
@click.argument("cn", metavar="[netgroup name]", required=1)
@click.option("-t", "--type", "nisNetgroupType", default='generic',
        metavar="[netgroup type]")
@click.option("--description", "description", metavar="[netgroup description]")
@click.option("-T", "--with-triples", "nisNetgroupTriple",
        multiple=True, metavar="[netgroup triples to add]")
@click.option("-M", "--with-members", "memberNisNetgroup",
        multiple=True, metavar="[netgroup member groups to add]")
@pass_context
@prep_args
def add(ctx, **args):
    """add a netgroup"""
    netgroup_data = util.merge(netgroups.get(args.pop('nisNetgroupType')), args)
    if netgroup_type in netgroups.keys():
        cn = netgroup_data.get('cn')
        path = netgroup_data.pop('path', None)
        requires = netgroup_data.pop('requires', None)
        dn = "cn=%s,%s" % (cn, dir.get_netgroup_base(netgroup_type))
        netgroup_entry = dir.Entry(dn=dn, attrs=netgroup_data)
        newnetgroup = Netgroup(cn, netgroup_entry)
        newnetgroup.add()
    else:
        print "Netgroup type %s is not exactly known." % netgroup_type
        sys.exit(1)


@cli.command(name="edit", help="edit a netgroup")
@click.argument("cn", metavar="[group name]", required=1)
@click.option("--add-triple", "addNisNetgroupTriple", multiple=True,
        metavar="[triples to add]")
@click.option("--del-triple", "delNisNetgroupTriple", multiple=True,
        metavar="[triples to remove]")
@click.option("--add-member", "addmemberNisNetgroup", multiple=True,
        metavar="[netgroup members to add]")
@click.option("--del-member", "delmemberNisNetgroup", multiple=True,
        metavar="[netgroup members to remove]")
@click.option("--description", "description", metavar="[netgroup description]")
@pass_context
@prep_args
def edit(ctx, **args):
    """edit a netgroup"""
    netgroup = Netgroup(args.pop('cn'))
    for attr, val in args.items():
        attr = attr.lower()
        if attr == 'description':
            netgroup.set_description(val)
        elif attr == 'addnisnetgrouptriple':
            netgroup.add_triple(val)
        elif attr == 'delnisnetgrouptriple':
            netgroup.del_triple(val)
        elif attr == 'addmembernisnetgroup':
            netgroup.add_member(val)
        elif attr == 'delmembernisnetgroup':
            netgroup.del_member(val)
    netgroup.commit_changes()


@cli.command(name="rename", help="change a netgroup name")
@click.argument("cn", metavar="[netgroup name]", required=1)
@click.option("-n", "--new-name", "newCn", metavar="[new netgroup name]",
        required=1)
@pass_context
@prep_args
def rename(ctx, **args):
    """change netgroup name"""
    netgroup = Netgroup(args.get('cn'))
    netgroup.rename(args.get('newCn'))


@cli.command(name="remove", help="remove a netgroup")
@click.argument("cn", metavar="[netgroup name]", required=1)
@pass_context
@prep_args
def remove(ctx, **args):
    """remove a netgroup"""
    netgroup = Netgroup(cn)
    netgroup.remove()


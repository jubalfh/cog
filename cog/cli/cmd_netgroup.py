# coding: utf-8

# Copyright (c) 2013, Activision Publishing, Inc.
# Copyright (c) 2014, 2015 Miroslaw Baran <miroslaw+p+cog@makabra.org>

# the cog project is free software under 3-clause BSD licence
# see the LICENCE file in the project root for copying terms


import os
import sys
import click
import yaml
import cog.directory as dir
from cog.objects.netgroup import Netgroup
from cog.config.templates import Templates
from cog.util.misc import dict_merge
from cog.cmd import pass_context, prep_args, CogCLI


netgroups = Templates().get('netgroups')


@click.group()
@pass_context
def cli(ctx):
    """netgroup management"""


@cli.command(name="add", help="add a netgroup")
@click.argument("cn", metavar="[netgroup name]", required=1)
@click.option("-t", "--type", "nisNetgroupType", default='generic',
        type=click.Choice(netgroups.keys()))
@click.option("--description", "description", metavar="[netgroup description]")
@click.option("-T", "--with-triples", "nisNetgroupTriple",
        multiple=True, metavar="[netgroup triples to add]")
@click.option("-M", "--with-members", "memberNisNetgroup",
        multiple=True, metavar="[netgroup member groups to add]")
@pass_context
@prep_args
def add(ctx, **args):
    """add a netgroup"""
    type = args.pop('nisNetgroupType')
    data = dict_merge(netgroups.get(type), args)
    path = data.pop('path', None)
    cn = data.get('cn')
    path = data.pop('path', None)
    requires = data.pop('requires', None)
    dn = "cn=%s,%s" % (cn, dir.get_netgroup_base(type))
    print dn
    netgroup_entry = dir.Entry(dn=dn, attrs=data)
    newnetgroup = Netgroup(cn, netgroup_entry)
    newnetgroup.add()


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
def rename(ctx, cn, newCn):
    """change netgroup name"""
    netgroup = Netgroup(cn)
    if netgroup.exists:
        netgroup.rename(args.get('newCn'))
    else:
        click.echo("Group %s does not exist." % cn)
        sys.exit(1)


@cli.command(name="remove", help="remove a netgroup")
@click.argument("cn", metavar="[netgroup name]", required=1)
@pass_context
@prep_args
def remove(ctx, **args):
    """remove a netgroup"""
    netgroup = Netgroup(cn)
    if netgroup.exists:
        netgroup.remove()


@cli.command(name="show", help="show netgroup details")
@click.argument("cn", metavar="[netgroup name]", required=1)
@pass_context
@prep_args
def show(ctx, cn):
    """show netgroup details"""
    netgroup = Netgroup(cn)
    if netgroup.exists:
        del(netgroup.data['objectClass'])
        data = dict(netgroup.data)
        print yaml.safe_dump({ cn: data }, allow_unicode=True, default_flow_style=False)


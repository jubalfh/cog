# -*- coding: utf-8 -*-

# Copyright (c) 2013, Activision Publishing, Inc.
# Copyright (c) 2014, 2015 Miroslaw Baran, <miroslaw+p+cog@makabra.org>

# the cog project is free software under 3-clause BSD licence
# see the LICENCE file in the project root for copying terms

import sys
import yaml
import click
import cog.directory as dir
import cog.util.passwd as passwd
from cog.config.settings import Profiles
from cog.config.templates import Templates
from cog.cmd import CogCLI, prep_args, pass_context
from cog.util.io import read_ssh_keys
from cog.util.misc import get_current_uid, loop_on, dict_merge, flatten
from cog.objects.user import User
from cog.objects.group import Group

accounts = Templates().get('accounts')
groups = Templates().get('groups')

settings = Profiles()
user_rdn = settings.user_rdn

# main context
@click.group()
@pass_context
def cli(ctx):
    """user management"""


# add new user
@cli.command(name="add", help="add new user to the directory")
# argument(s)
@click.argument("uid", metavar="[user name]", required=1)
# uid and group memberships
@click.option("-t", "--type", "accountType",
        type=click.Choice(accounts.keys()), default="generic",
        help="account type")
@click.option("-u", "--uid-number", "uidNumber",
        metavar="[uid]", help="user id (numerical)")
@click.option("-g", "--gid-number", "gidNumber",
        metavar="[gid]", help="primary group id")
@click.option("-G", "--add-group", "group", multiple=True,
        metavar="[group name]", help="user's secondary group")
@click.option("-U", "--add-usergroup", "userGroup", is_flag=True,
        help="create dedicated user group")
# account & password details
@click.option("-d", "--home", "homeDirectory",
        metavar="[path]", help="path to home directory")
@click.option("-s", "--shell", "loginShell",
        metavar="[path]", help="path to user's shell")
@click.option("-c", "--gecos", "gecos",
        metavar="[freeform text]", help="the GECOS field")
# personal information
@click.option("-F", "--full-name", "cn",
        metavar="[text]", help="user's full name")
@click.option("--first-name", "givenName",
        metavar="[text]", help="user's first name")
@click.option("--last-name", "sn", required=1,
        metavar="[text]", help="user's last name")
@click.option("-m", "--email", "mail", multiple=True,
        metavar="[e-mail]", help="user's e-mail address")
@click.option("-P", "--phone-no", "telephoneNumber", multiple=True,
        metavar="[phone no.]", help="user's phone number")
@click.option("-o", "--organization", "o",
        metavar="[freeform text]", help="user's organization")
# public ssh key
@click.option("-k", "--ssh-public-key", "sshPublicKey", multiple=True)
@pass_context
@prep_args
def add(ctx, **args):
    """Adds new user to the directory."""
    account_type = args.pop('accountType')
    user_group = args.pop('userGroup', settings.usergroups)
    user_data = dict_merge(accounts.get(account_type), args)
    name = user_data.pop('uid')
    user_data[user_rdn] = name
    path = user_data.pop('path', None)
    secondary_groups = user_data.pop('group', None)
    requires = user_data.pop('requires', None)
    dn = "%s=%s,%s" % (user_rdn, name, dir.get_account_base(account_type))
    operator_uid = get_current_uid()
    for nameattr in ['cn', 'sn', 'givenName']:
        if not user_data.get(nameattr) and nameattr in requires:
            user_data[nameattr] = '%s (ask %s to fix me)' % (name, operator_uid)
    if 'uidNumber' not in user_data and 'uidNumber' in requires:
        user_data['uidNumber'] = dir.get_probably_unique_uidnumber()
    if 'homeDirectory' not in user_data and 'homeDirectory' in requires:
        user_data['homeDirectory'] = "/home/%s" % user_data['uid']
    user_data['userPassword'] = passwd.make_sha512(passwd.random_string())
    if 'sshpublickey' in user_data:
        ssh_key = read_ssh_keys(user_data.pop('sshpublickey'))
        user_data['sshPublicKey'] = ssh_key
        user_data['objectClass'].append('ldapPublicKey')
    if user_group:
        group_type = account_type if account_type in groups else 'generic'
        group_dn = "cn=%s,%s" % (name, dir.get_group_base(group_type))
        group_id = dir.get_probably_unique_gidnumber()
        group_data = {
            'cn': name,
            'description': 'Personal group for %s.' % name,
            'gidNumber': group_id}
        group_entry = dir.Entry(dn=group_dn, attrs=group_data)
        user_data['gidNumber'] = group_id
        try:
            newgroup = Group(name, group_entry)
            newgroup.add()
        except:
            print "There was a problem with creating user group %s." % name
    user_entry = dir.Entry(dn=dn, attrs=user_data)
    newuser = User(name, user_entry, groups=secondary_groups)
    newuser.add()


# modify user object
@cli.command(name="edit", help="edit and modify user data")
# argument(s)
@click.argument("uid", metavar="[user name]", required=1)
# uid and group management
@click.option("-u", "--uid-number", "uidNumber", metavar="[uid]",
        help="change user id [numerical]")
@click.option("-g", "--group-id", "gidNumber", metavar="[gid]",
        help="change primary group id")
@click.option("-G", "--add-group", "addgroup", multiple=True,
        metavar="[group name]", help="[add user to the group]")
@click.option("-D", "--del-group", "delgroup", multiple=True,
        metavar="[group name]", help="[remove user from the group]")
# account & password management
@click.option("-r", "--reset-password", "resetPassword", is_flag=True,
        help="reset user's password]")
@click.option("-d", "--home", "homeDirectory",
        metavar="[path]", help="new home directory path")
@click.option("-s", "--shell", "loginShell",
        metavar="[path]", help="shell interpreter path")
@click.option("-c", "--gecos", "gecos",
        metavar="[freeform text]", help="the GECOS field")
# personal information management
@click.option("-F", "--full-name", "cn", help="[new full name]")
@click.option("--first-name", "givenName", 
        metavar="[freeform text]", help="new first name")
@click.option("--last-name", "sn",
        metavar="[freeform text]", help="new last name")
@click.option("-m", "--add-email", "addMail", multiple=True,
        metavar="[e-mail address]", help="add new e-mail address")
@click.option("-M", "--del-email", "delMail", multiple=True,
        metavar="[e-mail address]", help="remove e-mail address")
@click.option("-p", "--add-phone-no", "addTelephoneNumber",
        multiple=True, metavar="[phone no.]", help="new phone number to add")
@click.option("-P", "--del-phone-no", "delTelephoneNumber",
        multiple=True, metavar="[phone no.]", help="phone number to remove")
@click.option("-o", "--organization", "o", metavar="[freeform text]",
        help="user's organization")
# ssh key management
@click.option("-k", "--add-ssh-public-key", "addSshPublicKey",
        multiple=True, metavar="[path]", help="add specified ssh key")
@click.option("-K", "--del-ssh-public-key", "delSshPublicKey",
        multiple=True, metavar="[ssh key or fingerprint]",
        help="remove user's ssh key")
@pass_context
@prep_args
def edit(ctx, **args):
    replacable_attrs = ['uidnumber', 'gidnumber', 'sn', 'cn', 'givenname',
                        'homedirectory', 'loginshell', 'o', 'gecos']
    appendable_attrs = ['addmail', 'addtelephonenumber']
    removable_attrs = ['delmail', 'deltelephonenumber']

    user = User(args.pop('uid'), bind=True)

    if args.get('resetPassword'):
        del args['resetPassword']
        user.set_password(password=None)

    for attr, val in args.items():
        attr = attr.lower()
        if attr in replacable_attrs:
            user.replace_item(attr, val)
        if attr in appendable_attrs:
            user.append_to_item(attr[3:], val)
        if attr in removable_attrs:
            user.remove_from_item(attr[3:], val)
        if attr == 'delgroup':
            for group in val:
                user.delgroup(group)
        if attr == 'addgroup':
            for group in val:
                user.addgroup(group)
        if attr == 'delsshpublickey':
            for path in loop_on(val):
                ssh_keys = read_ssh_keys(path)
                if ssh_keys:
                    user.remove_from_item(attr[3:], ssh_keys)
        if attr == 'addsshpublickey':
            for path in loop_on(val):
                ssh_keys = read_ssh_keys(path)
                if ssh_keys:
                    user.append_to_item(attr[3:], ssh_keys)
                    user.append_to_item('objectClass', 'ldapPublicKey')

    user.commit_changes()


# rename user
@cli.command(name="rename", help="change user's uid")
@click.argument("uid", metavar="[uid]", required=1)
@click.option("-n", "--new-name", "newUid",
        metavar="[uid]", help="new user's name")
@pass_context
@prep_args
def rename(ctx, **args):
    user = User(args.get('uid'), bind=True)
    user.rename(args.get('newUid'))


# retire user (or users)
@cli.command(name="retire", help="retire user (with extreme prejudice)")
@click.argument("uid", nargs=-1, metavar="[user name]", required=1)
@pass_context
@prep_args
def retire(ctx, **args):
    """Move the user(s) to the limbo."""
    for name in args.get('uid'):
        user = User(name, bind=True)
        user.retire()


# remove user (or more)
@cli.command(name="remove", help="remove user from directory")
@click.argument("uid", nargs=-1, metavar="[name]", required=1)
@click.option("-v", "--verbose", "verbose", is_flag=True)
@pass_context
@prep_args
def remove(ctx, **args):
    """Actually remove the user(s)."""
    for name in args.get('uid'):
        user = User(name, bind=True)
        user.remove()


# show user information
@cli.command(name="show", help="display user information")
@click.argument("uid", nargs=-1, metavar="[user name]", required=1)
@click.option("-v", "--verbose", "verbose", is_flag=True)
@pass_context
@prep_args
def show(ctx, **args):
    names = args.get('uid')
    tree = dir.Tree()
    query = '(&(objectClass=*)(%s=%s))'
    attrs = ['uid', 'cn', 'gecos', 'mail', 'telephoneNumber', 'title',
            'o', 'uidNumber', 'gidNumber']
    if args.get('verbose'):
        attrs += ['objectClass', 'memberOf', 'loginShell', 'homeDirectory',
                  'modifiersName', 'modifyTimestamp', 'sshPublicKey']
    for name in names:
        search = tree.search(search_filter=(query % (user_rdn, name)), attributes=attrs)
        user = User(name)
        for item in search:
            groups = {'groups': sorted(flatten([group for group in user.find_groups()]))}
            account = {name: dict_merge(dict(item), groups)}
            print yaml.safe_dump(account, allow_unicode=True, default_flow_style=False)


# list user templates
@cli.command(name="type", help="user template helper")
@click.option("-l", "--list", "list_types", is_flag=True,
        help="list user types")
@pass_context
@prep_args
def list_type(ctx, **args):
    if args.get('list_types'):
        print "Available account types:"
        for role in accounts.values():
            print "  %s – %s" % (role.name, role.desc)

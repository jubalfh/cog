# -*- coding: utf-8 -*-

# Copyright (c) 2013 Activision Publishing, Inc.
# Copyright (c) 2014, 2015 Miroslaw Baran <miroslaw+p+cog@makabra.org>

# the cog project is free software under 3-clause BSD licence
# see the LICENCE file in the project root for copying terms


import os
import sys
import click
from pprint import pprint
from cog.util.misc import loop_on, to_utf8
from cog.config.settings import Profiles


CONTEXT = dict(auto_envvar_prefix='COG_')
cmd_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cli')
settings = Profiles()


def prep_args(f):
    """Massages data returned by click for further consumption"""
    def _cleanup(d):
        for k, v in d.items():
            if not v:
                del(d[k])
            elif isinstance(v, dict):
                d[k] = _cleanup(v)
            elif isinstance(v, tuple) or isinstance(v, list):
                d[k] = list(to_utf8(e) for e in v)
            else:
                d[k] = to_utf8(v)
        return d

    def _prep_args(*ctx, **args):
        args = _cleanup(args)
        return(f(*ctx, **args))
    return _prep_args


class Context(object):

    def log(self, msg, *args):
        """Logs a message to stderr."""
        if args:
            msg %= args
        click.echo(msg, file=sys.stderr)

    def vlog(self, msg, *args):
        """Logs a message to stderr only if verbose is enabled."""
        if self.verbose:
            self.log(msg, *args)


pass_context = click.make_pass_decorator(Context, ensure=True)


class CogCLI(click.MultiCommand):

    def list_commands(self, ctx):
        commands = []
        for filename in os.listdir(cmd_folder):
            if filename.endswith('.py') and filename.startswith('cmd_'):
                commands.append(filename[4:-3])
        commands.sort()
        return commands

    def get_command(self, ctx, name):
        try:
            mod = __import__('cog.cli.cmd_%s' % name, None, None, ['cli'])
        except ImportError as exc:
            print exc
            return
        return mod.cli


@click.command(cls=CogCLI, context_settings=CONTEXT)
@click.option('-p', '--profile', 'profile', type=click.Choice(settings.list()),
              help="connection profile")
@pass_context
def cli(ctx, profile):
    """cog, a flexible manager for modestly-sized LDAP directories"""
    if profile:
        settings.use(profile)


if __name__ == '__main__':
    cli()

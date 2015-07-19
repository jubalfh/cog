# -*- coding: utf-8 -*-

# Copyright (c) 2013 Activision Publishing, Inc.
# Copyright (c) 2014, 2015 Miroslaw Baran <miroslaw+p+cog@makabra.org>

# the cog project is free software under 3-clause BSD licence
# see the LICENCE file in the project root for copying terms

import os
import sys
import click
#from cog.config import Profiles, make_user_config


CONTEXT = dict()
cmd_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cli')


def prep_args(f):
    """Cleans up values returned by click."""
    def _cleanup(d):
        for k, v in d.items():
            if not v:
                del(d[k])
            elif isinstance(v, dict):
                d[k] = dict_clean(v)
            elif isinstance(v, tuple):
                d[k] = list(v)
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
        commands.sort
        return commands

    def get_command(self, ctx, name):
        try:
            mod = __import__('cog.cli.cmd_%s' % name, None, None, ['cli'])
        except ImportError as exc:
            print exc
            return
        return mod.cli


@click.command(cls=CogCLI, context_settings=CONTEXT)
@pass_context
def cli(ctx):
    """cog, a flexible directory manager"""

if __name__ == '__main__':
    cli()

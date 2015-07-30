# -*- coding: utf-8 -*-

# Copyright (c) 2013, Activision Publishing, Inc.
# Copyright (c) 2014, 2015 Miroslaw Baran <miroslaw+p+cog@makabra.org>

# the cog project is free software under 3-clause BSD licence
# see the LICENCE file in the project root for copying terms

# simplistic yaml-based templates (for LDAP objects)

import os
import sys
from os.path import join as pathjoin
from pprint import pprint
from cog.util.io import list_files, merge_data
from cog.util.misc import dict_merge, Singleton
from cog.config.settings import Profiles

cfg = Profiles()


class Template(dict):
    def __init__(self, name, desc, limits, attrs):
        self.name = name
        self.desc = desc
        self.limits = limits
        self.update(attrs)


class Templates(dict):

    def __init__(self):
        tmpl_files = []
        for dir in cfg.cfg_dirs:
            tmpl_files.append(pathjoin(dir, 'templates.yaml'))
            tmpl_files += list_files(pathjoin(dir, 'templates.d'))
        self.update(self.expand_inheritances(merge_data(*tmpl_files)))

    @staticmethod
    def expand_inheritances(templates):
        """Expand inheritances in object templates."""
        # FIXME: v. naive approach, enforces default inheritance if loop
        # detected, should we perhaps scream and throw an exception
        # instead?
        expanded = dict()
        for type, data in templates.items():
            expanded.update({type: {}})
            for name, template in data.items():
                desc = template.get(
                    'desc', '{} template for {} object'.format(name, type))
                attrs = template.get('default')
                parents = ['generic']
                parent = template.get('inherits', None)
                while True:
                    if parent and parent not in parents:
                        parents.append(parent)
                        parent = data.get(parent).get('inherits', None)
                    else:
                        break
                for parent in reversed(parents):
                    parent_attrs = data.get(parent).get('default')
                    attrs = dict_merge(parent_attrs, attrs)
                limits = attrs.pop('limits', None)
                expanded[type].update({name: Template(name, desc, limits, attrs)})
        return expanded

    def types(self):
        """Return available object types."""
        return sorted(self.keys())

    def list(self, type):
        """List available object types."""
        return sorted(self.get(type).keys()) or None

    def desc(self, type, name):
        return self.get(type).get(name).desc


if __name__ == "__main__":
    tmpl = Templates()
    for t in tmpl.types(): print t, tmpl.list(t)
    for type, templates in tmpl.items():
        print "Object type: {}".format(type)
        for name, template in templates.items():
            print "  {:<10}: {:<30}".format(name, template.desc)

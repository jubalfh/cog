# -*- coding: utf-8 -*-

# Copyright (c) 2013, Activision Publishing, Inc.
# Copyright (c) 2014, 2015 Miroslaw Baran <miroslaw+p+cog@makabra.org>

# the cog project is free software under 3-clause BSD licence
# see the LICENCE file in the project root for copying terms

# process configuration files

import os
import sys
import re
import yaml

from cog.util.misc import dict_merge, loop_on

def list_files(path, ext='.yaml'):
    """Given a directory, list all files with specified extension."""
    try:
        for entry in os.listdir(path):
            file_path = os.path.join(path, entry)
            if os.path.isfile(file_path) and file_path.endswith(ext):
                yield file_path
    except OSError:
        pass


def read_yaml(filename):
    """Read yaml file into a dictionary."""
    data = dict()
    try:
        with open(filename) as fh:
            data = yaml.safe_load(fh)
    except (IOError, yaml.YAMLError), e:
        print e
    return data


def merge_data(*files):
    """Merge data from multiple YAML files."""
    data = dict()
    for file in files:
        if os.path.isfile(file):
            data = dict_merge(data, read_yaml(file))
    return data


def read_ssh_keys(path):
    """Given a path, do read SSH key(s) from a file.

       Handles the typical format of authorized_keys file, including
       the options at the beginning of the line and the free-form
       comment at the end of it. """
    
    ssh_key = re.compile(
        r'^(?P<options>.*[ \t]+)?(?P<data>ssh-(?:dss|rsa|ecdsa|ed25519) (?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=|[A-Za-z0-9+/]{4}).*)$')
    keys = set()
    try:
        if os.path.isfile(path) and os.stat(path).st_size != 0:
            with open(path) as key_fh:
                for line in key_fh:
                    if line.strip().startswith('#') or line.strip() == '\n':
                        continue
                    m = ssh_key.match(line)
                    try:
                        options, data = m.group('options'), m.group('data')
                        kh = SSHKey(data)
                        key = kh.keydata.strip()
                        if options:
                            key = options + key
                        keys.add(key)
                    except Exception as exc:
                        print exc.message
    except (OSError, IOError) as exc:
        print exc.message
    return list(keys)

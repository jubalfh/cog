# -*- coding: utf-8 -*-

# Copyright (c) 2013, Activision Publishing, Inc.
# Copyright (c) 2014, 2015 Miroslaw Baran <miroslaw+p+cog@makabra.org>

# the cog project is free software under 3-clause BSD licence
# see the LICENCE file in the project root for copying terms

# miscellaneous utility functions, some of them borrowed


import os
import sys
import pwd
import string
from itertools import chain


# encoding conversion functions
def to_utf8(obj):
    """
    Convert non-utf-8 bytestream or a unicode string to a utf-8 bytestream.
    """
    local_encoding = sys.stdin.encoding
    if isinstance(obj, unicode):
        obj = obj.encode('utf-8')
    elif isinstance(obj, basestring) and local_encoding != 'utf-8':
        obj = obj.decode(local_encoding).encode('utf-8')
    return obj


def to_unicode(obj, encoding='utf-8'):
    """
    Convert bytestream to unicode.
    """
    if isinstance(obj, basestring):
        if not isinstance(obj, unicode):
            obj = unicode(obj, encoding)
    return obj


def get_current_uid():
    """
    Return the owner of the cog process.
    """
    return pwd.getpwuid(os.getuid()).pw_name


# data structure helpers
def loop_on(input):
    if isinstance(input, basestring):
        yield input
    else:
        try:
            for item in input:
                yield item
        except TypeError:
            yield input


def flatten(list_of_lists):
    """
    Flatten one level of nesting
    """
    return chain.from_iterable(list_of_lists)


def dict_merge(d1, d2):
    """
    Merge two dictionaries recursively. Merge the lists embedded within
    dictionary at the same positions too (with caveats).
    """
    for k1, v1 in d1.items():
        if k1 not in d2:
            d2[k1] = v1
        elif isinstance(v1, list):
            d2[k1] = list(set(d2[k1] + v1))
        elif isinstance(v1, dict):
            dict_merge(v1, d2[k1])
    return d2


def apply_to(d, f):
    """
    Apply a function to dictionary-like object values, recursively.
    """
    for k in d:
        if isinstance(d[k], dict):
            d[k] = apply_to(d.get(k), f)
        else:
            d[k] = f(d[k])
    return d


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

# -*- coding: utf-8 -*-

# Copyright (c) 2013, Activision Publishing, Inc.
# Copyright (c) 2014, 2015 Miroslaw Baran <miroslaw+p+cog@makabra.org>

# the cog project is free software under 3-clause BSD licence
# see the LICENCE file in the project root for copying terms

# miscellaneous utility functions, some of them borrowed

import os
import pwd
import string
import random
import keyring
import getpass
import sshpubkeys
from sshpubkeys import SSHKey
from itertools import chain
from functools import wraps
from passlib.hash import sha512_crypt


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


# password & system helpers
def randomized_string(size=16, chars=string.letters + string.digits + string.punctuation):
    """
    Generate randomized string using printable character. (Not using
    string.printable here because it does produce more than we can eat,
    unfortunately.)
    """
    return ''.join(random.choice(chars) for x in range(size))


def make_pass(passwd=None):
    """
    Generate password using SHA-512 method, randomized salt and randomized
    number of rounds.
    """
    if passwd is None:
        passwd = randomized_string(17)
    salt = randomized_string(16, ('./' + string.letters + string.digits))
    iterations = random.randint(40000, 80000)
    return '{CRYPT}' + sha512_crypt.encrypt(passwd, salt=salt, rounds=iterations)


def get_pass(username, service, prompt, use_keyring=False):
    """
    get a password string, either from user input or from system key/password
    store
    """
    password = None
    if use_keyring:
        password = keyring.get_password(service, username)
        if not password:
            password = getpass.getpass(prompt)
            if password:
                keyring.set_password(service, username, password)
    else:
        password = getpass.getpass(prompt)
    return password


def read_ssh_key(path):
    """
    Read an SSH key given path, bail out when bad. Limit the keyfile length.
    """
    key = None
    try:
        with open(path) as key_fh:
            key = SSHKey(key_fh.read(262144)).keydata.strip()
    except IOError as io_exc:
        print io_exc.message
    except sshpubkeys.InvalidKeyException as key_exc:
        print key_exc.message
    return key


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


def merge(d1, d2):
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
            merge(v1, d2[k1])
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

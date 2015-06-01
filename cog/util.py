# -*- coding: utf-8 -*-

# Copyright (c) 2013, Activision Publishing, Inc.

# the cog project is free software under 3-clause BSD licence
# see the LICENCE file in the project root for copying terms

# miscellaneous utility functions, mostly borrowed

import os
import pwd
import string
import random
import keyring
import getpass

from itertools import chain
from passlib.hash import sha512_crypt


def randomized_string(size=16, chars=string.letters + string.digits + string.punctuation):
    """
    Generate randomized string using printable character. (Not using
    string.printable here because it does produce more than we can eat,
    unfortunately.)
    """
    return ''.join(random.choice(chars) for x in range(size))


def make_pass(passwd=None):
    """
    generate password using SHA-512 method, randomized salt and randomized
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


def get_current_uid():
    return pwd.getpwuid(os.getuid()).pw_name


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
    for k1, v1 in d1.iteritems():
        if k1 not in d2:
            d2[k1] = v1
        elif isinstance(v1, list):
            d2[k1] = list(set(d2[k1] + v1))
        elif isinstance(v1, dict):
            merge(v1, d2[k1])
    return d2


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

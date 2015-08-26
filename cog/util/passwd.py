# -*- coding: utf-8 -*-

# Copyright (c) 2013, Activision Publishing, Inc.
# Copyright (c) 2014, 2015 Miroslaw Baran <miroslaw+p+cog@makabra.org>

# the cog project is free software under 3-clause BSD licence
# see the LICENCE file in the project root for copying terms

# password utility functions

import string
import random
import keyring
import getpass
from passlib.hash import sha512_crypt


rnd = random.SystemRandom()


# password & system helpers
def random_string(size=32, chars=string.letters + string.digits + string.punctuation):
    """
    Generate randomized string using reasonably wide set of ASCII characters.
    """
    return ''.join(rnd.choice(chars) for x in range(size))


def make_sha512(passwd=None):
    """
    Generate password using SHA-512 method, randomized salt and randomized
    number of rounds.
    """
    if passwd is None:
        passwd = random_string(17)
    salt = random_string(16, ('./' + string.letters + string.digits))
    iterations = rnd.randint(40000, 80000)
    return '{CRYPT}' + sha512_crypt.encrypt(passwd, salt=salt, rounds=iterations)


def get_passwd(username, service, prompt, use_keyring=False):
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

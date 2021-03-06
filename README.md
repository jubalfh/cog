cog
===

a flexible LDAP management tool

# Setup #

From the root of the source tree run:

    python setup.py install

or

    sudo python setup.py install

The tool should now work properly when installed in virtualenv.

# Usage #

    cog --help
    cog [-p|--profile profile ] user --help
    cog [-p|--profile profile ] group --help
    cog [-p|--profile profile ] netgroup --help
    cog [-p|--profile profile ] access --help

The tool copies its configuration files into ~/.cog on first run; the
system-wide configuration is in /etc/cog, the settings are merged when
the tool is being run. This version of cog supports storing user
credentials in your system's wallet/keyring/keychain: add `use_keyring:
true` to your settings file in order to enable it.

To start using the tool please either create a new profile similar to
the default (“local”) and set up is as default or simply edit the local
profile in the global settings file to your tastes.

List of available account types (roles) is available through

    cog user type -l

# Development #

Cog is a work in progress and still in an early stage of development
– feel free to request features and send patches. See the TODO.md file
for the list of the improvements that will be implemented first.

I'm trying to use the git-flow (in the avh flavour), see that you
either have the git-flow package installed or check out the
[gitflow-avh](https://github.com/petervanderdoes/gitflow) sources and
install the extension manually.

After cloning the repository for the first time, please run `sh flow-init`
– it will initialise git flow with the values I'm using.

# OS-specific notes #

* Python-ldap does not agree with libldap shipped with OS X Yosemite,
  using non-system build of openldap libraries for python-ldap is
  probably the best solution. If you're using Homebrew, please install
  openldap (from the homebrew/dupes tap), and change python-ldap's
  setup.cfg to include /usr/local/opt/openldap/{lib,include} before any
  other paths listed (you need to install python-ldap manually for that
  until the paths get fixed upstream).

# Known Bugs and Limitations #

* cog requires locale settings that use UTF-8,
* error handling is abysmal, exceptions are thrown everywhere,
* existing tests are broken,

# Testing #

To test you must also install the following dependencies:

* python-nose
* python-mock

To run all tests, run the following in the root directory:

    nosetests

# Dependencies #

To install cog you need:

* pbr
* passlib
* python-setuptools
* python-ldap
* PyYAML
* keyring
* sshpubkeys

cog object templates
====================

# Preface

The object templates are used to translate user-facing abstractions
(“users”, “groups”, “netgroups”, “access definitions”) to underlying
LDAP directory and object structure.

The concept is simple: a template is a YAML dictionary which is used as
a base for merge with user-supplied data.

The format is this:

```yaml
object_type:
  object_name:
    desc: Freeform object description
    default:
      inherits: parent_object_name
      path: path/to/object
      limits:
        minuidnumber: lower limit for user id
        maxuidnumber: upper limit for user id
        mingidnumber: lower limit for group id
        maxgidnumber: upper limit for group id
      objectClass:
      - list
      - of
      - object classess
      requires:
      - list
      - of
      - required
      - attributes
      attribute_one: value
      attribute_two: some other value
      attribute_three: yet another value
```

# Object types

There are three valid object types so far: _account_, _group_ and
_netgroup_.

# Description

Description is a free-form text that's supposed to be presented to user
when they list the available object types.

# The `default` section

The actual template is contained within the `default` section.

## Inherits

When the optional section `inherits:` is used, the templates are merged
in the order of inheritance, with most-specific values always
overriding base templates.

## Path

The path defines location of the object in the LDAP tree and it's
unconditionally translated to a series of OUs which are then
concatenated with the base DN defined for the object type.

For example, for a user template in a directory, where user objects are
located in `ou=accounts,dc=bar` a path of `services/moo/foo` will
render `ou=foo,ou=moo,ou=services,ou=accounts,dc=bar`.

Each object type has its base DN defined in cog's configuration file.

## Limits

Limits allow for definition of UID/GID boundaries. Not enforced now.

## ObjectClass

The objectClass section is a list of object classess that will be
pulled in when creating an LDAP object. 

## Requires

As the name suggests, this section contains a list of LDAP attributes
that are required to be present in an object. The handling is done
semi-manually by the CLI subcommands, in the future I hope to augment
this list using the directory schema definitions.

## Attributes

The (unnamed) attributes section is a list of key-value pairs, where
the keys are attribute names and values are the default attribute
values. User-provided values always override the defaults.

# Examples

## an administrative account for a directory

```yaml
accounts:
  ldap-admin:
    desc: LDAP administrative account template
    default:
      path: admin
      objectClass:
      - top
      - inetOrgPerson
      requires:
      - cn
      - sn
```

## a default posix group

```yaml
groups:
  generic:
    desc: generic system groups
    default:
      path: system groups
      limits:
        gidMin: '5000001'
        gidMax: '6000000'
      requires:
      - cn
      - gidNumber
      objectClass:
      - top
      - posixGroup
```

## a very typical user account

```yaml
accounts:
  generic:
    desc: generic user account
    default:
      path: /
      limits:
        uidMin: 42000000
        uidMax: 50000000
        gidMin: 42000000
        gidMax: 50000000
      objectClass:
      - top
      - inetOrgPerson
      - posixAccount
      - shadowAccount
      requires:
      - cn
      - givenName
      - sn
      - uidNumber
      - userPassword
      - homeDirectory
      - uid
      gidNumber: '100'
      loginShell: /bin/bash
```

## netgroup definition (with inheritance)

```yaml
netgroups:
  generic:
    desc: netgroup
    default:
      path: /
      requires:
      - cn
      objectClass:
      - top
      - nisNetgroup

  security:
    desc: host access policies
    inherits: generic
    default:
      path: host access
```

Changelog
=========

# release 2.1 #

* Mostly bugfix release.

* user-visible changes:
  *  support for creating per-user groups at account creation time,
     (`cog user add -U/--add-user-group` will create one and there is
     new global config option: `usergroups`),
  *  added short options for `cog user edit`,
  *  remove a no-op `--password` option from `cog user add` (use `cog
     user edit -r` to reset it afterwards),

* a bunch of brown paper bag errors eradicated

# release 2.0 #

* user-visible changes:
  *  better command line handling
  *  full support for running in a virtualenv
  *  support for transparent store of passwords in system keyrings
     (through python-keyring)

* command line options are now being handled by the excellent click
  framework instead of half-arsed hack,

* config, template and util functions have been split, cleaned up,
  partly rewritten and made more resilient (the config/settings
  specifically)

* remove user_config option (user config is now mandatory).

# release 1.3 #

* cog now helps managing SSH public keys if your directory supports the
  openssh-lpk schema:

* `cog netgroup` has been updated to actually work, and does support
  the memberNisNetgroup attribute now,

* `cog access` has been updated to support privileged access management,

* a number of small fixes, code optimisations and style updates went
  into this release too, see commit messages.


Changelog
=========

= release 1.99x =

* command line options are now being handled by the excellent click
  framework instead of half-arsed hack,

* config, template and util functions have been split, cleaned up,
  partly rewritten and made more resilient (the config/settings
  specifically)

* user-visible changes: -h is not a shortcut for --help anymore

* first attempts at unfucking uidnumber/gidnumber tests.

* remove user_config option (user config is now mandatory).

= release 1.3 =

* cog now helps managing SSH public keys if your directory supports the
  openssh-lpk schema:

* `cog netgroup` has been updated to actually work, and does support
  the memberNisNetgroup attribute now,

* `cog access` has been updated to support privileged access management,

* a number of small fixes, code optimisations and style updates went
  into this release too, see commit messages.


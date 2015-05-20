
# -*- coding: utf-8 -*-
# generated from access.yaml

import sys
import argparse

arg_no = len(sys.argv)
tool_parser = argparse.ArgumentParser(add_help=False)
tool_subparsers = tool_parser.add_subparsers(help='commands', dest='command')


# The deny command.
deny_parser = tool_subparsers.add_parser('deny', help='deny access to user(s) at specified host(s)')
deny_parser.add_argument(
  '--on-host', '-H', action='append', dest='services', nargs='+', metavar='<host name>'
)
deny_parser.add_argument(
  '--on-service', '-s', action='append', dest='services', nargs='+', metavar='<service short name>'
)
deny_parser.add_argument(
  '--on-cluster', '-c', action='append', dest='services', nargs='+', metavar='<cluster name>'
)
deny_parser.add_argument(
  '--to-user', '-u', action='append', dest='uid', nargs='+', metavar='<user name>'
)

# The grant command.
grant_parser = tool_subparsers.add_parser('grant', help='grant access to user(s) at specified host(s)')
grant_parser.add_argument(
  '--on-host', '-H', action='append', dest='services', nargs='+', metavar='<host name>'
)
grant_parser.add_argument(
  '--on-service', '-s', action='append', dest='services', nargs='+', metavar='<service short name>'
)
grant_parser.add_argument(
  '--on-cluster', '-c', action='append', dest='services', nargs='+', metavar='<cluster name>'
)
grant_parser.add_argument(
  '--to-user', '-u', action='append', dest='uid', nargs='+', metavar='<user name>'
)
grant_parser.add_argument(
  '--privileged', '-P', dest='privileged', action='store_true', help='make the access privileged'
)

# The revoke command.
revoke_parser = tool_subparsers.add_parser('revoke', help='revoke access grant or denial')
revoke_parser.add_argument(
  '--on-host', '-H', action='append', dest='services', nargs='+', metavar='<host name>'
)
revoke_parser.add_argument(
  '--on-service', '-s', action='append', dest='services', nargs='+', metavar='<service name>'
)
revoke_parser.add_argument(
  '--revoke-type', '-t', choices=['granted', 'denied', 'privileged'], action='append', dest='revoke_levels', metavar='<access level>'
)
revoke_parser.add_argument(
  '--from-user', '-u', action='append', dest='uid', nargs='+', metavar='<user name>'
)
revoke_parser.add_argument(
  '--on-cluster', '-c', action='append', dest='services', nargs='+', metavar='<cluster name>'
)

# The show command.
show_parser = tool_subparsers.add_parser('show', help='show access details for user(s) or host(s)')
show_parser.add_argument(
  'query', nargs='+', help='<hosts, users or services>'
)
show_parser.add_argument(
  '--type', '-t', choices=['user', 'host', 'service', 'cluster'], action='store', dest='query_type'
)


import asyncio
import logging
import argparse

from houdini.houdini import Houdini
from houdini.constants import Language, ConflictResolution, ClientType

if __name__ == '__main__':
    logger = logging.getLogger('houdini')

    parser = argparse.ArgumentParser(description='Boot a Houdini server')
    parser.add_argument('type', action='store', default='login',
                        choices=['login', 'world'], help='Name of the server to boot')

    parser.add_argument('-id', action='store', default=3100, type=int, help='Houdini server ID')
    parser.add_argument('-n', '--name', action='store', help='Houdini server name')
    parser.add_argument('-a', '--address', action='store', default='0.0.0.0',
                        help='Houdini server address')
    parser.add_argument('-p', '--port', action='store', help='Houdini server port', default=None, type=int)
    parser.add_argument('-c', '--capacity', action='store', default=200,
                        help='Houdini server capacity', type=int)
    parser.add_argument('-C', '--cache-expiry', dest='cache_expiry', action='store', default=3600,
                        help='Cache expiry (seconds)', type=int)
    parser.add_argument('-P', '--plugins', action='store', default='*',
                        nargs='*', help='Plugins to load')
    parser.add_argument('-l', '--lang', action='store', default='en', help='Houdini language',
                        choices=['en', 'fr', 'pt', 'es', 'de', 'ru'])
    parser.add_argument('-tz', '--timezone', action='store', default='America/Vancouver',
                        help='Server timezone')

    login_group = parser.add_argument_group('login')
    login_group.add_argument('--login-failure-limit', action='store', default=5, help='Limit before flood limit',
                             type=int)
    login_group.add_argument('--login-failure-timer', action='store', default=3600, help='Timeout after flood limit',
                             type=int)
    login_group.add_argument('-S', '--staff', action='store_true', help='Staff-only server mode')

    logging_group = parser.add_argument_group('logging')
    logging_group.add_argument('-lg', '--logging-general', action='store',
                               dest='logging_general_path',
                               help='General log path')
    logging_group.add_argument('-le', '--logging-error', action='store',
                               dest='logging_error_path',
                               help='Error log path')
    logging_group.add_argument('-ll', '--logging-level', action='store',
                               default='INFO',
                               dest='logging_level',
                               help='Logging level')

    database_group = parser.add_argument_group('database')
    database_group.add_argument('-da', '--database-address', action='store',
                                dest='database_address',
                                default='localhost',
                                help='Postgresql database address')
    database_group.add_argument('-du', '--database-username', action='store',
                                dest='database_username',
                                default='postgres',
                                help='Postgresql database username')
    database_group.add_argument('-dp', '--database-password', action='store',
                                dest='database_password',
                                default='password',
                                help='Postgresql database password')
    database_group.add_argument('-dn', '--database-name', action='store',
                                dest='database_name',
                                default='postgres',
                                help='Postgresql database name')

    redis_group = parser.add_argument_group('redis')
    redis_group.add_argument('-ra', '--redis-address', action='store',
                             dest='redis_address',
                             default='localhost',
                             help='Redis server address')
    redis_group.add_argument('-rp', '--redis-port', action='store',
                             dest='redis_port',
                             type=int,
                             default=6379,
                             help='Redis server port')

    command_group = parser.add_argument_group('commands')
    command_group.add_argument('-cp', '--command-prefix', action='store', dest='command_prefix',
                               nargs='*',
                               default=['!', '?', '.'],
                               help='Command prefixes')
    command_group.add_argument('-csd', '--command-string-delimiters', action='store', dest='command_string_delimiters',
                               nargs='*',
                               default=['"', "'"],
                               help='Command string delimiters')
    command_group.add_argument('-ccm', '--command-conflict-mode', action='store', dest='command_conflict_mode',
                               default='silent',
                               help='Command conflict mode', choices=['silent', 'append', 'exception'])

    games_group = parser.add_argument_group('games')
    games_group.add_argument('--max-coins', action='store',
                             default=1000000, type=int, help='Max coins earnable')
    games_group.add_argument('--max-coins-per-min', action='store',
                             default=250, type=int, help='Max coins per min')

    client_group = parser.add_argument_group('client')
    client_mode = client_group.add_mutually_exclusive_group()
    client_mode.add_argument('--single-client-mode', action='store_true',
                             help='Run server with support for default client only')
    client_group.add_argument('--legacy-version', action='store',
                              type=int,
                              default=153,
                              help='Legacy client version to identify legacy clients')
    client_group.add_argument('--vanilla-version', action='store',
                              type=int,
                              default=253,
                              help='Vanilla client version to identify vanilla clients')
    client_group.add_argument('--default-version', action='store',
                              type=int,
                              default=153,
                              help='Default version to identify clients when multi-client is off')
    client_group.add_argument('--default-client', action='store',
                              choices=['legacy', 'vanilla'],
                              default='legacy',
                              help='Default client when multi-client is off')
    client_group.add_argument('-k', '--auth-key', action='store',
                              default='houdini',
                              help='Static key to use in place of the deprecated random key')
    client_group.add_argument('-kt', '--auth-ttl', action='store', type=int, default=3000,
                              help='Auth key TTL (seconds)')

    membership_group = parser.add_argument_group('membership')
    membership_group.add_argument('--expire-membership', action='store_true', help='Should membership expire?')

    args = parser.parse_args()

    args.port = args.port if args.port else 9875 if args.type == 'world' else 6112
    args.name = args.name if args.name else 'World' if args.type == 'world' else 'Login'
    args.lang = dict(en=Language.En, fr=Language.Fr, pt=Language.Pt,
                     es=Language.Es, de=Language.De, ru=Language.Ru).get(args.lang)
    args.command_conflict_mode = dict(silent=ConflictResolution.Silent, append=ConflictResolution.Append,
                                      exception=ConflictResolution.Exception).get(args.command_conflict_mode)
    args.default_client = dict(legacy=ClientType.Legacy, vanilla=ClientType.Vanilla).get(args.default_client)

    factory_instance = Houdini(args)
    try:
        asyncio.run(factory_instance.start())
    except KeyboardInterrupt:
        logger.info('Shutting down...')

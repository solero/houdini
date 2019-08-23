import asyncio
import logging
import argparse
import config

from houdini.houdini import Houdini
from houdini.constants import ConflictResolution, Language, ClientType

if __name__ == '__main__':
    logger = logging.getLogger('houdini')

    parser = argparse.ArgumentParser(description='Boot a Houdini server')
    parser.add_argument('server', action='store', default='Login',
                        help='Name of the server to boot')

    parser.add_argument('-id', action='store', help='Houdini server ID')
    parser.add_argument('-a', '--address', action='store', help='Houdini server address')
    parser.add_argument('-p', '--port', action='store', help='Houdini server port', type=int)
    parser.add_argument('-c', '--capacity', action='store', help='Houdini server capacity', type=int)
    parser.add_argument('-C', '--cache-expiry', dest='cache_expiry', action='store',
                        help='Cache expiry (seconds)', type=int)
    parser.add_argument('-P', '--plugins', action='store',
                        nargs='*', help='Plugins to load')
    parser.add_argument('-l', '--language', action='store', help='Houdini language',
                        choices=['En', 'Fr', 'Pt', 'Es', 'De', 'Ru'])

    boot_modes = parser.add_mutually_exclusive_group()
    boot_modes.add_argument('-W', '--world', action='store_true', help='Run server in world mode')
    boot_modes.add_argument('-L', '--login', action='store_true', help='Run server in login mode')

    logging_group = parser.add_argument_group('logging')
    logging_group.add_argument('-lg', '--logging-general', action='store',
                               dest='logging_general_path',
                               help='General log path')
    logging_group.add_argument('-le', '--logging-error', action='store',
                               dest='logging_error_path',
                               help='Error log path')
    logging_group.add_argument('-ll', '--logging-level', action='store',
                               dest='logging_level',
                               help='Logging level')

    database_group = parser.add_argument_group('database')
    database_group.add_argument('-da', '--database-address', action='store',
                                dest='database_address',
                                default=config.database['Address'],
                                help='Postgresql database address')
    database_group.add_argument('-du', '--database-username', action='store',
                                dest='database_username',
                                default=config.database['Username'],
                                help='Postgresql database username')
    database_group.add_argument('-dp', '--database-password', action='store',
                                dest='database_password',
                                default=config.database['Password'],
                                help='Postgresql database password')
    database_group.add_argument('-dn', '--database-name', action='store',
                                dest='database_name',
                                default=config.database['Name'],
                                help='Postgresql database name')

    redis_group = parser.add_argument_group('redis')
    redis_group.add_argument('-ra', '--redis-address', action='store',
                             dest='redis_address',
                             default=config.redis['Address'],
                             help='Redis server address')
    redis_group.add_argument('-rp', '--redis-port', action='store',
                             dest='redis_port',
                             type=int,
                             default=config.redis['Port'],
                             help='Redis server port')

    command_group = parser.add_argument_group('commands')
    command_group.add_argument('-cp', '--command-prefix', action='store', dest='command_prefix',
                               nargs='*',
                               default=config.commands['Prefix'],
                               help='Command prefixes')
    command_group.add_argument('-csd', '--command-string-delimiters', action='store', dest='command_string_delimiters',
                               nargs='*',
                               default=config.commands['StringDelimiters'],
                               help='Command string delimiters')
    command_group.add_argument('-ccm', '--command-conflict-mode', action='store', dest='command_conflict_mode',
                               default=config.commands['ConflictMode'].name,
                               help='Command conflict mode', choices=['Silent', 'Append', 'Exception'])

    client_group = parser.add_argument_group('client')
    client_mode = client_group.add_mutually_exclusive_group()
    client_mode.add_argument('--multi-client-mode', action='store_true',
                              help='Run server with support for both clients')
    client_mode.add_argument('--single-client-mode', action='store_true',
                              help='Run server with support for default client only')
    client_group.add_argument('--legacy-version', action='store',
                              type=int,
                              default=config.client['LegacyVersionChk'],
                              help='Legacy client version to identify legacy clients')
    client_group.add_argument('--vanilla-version', action='store',
                              type=int,
                              default=config.client['VanillaVersionChk'],
                              help='Vanilla client version to identify vanilla clients')
    client_group.add_argument('--default-version', action='store',
                              type=int,
                              default=config.client['DefaultVersionChk'],
                              help='Default version to identify clients when multi-client is off')
    client_group.add_argument('--default-client', action='store',
                              choices=['Legacy', 'Vanilla'],
                              default=config.client['DefaultClientType'].name,
                              help='Default client when multi-client is off')
    client_group.add_argument('-k', '--auth-key', action='store',
                              default='houdini',
                              help='Static key to use in place of the deprecated random key')

    args = parser.parse_args()

    database = {
        'Address': args.database_address,
        'Username': args.database_username,
        'Password': args.database_password,
        'Name': args.database_name
    }

    redis = {
        'Address': args.redis_address,
        'Port': args.redis_port
    }

    commands = {
        'Prefix': args.command_prefix,
        'StringDelimiters': args.command_string_delimiters,
        'ConflictMode': getattr(ConflictResolution, args.command_conflict_mode)
    }

    client = {
        'MultiClientSupport': True if args.multi_client_mode else False if args.single_client_mode
        else config.client['MultiClientSupport'],
        'LegacyVersionChk': args.legacy_version,
        'VanillaVersionChk': args.vanilla_version,

        'DefaultVersionChk': args.default_version,
        'DefaultClientType': getattr(ClientType, args.default_client),

        'AuthStaticKey': args.auth_key
    }

    server = {
        'Address': args.address or config.servers[args.server]['Address'],
        'Port': args.port or config.servers[args.server]['Port'],
        'World': True if args.world else False if args.login else None or config.servers[args.server]['World'],
        'Plugins': True if args.plugins and '*' in args.plugins
        else args.plugins or config.servers[args.server]['Plugins']
    }

    logging = {
        'General': args.logging_general_path or config.servers[args.server]['Logging']['General'],
        'Errors': args.logging_error_path or config.servers[args.server]['Logging']['Errors'],
        'Level': args.logging_level or config.servers[args.server]['Logging']['Level']
    }

    if server['World']:
        server.update({
            'Id': args.id or config.servers[args.server]['Id'],
            'Language': getattr(Language, args.language) if args.language else config.servers[args.server]['Language'],
            'Capacity': args.capacity or config.servers[args.server]['Capacity'],
            'CacheExpiry': args.cache_expiry or config.servers[args.server]['CacheExpiry']
        })

    server['Logging'] = logging

    factory_instance = Houdini(args.server,
                               database=database,
                               redis=redis,
                               commands=commands,
                               client=client,
                               server=server)
    try:
        asyncio.run(factory_instance.start())
    except KeyboardInterrupt:
        logger.info('Shutting down...')

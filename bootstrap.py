import asyncio
import logging
import argparse
import config

from houdini.houdini import Houdini
from houdini import ConflictResolution
from houdini import Language

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
                               server=server)
    try:
        asyncio.run(factory_instance.start())
    except KeyboardInterrupt:
        logger.info('Shutting down...')

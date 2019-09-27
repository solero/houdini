from houdini.constants import ConflictResolution, Language, ClientType

database = {
    'Address': 'localhost',
    'Username': 'postgres',
    'Password': 'password',
    'Name': 'houdini',
}

redis = {
    'Address': '127.0.0.1',
    'Port': 6379
}

commands = {
    'Prefix': ['!', '?', '.'],
    'StringDelimiters': ['"', "'"],
    'ConflictMode': ConflictResolution.Silent
}

client = {
    'MultiClientSupport': True,
    'LegacyVersionChk': 153,
    'VanillaVersionChk': 253,

    'DefaultVersionChk': 253,
    'DefaultClientType': ClientType.Vanilla,

    'AuthStaticKey': 'houdini'
}

servers = {
    'Login': {
        'Address': '0.0.0.0',
        'Port': 6112,
        'World': False,
        'Plugins': [
            'Example'
        ],
        'Logging': {
            'General': 'logs/login.log',
            'Errors': 'logs/login-errors.log',
            'Level': 'DEBUG'
        },
        'LoginFailureLimit': 5,
        'LoginFailureTimer': 3600,
        'KeyTTL': 3000
    },
    'Blizzard': {
        'Id': '100',
        'Address': '0.0.0.0',
        'Port': 9875,
        'Language': Language.En,
        'World': True,
        'Capacity': 200,
        'CacheExpiry': 3600,
        'Plugins': [
        ],
        'Logging': {
            'General': 'logs/blizzard.log',
            'Errors': 'logs/blizzard-errors.log',
            'Level': 'INFO'
        }
    }
}

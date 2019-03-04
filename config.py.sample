database = {
    "Address": "localhost",
    "Username": "postgres",
    "Password": "password",
    "Name": "houdini",
}

redis = {
    "Address": "127.0.0.1",
    "Port": 6379
}

servers = {
    "Login": {
        "Address": "0.0.0.0",
        "Port": 6112,
        "World": False,
        "Plugins": [
            "Example"
        ],
        "Logging": {
            "General": "logs/login.log",
            "Errors": "logs/login-errors.log",
            "Level": "DEBUG"
        },
        "LoginFailureLimit": 5,
        "LoginFailureTimer": 3600
    },
    "Wind": {
        "Id": "100",
        "Address": "0.0.0.0",
        "Port": 9875,
        "World": True,
        "Capacity": 200,
        "CacheExpiry": 3600,
        "Plugins": [
            "Commands",
            "Bot",
            "Rank"
        ],
        "Logging": {
            "General": "logs/wind.log",
            "Errors": "logs/wind-errors.log",
            "Level": "INFO"
        }
    }
}

tables = {
    "Four": [
        {"RoomId": 220, "Tables": [205, 206, 207]},
        {"RoomId": 221, "Tables": [200, 201, 202, 203, 204]}
    ],
    "Mancala": [
        {"RoomId": 111, "Tables": [100, 101, 102, 103, 104]}
    ],
    "Treasure": [
        {"RoomId": 422, "Tables": [300, 301, 302, 303, 304, 305, 306, 307]}
    ]
}

waddles = {
    "Sled": [
        {"RoomId": 230, "Waddles": [
            {"Id": 100, "Seats": 4},
            {"Id": 101, "Seats": 3},
            {"Id": 102, "Seats": 2},
            {"Id": 103, "Seats": 2}
        ]}
    ],
    "Card": [
        {"RoomId": 320, "Waddles": [
            {"Id": 200, "Seats": 2},
            {"Id": 201, "Seats": 2},
            {"Id": 202, "Seats": 2},
            {"Id": 203, "Seats": 2}
        ]}
    ],
    "CardFire": [
        {"RoomId": 812, "Waddles": [
            {"Id": 300, "Seats": 2},
            {"Id": 301, "Seats": 2},
            {"Id": 302, "Seats": 3},
            {"Id": 303, "Seats": 4}
        ]}
    ]
}

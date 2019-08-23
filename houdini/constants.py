import enum


class StatusField(enum.IntEnum):
    OpenedIglooViewer = 1
    ActiveIglooLayoutOpenFlag = 2
    PuffleTreasureInfographic = 512
    PlayerOptInAbTestDayZero = 1024
    PlayerSwapPuffle = 2048
    MoreThanTenPufflesBackyardMessage = 4096
    VisitBackyardFirstTime = 8192
    HasWalkedPuffleFirstTime = 65536
    HasWalkedPuffleSecondTime = 131072


class ConflictResolution(enum.Enum):
    Silent = 0
    Append = 1
    Exception = 2


class Language(enum.IntEnum):
    En = 1
    Pt = 2
    Fr = 4
    Es = 8
    De = 32
    Ru = 64


class ClientType(enum.Enum):
    Legacy = 'legacy'
    Vanilla = 'vanilla'

import asyncio
import re
from datetime import date, datetime

from gino.loader import ColumnLoader

from houdini import handlers
from houdini.constants import ClientType
from houdini.crypto import Crypto
from houdini.data import db
from houdini.data.music import PenguinTrack, TrackLike
from houdini.handlers import XTPacket


class SoundStudio:
    StudioRoomId = 120
    DeckRoomId = 898

    def __init__(self, server):
        self.server = server

        self.broadcasting = False

        self.playlist = []
        self.current_track = None

        self.room = server.rooms[SoundStudio.StudioRoomId]

    async def broadcast_next_track(self):
        await self.get_tracks()
        if not self.room.penguins_by_id or not self.playlist:
            await self.send_broadcasted_tracks()
            await self.stop_broadcasting()
        else:
            next_track = self.playlist[0]
            if self.current_track is not None:
                while next_track.id != self.current_track.id:
                    self.playlist.append(self.playlist.pop(0))
                    if next_track.id == self.playlist[0].id:
                        break
                    next_track = self.playlist[0]
                self.playlist.append(self.playlist.pop(0))

            self.current_track = self.playlist[0]
            await self.send_broadcasted_tracks()

    async def broadcast_tracks(self):
        while self.broadcasting:
            await self.broadcast_next_track()

            if self.broadcasting:
                song_length = determine_song_length(self.current_track.pattern)
                await asyncio.sleep(song_length)

    async def start_broadcasting(self):
        if not self.broadcasting:
            self.broadcasting = True
            asyncio.create_task(self.broadcast_tracks())

    async def stop_broadcasting(self):
        if self.broadcasting:
            self.broadcasting = False
            self.current_track = None

    async def get_tracks(self):
        self.playlist = []
        likes = db.func.count(TrackLike.track_id)
        tracks_query = db.select([PenguinTrack, likes]) \
            .select_from(PenguinTrack.outerjoin(TrackLike)) \
            .where((PenguinTrack.owner_id.in_(tuple(self.room.penguins_by_id.keys())))
                   & (PenguinTrack.sharing == True)) \
            .group_by(PenguinTrack.id).gino.load(PenguinTrack.load(likes=ColumnLoader(likes)))
        async with db.transaction():
            async for track in tracks_query.iterate():
                self.playlist.append(track)

    async def send_broadcasted_tracks(self):
        broadcasted_tracks = await self.get_broadcasted_tracks()
        for penguin in self.room.penguins_by_id.values():
            playlist_position = get_playlist_position(penguin)
            await penguin.send_xt('broadcastingmusictracks', len(self.playlist),
                                  playlist_position, broadcasted_tracks)

    async def get_broadcasted_tracks(self):
        penguins = self.server.penguins_by_id
        broadcasted_tracks = ','.join(f'{track.owner_id}|{penguins[track.owner_id].safe_name}|'
                                      f'{track.owner_id}|{track.id}|{track.likes}'
                                      for track in self.playlist)
        return broadcasted_tracks


async def get_player_tracks(p):
    player_tracks = []
    likes = db.func.count(TrackLike.track_id)
    tracks_query = db.select([PenguinTrack, likes])\
        .select_from(PenguinTrack.outerjoin(TrackLike))\
        .where(PenguinTrack.owner_id == p.id)\
        .group_by(PenguinTrack.id).gino.load(PenguinTrack.load(likes=ColumnLoader(likes)))
    async with db.transaction():
        async for track in tracks_query.iterate():
            player_tracks.append(f'{track.id}|{track.name}|{int(track.sharing)}|{track.likes}')
    return player_tracks


async def get_shared_tracks(p):
    shared_tracks = []
    likes = db.func.count(TrackLike.track_id)
    tracks_query = db.select([PenguinTrack, likes])\
        .select_from(PenguinTrack.outerjoin(TrackLike))\
        .where((PenguinTrack.owner_id.in_(tuple(p.server.penguins_by_id.keys())) & (PenguinTrack.sharing == True)))\
        .group_by(PenguinTrack.id).gino.load(PenguinTrack.load(likes=ColumnLoader(likes)))
    async with db.transaction():
        async for track in tracks_query.iterate():
            penguin = p.server.penguins_by_id[track.owner_id]
            shared_tracks.append(f'{penguin.id}|{penguin.safe_name}|{track.id}|{track.likes}')
    return shared_tracks


async def get_track(owner_id, track_id):
    likes = db.func.count(TrackLike.track_id)
    track = await db.select([PenguinTrack, likes])\
        .select_from(PenguinTrack.outerjoin(TrackLike))\
        .where((PenguinTrack.owner_id == owner_id) & (PenguinTrack.id == track_id))\
        .group_by(PenguinTrack.id).gino.load(PenguinTrack.load(likes=ColumnLoader(likes))).first()
    return track


async def can_like_track(p, owner_id: int, track_id: int):
    yesterday = datetime.combine(date.today(), datetime.min.time())
    like = await db.select(TrackLike) \
        .select_from(TrackLike.outerjoin(PenguinTrack)) \
        .where((PenguinTrack.owner_id == owner_id)
               & (TrackLike.penguin_id == p.id)
               & (TrackLike.track_id == track_id)
               & (TrackLike.date > yesterday)).gino.first()
    return like is None


def get_playlist_position(p):
    for position, track in enumerate(p.server.music.playlist):
        if track.owner_id == p.id:
            return position + 1
    return -1


def encode_music_track(track_pattern):
    encoded_track_pattern = track_pattern[::-1]
    encoded_track_pattern = Crypto.hash(encoded_track_pattern)
    return encoded_track_pattern[16:32] + encoded_track_pattern[0:16]


def determine_song_length(track_pattern):
    if track_pattern == '0':
        return 0
    track_length = track_pattern.split(',')[-1]
    track_length = track_length.split('|')[1]
    return int(track_length, 16) // 1000


@handlers.boot
async def music_service_start(server):
    server.music = SoundStudio(server)


@handlers.handler(XTPacket('musictrack', 'broadcastingmusictracks'), client=ClientType.Vanilla)
@handlers.player_in_room(SoundStudio.StudioRoomId)
async def handle_broadcasting_tracks(p):
    if not p.server.music.broadcasting:
        await p.server.music.start_broadcasting()
    elif not p.server.music.playlist:
        await p.send_xt('broadcastingmusictracks', 0, -1, '')
    else:
        playlist_position = get_playlist_position(p)
        broadcasted_tracks = await p.server.music.get_broadcasted_tracks()
        await p.send_xt('broadcastingmusictracks', len(p.server.music.playlist),
                        playlist_position, broadcasted_tracks)


@handlers.handler(XTPacket('musictrack', 'getmymusictracks'), client=ClientType.Vanilla)
async def handle_get_my_music_tracks(p):
    player_tracks = await get_player_tracks(p)
    await p.send_xt('getmymusictracks', len(player_tracks), ','.join(player_tracks))


@handlers.handler(XTPacket('musictrack', 'getsharedmusictracks'), client=ClientType.Vanilla)
@handlers.player_in_room(SoundStudio.StudioRoomId, SoundStudio.DeckRoomId)
async def handle_get_shared_music_tracks(p):
    shared_tracks = await get_shared_tracks(p)
    await p.send_xt('getsharedmusictracks', len(shared_tracks), ','.join(shared_tracks))


@handlers.handler(XTPacket('musictrack', 'loadmusictrack'), client=ClientType.Vanilla)
@handlers.player_in_room(SoundStudio.StudioRoomId, SoundStudio.DeckRoomId)
async def handle_load_music_track(p, owner_id: int, track_id: int):
    track = await get_track(owner_id, track_id)
    encoded_track_pattern = encode_music_track(track.pattern)
    await p.send_xt('loadmusictrack', track.id, track.name, int(track.sharing), track.pattern,
                    encoded_track_pattern, track.likes)


@handlers.handler(XTPacket('musictrack', 'savemymusictrack'), client=ClientType.Vanilla)
@handlers.player_in_room(SoundStudio.DeckRoomId)
@handlers.cooldown()
async def handle_save_my_music_track(p, track_name, track_pattern, track_hash):
    encoded_track_pattern = encode_music_track(track_pattern)
    song_length = determine_song_length(track_pattern)
    if encoded_track_pattern != track_hash or song_length > 180:
        return

    pattern_regex = r'^([0-9a-fA-F]+,[0-9a-fA-F]+\|){0,1000}[0-9a-fA-F]+,FFFF\|[0-9a-fA-F]+$'
    if not re.match(pattern_regex, track_pattern):
        return

    track_count = await db.select([db.func.count(PenguinTrack.id)])\
        .where(PenguinTrack.owner_id == p.id).gino.scalar()
    if track_count >= 12:
        return
    track = await PenguinTrack.create(owner_id=p.id, name=track_name, pattern=track_pattern)
    await p.send_xt('savemymusictrack', track.id)


@handlers.handler(XTPacket('musictrack', 'refreshmytracklikes'), client=ClientType.Vanilla)
@handlers.player_in_room(SoundStudio.StudioRoomId, SoundStudio.DeckRoomId)
async def handle_refresh_my_track_likes(p):
    likes = db.func.count(TrackLike.track_id)
    track_likes_query = db.select([PenguinTrack.id, likes])\
        .select_from(PenguinTrack.outerjoin(TrackLike))\
        .where(PenguinTrack.owner_id == p.id)\
        .group_by(PenguinTrack.id).gino.load(PenguinTrack.load(likes=ColumnLoader(likes)))
    async with db.transaction():
        async for track in track_likes_query.iterate():
            await p.send_xt('getlikecountfortrack', p.id, track.id, track.likes)


@handlers.handler(XTPacket('musictrack', 'sharemymusictrack'), client=ClientType.Vanilla)
@handlers.player_in_room(SoundStudio.StudioRoomId, SoundStudio.DeckRoomId)
@handlers.cooldown()
async def handle_share_my_music_track(p, track_id: int, sharing: int):
    if sharing:
        await PenguinTrack.update.values(sharing=False)\
            .where(PenguinTrack.owner_id == p.id).gino.status()
    await PenguinTrack.update.values(sharing=bool(sharing))\
        .where((PenguinTrack.id == track_id)
               & (PenguinTrack.owner_id == p.id)).gino.status()
    if p.server.music.current_track is not None and \
            p.server.music.current_track.id == track_id and \
            p.server.music.current_track.owner_id == p.id:
        await p.server.music.broadcast_next_track()
    await p.send_xt('sharemymusictrack', 1)


@handlers.handler(XTPacket('musictrack', 'deletetrack'), client=ClientType.Vanilla)
@handlers.player_in_room(SoundStudio.StudioRoomId, SoundStudio.DeckRoomId)
async def handle_delete_track(p, track_id: int):
    await PenguinTrack.delete.where((PenguinTrack.id == track_id)
                                    & (PenguinTrack.owner_id == p.id)).gino.status()
    await p.send_xt('deletetrack', 1)


@handlers.handler(XTPacket('musictrack', 'canliketrack'), client=ClientType.Vanilla)
@handlers.player_in_room(SoundStudio.StudioRoomId, SoundStudio.DeckRoomId)
async def handle_can_like_track(p, owner_id: int, track_id: int):
    can_like = await can_like_track(p, owner_id, track_id)
    await p.send_xt('canliketrack', track_id, int(can_like))


@handlers.handler(XTPacket('musictrack', 'liketrack'), client=ClientType.Vanilla)
@handlers.player_in_room(SoundStudio.StudioRoomId, SoundStudio.DeckRoomId)
@handlers.cooldown()
async def handle_like_track(p, owner_id: int, track_id: int):
    can_like = await can_like_track(p, owner_id, track_id)
    if can_like:
        await TrackLike.create(penguin_id=p.id, track_id=track_id)
        like_count = await db.select([db.func.count(TrackLike.track_id)])\
            .where(TrackLike.track_id == track_id).gino.scalar()
        await p.room.send_xt('liketrack', owner_id, track_id, like_count)
